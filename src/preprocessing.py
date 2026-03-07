#!/usr/bin/env python3
"""
Data preprocessing module for Notification Priority Classification Project

This module contains functions for cleaning, sanitizing, and preprocessing 
notification text data for machine learning models.

Authors: Oliver Holmes, Sofia Bonoan, Denis Sokolov, Gonzalo Fernández
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from sklearn.model_selection import train_test_split
from typing import Tuple, List, Dict


def sanitize_text(text: str) -> str:
    """
    Remove or mask sensitive information from notification text.
    
    Args:
        text (str): Input text to sanitize
        
    Returns:
        str: Sanitized text with sensitive info masked
    """
    if pd.isna(text) or text == '':
        return text
    
    text = str(text)
    
    # Email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    text = re.sub(email_pattern, '<EMAIL>', text)
    
    # Phone numbers (various formats)
    phone_patterns = [
        r'\b\d{3}-\d{3}-\d{4}\b',  # 123-456-7890
        r'\b\(\d{3}\)\s*\d{3}-\d{4}\b',  # (123) 456-7890
        r'\b\d{3}\.\d{3}\.\d{4}\b',  # 123.456.7890
        r'\b\+?\d{1,4}[\s-]?\d{3,4}[\s-]?\d{3,4}[\s-]?\d{3,4}\b',  # International
        r'\b\d{10,15}\b'  # Long number sequences (be careful with this one)
    ]
    for pattern in phone_patterns:
        text = re.sub(pattern, '<PHONE>', text)
    
    # URLs and links
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    text = re.sub(url_pattern, '<URL>', text)
    
    # Domain names without http
    domain_pattern = r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b'
    text = re.sub(domain_pattern, '<DOMAIN>', text)
    
    # Credit card numbers (basic)
    cc_pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
    text = re.sub(cc_pattern, '<CARD>', text)
    
    # OTP/verification codes (3-8 digit sequences)
    text = re.sub(r'\b(?:code|otp|pin|verify).*?(\d{3,8})\b', '<CODE>', text, flags=re.IGNORECASE)
    
    # ZIP codes (US format)
    zip_pattern = r'\b\d{5}(?:-\d{4})?\b'
    text = re.sub(zip_pattern, '<ZIP>', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def assign_priority_label(text: str) -> str:
    """
    Assign priority labels based on notification text content.
    
    Args:
        text (str): Notification text to classify
        
    Returns:
        str: Priority level ('High', 'Medium', 'Low')
    """
    if pd.isna(text) or text == '':
        return 'Low'
    
    text_lower = str(text).lower()
    
    # High priority patterns
    high_priority_patterns = [
        # Security & urgent actions
        r'\b(security|breach|hack|fraud|unauthorized|suspicious)\b',
        r'\b(verify|confirm|authenticate).*?(now|immediately|asap|urgent)\b',
        r'\b(login|sign[\s-]?in).*?(attempt|failed|blocked)\b',
        
        # Payment & financial
        r'\b(payment|transaction).*?(failed|declined|error|problem)\b',
        r'\b(account|card).*?(suspended|blocked|locked|frozen)\b',
        r'\b(insufficient|low).*?funds?\b',
        
        # Time-sensitive
        r'\b(expire|expires?|expired).*?(today|soon|now)\b',
        r'\b(urgent|emergency|critical|important|asap)\b',
        r'\b(starting|begins?|happening).*?(now|soon|in.*?minutes?)\b',
        r'\b(last.*?chance|final.*?notice|immediate.*?action)\b',
        
        # OTPs and codes
        r'\b(otp|verification|confirm|authenticate).*?<CODE>\b',
        r'\b<CODE>.*?(otp|verification|confirm)\b',
        
        # Meetings and calls
        r'\b(meeting|call|conference).*?(starting|begins?|now)\b',
        r'\b(late|missed).*?(meeting|call|appointment)\b'
    ]
    
    # Medium priority patterns
    medium_priority_patterns = [
        # Delivery and shipping
        r'\b(package|delivery|shipped|tracking|order).*?(update|status|arrived|delivered)\b',
        r'\b(out.*?for.*?delivery|delivery.*?attempt)\b',
        
        # Reminders and appointments
        r'\b(reminder|appointment|meeting|event).*?(tomorrow|later|upcoming)\b',
        r'\b(due|deadline).*?(tomorrow|next|week|month)\b',
        
        # Account updates (non-urgent)
        r'\b(account|profile|settings).*?(updated|changed|modified)\b',
        r'\b(password|email).*?(changed|updated|reset)\b',
        
        # News and updates (important)
        r'\b(update|news|announcement).*?(important|new|latest)\b',
        r'\b(policy|terms).*?(updated|changed|new)\b'
    ]
    
    # Check for high priority patterns first
    for pattern in high_priority_patterns:
        if re.search(pattern, text_lower):
            return 'High'
    
    # Check for medium priority patterns
    for pattern in medium_priority_patterns:
        if re.search(pattern, text_lower):
            return 'Medium'
    
    # Low priority patterns (promotional, social, etc.)
    low_priority_patterns = [
        r'\b(sale|discount|offer|deal|promotion|coupon)\b',
        r'\b(newsletter|subscribe|follow|like|share)\b',
        r'\b(recommended|suggested|you.*?might.*?like)\b',
        r'\b(new.*?post|friend.*?request|follower|activity)\b',
        r'\b(weather|news|entertainment|sports|celebrity)\b'
    ]
    
    # Check for explicit low priority patterns
    for pattern in low_priority_patterns:
        if re.search(pattern, text_lower):
            return 'Low'
    
    # Default to Low for general notifications
    return 'Low'


def preprocess_notifications(
    df: pd.DataFrame,
    text_columns: List[str] = None,
    combine_text: bool = True,
    sanitize: bool = True,
    create_labels: bool = True
) -> pd.DataFrame:
    """
    Complete preprocessing pipeline for notification data.
    
    Args:
        df (pd.DataFrame): Input dataframe
        text_columns (List[str]): Names of text columns to process
        combine_text (bool): Whether to combine multiple text columns
        sanitize (bool): Whether to apply text sanitization
        create_labels (bool): Whether to create priority labels
        
    Returns:
        pd.DataFrame: Processed dataframe
    """
    df_processed = df.copy()
    
    # Auto-detect text columns if not specified
    if text_columns is None:
        text_columns = []
        for col in df_processed.columns:
            if any(keyword in col.lower() for keyword in ['title', 'body', 'text', 'message', 'content']):
                text_columns.append(col)
    
    print(f"Processing text columns: {text_columns}")
    
    # Clean text columns
    for col in text_columns:
        if col in df_processed.columns:
            df_processed[col] = df_processed[col].astype(str)
            df_processed[col] = df_processed[col].replace('nan', '')
            df_processed[col] = df_processed[col].str.strip()
    
    # Combine text if requested
    if combine_text and len(text_columns) > 0:
        df_processed['combined_text'] = ''
        for col in text_columns:
            df_processed['combined_text'] += df_processed[col].fillna('') + ' '
        df_processed['combined_text'] = df_processed['combined_text'].str.strip()
    elif len(text_columns) == 1:
        df_processed['combined_text'] = df_processed[text_columns[0]]
    
    # Apply sanitization
    if sanitize and 'combined_text' in df_processed.columns:
        df_processed['combined_text_sanitized'] = df_processed['combined_text'].apply(sanitize_text)
    
    # Create priority labels
    if create_labels:
        text_col = 'combined_text_sanitized' if sanitize else 'combined_text'
        if text_col in df_processed.columns:
            df_processed['priority'] = df_processed[text_col].apply(assign_priority_label)
    
    # Remove empty rows
    if 'combined_text_sanitized' in df_processed.columns:
        df_processed = df_processed[df_processed['combined_text_sanitized'].str.len() > 0]
    elif 'combined_text' in df_processed.columns:
        df_processed = df_processed[df_processed['combined_text'].str.len() > 0]
    
    return df_processed


def create_stratified_split(
    df: pd.DataFrame,
    text_column: str = 'combined_text_sanitized',
    target_column: str = 'priority',
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Create stratified train/validation/test splits.
    
    Args:
        df (pd.DataFrame): Input dataframe
        text_column (str): Column containing text features
        target_column (str): Column containing target labels
        train_ratio (float): Proportion for training set
        val_ratio (float): Proportion for validation set
        test_ratio (float): Proportion for test set
        random_state (int): Random seed for reproducibility
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: train, validation, test dataframes
    """
    
    # Verify ratios sum to 1
    if not abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6:
        raise ValueError("Split ratios must sum to 1.0")
    
    # Prepare data
    df_split = df[[text_column, target_column]].copy()
    df_split = df_split.dropna()
    
    # First split: train vs (val + test)
    X = df_split[text_column]
    y = df_split[target_column]
    
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y,
        test_size=(val_ratio + test_ratio),
        stratify=y,
        random_state=random_state
    )
    
    # Second split: val vs test
    val_size_adjusted = val_ratio / (val_ratio + test_ratio)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp,
        test_size=(1 - val_size_adjusted),
        stratify=y_temp,
        random_state=random_state
    )
    
    # Create DataFrames
    train_df = pd.DataFrame({text_column: X_train, target_column: y_train}).reset_index(drop=True)
    val_df = pd.DataFrame({text_column: X_val, target_column: y_val}).reset_index(drop=True)
    test_df = pd.DataFrame({text_column: X_test, target_column: y_test}).reset_index(drop=True)
    
    return train_df, val_df, test_df


def calculate_priority_score(predictions: np.ndarray) -> np.ndarray:
    """
    Calculate priority scores from model predictions for ranking.
    
    Args:
        predictions (np.ndarray): Model predictions [P(High), P(Medium), P(Low)]
        
    Returns:
        np.ndarray: Priority scores for ranking
    """
    if predictions.ndim == 1:
        # Single prediction
        return predictions[0] + 0.5 * predictions[1]  # High + 0.5 * Medium
    else:
        # Multiple predictions
        return predictions[:, 0] + 0.5 * predictions[:, 1]


def load_processed_data(data_dir: str = "../data/processed") -> Dict[str, pd.DataFrame]:
    """
    Load preprocessed data splits.
    
    Args:
        data_dir (str): Directory containing processed data files
        
    Returns:
        Dict[str, pd.DataFrame]: Dictionary containing train/val/test dataframes
    """
    data_path = Path(data_dir)
    
    datasets = {}
    for split in ['train', 'val', 'test']:
        filepath = data_path / f"notifications_{split}.csv"
        if filepath.exists():
            datasets[split] = pd.read_csv(filepath)
        else:
            print(f"Warning: {filepath} not found")
    
    return datasets