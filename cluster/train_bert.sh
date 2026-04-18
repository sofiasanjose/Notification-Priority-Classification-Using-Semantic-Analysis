#!/bin/bash
# =============================================================================
# SLURM Job: Fine-tune BERT for Notification Priority Classification
# IE University HPC Cluster — gpu partition (haskell node)
# =============================================================================
#
# Submit:    sbatch ~/nlp-project/cluster/train_bert.sh
# Monitor:   squeue -u $USER
# Read log:  cat ~/nlp-project/logs/bert_<JOBID>.log
#
# After the job finishes, copy results back to your laptop:
#   scp -r nlp10@10.205.20.10:~/nlp-project/results/ ./results/
# =============================================================================

#SBATCH --job-name=nlp10-bert
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/home/%u/nlp-project/logs/bert_%j.log
#SBATCH --error=/home/%u/nlp-project/logs/bert_%j.log

# ---------------------------------------------------------------------------
# 0. Paths & environment
# ---------------------------------------------------------------------------
PROJECT_DIR="$HOME/nlp-project"
CONDA_ENV="nlp"

cd "$PROJECT_DIR" || { echo "ERROR: $PROJECT_DIR not found. Did you scp the project?"; exit 1; }

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

echo "============================================================"
echo " NLP10 — BERT Training Job"
echo " Node     : $(hostname)"
echo " Date     : $(date)"
echo " Job ID   : $SLURM_JOB_ID"
echo " GPU(s)   : $CUDA_VISIBLE_DEVICES"
echo " Work dir : $(pwd)"
echo "============================================================"

# Activate conda environment
source "$HOME/miniforge3/bin/activate" "$CONDA_ENV" 2>/dev/null \
    || { echo "ERROR: conda env '$CONDA_ENV' not found. Run cluster/setup_env.sh first."; exit 1; }

echo "Python    : $(which python)"
echo "Torch     : $(python -c 'import torch; print(torch.__version__)')"
echo "CUDA avail: $(python -c 'import torch; print(torch.cuda.is_available())')"
echo "GPU name  : $(python -c 'import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\")')"
echo "------------------------------------------------------------"

# ---------------------------------------------------------------------------
# 1. Fine-tune BERT (bert-base-uncased)
# ---------------------------------------------------------------------------
echo ""
echo "[1/2] Training bert-base-uncased ..."
echo ""

python scripts/train_transformer.py \
    --model_name  bert-base-uncased \
    --data_dir    data/processed \
    --output_dir  results/bert-base-uncased \
    --epochs      5 \
    --batch_size  16 \
    --lr          2e-5 \
    --max_len     64 \
    --patience    2 \
    --seed        42

BERT_EXIT=$?

if [ $BERT_EXIT -ne 0 ]; then
    echo "ERROR: BERT training failed (exit code $BERT_EXIT)"
    exit $BERT_EXIT
fi

echo ""
echo "BERT training complete."

# ---------------------------------------------------------------------------
# 2. Fine-tune RoBERTa (roberta-base) — runs sequentially on the same GPU
#    Comment this block out if you only want BERT results.
# ---------------------------------------------------------------------------
echo ""
echo "[2/2] Training roberta-base ..."
echo ""

python scripts/train_transformer.py \
    --model_name  roberta-base \
    --data_dir    data/processed \
    --output_dir  results/roberta-base \
    --epochs      5 \
    --batch_size  16 \
    --lr          2e-5 \
    --max_len     64 \
    --patience    2 \
    --seed        42

ROBERTA_EXIT=$?

if [ $ROBERTA_EXIT -ne 0 ]; then
    echo "WARNING: RoBERTa training failed (exit code $ROBERTA_EXIT)"
    echo "BERT results are still valid — check results/bert-base-uncased/"
fi

# ---------------------------------------------------------------------------
# 3. Summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " Job finished: $(date)"
echo ""
echo " Results saved to:"
echo "   $PROJECT_DIR/results/bert-base-uncased/val_metrics.json"
echo "   $PROJECT_DIR/results/bert-base-uncased/test_predictions.csv"
[ $ROBERTA_EXIT -eq 0 ] && echo "   $PROJECT_DIR/results/roberta-base/val_metrics.json"
[ $ROBERTA_EXIT -eq 0 ] && echo "   $PROJECT_DIR/results/roberta-base/test_predictions.csv"
echo ""
echo " Copy to your laptop:"
echo "   scp -r nlp10@10.205.20.10:~/nlp-project/results/ ./results/"
echo "============================================================"
