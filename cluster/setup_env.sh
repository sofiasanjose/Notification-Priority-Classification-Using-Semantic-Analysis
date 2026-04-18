#!/bin/bash
# =============================================================================
# One-time environment setup on the IE University HPC cluster
# Run this ONCE after SSHing in for the first time.
#
# Usage (from the cluster login node):
#   bash ~/nlp-project/cluster/setup_env.sh
# =============================================================================

set -e   # exit immediately if any command fails

PROJECT_DIR="$HOME/nlp-project"
MINIFORGE_DIR="$HOME/miniforge3"
CONDA_ENV="nlp"

echo "============================================================"
echo " NLP10 — Cluster Environment Setup"
echo " Node : $(hostname)  |  Date : $(date)"
echo "============================================================"

# ---------------------------------------------------------------------------
# 1. Install Miniforge (if not already present)
# ---------------------------------------------------------------------------
if [ -d "$MINIFORGE_DIR" ]; then
    echo "[1/4] Miniforge already installed at $MINIFORGE_DIR — skipping."
else
    echo "[1/4] Installing Miniforge to $MINIFORGE_DIR ..."
    wget -q https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh \
        -O /tmp/Miniforge3.sh
    bash /tmp/Miniforge3.sh -b -p "$MINIFORGE_DIR"
    rm /tmp/Miniforge3.sh
    echo "Miniforge installed."
fi

# Activate conda for this session
eval "$($MINIFORGE_DIR/bin/conda shell.bash hook)"
conda init bash 2>/dev/null || true

# ---------------------------------------------------------------------------
# 2. Create the project conda environment
# ---------------------------------------------------------------------------
if conda env list | grep -q "^$CONDA_ENV "; then
    echo "[2/4] Conda env '$CONDA_ENV' already exists — skipping creation."
else
    echo "[2/4] Creating conda env '$CONDA_ENV' with Python 3.11 ..."
    conda create -n "$CONDA_ENV" python=3.11 -y
fi

conda activate "$CONDA_ENV"

# ---------------------------------------------------------------------------
# 3. Install Python packages
# ---------------------------------------------------------------------------
echo "[3/4] Installing Python packages ..."

# PyTorch with CUDA 12.4 support (matches the RTX 6000 Ada on haskell)
pip install torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu124 \
    --quiet

# HuggingFace + ML stack
pip install \
    transformers>=4.30.0 \
    scikit-learn>=1.3.0 \
    pandas>=2.0.0 \
    numpy>=1.24.0 \
    evaluate>=0.4.0 \
    --quiet

echo "Packages installed."

# ---------------------------------------------------------------------------
# 4. Create project directory structure
# ---------------------------------------------------------------------------
echo "[4/4] Setting up project directories ..."
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/results/bert-base-uncased"
mkdir -p "$PROJECT_DIR/results/roberta-base"
mkdir -p "$PROJECT_DIR/models"

# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " Setup complete! Verification:"
echo "   Python  : $(python --version)"
echo "   Torch   : $(python -c 'import torch; print(torch.__version__)')"
echo "   CUDA    : $(python -c 'import torch; print(torch.cuda.is_available())')"
echo ""
echo " Next step — submit the training job:"
echo "   sbatch ~/nlp-project/cluster/train_bert.sh"
echo "============================================================"
