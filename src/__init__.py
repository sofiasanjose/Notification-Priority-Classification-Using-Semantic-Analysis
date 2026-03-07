"""
Notification Priority Classification - Source Code Package

This package contains modules for the notification priority classification project:
- data_collection: Kaggle dataset download and initial exploration
- preprocessing: Data cleaning, sanitization, and labeling functions
- models: Machine learning model implementations (to be added)
- evaluation: Model evaluation and metrics (to be added)

Authors: Oliver Holmes, Sofia Bonoan, Denis Sokolov, Gonzalo Fernández
"""

__version__ = "0.1.0"
__author__ = "Oliver Holmes, Sofia Bonoan, Denis Sokolov, Gonzalo Fernández"
__email__ = "oholmes.ieu2023@student.ie.edu"

# Import main functions for convenience
from .preprocessing import (
    sanitize_text,
    assign_priority_label, 
    preprocess_notifications,
    create_stratified_split,
    calculate_priority_score,
    load_processed_data
)

__all__ = [
    'sanitize_text',
    'assign_priority_label',
    'preprocess_notifications', 
    'create_stratified_split',
    'calculate_priority_score',
    'load_processed_data'
]