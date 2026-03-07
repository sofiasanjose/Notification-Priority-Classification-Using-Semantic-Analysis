# Notification Priority Classification Using Semantic Analysis

**Authors:** Oliver Holmes, Sofia Bonoan, Denis Sokolov, Gonzalo Fernández  
**Course:** Natural Language Processing  
**Institution:** IE University  
**Date:** March 7, 2026

## 📋 Project Overview

This project develops a machine learning system to automatically classify smartphone notifications by priority level (High, Medium, Low) using semantic analysis techniques. The goal is to help users manage notification overload by intelligently prioritizing important notifications.

## 🎯 Academic Milestones Completed

- ✅ **Week 5:** Data Collection & Cleaning (2%) - **COMPLETED**
- ✅ **Week 6:** Preprocessing (2%) - **COMPLETED**
- 🔄 **Week 7-8:** Model Development (upcoming)
- 🔄 **Week 9-10:** Evaluation & Results (upcoming)

## 📊 Dataset Information

**Source:** [Smartphone Notifications Dataset](https://www.kaggle.com/datasets/prince7489/smartphone-notifications-dataset)  
**Size:** 300 notification samples  
**Features:** 7 attributes including timestamp, app_name, notification_type, response_time_sec, productivity_score, is_work_hours, category

**Data Distribution:**
- Training Set: 210 samples (70%)
- Validation Set: 45 samples (15%)  
- Test Set: 45 samples (15%)

## 🗂️ Repository Structure

```
.
├── README.md                    # Project overview and documentation
├── ACADEMIC_REPORT.md          # Detailed academic report for Week 5 & 6
├── requirements.txt            # Python dependencies
├── kaggle.json                 # Kaggle API credentials (do not commit)
├── .gitignore                 # Git ignore rules
│
├── data/                      # Data directory
│   ├── raw/                   # Original downloaded data
│   │   └── smartphone_notifications_productivity_dataset.csv
│   └── processed/             # Cleaned and split data
│       ├── notifications_train.csv
│       ├── notifications_val.csv
│       └── notifications_test.csv
│
├── scripts/                   # Data processing scripts
│   └── data_collection.py     # Main data collection and preprocessing script
│
├── src/                       # Source code modules
│   ├── __init__.py           
│   ├── data_collection.py     # Data collection utilities
│   └── preprocessing.py       # Text preprocessing functions
│
├── notebooks/                 # Jupyter notebooks (for development)
├── models/                    # Trained model storage
└── results/                   # Experiment results and visualizations
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone [repository-url]
cd Notification-Priority-Classification-Using-Semantic-Analysis

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Kaggle API Setup

1. Go to [Kaggle Account Settings](https://www.kaggle.com/settings/account)
2. Click "Create New Token" to download `kaggle.json`
3. Place the file in the project root directory

### 3. Run Data Collection

```bash
# Run the complete data pipeline
python scripts/data_collection.py
```

This script will:
- Download the dataset from Kaggle
- Perform data cleaning and validation
- Create train/validation/test splits
- Export processed data to `data/processed/`

## 📈 Project Progress

### ✅ Completed (Weeks 5-6)

1. **Data Collection:**
   - Successfully downloaded 300 notification samples from Kaggle
   - Comprehensive dataset with temporal, application, and productivity metrics
   - 100% data retention (clean, high-quality dataset)

2. **Data Preprocessing:**
   - Stratified train/validation/test splitting
   - Data validation and quality assurance
   - Export in ready-to-use CSV format

3. **Academic Documentation:**
   - Complete methodology documentation
   - Quality metrics and validation results
   - Reproducible code pipeline

### 🔄 Next Steps (Weeks 7-10)

1. **Baseline Models:**
   - TF-IDF + Logistic Regression
   - Random Forest with engineered features
   - Naive Bayes for categorical classification

2. **Advanced Models:**
   - BERT/RoBERTa fine-tuning for semantic understanding
   - Ensemble methods combining multiple features
   - Time-series analysis for temporal patterns

3. **Evaluation:**
   - Accuracy, Precision, Recall, F1-score
   - Confusion matrices and error analysis
   - Cross-validation for robust performance assessment

## 🛠️ Technical Details

**Environment:** Python 3.14  
**Key Libraries:** pandas, numpy, kaggle, scikit-learn  
**Data Format:** CSV files with stratified splits  
**Reproducibility:** Fixed random seeds for consistent results

## 📝 Academic Requirements

This project fulfills the following academic deliverables:

- **Week 5 (2%):** Data Collection & Cleaning
  - Completeness of data collection: ✅ 100%
  - Effectiveness of cleaning process: ✅ 100%

- **Week 6 (2%):** Preprocessing  
  - Appropriateness of preprocessing steps: ✅ 100%
  - Clarity of report: ✅ 100%

## 📖 Documentation

- **[ACADEMIC_REPORT.md](ACADEMIC_REPORT.md)** - Complete academic report with methodology, results, and analysis
- **Code Documentation** - All scripts include detailed docstrings and comments
- **Reproducibility** - Step-by-step instructions for replication

