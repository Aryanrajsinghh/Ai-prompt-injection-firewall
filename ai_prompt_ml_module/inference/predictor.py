"""
Prompt predictor for inference.
"""
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

from utils.config import (
    EMBEDDING_MODEL_PATH,
    CLASSIFIER_MODEL_PATH,
    LABEL_ENCODER_PATH,
    ATTACK_CLASSES
)


class PromptPredictor:
    """
    Prompt prediction engine using Sentence-BERT + XGBoost.
    """
    
    def __init__(self):
        self.embedding_model = None
        self.classifier = None
        self.label_encoder = None
        self.is_loaded = False
    
    def load(self):
        """Load all model components."""
        # Load embedding model
        self.embedding_model = SentenceTransformer(str(EMBEDDING_MODEL_PATH))
        
        # Load classifier
        with open(CLASSIFIER_MODEL_PATH, "rb") as f:
            self.classifier = pickle.load(f)
        
        # Load label encoder
        with open(LABEL_ENCODER_PATH, "rb") as f:
            self.label_encoder = pickle.load(f)
        
        self.is_loaded = True
    
    def predict(self, prompt: str) -> dict:
        """
        Predict attack type and risk score for a prompt.
        
        Args:
            prompt: Input prompt text
            
        Returns:
            Dictionary with attack_type and risk_score
        """
        if not self.is_loaded:
            self.load()
        
        # Generate embedding
        embedding = self.embedding_model.encode(
            [prompt],
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        # Get prediction
        prediction = self.classifier.predict(embedding)[0]
        probabilities = self.classifier.predict_proba(embedding)[0]
        
        # Decode label
        attack_type = self.label_encoder.inverse_transform([prediction])[0]
        
        # Calculate risk score (probability of being malicious)
        safe_idx = list(self.label_encoder.classes_).index("SAFE")
        risk_score = 1.0 - probabilities[safe_idx]
        
        return {
            "attack_type": attack_type,
            "risk_score": round(float(risk_score), 4)
        }
