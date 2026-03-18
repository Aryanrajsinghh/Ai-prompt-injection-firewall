"""
Configuration settings for the ML module.
"""
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Model paths
MODEL_DIR = BASE_DIR / "models"
EMBEDDING_MODEL_PATH = MODEL_DIR / "embedding_model"
CLASSIFIER_MODEL_PATH = MODEL_DIR / "xgboost_classifier.pkl"
LABEL_ENCODER_PATH = MODEL_DIR / "label_encoder.pkl"

# Dataset path
DATASET_DIR = BASE_DIR / "datasets"
DATASET_PATH = DATASET_DIR / "prompt_dataset.csv"

# Sentence-BERT model
SENTENCE_BERT_MODEL = "all-MiniLM-L6-v2"

# Attack classes
ATTACK_CLASSES = [
    "SAFE",
    "PROMPT_INJECTION",
    "JAILBREAK",
    "DATA_EXFILTRATION",
    "ROLE_MANIPULATION"
]

# Continual learning threshold
CONTINUAL_LEARNING_THRESHOLD = 0.85

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8001
