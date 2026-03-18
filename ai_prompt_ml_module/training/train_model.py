"""
Training pipeline for the ML Detection Module.
"""
import pickle

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import LabelEncoder
from sentence_transformers import SentenceTransformer
import xgboost as xgb

from utils.config import (
    DATASET_PATH,
    EMBEDDING_MODEL_PATH,
    CLASSIFIER_MODEL_PATH,
    LABEL_ENCODER_PATH,
    SENTENCE_BERT_MODEL,
    ATTACK_CLASSES
)
from training.dataset_loader import combine_datasets


def load_dataset(use_combined=True):
    """
    Load the training dataset.

    Args:
        use_combined: If True, combine all available datasets.
                     If False, load from existing CSV only.
    """
    if use_combined:
        print("Loading combined datasets...")
        df = combine_datasets()
        # Save the combined dataset for future use
        df.to_csv(DATASET_PATH, index=False)
        print(f"Saved combined dataset to {DATASET_PATH}")
    else:
        print(f"Loading dataset from {DATASET_PATH}...")
        df = pd.read_csv(DATASET_PATH)

    return df["prompt"].tolist(), df["label"].tolist()


def generate_embeddings(prompts, model_name):
    """Generate Sentence-BERT embeddings for prompts."""
    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        prompts,
        convert_to_numpy=True,
        show_progress_bar=True,
        batch_size=32
    )
    return embeddings, model


def train_classifier(X_train, y_train, X_test, y_test):
    """Train XGBoost classifier and evaluate."""
    classifier = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=len(ATTACK_CLASSES),
        max_depth=6,
        learning_rate=0.1,
        n_estimators=100,
        random_state=42
    )
    
    classifier.fit(X_train, y_train)
    
    # Evaluate
    y_pred = classifier.predict(X_test)
    
    print("\n" + "="*50)
    print("MODEL EVALUATION")
    print("="*50)
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred, average='weighted'):.4f}")
    print(f"Recall: {recall_score(y_test, y_pred, average='weighted'):.4f}")
    print(f"F1 Score: {f1_score(y_test, y_pred, average='weighted'):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    return classifier


def save_models(embedding_model, classifier, label_encoder):
    """Save trained models."""
    # Save embedding model
    embedding_model.save(str(EMBEDDING_MODEL_PATH))
    print(f"\n✓ Embedding model saved to {EMBEDDING_MODEL_PATH}")
    
    # Save classifier
    with open(CLASSIFIER_MODEL_PATH, "wb") as f:
        pickle.dump(classifier, f)
    print(f"✓ Classifier saved to {CLASSIFIER_MODEL_PATH}")
    
    # Save label encoder
    with open(LABEL_ENCODER_PATH, "wb") as f:
        pickle.dump(label_encoder, f)
    print(f"✓ Label encoder saved to {LABEL_ENCODER_PATH}")


def main():
    """Main training pipeline."""
    print("="*50)
    print("AI PROMPT INJECTION FIREWALL - ML TRAINING")
    print("="*50)
    
    # Step 1: Load dataset
    print("\n[1/5] Loading dataset...")
    prompts, labels = load_dataset()
    print(f"Loaded {len(prompts)} samples")
    
    # Step 2: Encode labels
    print("\n[2/5] Encoding labels...")
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(labels)
    print(f"Classes: {list(label_encoder.classes_)}")
    
    # Step 3: Generate embeddings
    print(f"\n[3/5] Generating embeddings using {SENTENCE_BERT_MODEL}...")
    X, embedding_model = generate_embeddings(prompts, SENTENCE_BERT_MODEL)
    print(f"Embedding shape: {X.shape}")
    
    # Step 4: Split data
    print("\n[4/5] Splitting data (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Step 5: Train classifier
    print("\n[5/5] Training XGBoost classifier...")
    classifier = train_classifier(X_train, y_train, X_test, y_test)
    
    # Save models
    save_models(embedding_model, classifier, label_encoder)
    
    print("\n" + "="*50)
    print("TRAINING COMPLETE")
    print("="*50)


if __name__ == "__main__":
    main()
