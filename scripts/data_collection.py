#!/usr/bin/env python3
"""
Notification Priority Classification - Data Collection Script

This script downloads the smartphone notifications dataset from Kaggle,
performs basic cleaning and preprocessing, and creates train/validation/test splits
for the notification priority classification project.

Authors: Oliver Holmes, Sofia Bonoan, Denis Sokolov, Gonzalo Fernández
Course: Natural Language Processing
Date: March 7, 2026

Usage:
    python scripts/data_collection.py

Requirements:
    - Kaggle API token set in environment or kaggle.json file
    - pandas, numpy, kaggle packages installed
"""

import os
import pandas as pd
import numpy as np
import re
import json
from pathlib import Path

print("🧪 Starting data collection process...")

# Set up environment
os.environ['KAGGLE_API_TOKEN'] = 'KGAT_c45cd833bf7e85b15ccc69436c1ee1e3'

# Test Kaggle API
print("\n📡 Testing Kaggle connection...")
try:
    import kaggle
    kaggle.api.authenticate()
    print("✅ Kaggle API authenticated")
except Exception as e:
    print(f"❌ Kaggle failed: {e}")
    exit(1)

# Download dataset
print("\n📥 Downloading dataset...")
data_dir = Path("data/raw")  # Changed from ../data/raw
data_dir.mkdir(parents=True, exist_ok=True)

try:
    kaggle.api.dataset_download_files(
        "prince7489/smartphone-notifications-dataset",
        path=str(data_dir),
        unzip=True
    )
    print("✅ Dataset downloaded")
except Exception as e:
    print(f"❌ Download failed: {e}")
    exit(1)

# Load and explore data
print("\n📊 Loading data...")
csv_files = list(data_dir.glob('*.csv'))
if not csv_files:
    print("❌ No CSV files found")
    exit(1)

main_file = csv_files[0]
print(f"📄 Loading: {main_file.name}")

df = pd.read_csv(main_file)
print(f"✅ Data loaded: {df.shape}")
print(f"📋 Columns: {list(df.columns)}")
print(f"📝 Sample data:")
print(df.head())

# Basic cleaning  
print(f"\n🧹 Basic cleaning...")
initial_rows = len(df)
df_clean = df.dropna(how='all').drop_duplicates()
print(f"✅ Cleaned: {initial_rows} → {len(df_clean)} rows")

# Simple data splits (manual without sklearn)
print(f"\n✂️ Creating data splits...")
df_shuffled = df_clean.sample(frac=1, random_state=42).reset_index(drop=True)

n_total = len(df_shuffled)
n_train = int(0.7 * n_total)
n_val = int(0.15 * n_total)

train_df = df_shuffled[:n_train]
val_df = df_shuffled[n_train:n_train+n_val]
test_df = df_shuffled[n_train+n_val:]

print(f"✅ Splits created:")
print(f"   Train: {len(train_df)} (70%)")
print(f"   Val: {len(val_df)} (15%)")
print(f"   Test: {len(test_df)} (15%)")

# Export data
print(f"\n💾 Exporting processed data...")
processed_dir = Path("data/processed")  # Changed from ../data/processed
processed_dir.mkdir(parents=True, exist_ok=True)

train_df.to_csv(processed_dir / "notifications_train.csv", index=False)
val_df.to_csv(processed_dir / "notifications_val.csv", index=False)
test_df.to_csv(processed_dir / "notifications_test.csv", index=False)

print(f"✅ Data exported to: {processed_dir}")
print(f"\n🎉 Data collection completed successfully!")
print(f"\n📊 Summary:")
print(f"   Original data: {initial_rows:,} samples")
print(f"   Final data: {len(df_clean):,} samples")  
print(f"   Ready for Week 5 & 6 academic requirements!")