import argparse
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    get_linear_schedule_with_warmup,
)
from sklearn.metrics import f1_score, classification_report

LABEL2ID = {'low': 0, 'medium': 1, 'high': 2}
ID2LABEL  = {v: k for k, v in LABEL2ID.items()}
NUM_LABELS = 3




class NotificationDataset(Dataset):
    """Tokenises a list of notification texts + urgency labels."""

    def __init__(self, texts, labels, tokenizer, max_len: int):
        self.encodings = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=max_len,
            return_tensors='pt',
        )
        self.labels = torch.tensor([LABEL2ID[l] for l in labels], dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return {k: v[idx] for k, v in self.encodings.items()}, self.labels[idx]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compute_class_weights(labels, device):
    """Inverse-frequency class weights to handle mild class imbalance."""
    counts  = np.bincount([LABEL2ID[l] for l in labels], minlength=NUM_LABELS).astype(float)
    weights = len(labels) / (NUM_LABELS * counts)
    return torch.tensor(weights, dtype=torch.float32).to(device)


def train_epoch(model, loader, optimizer, scheduler, loss_fn, device):
    model.train()
    total_loss = 0.0
    for batch, labels in loader:
        batch  = {k: v.to(device) for k, v in batch.items()}
        labels = labels.to(device)
        optimizer.zero_grad()
        loss = loss_fn(model(**batch).logits, labels)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()
        total_loss += loss.item()
    return total_loss / len(loader)


@torch.no_grad()
def evaluate(model, loader, loss_fn, device):
    """Returns macro-F1, mean loss, predictions, true labels, and softmax probs."""
    model.eval()
    all_preds, all_labels, all_probs = [], [], []
    total_loss = 0.0
    for batch, labels in loader:
        batch  = {k: v.to(device) for k, v in batch.items()}
        labels = labels.to(device)
        logits = model(**batch).logits
        total_loss += loss_fn(logits, labels).item()
        probs = torch.softmax(logits, dim=-1)
        all_probs.append(probs.cpu().numpy())
        all_preds.extend(logits.argmax(dim=-1).cpu().tolist())
        all_labels.extend(labels.cpu().tolist())
    macro_f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)
    return macro_f1, total_loss / len(loader), all_preds, all_labels, np.vstack(all_probs)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Fine-tune a transformer for notification urgency classification'
    )
    parser.add_argument('--model_name', default='bert-base-uncased',
                        help='HuggingFace model name or local path')
    parser.add_argument('--data_dir',   default='data/processed',
                        help='Directory containing notifications_{train,val,test}.csv')
    parser.add_argument('--output_dir', default='results/bert-base-uncased',
                        help='Where to save the model checkpoint and result files')
    parser.add_argument('--epochs',     type=int,   default=5)
    parser.add_argument('--batch_size', type=int,   default=16)
    parser.add_argument('--lr',         type=float, default=2e-5)
    parser.add_argument('--max_len',    type=int,   default=64,
                        help='Max tokeniser length (64 covers ~98% of notifications)')
    parser.add_argument('--patience',   type=int,   default=2,
                        help='Early stopping patience (epochs without val-F1 improvement)')
    parser.add_argument('--seed',       type=int,   default=42)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'Device      : {device}')
    print(f'Model       : {args.model_name}')
    print(f'Output dir  : {args.output_dir}')

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    data_dir = Path(args.data_dir)
    train_df = pd.read_csv(data_dir / 'notifications_train.csv')
    val_df   = pd.read_csv(data_dir / 'notifications_val.csv')
    test_df  = pd.read_csv(data_dir / 'notifications_test.csv')

    for df in (train_df, val_df, test_df):
        df['urgency'] = df['urgency'].str.lower().str.strip()

    X_train = train_df['notif_content'].fillna('').tolist()
    y_train = train_df['urgency'].tolist()
    X_val   = val_df['notif_content'].fillna('').tolist()
    y_val   = val_df['urgency'].tolist()
    X_test  = test_df['notif_content'].fillna('').tolist()
    y_test  = test_df['urgency'].tolist()

    print(f'Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}')

    # ------------------------------------------------------------------
    # Tokenise & build DataLoaders
    # ------------------------------------------------------------------
    tokenizer  = AutoTokenizer.from_pretrained(args.model_name)
    train_ds   = NotificationDataset(X_train, y_train, tokenizer, args.max_len)
    val_ds     = NotificationDataset(X_val,   y_val,   tokenizer, args.max_len)
    test_ds    = NotificationDataset(X_test,  y_test,  tokenizer, args.max_len)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,  num_workers=2)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch_size * 2, num_workers=2)
    test_loader  = DataLoader(test_ds,  batch_size=args.batch_size * 2, num_workers=2)

    # ------------------------------------------------------------------
    # Model, loss, optimiser, scheduler
    # ------------------------------------------------------------------
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    model.to(device)

    class_weights = compute_class_weights(y_train, device)
    loss_fn       = nn.CrossEntropyLoss(weight=class_weights)

    optimizer     = AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps   = len(train_loader) * args.epochs
    scheduler     = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(0.1 * total_steps),
        num_training_steps=total_steps,
    )

    # ------------------------------------------------------------------
    # Training loop with early stopping
    # ------------------------------------------------------------------
    best_val_f1     = 0.0
    patience_count  = 0
    metrics_history = []

    print('\n--- Training ---')
    for epoch in range(1, args.epochs + 1):
        train_loss = train_epoch(model, train_loader, optimizer, scheduler, loss_fn, device)
        val_f1, val_loss, _, _, _ = evaluate(model, val_loader, loss_fn, device)

        row = {
            'epoch':        epoch,
            'train_loss':   round(train_loss, 4),
            'val_loss':     round(val_loss,   4),
            'val_macro_f1': round(val_f1,     4),
        }
        metrics_history.append(row)
        print(f'Epoch {epoch}/{args.epochs}  train_loss={train_loss:.4f}  '
              f'val_loss={val_loss:.4f}  val_f1={val_f1:.4f}')

        if val_f1 > best_val_f1:
            best_val_f1    = val_f1
            patience_count = 0
            model.save_pretrained(out_dir / 'best_model')
            tokenizer.save_pretrained(out_dir / 'best_model')
            print(f'  -> New best val_f1={best_val_f1:.4f}  checkpoint saved.')
        else:
            patience_count += 1
            print(f'  -> No improvement ({patience_count}/{args.patience})')
            if patience_count >= args.patience:
                print('Early stopping triggered.')
                break

    # ------------------------------------------------------------------
    # Evaluate best checkpoint on test set
    # ------------------------------------------------------------------
    print('\n--- Test evaluation ---')
    best_model = AutoModelForSequenceClassification.from_pretrained(out_dir / 'best_model').to(device)
    test_f1, test_loss, test_preds, test_true, test_probs = \
        evaluate(best_model, test_loader, loss_fn, device)

    print(f'Test macro-F1 : {test_f1:.4f}')
    print(classification_report(
        test_true, test_preds,
        target_names=[ID2LABEL[i] for i in range(NUM_LABELS)],
        zero_division=0,
    ))

    # ------------------------------------------------------------------
    # Persist results
    # ------------------------------------------------------------------
    summary = {
        'model':             args.model_name,
        'best_val_macro_f1': round(best_val_f1, 4),
        'test_macro_f1':     round(test_f1, 4),
        'epochs_run':        len(metrics_history),
        'hyperparams':       vars(args),
        'history':           metrics_history,
    }
    metrics_path = out_dir / 'val_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'Metrics saved   -> {metrics_path}')

    # test_predictions.csv: used by notebooks/04_evaluation.ipynb
    pred_df = pd.DataFrame({
        'text':        X_test,
        'true_label':  [ID2LABEL[i] for i in test_true],
        'pred_label':  [ID2LABEL[i] for i in test_preds],
        'prob_low':    test_probs[:, LABEL2ID['low']],
        'prob_medium': test_probs[:, LABEL2ID['medium']],
        'prob_high':   test_probs[:, LABEL2ID['high']],
    })
    preds_path = out_dir / 'test_predictions.csv'
    pred_df.to_csv(preds_path, index=False)
    print(f'Predictions saved -> {preds_path}')


if __name__ == '__main__':
    main()
