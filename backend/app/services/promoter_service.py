"""
Promoter Risk Analysis Service
Searches for promoter background and identifies risk factors.
"""

import json
import re
import logging
from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import PromoterAnalysis, RiskLevel, FinancialMetric
from app.services.research_service import research_intelligence_service

logger = logging.getLogger(__name__)
settings = get_settings()


class PromoterRiskService:
    """Analyzes promoter/director risk profiles."""

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                api_key=settings.openai_api_key,
            )
        return self._llm

    def analyze_promoters(
        self,
        company_id: str,
        company_name: str,
        promoter_names: List[str],
        db: Session,
    ) -> List[Dict[str, Any]]:
        """Run promoter risk analysis for all identified promoters."""
        # If no promoter names provided, try to get from extracted financials
        if not promoter_names:
            promoter_names = self._get_promoter_names_from_db(company_id, db)

        if not promoter_names:
            # Use GPT to identify key promoters/directors
            promoter_names = self._identify_promoters_via_gpt(company_name)

        if not promoter_names:
            logger.warning(f"No promoter names found for company {company_id}")
            return []

        results = []
        for name in promoter_names:
            try:
                analysis = self._analyze_single_promoter(name, company_name)
                promoter_record = PromoterAnalysis(
                    company_id=company_id,
                    promoter_name=name,
                    designation=analysis.get("designation"),
                    background_summary=analysis.get("background_summary"),
                    bankruptcy_flag=analysis.get("bankruptcy_flag", False),
                    fraud_flag=analysis.get("fraud_flag", False),
                    regulatory_violation_flag=analysis.get("regulatory_violation_flag", False),
                    associated_companies=analysis.get("associated_companies"),
                    risk_summary=analysis.get("risk_summary"),
                    risk_level=analysis.get("risk_level", RiskLevel.LOW),
                    sources=analysis.get("sources"),
                )
                db.add(promoter_record)
                results.append(analysis)
            except Exception as e:
                logger.error(f"Promoter analysis failed for {name}: {e}")

        db.commit()
        return results

    def _get_promoter_names_from_db(self, company_id: str, db: Session) -> List[str]:
        """Retrieve promoter names from previously extracted financial data."""
        metrics = (
            db.query(FinancialMetric)
            .filter(FinancialMetric.company_id == company_id)
            .all()
        )
        names = set()
        for m in metrics:
            if m.director_names:
                for name in m.director_names:
                    names.add(name)
        return list(names)

    def _identify_promoters_via_gpt(self, company_name: str) -> List[str]:
        """Use GPT to identify key promoters/directors of a company."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a corporate research analyst specializing in Indian companies.
Given a company name, return the names of 2-4 key promoters, directors, or senior management personnel.
Return ONLY a valid JSON array of full names. Example: ["John Doe", "Jane Smith"]
If you are not sure about specific names, provide the most likely senior leadership based on your knowledge.
Do not include markdown fencing or any other text outside the JSON array."""),
            ("human", "Company: {company_name}\nReturn the key promoters/directors as a JSON array."),
        ])
        try:
            formatted = prompt.format_messages(company_name=company_name)
            response = self.llm.invoke(formatted)
            raw = response.content.strip()
            # Strip markdown fences if present
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
            if json_match:
                raw = json_match.group(1).strip()
            # Extract just the JSON array portion
            array_match = re.search(r'\[[\s\S]*\]', raw)
            if array_match:
                raw = array_match.group(0)
            names = json.loads(raw)
            if isinstance(names, list) and all(isinstance(n, str) for n in names):
                logger.info(f"GPT identified {len(names)} promoters for {company_name}: {names}")
                return names[:4]
        except json.JSONDecodeError:
            # Fallback: try to extract quoted names from the raw response
            fallback_names = re.findall(r'"([A-Z][a-zA-Z\s.]+?)"', raw if 'raw' in dir() else response.content)
            if fallback_names:
                logger.info(f"GPT promoter ID fallback extracted: {fallback_names}")
                return fallback_names[:4]
            logger.error(f"GPT promoter identification failed: could not parse JSON from response")
        except Exception as e:
            logger.error(f"GPT promoter identification failed: {e}")
        return []

    def _analyze_single_promoter(
        self, promoter_name: str, company_name: str
    ) -> Dict[str, Any]:
        """Analyze a single promoter's background and risk profile."""
        # Search web for promoter information
        search_results = research_intelligence_service._search_web(
            f'"{promoter_name}" director company fraud bankruptcy litigation'
        )

        # Collect snippets from search results
        web_context = ""
        sources = []
        for result in search_results[:5]:
            web_context += f"\nTitle: {result.get('title', '')}\n"
            web_context += f"Snippet: {result.get('snippet', '')}\n"
            sources.append(result.get("link", ""))

            # Try to scrape for more context
            content = research_intelligence_service._scrape_page(result.get("link", ""))
            if content:
                web_context += f"Content: {content[:2000]}\n"

        # Use GPT to analyze
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a corporate due diligence analyst. Analyze the background of a company promoter/director
for credit risk assessment. Based on the web research provided, generate a risk assessment.

Respond in JSON format:
{{
    "designation": "likely designation or role",
    "background_summary": "2-3 paragraph background summary",
    "bankruptcy_flag": true/false,
    "fraud_flag": true/false,
    "regulatory_violation_flag": true/false,
    "associated_companies": ["list of associated companies"],
    "risk_summary": "1-2 sentence risk summary",
    "risk_level": "low" or "medium" or "high" or "critical"
}}

Be factual. Only flag risks that are supported by the evidence. If no negative information is found, indicate low risk."""),
            ("human", """Promoter Name: {promoter_name}
Company: {company_name}

Web Research Results:
{web_context}"""),
        ])

        try:
            formatted = prompt.format_messages(
                promoter_name=promoter_name,
                company_name=company_name,
                web_context=web_context[:8000],
            )
            response = self.llm.invoke(formatted)
            raw = response.content.strip()
            # Strip markdown code fences
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
            if json_match:
                raw = json_match.group(1).strip()
            analysis = json.loads(raw)
            analysis["sources"] = sources

            # Map risk_level string to enum
            risk_map = {
                "low": RiskLevel.LOW,
                "medium": RiskLevel.MEDIUM,
                "high": RiskLevel.HIGH,
                "critical": RiskLevel.CRITICAL,
            }
            analysis["risk_level"] = risk_map.get(
                analysis.get("risk_level", "low"), RiskLevel.LOW
            )
            return analysis
        except Exception as e:
            logger.error(f"GPT analysis failed for promoter {promoter_name}: {e}")
            return {
                "designation": None,
                "background_summary": "Analysis could not be completed.",
                "bankruptcy_flag": False,
                "fraud_flag": False,
                "regulatory_violation_flag": False,
                "associated_companies": [],
                "risk_summary": "Insufficient data for risk assessment.",
                "risk_level": RiskLevel.MEDIUM,
                "sources": sources,
            }


promoter_risk_service = PromoterRiskService()
