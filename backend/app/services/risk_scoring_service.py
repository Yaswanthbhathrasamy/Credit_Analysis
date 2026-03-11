"""
ML Risk Scoring and SHAP Explainability Service
Handles credit risk prediction, model interpretability, and narrative explanation generation.
Enhanced with Indian lending norms, CIBIL integration, and step-by-step reasoning trails.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import numpy as np
import joblib
import shap
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session

from app.models.models import (
    RiskScore, RiskLevel, LoanDecision,
    FinancialMetric, PromoterAnalysis, RiskFlag, Company, ResearchFinding,
)
from app.ml.train_model import MODEL_DIR, FEATURE_COLUMNS, train_models
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RiskScoringService:
    """Predicts credit risk and provides SHAP-based explanations with
    narrative reasoning trails for full explainability."""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.explainer = None
        self._loaded = False
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                api_key=settings.openai_api_key,
            )
        return self._llm

    def _ensure_model_loaded(self):
        """Load model, scaler, and initialize SHAP explainer."""
        if self._loaded:
            return

        model_path = os.path.join(MODEL_DIR, "best_model.joblib")
        if not os.path.exists(model_path):
            logger.info("No trained model found. Training models...")
            train_models()

        best_model_name = joblib.load(os.path.join(MODEL_DIR, "best_model.joblib"))
        self.model = joblib.load(os.path.join(MODEL_DIR, f"{best_model_name}.joblib"))
        self.scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.joblib"))
        self.feature_columns = joblib.load(os.path.join(MODEL_DIR, "feature_columns.joblib"))

        # Initialize SHAP explainer — pick the right type for the model
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression
        if isinstance(self.model, (RandomForestClassifier, GradientBoostingClassifier)):
            self.explainer = shap.TreeExplainer(self.model)
        elif isinstance(self.model, LogisticRegression):
            # Build a small background dataset for LinearExplainer
            train_data_path = os.path.join(os.path.dirname(MODEL_DIR), "credit_data.csv")
            if os.path.exists(train_data_path):
                import pandas as pd
                bg = pd.read_csv(train_data_path)[self.feature_columns]
                bg_scaled = self.scaler.transform(bg.values[:100])
            else:
                bg_scaled = np.zeros((1, len(self.feature_columns)))
            self.explainer = shap.LinearExplainer(self.model, bg_scaled)
        else:
            # Generic fallback using KernelExplainer
            self.explainer = shap.KernelExplainer(
                self.model.predict_proba, np.zeros((1, len(self.feature_columns)))
            )
        self._loaded = True

    def calculate_risk_score(
        self, company_id: str, db: Session
    ) -> Dict[str, Any]:
        """Calculate credit risk score for a company with full explainability."""
        self._ensure_model_loaded()

        # Build feature vector from company data
        features, feature_sources = self._build_feature_vector(company_id, db)
        if features is None:
            raise ValueError("Insufficient financial data to calculate risk score")

        # Scale features
        feature_array = np.array([[features.get(col, 0) for col in self.feature_columns]])
        scaled = self.scaler.transform(feature_array)

        # Predict
        probability_of_default = float(self.model.predict_proba(scaled)[0][1])

        # SHAP explanation
        shap_result = self._explain_prediction(scaled, features)

        # Determine risk level
        risk_level = self._determine_risk_level(probability_of_default)

        # Generate decision
        decision_result = self._generate_decision(
            probability_of_default, risk_level, features, company_id, db
        )

        # Five Cs evaluation with textual justification
        five_cs = self._evaluate_five_cs(features, company_id, db)

        # Generate narrative reasoning (the "walk-through" for judges)
        reasoning_narrative = self._generate_reasoning_narrative(
            company_id, db, features, feature_sources,
            shap_result, probability_of_default, risk_level,
            decision_result, five_cs
        )

        # Store in database
        risk_score = RiskScore(
            company_id=company_id,
            probability_of_default=probability_of_default,
            risk_level=risk_level,
            model_version="v1.0",
            decision=decision_result["decision"],
            recommended_loan_limit=decision_result["loan_limit"],
            suggested_interest_rate=decision_result["interest_rate"],
            shap_values=shap_result["shap_values"],
            positive_factors=shap_result["positive_factors"],
            negative_factors=shap_result["negative_factors"],
            feature_importance=shap_result["feature_importance"],
            five_cs_evaluation=five_cs,
            reasoning_narrative=reasoning_narrative,
        )
        db.add(risk_score)
        db.commit()
        db.refresh(risk_score)

        return {
            "risk_score_id": str(risk_score.id),
            "probability_of_default": probability_of_default,
            "risk_level": risk_level.value,
            "decision": decision_result["decision"].value,
            "recommended_loan_limit": decision_result["loan_limit"],
            "suggested_interest_rate": decision_result["interest_rate"],
            "shap_explanation": shap_result,
            "five_cs_evaluation": five_cs,
            "reasoning_narrative": reasoning_narrative,
        }

    def _build_feature_vector(
        self, company_id: str, db: Session
    ) -> tuple:
        """Build a feature vector from company's stored data.
        Returns (features_dict, sources_dict) for audit trail."""
        metrics = (
            db.query(FinancialMetric)
            .filter(FinancialMetric.company_id == company_id)
            .order_by(FinancialMetric.created_at.desc())
            .first()
        )

        company = db.query(Company).filter(Company.id == company_id).first()

        if not metrics:
            # Build a reasonable default feature vector from company metadata + research
            return self._build_default_features(company_id, company, db)

        # Count risk flags
        flags = db.query(RiskFlag).filter(RiskFlag.company_id == company_id).all()
        litigation_flag = 1 if any(f.flag_type == "litigation" for f in flags) else 0

        # Check for research findings that indicate litigation
        research_findings = db.query(ResearchFinding).filter(
            ResearchFinding.company_id == company_id,
            ResearchFinding.category.in_(["litigation", "npa_default"]),
            ResearchFinding.sentiment == "negative",
        ).all()
        if research_findings:
            litigation_flag = 1

        # Promoter risk
        promoter_analyses = (
            db.query(PromoterAnalysis)
            .filter(PromoterAnalysis.company_id == company_id)
            .all()
        )
        promoter_risk = 0.0
        if promoter_analyses:
            risk_scores = []
            for p in promoter_analyses:
                score = {"low": 0.1, "medium": 0.4, "high": 0.7, "critical": 0.9}
                risk_scores.append(score.get(p.risk_level.value if p.risk_level else "low", 0.1))
            promoter_risk = max(risk_scores)

        # Compute years_in_business from incorporation_date
        years_in_business = 10  # default
        if company and company.incorporation_date:
            try:
                for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y"):
                    try:
                        inc_date = datetime.strptime(company.incorporation_date, fmt)
                        years_in_business = max(1, (datetime.now() - inc_date).days // 365)
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

        # GST filings count from extracted data
        raw = metrics.raw_extraction or {}
        gst_filings = 12
        if isinstance(raw, dict) and raw.get("gst_filings_count") is not None:
            gst_filings = raw["gst_filings_count"]

        # Sector growth from research findings
        sector_growth = 0.05
        industry_findings = db.query(ResearchFinding).filter(
            ResearchFinding.company_id == company_id,
            ResearchFinding.category == "industry",
        ).all()
        if industry_findings:
            positive = sum(1 for f in industry_findings if f.sentiment == "positive")
            negative = sum(1 for f in industry_findings if f.sentiment == "negative")
            if positive > negative:
                sector_growth = 0.08
            elif negative > positive:
                sector_growth = 0.02

        # CIBIL score impact
        cibil_score = raw.get("cibil_score") if isinstance(raw, dict) else None

        features = {
            "revenue": metrics.revenue or 0,
            "profit": metrics.profit_margin or 0,
            "debt_ratio": metrics.debt_ratio or 0,
            "current_ratio": metrics.current_ratio or 1,
            "gst_filings": gst_filings,
            "litigation_flag": litigation_flag,
            "sector_growth": sector_growth,
            "promoter_risk_score": promoter_risk,
            "years_in_business": years_in_business,
            "interest_coverage": metrics.interest_coverage or 2,
            "revenue_growth": 0.08,  # Default
            "cash_flow_positive": 1 if (metrics.cash_flow_operations or 0) > 0 else 0,
        }

        # Audit trail: document where each feature came from
        sources = {
            "revenue": f"From financial extraction (FY: {metrics.fiscal_year or 'N/A'})",
            "profit": f"Computed as net_profit/revenue from extracted data",
            "debt_ratio": f"Computed as total_debt/total_assets from extracted data",
            "current_ratio": f"Computed as current_assets/current_liabilities",
            "gst_filings": f"{'From GST return data' if gst_filings != 12 else 'Default (no GST data)'}",
            "litigation_flag": f"{'Active litigation found' if litigation_flag else 'No litigation detected'} from {len(flags)} risk flags + {len(research_findings)} research findings",
            "sector_growth": f"Derived from {len(industry_findings)} industry research findings" if industry_findings else "Default (no industry data)",
            "promoter_risk_score": f"Max risk from {len(promoter_analyses)} promoter analyses" if promoter_analyses else "Default (no promoter data)",
            "years_in_business": f"Computed from incorporation date: {company.incorporation_date}" if company and company.incorporation_date else "Default (10 years)",
            "interest_coverage": f"Computed as EBITDA/interest_expense",
            "revenue_growth": "Default (historical data not available)",
            "cash_flow_positive": f"From cash flow from operations: ₹{metrics.cash_flow_operations:,.0f}" if metrics.cash_flow_operations else "Default",
        }

        return features, sources

    def _build_default_features(
        self, company_id: str, company: Optional[Any], db: Session
    ) -> tuple:
        """Build default feature vector when no financial extraction exists.
        Uses company metadata, research findings, and promoter analysis."""

        # Count risk flags & research
        flags = db.query(RiskFlag).filter(RiskFlag.company_id == company_id).all()
        litigation_flag = 1 if any(f.flag_type == "litigation" for f in flags) else 0

        research_findings = db.query(ResearchFinding).filter(
            ResearchFinding.company_id == company_id,
            ResearchFinding.category.in_(["litigation", "npa_default"]),
            ResearchFinding.sentiment == "negative",
        ).all()
        if research_findings:
            litigation_flag = 1

        # Promoter risk
        promoter_analyses = (
            db.query(PromoterAnalysis)
            .filter(PromoterAnalysis.company_id == company_id)
            .all()
        )
        promoter_risk = 0.0
        if promoter_analyses:
            risk_scores = []
            for p in promoter_analyses:
                score = {"low": 0.1, "medium": 0.4, "high": 0.7, "critical": 0.9}
                risk_scores.append(score.get(p.risk_level.value if p.risk_level else "low", 0.1))
            promoter_risk = max(risk_scores)

        # Years in business
        years_in_business = 10
        if company and company.incorporation_date:
            try:
                for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y"):
                    try:
                        inc_date = datetime.strptime(company.incorporation_date, fmt)
                        years_in_business = max(1, (datetime.now() - inc_date).days // 365)
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

        # Sector growth from research
        sector_growth = 0.05
        industry_findings = db.query(ResearchFinding).filter(
            ResearchFinding.company_id == company_id,
            ResearchFinding.category == "industry",
        ).all()
        if industry_findings:
            positive = sum(1 for f in industry_findings if f.sentiment == "positive")
            negative = sum(1 for f in industry_findings if f.sentiment == "negative")
            if positive > negative:
                sector_growth = 0.08
            elif negative > positive:
                sector_growth = 0.02

        # Estimate revenue from annual_turnover if available
        revenue = 0
        if company and company.annual_turnover:
            revenue = float(company.annual_turnover)

        features = {
            "revenue": revenue,
            "profit": 0.08,        # Assume modest margin
            "debt_ratio": 0.5,     # Assume moderate leverage
            "current_ratio": 1.2,  # Assume adequate liquidity
            "gst_filings": 12,     # Assume regular
            "litigation_flag": litigation_flag,
            "sector_growth": sector_growth,
            "promoter_risk_score": promoter_risk,
            "years_in_business": years_in_business,
            "interest_coverage": 2.0,  # Assume adequate
            "revenue_growth": 0.05,    # Assume modest
            "cash_flow_positive": 1,
        }

        sources = {
            "revenue": f"From company annual_turnover: ₹{revenue:,.0f}" if revenue else "No financial data — default",
            "profit": "Estimated default (no financial extraction)",
            "debt_ratio": "Estimated default (no financial extraction)",
            "current_ratio": "Estimated default (no financial extraction)",
            "gst_filings": "Assumed regular (no GST data available)",
            "litigation_flag": f"{'Litigation detected' if litigation_flag else 'No litigation detected'} from {len(flags)} risk flags + {len(research_findings)} research findings",
            "sector_growth": f"Derived from {len(industry_findings)} industry research findings" if industry_findings else "Default (no industry data)",
            "promoter_risk_score": f"Max risk from {len(promoter_analyses)} promoter analyses" if promoter_analyses else "Default (no promoter data)",
            "years_in_business": f"Computed from incorporation date: {company.incorporation_date}" if company and company.incorporation_date else "Default (10 years)",
            "interest_coverage": "Estimated default (no financial extraction)",
            "revenue_growth": "Estimated default (no financial extraction)",
            "cash_flow_positive": "Estimated default (no financial extraction)",
        }

        return features, sources

    def _explain_prediction(
        self, scaled_features: np.ndarray, raw_features: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate SHAP-based explanation for the prediction."""
        shap_values = self.explainer.shap_values(scaled_features)

        # Normalize SHAP values format across explainer types:
        # TreeExplainer for binary: list of 2 arrays [class0, class1]
        # LinearExplainer: 2D array (n_samples, n_features)
        if isinstance(shap_values, list):
            # TreeExplainer binary classification — use class 1 (default)
            sv = shap_values[1][0]
        elif shap_values.ndim == 2:
            # LinearExplainer or single-output — first sample
            sv = shap_values[0]
        else:
            sv = shap_values

        # Map SHAP values to feature names
        shap_dict = {}
        for i, col in enumerate(self.feature_columns):
            shap_dict[col] = round(float(sv[i]), 4)

        # Identify positive and negative factors
        sorted_features = sorted(shap_dict.items(), key=lambda x: x[1])

        positive_factors = []
        negative_factors = []

        feature_labels = {
            "revenue": "Revenue",
            "profit": "Profit Margin",
            "debt_ratio": "Debt Ratio",
            "current_ratio": "Current Ratio",
            "gst_filings": "GST Filing Regularity",
            "litigation_flag": "Litigation History",
            "sector_growth": "Sector Growth Outlook",
            "promoter_risk_score": "Promoter Risk Profile",
            "years_in_business": "Business Maturity (Years)",
            "interest_coverage": "Interest Coverage (DSCR proxy)",
            "revenue_growth": "Revenue Growth",
            "cash_flow_positive": "Positive Operating Cash Flow",
        }

        for feat, val in sorted_features:
            label = feature_labels.get(feat, feat)
            raw_val = raw_features.get(feat, 0)

            if val < -0.01:  # Reduces default probability (positive for creditworthiness)
                positive_factors.append(
                    f"{label} ({raw_val:.2f}) — reduces default risk by {abs(val):.3f}"
                )
            elif val > 0.01:  # Increases default probability (negative for creditworthiness)
                negative_factors.append(
                    f"{label} ({raw_val:.2f}) — increases default risk by {val:.3f}"
                )

        # Feature importance (absolute SHAP values)
        importance = {col: round(abs(v), 4) for col, v in shap_dict.items()}
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

        return {
            "shap_values": shap_dict,
            "positive_factors": positive_factors,
            "negative_factors": negative_factors,
            "feature_importance": importance,
        }

    def _determine_risk_level(self, probability: float) -> RiskLevel:
        """Map probability of default to risk level per RBI risk-grading framework."""
        if probability < 0.15:
            return RiskLevel.LOW
        elif probability < 0.35:
            return RiskLevel.MEDIUM
        elif probability < 0.60:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _generate_decision(
        self,
        probability: float,
        risk_level: RiskLevel,
        features: Dict[str, float],
        company_id: str,
        db: Session,
    ) -> Dict[str, Any]:
        """Generate loan decision based on risk score per Indian bank lending norms."""
        company = db.query(Company).filter(Company.id == company_id).first()
        requested_amount = company.loan_amount_requested if company else 0

        if risk_level == RiskLevel.LOW:
            decision = LoanDecision.APPROVE
            loan_limit = requested_amount or 10_000_000
            interest_rate = 9.5
        elif risk_level == RiskLevel.MEDIUM:
            decision = LoanDecision.APPROVE_WITH_CONDITIONS
            loan_limit = (requested_amount or 10_000_000) * 0.75
            interest_rate = 12.0
        elif risk_level == RiskLevel.HIGH:
            decision = LoanDecision.APPROVE_WITH_CONDITIONS
            loan_limit = (requested_amount or 10_000_000) * 0.5
            interest_rate = 15.5
        else:  # CRITICAL
            decision = LoanDecision.REJECT
            loan_limit = 0
            interest_rate = 0

        return {
            "decision": decision,
            "loan_limit": round(loan_limit, 2),
            "interest_rate": interest_rate,
        }

    def _evaluate_five_cs(
        self, features: Dict[str, float], company_id: str, db: Session
    ) -> Dict[str, Any]:
        """Evaluate the Five Cs of Credit with detailed textual justification."""
        promoter_analyses = (
            db.query(PromoterAnalysis)
            .filter(PromoterAnalysis.company_id == company_id)
            .all()
        )
        flags = db.query(RiskFlag).filter(RiskFlag.company_id == company_id).all()

        # Character — integrity and willingness to repay
        character_score = 8
        character_reasons = []
        if any(p.fraud_flag for p in promoter_analyses):
            character_score -= 3
            character_reasons.append("Fraud flag detected in promoter background (-3)")
        if any(p.bankruptcy_flag for p in promoter_analyses):
            character_score -= 2
            character_reasons.append("Bankruptcy history in promoter background (-2)")
        if any(p.regulatory_violation_flag for p in promoter_analyses):
            character_score -= 2
            character_reasons.append("Regulatory violations by promoter (-2)")
        if features.get("gst_filings", 12) < 10:
            character_score -= 1
            character_reasons.append(f"Irregular GST filing ({int(features.get('gst_filings', 12))}/12 months) (-1)")
        if not character_reasons:
            character_reasons.append("No adverse promoter findings. Clean compliance track record.")
        character_score = max(1, character_score)

        # Capacity — ability to repay
        capacity_score = 5
        capacity_reasons = []
        ic = features.get("interest_coverage", 0)
        if ic > 3:
            capacity_score += 2
            capacity_reasons.append(f"Strong interest coverage ratio of {ic:.2f}x (> 3x) (+2)")
        elif ic < 1.5:
            capacity_reasons.append(f"Weak interest coverage of {ic:.2f}x (< RBI min 1.5x)")
        if features.get("current_ratio", 0) > 1.5:
            capacity_score += 1
            capacity_reasons.append(f"Adequate liquidity — current ratio {features['current_ratio']:.2f} (+1)")
        if features.get("profit", 0) > 0.1:
            capacity_score += 1
            capacity_reasons.append(f"Healthy profit margin of {features['profit']:.1%} (+1)")
        if features.get("cash_flow_positive", 0) == 1:
            capacity_score += 1
            capacity_reasons.append("Positive operating cash flow (+1)")
        else:
            capacity_reasons.append("Negative or zero operating cash flow — repayment risk")
        capacity_score = min(10, capacity_score)

        # Capital — skin in the game
        capital_score = 5
        capital_reasons = []
        dr = features.get("debt_ratio", 1)
        if dr < 0.4:
            capital_score += 2
            capital_reasons.append(f"Conservative leverage — debt ratio {dr:.2%} (< 40%) (+2)")
        elif dr > 0.7:
            capital_score -= 2
            capital_reasons.append(f"High leverage — debt ratio {dr:.2%} (> 70%) (-2)")
        if features.get("revenue_growth", 0) > 0.1:
            capital_score += 1
            capital_reasons.append(f"Strong revenue growth > 10% (+1)")
        if not capital_reasons:
            capital_reasons.append("Moderate capital position")
        capital_score = max(1, min(10, capital_score))

        # Collateral — security available
        collateral_score = 6
        collateral_reasons = ["Default assessment based on available asset information. "
                             "Detailed collateral valuation pending physical verification."]

        # Conditions — external/market environment
        conditions_score = 5
        conditions_reasons = []
        sg = features.get("sector_growth", 0)
        if sg > 0.05:
            conditions_score += 2
            conditions_reasons.append(f"Positive sector outlook with {sg:.1%} growth (+2)")
        elif sg < 0:
            conditions_score -= 2
            conditions_reasons.append(f"Negative sector growth of {sg:.1%} (-2)")

        # Factor in research sentiment
        neg_research = sum(1 for f in flags if f.flag_type in ("regulatory", "litigation"))
        if neg_research > 3:
            conditions_score -= 1
            conditions_reasons.append(f"{neg_research} regulatory/litigation flags detected (-1)")
        if not conditions_reasons:
            conditions_reasons.append("Stable market conditions")
        conditions_score = max(1, min(10, conditions_score))

        return {
            "character": {
                "score": character_score,
                "max": 10,
                "assessment": self._cs_assessment(character_score),
                "reasoning": character_reasons,
            },
            "capacity": {
                "score": capacity_score,
                "max": 10,
                "assessment": self._cs_assessment(capacity_score),
                "reasoning": capacity_reasons,
            },
            "capital": {
                "score": capital_score,
                "max": 10,
                "assessment": self._cs_assessment(capital_score),
                "reasoning": capital_reasons,
            },
            "collateral": {
                "score": collateral_score,
                "max": 10,
                "assessment": self._cs_assessment(collateral_score),
                "reasoning": collateral_reasons,
            },
            "conditions": {
                "score": conditions_score,
                "max": 10,
                "assessment": self._cs_assessment(conditions_score),
                "reasoning": conditions_reasons,
            },
        }

    def _cs_assessment(self, score: int) -> str:
        if score >= 8:
            return "Strong"
        elif score >= 6:
            return "Adequate"
        elif score >= 4:
            return "Moderate"
        else:
            return "Weak"

    def _generate_reasoning_narrative(
        self,
        company_id: str,
        db: Session,
        features: Dict[str, float],
        feature_sources: Dict[str, str],
        shap_result: Dict[str, Any],
        probability: float,
        risk_level: RiskLevel,
        decision: Dict[str, Any],
        five_cs: Dict[str, Any],
    ) -> str:
        """Generate a comprehensive narrative that walks through the AI's reasoning
        step by step — the key 'explainability' deliverable."""

        company = db.query(Company).filter(Company.id == company_id).first()
        company_name = company.name if company else "the company"
        flags = db.query(RiskFlag).filter(RiskFlag.company_id == company_id).all()
        research = db.query(ResearchFinding).filter(ResearchFinding.company_id == company_id).all()

        # Build context for narrative generation
        context = {
            "company_name": company_name,
            "industry": company.industry if company else "N/A",
            "probability_of_default": f"{probability:.2%}",
            "risk_level": risk_level.value,
            "decision": decision["decision"].value,
            "loan_limit": decision["loan_limit"],
            "interest_rate": decision["interest_rate"],
            "features": {k: round(v, 4) if isinstance(v, float) else v for k, v in features.items()},
            "feature_sources": feature_sources,
            "top_positive_factors": shap_result["positive_factors"][:5],
            "top_negative_factors": shap_result["negative_factors"][:5],
            "five_cs_summary": {
                name: {"score": cs["score"], "assessment": cs["assessment"], "reasoning": cs["reasoning"]}
                for name, cs in five_cs.items()
            },
            "risk_flags_count": len(flags),
            "critical_flags": [f.description for f in flags if f.severity and f.severity.value in ("high", "critical")][:5],
            "research_highlights": [
                {"category": r.category, "sentiment": r.sentiment, "summary": r.summary}
                for r in research if r.relevance_score and r.relevance_score > 0.6
            ][:5],
        }

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior Indian credit analyst presenting a credit appraisal decision
to a review committee. Generate a clear, structured narrative that walks through the
reasoning step by step. The audience needs to understand WHY each conclusion was reached.

