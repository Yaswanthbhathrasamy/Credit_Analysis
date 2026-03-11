"""
ML Model Training Script
Trains Random Forest, Logistic Regression, and Gradient Boosting classifiers
for corporate credit risk prediction.
"""

import os
import logging
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report, confusion_matrix
)

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    "revenue", "profit", "debt_ratio", "current_ratio", "gst_filings",
    "litigation_flag", "sector_growth", "promoter_risk_score",
    "years_in_business", "interest_coverage", "revenue_growth",
    "cash_flow_positive",
]

MODEL_DIR = os.path.join(os.path.dirname(__file__), "trained_models")


def train_models(data_path: str = None) -> dict:
    """Train all credit risk models and save to disk."""
    os.makedirs(MODEL_DIR, exist_ok=True)

    if data_path is None:
        data_path = os.path.join(os.path.dirname(__file__), "credit_data.csv")

    if not os.path.exists(data_path):
        # Generate data if it doesn't exist
        from app.ml.generate_data import generate_credit_dataset
        df = generate_credit_dataset()
        df.to_csv(data_path, index=False)
    else:
        df = pd.read_csv(data_path)

    X = df[FEATURE_COLUMNS]
    y = df["loan_default"]

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    models = {
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=10, random_state=42, n_jobs=-1
        ),
        "logistic_regression": LogisticRegression(
            max_iter=1000, random_state=42, C=1.0
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.1, random_state=42
        ),
    }

    results = {}
    best_auc = 0
    best_model_name = None

    for name, model in models.items():
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy": round(accuracy_score(y_test, y_pred), 4),
            "precision": round(precision_score(y_test, y_pred), 4),
            "recall": round(recall_score(y_test, y_pred), 4),
            "f1": round(f1_score(y_test, y_pred), 4),
            "auc_roc": round(roc_auc_score(y_test, y_proba), 4),
        }

        cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring="roc_auc")
        metrics["cv_auc_mean"] = round(cv_scores.mean(), 4)

        results[name] = metrics

        # Save model
        model_path = os.path.join(MODEL_DIR, f"{name}.joblib")
        joblib.dump(model, model_path)

        if metrics["auc_roc"] > best_auc:
            best_auc = metrics["auc_roc"]
            best_model_name = name

        logger.info(f"{name}: AUC={metrics['auc_roc']}, F1={metrics['f1']}")

    # Save scaler and metadata
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.joblib"))
    joblib.dump(FEATURE_COLUMNS, os.path.join(MODEL_DIR, "feature_columns.joblib"))
    joblib.dump(best_model_name, os.path.join(MODEL_DIR, "best_model.joblib"))

    results["best_model"] = best_model_name
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = train_models()
    for name, metrics in results.items():
        if isinstance(metrics, dict):
            print(f"\n{name}:")
            for k, v in metrics.items():
                print(f"  {k}: {v}")
        else:
            print(f"\nBest model: {metrics}")
