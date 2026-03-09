# Notification Priority Classification Using Semantic Analysis

**Authors:** Oliver Holmes, Sofia Bonoan, Denis Sokolov, Gonzalo Fernández  
**Course:** Natural Language Processing  
**Institution:** IE University  
**Date:** March 9, 2026

## 📋 Project Overview

This project develops a transformer-based machine learning system to automatically classify smartphone notifications by urgency level (High, Medium, Low) using semantic analysis of notification text content. The system addresses notification overload by intelligently prioritizing time-sensitive and important notifications based on their semantic meaning.

## 🎯 Research Focus

- **Content-based urgency detection** using notification text analysis
- **Transformer model fine-tuning** (BERT/RoBERTa) for 3-class classification  
- **Privacy-preserving preprocessing** with automatic anonymization
- **Semantic pattern analysis** of urgency indicators in notification language

## 📊 Dataset Information

**Source:** Curated NLP Notifications Dataset (Real notification text content)  
**Original Size:** 742 notification samples  
**Processed Size:** 737 notification samples (5 removed during cleaning)  
**Features:** timestamp, app_name, notif_type, notif_content, urgency  

**Urgency Distribution:**
- **High:** ~258 notifications (35.0%) - urgent/time-sensitive  
- **Medium:** ~196 notifications (26.6%) - important but can wait
- **Low:** ~283 notifications (38.4%) - informational/promotional

**Stratified Splits:**
- **Training:** 519 samples (70.4%)
- **Validation:** 109 samples (14.8%)  
- **Test:** 109 samples (14.8%)

## 🗂️ Repository Structure

```
.
├── README.md                           # Project overview and documentation
├── requirements.txt                    # Python dependencies for semantic analysis
├── .gitignore                         # Git ignore rules
├── NLP_Notifications_final.dataset.csv  # Curated notification dataset
│
├── data/                              # Data directory
│   ├── raw/                           # Raw data storage (empty - using curated dataset)
│   └── processed/                     # Preprocessed train/validation/test splits
│       ├── notifications_train.csv    # Training data (519 samples)
│       ├── notifications_val.csv      # Validation data (109 samples)
│       └── notifications_test.csv     # Test data (109 samples)
│
├── scripts/                           # Data processing pipeline
│   └── data_preprocessing.py          # Privacy-aware preprocessing with anonymization
│
├── notebooks/                         # Analysis and exploration
│   └── 01_data_exploration.ipynb     # Dataset analysis and semantic pattern discovery
│
├── models/                            # Model storage (ready for training)
└── results/                           # Experiment results (ready for evaluation)
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Navigate to the project directory
cd Notification-Priority-Classification-Using-Semantic-Analysis

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or: venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Data Preprocessing

The curated dataset (`NLP_Notifications_final.dataset.csv`) contains real notification text content. 
To create the train/validation/test splits:

```bash
# Run the preprocessing pipeline
python scripts/data_preprocessing.py --input NLP_Notifications_final.dataset.csv

# This creates privacy-anonymized splits in data/processed/
```

### 3. Data Exploration

```bash
# Start Jupyter notebook
jupyter notebook

# Open notebooks/01_data_exploration.ipynb
# Run all cells to analyze the dataset and semantic patterns
```
## 🔍 Semantic Analysis Features

### Text-Based Urgency Detection
- **Time-sensitive language:** "now", "urgent", "expires", "deadline"
- **Action-required words:** "verify", "confirm", "failed", "error"  
- **Punctuation patterns:** Exclamation marks, capitalization
- **Context understanding:** Contextual meaning through transformer models

### Privacy-Preserving Preprocessing
- **Automatic anonymization:** Emails → `<EMAIL>`, URLs → `<URL>`, Phone numbers → `<PHONE>`
- **Sensitive data protection:** Numbers, amounts, names replaced with placeholders
- **Clean text normalization:** Whitespace handling, structure preservation

## 🏗️ Technical Implementation

**Core Technologies:**
- **Transformer Models:** BERT/RoBERTa for semantic understanding
- **PyTorch:** Deep learning framework
- **Hugging Face Transformers:** Pre-trained model fine-tuning
- **scikit-learn:** Baseline models and evaluation metrics

**Methodology:**
- **3-class classification:** High, Medium, Low urgency levels
- **Stratified splitting:** Maintains class balance across train/val/test
- **Priority scoring:** `P(High) + 0.5*P(Medium)` for ranking
- **Macro-F1 evaluation:** Handles class imbalance appropriately

## 📊 Results Preview

**Dataset Characteristics:**
- **737 real notifications** with authentic text content
- **Mean content length:** 55.3 characters
- **10 different apps:** Gmail, WhatsApp, Instagram, iOS, Messages, etc.
- **5 notification types:** message, alert, ping, reminder, email

**Semantic Patterns Discovered:**
- **High urgency** notifications use immediate language ("now", "critical", "failed")
- **Medium urgency** contains planning language ("tonight", "later", "remind")  
- **Low urgency** features informational content (promotions, updates)

## 🚀 Next Steps

1. **Transformer Model Training:**
   ```bash
   # Fine-tune BERT for urgency classification
   python train_model.py --model bert-base-uncased --epochs 3
   ```

2. **Model Evaluation:**
   - Macro-F1 score for balanced performance
   - Confusion matrix analysis  
   - Top-k ranking evaluation

3. **Deployment Preparation:**
   - Model serialization and optimization
   - API endpoint for real-time classification

## 📚 Research Contribution

This project advances notification management research by:
- **Focusing on content semantics** rather than metadata-based features
- **Privacy-preserving preprocessing** suitable for real-world deployment  
- **Transformer-based urgency detection** leveraging contextual understanding
- **Practical urgency classification** with actionable priority levels

## 📞 Contact

**Team Members:**
- Oliver Holmes - oholmes.ieu2023@student.ie.edu
- Sofia Bonoan - sbonoan.ieu2023@student.ie.edu  
- Denis Sokolov - denis_sokolov@student.ie.edu
- Gonzalo Fernández - gfernandezde.ieu2023@student.ie.edu

**Institution:** IE University, Computer Science and Artificial Intelligence Program

