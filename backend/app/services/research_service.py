"""
Research Intelligence Service
Uses SerpAPI for web search and BeautifulSoup for scraping.
LangChain + GPT for summarization.
Enhanced with deep Indian regulatory and legal source coverage.
"""

import logging
import time
import json
import re
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import ResearchFinding

logger = logging.getLogger(__name__)
settings = get_settings() 

# India-specific research categories with targeted search queries
INDIA_RESEARCH_QUERIES = {
    "litigation": [
        '"{company}" litigation court cases India',
        '"{company}" NCLT NCLAT insolvency proceedings',
        '"{company}" site:indiankanoon.org',
    ],
    "regulatory": [
        '"{company}" regulatory action penalty India',
        '"{company}" SEBI order penalty show cause',
        '"{company}" RBI penalty regulatory action',
        '"{company}" MCA ROC compliance default',
    ],
    "gst_compliance": [
        '"{company}" GST defaulter tax evasion',
        '"{company}" GST notice demand DGGI',
    ],
    "industry": [
        '"{company}" industry outlook sector analysis India',
    ],
    "reputation": [
        '"{company}" company reputation news India',
        '"{company}" SFIO investigation fraud India',
    ],
    "fraud_risk": [
        '"{company}" financial fraud default NPA India',
        '"{company}" wilful defaulter RBI bank',
    ],
    "npa_default": [
        '"{company}" NPA non-performing asset bank default',
        '"{company}" DRT debt recovery tribunal',
        '"{company}" SARFAESI bank auction',
    ],
    "environmental_social": [
        '"{company}" NGT pollution environmental penalty India',
        '"{company}" labour EPFO ESI violation India',
    ],
}


