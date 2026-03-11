"""
Multi-Agent News Intelligence Service
Uses LangChain multi-chain approach for autonomous research and news gathering.
Specialized LLM chains work together to find company news, sector analysis, and regulatory updates.
"""

import logging
import json
from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import ResearchFinding

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Agent Prompt Templates ──
## Each prompt instructs the LLM to return ONLY a valid JSON array/object with specific fields for structured parsing.

NEWS_ANALYST_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a seasoned Indian business journalist with deep knowledge of "
     "corporate India. You specialize in tracking company developments, "
     "management changes, financial results, and market sentiment for mid-sized "
     "Indian corporates. You always reference news from Economic Times, Moneycontrol, "
     "LiveMint, Business Standard, and other Indian financial media."),
    ("human",
     "Research and compile the latest news about {company_name} from Indian business media. "
     "Look for: financial results, management changes, major contracts, expansions, "
     "controversies, fraud allegations, and market sentiment.\n\n"
     "Return ONLY a valid JSON array of 3-5 findings:\n"
     '[{{"title": "...", "summary": "2-3 sentences", "sentiment": "positive/negative/neutral", '
     '"relevance": 0.0-1.0, "category": "news"}}]'),
])

REGULATORY_ANALYST_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert in Indian corporate regulations with deep knowledge of "
     "RBI circulars, SEBI orders, MCA/ROC filings, NCLT/NCLAT proceedings, "
     "DRT cases, GST/DGGI investigations, and NGT orders. You understand the "
     "credit risk implications of each regulatory finding."),
    ("human",
     "Investigate {company_name} for any regulatory actions, legal proceedings, or compliance issues in India. "
     "Check for: SEBI orders, RBI penalties, NCLT proceedings, DRT cases, GST demands, "
     "MCA defaults, wilful defaulter status, SARFAESI actions, and environmental violations.\n\n"
     "Return ONLY a valid JSON array of 3-5 findings:\n"
     '[{{"title": "...", "summary": "2-3 sentences", "sentiment": "positive/negative/neutral", '
     '"relevance": 0.0-1.0, "category": "regulatory"}}]'),
])

SECTOR_ANALYST_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a sector research analyst at a top Indian bank. You track industry "
     "trends, government policies, commodity prices, and macroeconomic factors "
     "that affect corporate creditworthiness in India. You reference CRISIL, "
     "ICRA, and RBI reports."),
    ("human",
     "Analyze the {industry} sector in India and its implications for {company_name}'s creditworthiness. "
     "Cover: sector growth outlook, regulatory changes, competition, commodity price impact, "
     "government policy support/headwinds, and key risk factors.\n\n"
     "Return ONLY a valid JSON array of 2-3 findings:\n"
     '[{{"title": "...", "summary": "2-3 sentences", "sentiment": "positive/negative/neutral", '
     '"relevance": 0.0-1.0, "category": "industry"}}]'),
])

SYNTHESIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior credit analyst at an Indian bank. You take news, regulatory, "
     "and sector research and distill it into actionable credit risk insights. "
     "You classify findings by severity and relate them to the Five Cs of credit. "
     "You are familiar with RBI IRAC norms and NPA classification."),
    ("human",
     "Review all research gathered about {company_name} and create a synthesized credit risk summary.\n\n"
     "NEWS FINDINGS:\n{news_findings}\n\n"
     "REGULATORY FINDINGS:\n{regulatory_findings}\n\n"
     "SECTOR FINDINGS:\n{sector_findings}\n\n"
     "Return ONLY valid JSON:\n"
     '{{"overall_sentiment": "positive/negative/neutral", '
     '"risk_level": "low/medium/high/critical", '
     '"top_concerns": ["..."], "top_positives": ["..."], '
     '"five_cs_mapping": {{"character": "...", "capacity": "...", "capital": "...", '
     '"collateral": "...", "conditions": "..."}}}}'),
])


def _parse_json_array(text: str) -> List[Dict[str, Any]]:
    """Extract and parse a JSON array from LLM output."""
    text = text.strip()
    start = text.find('[')
    end = text.rfind(']') + 1
    if start >= 0 and end > start:
        try:
            parsed = json.loads(text[start:end])
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
    # Try as single object
    start = text.find('{')
    end = text.rfind('}') + 1
    if start >= 0 and end > start:
        try:
            parsed = json.loads(text[start:end])
            if isinstance(parsed, dict):
                return [parsed]
        except json.JSONDecodeError:
            pass
    return []


def _parse_json_object(text: str) -> Dict[str, Any]:
    """Extract and parse a JSON object from LLM output."""
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}') + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return {}


class CrewAIResearchService:
    """Orchestrates multi-chain LLM research for company intelligence."""

    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                api_key=settings.openai_api_key,
            )
        return self._llm

    def _run_chain(self, prompt_template, variables: dict) -> str:
        """Run a single LangChain prompt and return raw text."""
        chain = prompt_template | self._get_llm() | StrOutputParser()
        return chain.invoke(variables)

    def run_crew_research(
        self,
        company_name: str,
        industry: str,
        company_id: str,
        db: Session,
    ) -> Dict[str, Any]:
        """Run multi-chain research pipeline.
        Returns dict with 'findings' list and 'synthesis' dict."""

        result = {"findings": [], "synthesis": None}
        industry = industry or "general"

        try:
            logger.info(f"Starting multi-agent research for {company_name}")

            # ── Run specialist chains ──
            news_raw = self._run_chain(
                NEWS_ANALYST_PROMPT,
                {"company_name": company_name},
            )
            regulatory_raw = self._run_chain(
                REGULATORY_ANALYST_PROMPT,
                {"company_name": company_name},
            )
            sector_raw = self._run_chain(
                SECTOR_ANALYST_PROMPT,
                {"company_name": company_name, "industry": industry},
            )

            # ── Parse specialist outputs ──
            chain_outputs = [
                (news_raw, "news"),
                (regulatory_raw, "regulatory"),
                (sector_raw, "industry"),
            ]

            for raw, category in chain_outputs:
                parsed_list = _parse_json_array(raw)
                for finding in parsed_list:
                    finding_record = {
                        "company_id": company_id,
                        "category": finding.get("category", category),
                        "title": finding.get("title", ""),
                        "summary": finding.get("summary", ""),
                        "source_url": finding.get("source_url", ""),
                        "sentiment": finding.get("sentiment", "neutral"),
                        "relevance_score": float(finding.get("relevance", 0.5)),
                        "raw_content": raw[:5000],
                    }
                    result["findings"].append(finding_record)
                    db.add(ResearchFinding(**finding_record))

            # ── Run synthesis chain ──
            synthesis_raw = self._run_chain(
                SYNTHESIS_PROMPT,
                {
                    "company_name": company_name,
                    "news_findings": news_raw,
                    "regulatory_findings": regulatory_raw,
                    "sector_findings": sector_raw,
                },
            )
            result["synthesis"] = _parse_json_object(synthesis_raw) or {"summary": synthesis_raw[:500]}

            db.commit()
            logger.info(
                f"Multi-agent research complete for {company_name}: "
                f"{len(result['findings'])} findings"
            )

        except Exception as e:
            logger.error(f"Multi-agent research failed for {company_name}: {e}")
            db.rollback()

        return result


crew_research_service = CrewAIResearchService()
