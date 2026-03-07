#!/usr/bin/env python3
"""
Data Collection Script for Notification Priority Classification Project

This script downloads the Smartphone Notifications Dataset from Kaggle
and performs initial data exploration.

Authors: Oliver Holmes, Sofia Bonoan, Denis Sokolov, Gonzalo Fernández
"""

import os
import sys
import pandas as pd
from pathlib import Path
import zipfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def setup_kaggle_api():
    """
    Setup Kaggle API credentials and import kaggle module.
    
    Returns:
        kaggle.api: Kaggle API instance
    """
    try:
        # Check if kaggle.json exists in standard locations
        home_kaggle = Path.home() / '.kaggle' / 'kaggle.json'
        project_kaggle = project_root / 'kaggle.json'
        
        if home_kaggle.exists():
            print(f"✓ Found Kaggle credentials at: {home_kaggle}")
        elif project_kaggle.exists():
            print(f"✓ Found Kaggle credentials at: {project_kaggle}")
            # Set environment variable to point to project kaggle.json
            os.environ['KAGGLE_CONFIG_DIR'] = str(project_root)
        elif 'KAGGLE_USERNAME' in os.environ and 'KAGGLE_KEY' in os.environ:
            print("✓ Found Kaggle credentials in environment variables")
        else:
            raise FileNotFoundError(
                "Kaggle credentials not found. Please set up kaggle.json or environment variables."
            )
        
        # Import and authenticate
        import kaggle
        kaggle.api.authenticate()
        print("✓ Kaggle API authenticated successfully")
        return kaggle.api
        
    except Exception as e:
        print(f"❌ Error setting up Kaggle API: {e}")
        print("\nPlease ensure you have:")
        print("1. kaggle.json file in ~/.kaggle/ or project root")
        print("2. Or set KAGGLE_USERNAME and KAGGLE_KEY environment variables")
        print("3. Run 'pip install kaggle' if not installed")
        raise


def download_dataset():
    """
    Download the smartphone notifications dataset from Kaggle.
    
    Returns:
        Path: Path to the downloaded dataset directory
    """
    print("\n📥 Downloading dataset from Kaggle...")
    
    # Dataset identifier
    dataset_name = "prince7489/smartphone-notifications-dataset"
    
    # Setup API
    api = setup_kaggle_api()
    
    # Create data directories
    raw_data_dir = project_root / 'data' / 'raw'
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download dataset
        print(f"Downloading {dataset_name}...")
        api.dataset_download_files(
            dataset_name, 
            path=str(raw_data_dir), 
            unzip=True
        )
        
        print(f"✓ Dataset downloaded to: {raw_data_dir}")
        return raw_data_dir
        
    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        raise


def explore_dataset(data_dir):
    """
    Perform initial exploration of the downloaded dataset.
    
    Args:
        data_dir (Path): Path to the directory containing dataset files
    """
    print("\n🔍 Exploring dataset structure...")
    
    # List all files in the data directory
    files = list(data_dir.glob('*'))
    print(f"Found {len(files)} files:")
    for file in files:
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"  - {file.name} ({size_mb:.1f} MB)")
    
    # Try to load the main dataset file
    csv_files = list(data_dir.glob('*.csv'))
    
    if not csv_files:
        print("❌ No CSV files found in dataset")
        return None
    
    # Load the first CSV file (assuming it's the main dataset)
    main_file = csv_files[0]
    print(f"\n📊 Loading main dataset: {main_file.name}")
    
    try:
        df = pd.read_csv(main_file)
        
        print(f"Dataset shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Show first few rows
        print("\nFirst 5 rows:")
        print(df.head())
        
        # Check for missing values
        print("\nMissing values:")
        print(df.isnull().sum())
        
        # Basic statistics
        print("\nDataset info:")
        print(df.info())
        
        return df
        
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return None


def create_placeholder_files():
    """Create placeholder files to maintain directory structure in git."""
    
    directories = [
        project_root / 'data' / 'raw',
        project_root / 'data' / 'processed', 
        project_root / 'results'
    ]
    
    for directory in directories:
        gitkeep_file = directory / '.gitkeep'
        if not gitkeep_file.exists():
            gitkeep_file.write_text('')
            print(f"Created {gitkeep_file}")


def main():
    """Main function to download and explore the dataset."""
    
    print("🚀 Starting data collection for Notification Priority Classification")
    print("=" * 70)
    
    try:
        # Create placeholder files for git
        create_placeholder_files()
        
        # Download dataset
        data_dir = download_dataset()
        
        # Explore dataset
        df = explore_dataset(data_dir)
        
        if df is not None:
            print("\n✅ Data collection completed successfully!")
            print(f"Dataset loaded with {len(df)} notifications")
            print("\nNext steps:")
            print("1. Open notebooks/01_data_exploration.ipynb for detailed analysis")
            print("2. Run data preprocessing with src/preprocessing.py")
            print("3. Start model development")
        else:
            print("⚠️  Data collection completed but dataset exploration failed")
            
    except Exception as e:
        print(f"\n❌ Data collection failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())