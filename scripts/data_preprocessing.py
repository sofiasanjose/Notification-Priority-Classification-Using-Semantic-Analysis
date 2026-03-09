#!/usr/bin/env python3
"""
Data Preprocessing Script for Notification Priority Classification
Authors: Oliver Holmes, Sofia Bonoan, Denis Sokolov, Gonzalo Fernández

This script handles:
1. Data loading and exploration
2. Text preprocessing and cleaning
3. Privacy-aware anonymization 
4. Stratified train/validation/test splits
5. Export to processed CSV files
"""

import csv
import re
import random
from collections import Counter, defaultdict
from pathlib import Path
import argparse
from typing import Dict, List, Tuple

class NotificationPreprocessor:
    def __init__(self, input_file: str, output_dir: str = "data/processed", test_size=0.15, val_size=0.15):
        self.input_file = input_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.test_size = test_size
        self.val_size = val_size
        self.train_size = 1.0 - test_size - val_size
        
        # Privacy patterns for anonymization
        self.privacy_patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+\d{1,3}\s?)?[\(\d][\d\s\(\)\-\.]{8,15}\b'),
            'url': re.compile(r'https?://[^\s]+'),
            'number': re.compile(r'\b\d{4,}\b'),  # 4+ digit numbers (codes, IDs, etc.)
            'amount': re.compile(r'\$\d+\.?\d*|\€\d+\.?\d*|£\d+\.?\d*'),
            'name_placeholder': re.compile(r'<NAME>')  # Already anonymized names
        }
        
    def load_data(self) -> List[Dict]:
        """Load the curated notification dataset."""
        data = []
        with open(self.input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        print(f"✓ Loaded {len(data)} notifications from {self.input_file}")
        return data
        
    def analyze_dataset(self, data: List[Dict]) -> None:
        """Print comprehensive dataset statistics."""
        print("\n" + "="*60)
        print("DATASET ANALYSIS")
        print("="*60)
        
        print(f"Total notifications: {len(data)}")
        
        # Urgency distribution
        urgency_counts = Counter(row['urgency'].lower() for row in data)
        print(f"\nUrgency distribution:")
        for urgency in ['high', 'medium', 'low']:
            count = urgency_counts[urgency]
            pct = count / len(data) * 100
            print(f"  {urgency.capitalize():6}: {count:3d} ({pct:5.1f}%)")
            
        # App distribution
        app_counts = Counter(row['app_name'] for row in data)
        print(f"\nTop 10 apps:")
        for app, count in app_counts.most_common(10):
            pct = count / len(data) * 100
            print(f"  {app:15}: {count:3d} ({pct:4.1f}%)")
            
        # Notification type distribution
        type_counts = Counter(row['notif_type'] for row in data)
        print(f"\nNotification types:")
        for ntype, count in sorted(type_counts.items()):
            pct = count / len(data) * 100
            print(f"  {ntype:10}: {count:3d} ({pct:4.1f}%)")
            
        # Content length analysis
        lengths = [len(row['notif_content']) for row in data]
        print(f"\nContent length statistics:")
        print(f"  Mean:   {sum(lengths)/len(lengths):5.1f} characters")
        print(f"  Max:    {max(lengths):5d} characters")
        print(f"  Min:    {min(lengths):5d} characters")
        print(f"  Median: {sorted(lengths)[len(lengths)//2]:5d} characters")
        
    def anonymize_text(self, text: str) -> str:
        """Apply privacy-preserving anonymization to notification text."""
        # Replace patterns with placeholders
        text = self.privacy_patterns['email'].sub('<EMAIL>', text)
        text = self.privacy_patterns['phone'].sub('<PHONE>', text)
        text = self.privacy_patterns['url'].sub('<URL>', text)
        text = self.privacy_patterns['amount'].sub('<AMOUNT>', text)
        # Keep some numbers but anonymize long ones that might be sensitive
        text = self.privacy_patterns['number'].sub('<NUMBER>', text)
        # Keep <NAME> placeholders as they are
        return text
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize notification text."""
        # Basic cleaning while preserving important punctuation for urgency detection
        text = text.strip()
        # Normalize whitespace but keep structure
        text = re.sub(r'\s+', ' ', text)
        # Keep punctuation as it can indicate urgency (!, ?, etc.)
        return text
        
    def preprocess_notifications(self, data: List[Dict]) -> List[Dict]:
        """Apply preprocessing to all notifications."""
        processed_data = []
        
        print(f"\nPreprocessing {len(data)} notifications...")
        
        for i, row in enumerate(data):
            # Create a copy to avoid modifying original
            processed_row = row.copy()
            
            # Clean and anonymize the notification content
            original_content = row['notif_content']
            processed_content = self.clean_text(original_content)
            processed_content = self.anonymize_text(processed_content)
            
            # Update the processed content
            processed_row['notif_content'] = processed_content
            
            # Standardize urgency labels (lowercase)
            processed_row['urgency'] = row['urgency'].lower().strip()
            
            # Skip empty content after processing
            if not processed_content.strip():
                print(f"  ⚠ Skipping empty notification at row {i+1}")
                continue
                
            processed_data.append(processed_row)
            
        print(f"✓ Processed {len(processed_data)} notifications successfully")
        print(f"  Removed {len(data) - len(processed_data)} notifications with empty content")
        
        return processed_data
        
    def stratified_split(self, data: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Create stratified train/validation/test splits."""
        print(f"\nCreating stratified splits...")
        print(f"  Train: {self.train_size*100:.0f}% | Val: {self.val_size*100:.0f}% | Test: {self.test_size*100:.0f}%")
        
        # Group data by urgency level
        urgency_groups = defaultdict(list)
        for row in data:
            urgency_groups[row['urgency']].append(row)
            
        train_data, val_data, test_data = [], [], []
        
        # Split each urgency group separately
        for urgency, group_data in urgency_groups.items():
            random.shuffle(group_data)  # Shuffle for randomness
            n = len(group_data)
            
            # Calculate split indices
            test_end = int(n * self.test_size)
            val_end = test_end + int(n * self.val_size)
            
            # Split the group
            test_split = group_data[:test_end]
            val_split = group_data[test_end:val_end]
            train_split = group_data[val_end:]
            
            # Add to respective datasets
            test_data.extend(test_split)
            val_data.extend(val_split)
            train_data.extend(train_split)
            
            print(f"  {urgency.capitalize():6}: {len(train_split):3d} train | {len(val_split):3d} val | {len(test_split):3d} test")
        
        # Shuffle the combined datasets
        random.shuffle(train_data)
        random.shuffle(val_data)
        random.shuffle(test_data)
        
        print(f"\nFinal split sizes:")
        print(f"  Training:   {len(train_data):3d} notifications")
        print(f"  Validation: {len(val_data):3d} notifications")  
        print(f"  Test:       {len(test_data):3d} notifications")
        
        return train_data, val_data, test_data
        
    def save_split(self, data: List[Dict], filename: str) -> None:
        """Save a data split to CSV file."""
        filepath = self.output_dir / filename
        
        if not data:
            print(f"⚠ No data to save for {filename}")
            return
            
        fieldnames = data[0].keys()
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            
        print(f"✓ Saved {len(data)} notifications to {filepath}")
        
    def run_preprocessing(self) -> None:
        """Execute the complete preprocessing pipeline."""
        print("🚀 Starting Notification Priority Classification Data Preprocessing")
        print("="*80)
        
        # Set random seed for reproducibility
        random.seed(42)
        
        # Load data
        raw_data = self.load_data()
        
        # Analyze raw dataset
        self.analyze_dataset(raw_data)
        
        # Preprocess notifications
        clean_data = self.preprocess_notifications(raw_data)
        
        # Create stratified splits
        train_data, val_data, test_data = self.stratified_split(clean_data)
        
        # Save splits
        print(f"\nSaving processed data to {self.output_dir}")
        self.save_split(train_data, "notifications_train.csv")
        self.save_split(val_data, "notifications_val.csv")
        self.save_split(test_data, "notifications_test.csv")
        
        # Final summary
        print("\n" + "="*60)
        print("PREPROCESSING COMPLETE! ✅")
        print("="*60)
        print(f"Processed {len(clean_data)} notifications from {self.input_file}")
        print(f"Created train/val/test splits in {self.output_dir}")
        print(f"Ready for model training and evaluation!")


def main():
    parser = argparse.ArgumentParser(description="Preprocess notification data for priority classification")
    parser.add_argument("--input", default="NLP_Notifications_final.dataset.csv", 
                       help="Input CSV file with notification data")
    parser.add_argument("--output", default="data/processed", 
                       help="Output directory for processed splits")
    parser.add_argument("--test-size", type=float, default=0.15, 
                       help="Test set size (default: 0.15)")
    parser.add_argument("--val-size", type=float, default=0.15, 
                       help="Validation set size (default: 0.15)")
    
    args = parser.parse_args()
    
    # Create and run preprocessor
    preprocessor = NotificationPreprocessor(
        input_file=args.input,
        output_dir=args.output,
        test_size=args.test_size,
        val_size=args.val_size
    )
    
    preprocessor.run_preprocessing()


if __name__ == "__main__":
    main()