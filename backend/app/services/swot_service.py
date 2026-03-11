"""
SWOT Analysis Service
Generates comprehensive SWOT analysis by triangulating extracted financial data,
research findings, promoter analysis, and risk flags using GPT-4o-mini.
"""

import json
import logging
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import (
    Company, FinancialMetric, RiskFlag, ResearchFinding,
    PromoterAnalysis, RiskScore, SWOTAnalysis,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class SWOTAnalysisService:
    """Generates AI-powered SWOT analysis triangulating multiple data sources."""

    def _get_llm(self):
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=settings.openai_api_key,
        )

    def generate_swot(self, company_id: str, db: Session) -> Dict[str, Any]:
        """Generate SWOT analysis from all available data sources."""
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"Company not found: {company_id}")

        # Gather all data sources
        metrics = (
            db.query(FinancialMetric)
            .filter(FinancialMetric.company_id == company_id)
            .order_by(FinancialMetric.created_at.desc())
            .all()
        )
        risk_flags = db.query(RiskFlag).filter(RiskFlag.company_id == company_id).all()
        research = db.query(ResearchFinding).filter(ResearchFinding.company_id == company_id).all()
        promoters = db.query(PromoterAnalysis).filter(PromoterAnalysis.company_id == company_id).all()
        risk_score = (
            db.query(RiskScore)
            .filter(RiskScore.company_id == company_id)
            .order_by(RiskScore.created_at.desc())
            .first()
        )

        # Build context for the LLM
        fin_context = self._build_financial_context(metrics)
        research_context = self._build_research_context(research)
        promoter_context = self._build_promoter_context(promoters)
        risk_context = self._build_risk_context(risk_flags, risk_score)

        data_sources = {
            "financial_records": len(metrics),
            "research_findings": len(research),
            "promoter_analyses": len(promoters),
            "risk_flags": len(risk_flags),
            "has_risk_score": risk_score is not None,
        }

        llm = self._get_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an expert Indian corporate credit analyst specializing in SWOT analysis. "
             "Generate a comprehensive SWOT analysis for a credit appraisal by triangulating "
             "financial data, web research, promoter backgrounds, and risk flags. "
             "Consider Indian-specific factors: RBI norms, GST compliance, CIBIL scores, "
             "sector trends in India, regulatory environment, and macro-economic conditions. "
             "Each SWOT item should be specific, data-backed, and actionable."),
            ("human",
             "Company: {company_name}\n"
             "Industry: {industry}\n"
             "Loan Requested: ₹{loan_amount}\n"
             "Loan Type: {loan_type}\n"
             "Annual Turnover: ₹{turnover}\n\n"
             "=== FINANCIAL DATA ===\n{fin_context}\n\n"
             "=== RESEARCH INTELLIGENCE ===\n{research_context}\n\n"
             "=== PROMOTER ANALYSIS ===\n{promoter_context}\n\n"
             "=== RISK FLAGS & SCORE ===\n{risk_context}\n\n"
             "Generate a detailed SWOT analysis. Return ONLY valid JSON:\n"
             '{{"strengths": ["specific strength 1", "specific strength 2", ...], '
             '"weaknesses": ["specific weakness 1", ...], '
             '"opportunities": ["specific opportunity 1", ...], '
             '"threats": ["specific threat 1", ...], '
             '"summary": "2-3 sentence executive summary of the SWOT analysis"}}'
             ),
        ])

        chain = prompt | llm | StrOutputParser()
        raw = chain.invoke({
            "company_name": company.name,
            "industry": company.industry or "General",
            "loan_amount": f"{company.loan_amount_requested:,.0f}" if company.loan_amount_requested else "N/A",
            "loan_type": company.loan_type or company.loan_purpose or "N/A",
            "turnover": f"{company.annual_turnover:,.0f}" if company.annual_turnover else "N/A",
            "fin_context": fin_context,
            "research_context": research_context,
            "promoter_context": promoter_context,
            "risk_context": risk_context,
        })

        # Parse LLM response
        parsed = self._parse_json(raw)
        if not parsed:
            parsed = {
                "strengths": ["Analysis could not be fully parsed"],
                "weaknesses": ["Insufficient data for complete analysis"],
                "opportunities": ["Further data collection recommended"],
                "threats": ["Incomplete analysis may miss critical factors"],
                "summary": raw[:500],
            }

        # Save to database
        swot = SWOTAnalysis(
            company_id=company_id,
            strengths=parsed.get("strengths", []),
            weaknesses=parsed.get("weaknesses", []),
            opportunities=parsed.get("opportunities", []),
            threats=parsed.get("threats", []),
            summary=parsed.get("summary", ""),
            data_sources=data_sources,
        )
        db.add(swot)
        db.commit()
        db.refresh(swot)

        return {
            "swot_id": str(swot.id),
            "strengths": swot.strengths,
            "weaknesses": swot.weaknesses,
            "opportunities": swot.opportunities,
            "threats": swot.threats,
            "summary": swot.summary,
            "data_sources": data_sources,
        }

    def _build_financial_context(self, metrics) -> str:
        if not metrics:
            return "No financial data available."
        items = []
        for m in metrics[:3]:
            items.append(
                f"FY {m.fiscal_year or 'N/A'}: Revenue=₹{m.revenue or 'N/A'}, "
                f"Profit=₹{m.net_profit or 'N/A'}, EBITDA=₹{m.ebitda or 'N/A'}, "
                f"Debt Ratio={m.debt_ratio or 'N/A'}, Current Ratio={m.current_ratio or 'N/A'}, "
                f"Interest Coverage={m.interest_coverage or 'N/A'}, "
                f"Profit Margin={m.profit_margin or 'N/A'}"
            )
        return "\n".join(items)

    def _build_research_context(self, research) -> str:
        if not research:
            return "No research intelligence available."
        items = []
        for r in research[:10]:
            items.append(
                f"[{r.category}] {r.title}: {r.summary[:200] if r.summary else 'N/A'} "
                f"(Sentiment: {r.sentiment}, Relevance: {r.relevance_score})"
            )
        return "\n".join(items)

    def _build_promoter_context(self, promoters) -> str:
        if not promoters:
            return "No promoter analysis available."
        items = []
        for p in promoters:
            flags = []
            if p.bankruptcy_flag:
                flags.append("BANKRUPTCY")
            if p.fraud_flag:
                flags.append("FRAUD")
            if p.regulatory_violation_flag:
                flags.append("REGULATORY")
            items.append(
                f"{p.promoter_name} ({p.designation or 'N/A'}): "
                f"Risk={p.risk_level.value if p.risk_level else 'N/A'}, "
                f"Flags=[{', '.join(flags) if flags else 'None'}], "
                f"Summary: {p.risk_summary or 'N/A'}"
            )
        return "\n".join(items)

    def _build_risk_context(self, risk_flags, risk_score) -> str:
        parts = []
        if risk_score:
            parts.append(
                f"ML Risk Score: PD={risk_score.probability_of_default:.2%}, "
                f"Level={risk_score.risk_level.value if risk_score.risk_level else 'N/A'}, "
                f"Decision={risk_score.decision.value if risk_score.decision else 'N/A'}"
            )
        if risk_flags:
            for f in risk_flags[:10]:
                parts.append(
                    f"[{f.severity.value if f.severity else 'medium'}] {f.flag_type}: {f.description}"
                )
        return "\n".join(parts) if parts else "No risk data available."

    def _parse_json(self, text: str):
        text = text.strip()
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        return None


swot_analysis_service = SWOTAnalysisService()
