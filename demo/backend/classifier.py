"""
Classifier module: loads all 3 trained models (TF-IDF+LR, BERT, RoBERTa)
and exposes a unified `classify_all(text)` interface.

Reuses the privacy-aware preprocessing from scripts/data_preprocessing.py
so inference-time inputs match the training distribution.
"""
from __future__ import annotations

import pickle
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


# Project root (three levels up: demo/backend/classifier.py -> project root)
ROOT = Path(__file__).resolve().parents[2]

LABELS = ["low", "medium", "high"]
LABEL2ID = {"low": 0, "medium": 1, "high": 2}


# Privacy patterns — copied verbatim from scripts/data_preprocessing.py so
# the demo tokenises text exactly the way the training pipeline did.
PRIVACY_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+\d{1,3}\s?)?[\(\d][\d\s\(\)\-\.]{8,15}\b"),
    "url": re.compile(r"https?://[^\s]+"),
    "number": re.compile(r"\b\d{4,}\b"),
    "amount": re.compile(r"\$\d+\.?\d*|\€\d+\.?\d*|£\d+\.?\d*"),
}


def clean_text(text: str) -> str:
    """Anonymise PII and normalise whitespace. Matches training preprocessing."""
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = PRIVACY_PATTERNS["email"].sub("<EMAIL>", text)
    text = PRIVACY_PATTERNS["phone"].sub("<PHONE>", text)
    text = PRIVACY_PATTERNS["url"].sub("<URL>", text)
    text = PRIVACY_PATTERNS["amount"].sub("<AMOUNT>", text)
    text = PRIVACY_PATTERNS["number"].sub("<NUMBER>", text)
    return text


@dataclass
class Prediction:
    label: str
    scores: Dict[str, float]

    def to_dict(self) -> dict:
        return {"label": self.label, "scores": self.scores}


class TransformerClassifier:
    """Wraps a HuggingFace sequence-classification checkpoint."""

    MAX_LEN = 64

    def __init__(self, model_path: Path, display_name: str):
        self.display_name = display_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        self.model = AutoModelForSequenceClassification.from_pretrained(str(model_path))
        self.model.to(self.device)
        self.model.eval()

        # Build an id2label map using the model's config, falling back to our
        # canonical LABELS order if the config is missing / numeric.
        cfg = self.model.config
        if getattr(cfg, "id2label", None) and all(
            isinstance(v, str) for v in cfg.id2label.values()
        ):
            self.id2label = {int(k): v.lower() for k, v in cfg.id2label.items()}
        else:
            self.id2label = {i: lbl for i, lbl in enumerate(LABELS)}

    @torch.no_grad()
    def predict(self, text: str) -> Prediction:
        cleaned = clean_text(text)
        enc = self.tokenizer(
            cleaned,
            truncation=True,
            padding=True,
            max_length=self.MAX_LEN,
            return_tensors="pt",
        ).to(self.device)
        logits = self.model(**enc).logits[0]
        probs = torch.softmax(logits, dim=-1).cpu().numpy()
        scores = {self.id2label[i]: float(probs[i]) for i in range(len(probs))}
        # Always return in canonical low/medium/high order.
        scores = {lbl: scores.get(lbl, 0.0) for lbl in LABELS}
        label = max(scores, key=scores.get)
        return Prediction(label=label, scores=scores)


class TfidfClassifier:
    """TF-IDF + Logistic Regression baseline loaded from pickles."""

    def __init__(self, vectorizer_path: Path, clf_path: Path, display_name: str = "TF-IDF + LR"):
        self.display_name = display_name
        with open(vectorizer_path, "rb") as f:
            self.vectorizer = pickle.load(f)
        with open(clf_path, "rb") as f:
            self.clf = pickle.load(f)

        # sklearn stores classes_ as ndarray of strings (e.g. ['high','low','medium'])
        self.classes: List[str] = [str(c).lower() for c in self.clf.classes_]

    def predict(self, text: str) -> Prediction:
        cleaned = clean_text(text)
        X = self.vectorizer.transform([cleaned])
        probs = self.clf.predict_proba(X)[0]
        raw_scores = {self.classes[i]: float(probs[i]) for i in range(len(probs))}
        scores = {lbl: raw_scores.get(lbl, 0.0) for lbl in LABELS}
        label = max(scores, key=scores.get)
        return Prediction(label=label, scores=scores)


class ModelHub:
    """Loads all available models and classifies in one shot."""

    # Order controls display order in the frontend comparison panel.
    MODEL_KEYS = ["tfidf", "bert", "roberta"]

    def __init__(self, project_root: Path = ROOT):
        self.project_root = project_root
        self.models: Dict[str, object] = {}
        self._load_all()

    def _load_all(self) -> None:
        tfidf_vec = self.project_root / "models" / "tfidf_vectorizer.pkl"
        tfidf_clf = self.project_root / "models" / "baseline_lr.pkl"
        if tfidf_vec.exists() and tfidf_clf.exists():
            try:
                self.models["tfidf"] = TfidfClassifier(tfidf_vec, tfidf_clf, "TF-IDF + LR")
                print(f"[classifier] Loaded TF-IDF baseline from {tfidf_vec.name}")
            except Exception as e:
                print(f"[classifier] Failed to load TF-IDF model: {e}")

        bert_dir = self.project_root / "results" / "bert-base-uncased" / "best_model"
        if bert_dir.exists():
            try:
                self.models["bert"] = TransformerClassifier(bert_dir, "BERT")
                print(f"[classifier] Loaded BERT from {bert_dir}")
            except Exception as e:
                print(f"[classifier] Failed to load BERT: {e}")

        roberta_dir = self.project_root / "results" / "roberta-base" / "best_model"
        if roberta_dir.exists():
            try:
                self.models["roberta"] = TransformerClassifier(roberta_dir, "RoBERTa")
                print(f"[classifier] Loaded RoBERTa from {roberta_dir}")
            except Exception as e:
                print(f"[classifier] Failed to load RoBERTa: {e}")

        if not self.models:
            raise RuntimeError(
                "No models could be loaded. Check that results/*/best_model and "
                "models/*.pkl exist in the project root."
            )

    @property
    def loaded_keys(self) -> List[str]:
        return [k for k in self.MODEL_KEYS if k in self.models]

    def classify_all(self, text: str) -> Dict[str, dict]:
        """Run every loaded model on `text`. Returns {model_key: {label, scores}}."""
        out: Dict[str, dict] = {}
        for key in self.loaded_keys:
            pred = self.models[key].predict(text)
            out[key] = {
                "display_name": self.models[key].display_name,
                **pred.to_dict(),
            }
        return out


_HUB: ModelHub | None = None


def get_hub() -> ModelHub:
    """Singleton accessor — loads models once per process."""
    global _HUB
    if _HUB is None:
        _HUB = ModelHub()
    return _HUB


if __name__ == "__main__":
    hub = get_hub()
    samples = [
        "URGENT: Your account has been compromised. Verify now!",
        "Dinner plans tonight at 8pm?",
        "50% off all items this weekend — shop now",
    ]
    for s in samples:
        print(f"\n{s!r}")
        for model_key, result in hub.classify_all(s).items():
            scores = " ".join(f"{k}={v:.2f}" for k, v in result["scores"].items())
            print(f"  [{model_key:8}] -> {result['label']:6} ({scores})")