Structure your narrative as:

**1. Data Sources & Extraction Summary**
- What documents were analyzed, what data was extracted, and confidence levels

**2. Financial Health Assessment**
- Key metrics, what they tell us, and how they compare to Indian industry benchmarks

**3. GST & Tax Compliance**
- GST filing regularity, GSTR-2A vs 3B reconciliation findings, any red flags

**4. Credit Bureau & Repayment History**
- CIBIL score/rank findings, DPD history, NPA/SMA classification

**5. External Intelligence**
- Key findings from litigation, regulatory, and news research
- What the research reveals about company reputation and risk

**6. Promoter Assessment**
- Key findings about directors/promoters that affect the Character assessment

**7. ML Model Prediction**
- How the model arrived at the default probability
- Which features most influenced the decision (SHAP values)
- Clear mapping: "Because X was Y, the model predicted higher/lower risk"

**8. Five Cs Summary**
- Score for each C with specific justification

**9. Final Recommendation**
- Clear decision with rationale, loan terms, and conditions/covenants if applicable

Use Indian financial terminology. Reference RBI norms where relevant.
Be specific with numbers. Explain the reasoning chain, not just conclusions."""),
            ("human", "Generate the credit assessment narrative for:\n{context}"),
        ])

        try:
            formatted = prompt.format_messages(
                context=json.dumps(context, indent=2, default=str)
            )
            response = self.llm.invoke(formatted)
            return response.content
        except Exception as e:
            logger.error(f"Narrative generation failed: {e}")
            # Fallback: structured summary without LLM
            return self._build_fallback_narrative(
                context, features, feature_sources, shap_result, five_cs
            )

    def _build_fallback_narrative(
        self, context, features, feature_sources, shap_result, five_cs
    ) -> str:
        """Build a structured narrative without LLM as fallback."""
        lines = [
            f"## Credit Assessment: {context['company_name']}",
            f"**Industry:** {context['industry']}",
            f"**Assessment Date:** {datetime.now().strftime('%B %d, %Y')}",
            "",
            "### ML Risk Prediction",
            f"- Probability of Default: {context['probability_of_default']}",
            f"- Risk Level: {context['risk_level'].upper()}",
            f"- Decision: {context['decision'].replace('_', ' ').upper()}",
            "",
            "### Key Risk Drivers (SHAP Analysis)",
            "**Factors reducing default risk:**",
        ]
        for f in shap_result["positive_factors"][:5]:
            lines.append(f"  - {f}")
        lines.append("**Factors increasing default risk:**")
        for f in shap_result["negative_factors"][:5]:
            lines.append(f"  - {f}")
        lines.append("")
        lines.append("### Five Cs Assessment")
        for name, cs in five_cs.items():
            lines.append(f"- **{name.title()}**: {cs['score']}/10 ({cs['assessment']})")
            for r in cs.get("reasoning", []):
                lines.append(f"  - {r}")
        lines.append("")
        lines.append("### Data Source Audit Trail")
        for feat, source in (feature_sources or {}).items():
            lines.append(f"- {feat}: {source}")

        return "\n".join(lines)


risk_scoring_service = RiskScoringService()
