"""
Sample credit data generator for training the ML risk scoring model.
Run this script to generate credit_data.csv for model training.
"""

import pandas as pd
import numpy as np


def generate_credit_dataset(n_samples: int = 2000, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic corporate credit dataset."""
    np.random.seed(seed)

    data = {
        "revenue": np.random.lognormal(mean=10, sigma=1.5, size=n_samples),
        "profit": np.random.normal(loc=0.1, scale=0.15, size=n_samples),
        "debt_ratio": np.random.beta(2, 5, size=n_samples),
        "current_ratio": np.random.lognormal(mean=0.5, sigma=0.5, size=n_samples),
        "gst_filings": np.random.randint(0, 13, size=n_samples),
        "litigation_flag": np.random.binomial(1, 0.15, size=n_samples),
        "sector_growth": np.random.normal(loc=0.05, scale=0.1, size=n_samples),
        "promoter_risk_score": np.random.beta(2, 8, size=n_samples),
        "years_in_business": np.random.randint(1, 50, size=n_samples),
        "interest_coverage": np.random.lognormal(mean=1, sigma=0.8, size=n_samples),
        "revenue_growth": np.random.normal(loc=0.08, scale=0.2, size=n_samples),
        "cash_flow_positive": np.random.binomial(1, 0.7, size=n_samples),
    }

    df = pd.DataFrame(data)

    # Generate loan_default based on a realistic relationship with features
    log_odds = (
        -2.0
        + 3.0 * df["debt_ratio"]
        - 1.5 * df["current_ratio"].clip(0, 5) / 5
        - 0.8 * df["gst_filings"] / 12
        + 1.5 * df["litigation_flag"]
        - 1.0 * df["sector_growth"] * 5
        + 2.0 * df["promoter_risk_score"]
        - 0.02 * df["years_in_business"]
        - 0.5 * df["interest_coverage"].clip(0, 10) / 10
        - 0.5 * df["revenue_growth"] * 3
        - 0.8 * df["cash_flow_positive"]
        + np.random.normal(0, 0.5, size=n_samples)
    )

    probability = 1 / (1 + np.exp(-log_odds))
    df["loan_default"] = (np.random.random(n_samples) < probability).astype(int)

    # Clean up values
    df["revenue"] = df["revenue"].round(2)
    df["profit"] = df["profit"].round(4)
    df["debt_ratio"] = df["debt_ratio"].round(4)
    df["current_ratio"] = df["current_ratio"].round(4)
    df["sector_growth"] = df["sector_growth"].round(4)
    df["promoter_risk_score"] = df["promoter_risk_score"].round(4)
    df["interest_coverage"] = df["interest_coverage"].round(4)
    df["revenue_growth"] = df["revenue_growth"].round(4)

    return df


if __name__ == "__main__":
    import os
    df = generate_credit_dataset()
    output_path = os.path.join(os.path.dirname(__file__), "credit_data.csv")
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} samples. Default rate: {df['loan_default'].mean():.2%}")
    print(f"Saved to {output_path}")
    print(f"\nDataset statistics:\n{df.describe()}")