class ResearchIntelligenceService:
    """Gathers web intelligence about a company for credit analysis.
    Enhanced with India-specific regulatory, legal, and compliance sources."""

    def __init__(self):
        self._llm = None
        self._ddgs = None
        self.serpapi_key = settings.serpapi_api_key

    @property
    def llm(self):
        if self._llm is None:
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                api_key=settings.openai_api_key,
            )
        return self._llm

    def run_research(
        self,
        company_name: str,
        company_id: str,
        db: Session,
    ) -> List[Dict[str, Any]]:
        """Run full research intelligence pipeline for a company.
        Searches India-specific regulatory, legal, and compliance databases.
        Falls back to GPT knowledge if web search is unavailable."""
        findings = []
        web_search_failures = 0
        total_queries = 0

        for category, query_templates in INDIA_RESEARCH_QUERIES.items():
            for query_template in query_templates:
                query = query_template.replace("{company}", company_name)
                total_queries += 1
                try:
                    search_results = self._search_web(query)

                    if not search_results:
                        web_search_failures += 1
                        continue

                    # Add delay between queries to avoid rate limiting
                    time.sleep(2)

                    for result in search_results[:3]:
                        content = self._scrape_page(result.get("link", ""))
                        if not content:
                            content = result.get("snippet", "")

                        if not content:
                            continue

                        summary = self._summarize_finding(
                            company_name, category, result.get("title", ""), content
                        )

                        # Skip irrelevant findings
                        if summary["relevance"] < 0.2:
                            continue

                        finding = {
                            "company_id": company_id,
                            "category": category,
                            "title": result.get("title", ""),
                            "summary": summary["summary"],
                            "source_url": result.get("link", ""),
                            "sentiment": summary["sentiment"],
                            "relevance_score": summary["relevance"],
                            "raw_content": content[:5000] if content else None,
                        }
                        findings.append(finding)

                        db_finding = ResearchFinding(**finding)
                        db.add(db_finding)

                except Exception as e:
                    web_search_failures += 1
                    logger.error(f"Research query failed for '{query}': {e}")

        # If most web searches failed, use GPT knowledge as fallback
        if web_search_failures >= total_queries * 0.7 and len(findings) < 3:
            logger.info(f"Web search mostly failed ({web_search_failures}/{total_queries}). Using GPT knowledge fallback.")
            gpt_findings = self._generate_gpt_research(company_name, company_id)
            for finding in gpt_findings:
                findings.append(finding)
                db_finding = ResearchFinding(**finding)
                db.add(db_finding)

        db.commit()
        return findings

    def _search_web(self, query: str) -> List[Dict[str, Any]]:
        """Search the web using SerpAPI, with DuckDuckGo HTML fallback."""
        # Try SerpAPI first
        if self.serpapi_key:
            try:
                params = {
                    "q": query,
                    "api_key": self.serpapi_key,
                    "engine": "google",
                    "num": 5,
                    "gl": "in",
                    "hl": "en",
                }
                response = requests.get(
                    "https://serpapi.com/search",
                    params=params,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                results = data.get("organic_results", [])
                if results:
                    return results
            except Exception as e:
                logger.warning(f"SerpAPI search failed, falling back to DuckDuckGo: {e}")

        # Fallback: DuckDuckGo HTML scraping
        return self._search_duckduckgo(query)

    def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """Fallback search using ddgs package when SerpAPI is unavailable."""
        try:
            from ddgs import DDGS
            if self._ddgs is None:
                self._ddgs = DDGS()
            raw_results = self._ddgs.text(query, max_results=5)
            results = []
            for r in raw_results:
                results.append({
                    "title": r.get("title", ""),
                    "link": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
            logger.info(f"DDGS fallback returned {len(results)} results for: {query[:60]}")
            return results
        except Exception as e:
            logger.error(f"DDGS fallback search failed: {e}")
            return []

    def _generate_gpt_research(
        self, company_name: str, company_id: str
    ) -> List[Dict[str, Any]]:
        """Generate research intelligence using GPT's training knowledge when web search is unavailable."""
        categories = list(INDIA_RESEARCH_QUERIES.keys())
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an Indian corporate credit research analyst with deep expertise in
Indian regulatory frameworks (RBI, SEBI, MCA, GST, NCLT, DRT, SARFAESI).

Based on your knowledge, provide a comprehensive credit risk research report for the company.
Cover these categories: {categories}

For each finding, provide:
- category: one of {categories}
- title: brief finding title
- summary: 2-3 sentence summary with specific Indian regulatory/legal context
- sentiment: positive, negative, or neutral
- relevance: 0.0-1.0 relevance to credit risk assessment

Return a JSON array of findings. Include 6-10 findings covering different categories.
If you have no specific knowledge about the company, provide general industry/sector risk factors.

Example: [{{"category": "regulatory", "title": "...", "summary": "...", "sentiment": "negative", "relevance": 0.7}}]

Respond with ONLY the JSON array, no markdown fencing."""),
            ("human", "Company: {company_name}\nProvide credit risk research findings."),
        ])

        try:
            formatted = prompt.format_messages(
                company_name=company_name,
                categories=", ".join(categories),
            )
            response = self.llm.invoke(formatted)
            raw = response.content.strip()

            # Strip markdown code fences if present
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
            if json_match:
                raw = json_match.group(1).strip()

            gpt_findings = json.loads(raw)
            findings = []
            for f in gpt_findings:
                findings.append({
                    "company_id": company_id,
                    "category": f.get("category", "industry"),
                    "title": f.get("title", "GPT Research Finding"),
                    "summary": f.get("summary", ""),
                    "source_url": "GPT Knowledge Base",
                    "sentiment": f.get("sentiment", "neutral"),
                    "relevance_score": float(f.get("relevance", 0.5)),
                    "raw_content": None,
                })
            logger.info(f"GPT knowledge fallback generated {len(findings)} findings for {company_name}")
            return findings
        except Exception as e:
            logger.error(f"GPT research fallback failed: {e}")
            return []

    def _scrape_page(self, url: str) -> Optional[str]:
        """Scrape text content from a web page using BeautifulSoup."""
        if not url:
            return None
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; IntelliCredit/1.0)"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            # Limit text size
            return text[:10000]
        except Exception as e:
            logger.warning(f"Failed to scrape {url}: {e}")
            return None

    def _summarize_finding(
        self,
        company_name: str,
        category: str,
        title: str,
        content: str,
    ) -> Dict[str, Any]:
        """Use GPT to summarize a research finding with Indian regulatory awareness."""
        # Category-specific analysis instructions
        category_context = {
            "litigation": "Focus on: NCLT/NCLAT insolvency proceedings, DRT cases, High Court/Supreme Court orders, arbitration. Note case stage (pending/decided/appealed) and amounts involved.",
            "regulatory": "Focus on: SEBI orders, RBI penalties, MCA compliance defaults, ROC penalties, FEMA violations. Note penalty amounts and compliance status.",
            "gst_compliance": "Focus on: GST demand notices, DGGI investigations, ITC mismatches, e-way bill violations, fake invoice cases. Note tax demand and penalty amounts.",
            "industry": "Focus on: Sector growth rate, regulatory changes affecting the sector, government policy impact, competition landscape in India.",
            "reputation": "Focus on: Company reputation in Indian market, customer complaints, SFIO investigations, management credibility issues.",
            "fraud_risk": "Focus on: Financial fraud allegations, wilful defaulter classification, forensic audit findings, fund diversion.",
            "npa_default": "Focus on: NPA classification by banks, DRT proceedings, SARFAESI actions, IBC proceedings, one-time settlement (OTS) history.",
            "environmental_social": "Focus on: NGT orders, pollution control board notices, EPFO/ESI compliance, labour law violations.",
        }

        context_note = category_context.get(category, "Analyze for credit risk relevance.")

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an Indian corporate credit research analyst with expertise in
Indian regulatory frameworks (RBI, SEBI, MCA, GST, NCLT, DRT).

Analyze the following web content about {company_name} in the context of {category} risk assessment.

{context_note}

Provide:
1. A concise 2-3 sentence summary of the key finding, noting specific Indian regulatory/legal context
2. Sentiment: positive, negative, or neutral
3. Relevance score from 0.0 to 1.0 for credit risk assessment
   - 0.9-1.0: Direct credit risk impact (NPA, wilful defaulter, fraud, insolvency)
   - 0.7-0.8: Significant regulatory/legal action
   - 0.5-0.6: Moderate concern (demand notices, investigations)
   - 0.2-0.4: Minor/indirect relevance
   - 0.0-0.1: Not relevant to credit assessment

Respond in JSON format: {{"summary": "...", "sentiment": "...", "relevance": 0.X}}"""),
            ("human", "Title: {title}\n\nContent:\n{content}"),
        ])

        try:
            formatted = prompt.format_messages(
                company_name=company_name,
                category=category,
                context_note=context_note,
                title=title,
                content=content[:5000],
            )
            response = self.llm.invoke(formatted)

            raw = response.content.strip()
            # Strip markdown code fences if present
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
            if json_match:
                raw = json_match.group(1).strip()
            # Try to find JSON object in the text
            obj_match = re.search(r'\{[^{}]*\}', raw)
            if obj_match:
                raw = obj_match.group(0)
            result = json.loads(raw)
            return {
                "summary": result.get("summary", ""),
                "sentiment": result.get("sentiment", "neutral"),
                "relevance": float(result.get("relevance", 0.5)),
            }
        except Exception as e:
            logger.warning(f"Summarization failed: {e}")
            return {
                "summary": title or "No summary available",
                "sentiment": "neutral",
                "relevance": 0.5,
            }


research_intelligence_service = ResearchIntelligenceService()
