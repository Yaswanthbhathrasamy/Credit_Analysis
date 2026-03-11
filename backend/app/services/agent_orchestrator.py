"""
LangGraph Agent Orchestrator
Implements a multi-agent pipeline using LangGraph where each credit analysis
step is a specialized AI agent node. Agents verify data, run analysis,
and pass state to the next agent in the graph.

Architecture:
  Document Agent → Financial Agent → Research Agent → Promoter Agent → Warning Agent → Risk Agent
"""

import logging
import json
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime
import operator

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import (
    Company, Document, FinancialMetric, ResearchFinding,
    PromoterAnalysis, RiskFlag, RiskScore, RiskLevel,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# ── State Definition ──

class AgentState(TypedDict):
    """Shared state that flows through all agent nodes."""
    company_id: str
    company_name: str
    industry: str
    # Agent results accumulate here
    agent_logs: Annotated[list, operator.add]
    document_summary: dict
    financial_summary: dict
    research_summary: dict
    promoter_summary: dict
    warning_summary: dict
    risk_summary: dict
    # Error tracking
    errors: Annotated[list, operator.add]
    # Current step for progress tracking
    current_step: str


def _get_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        api_key=settings.openai_api_key,
    )


# ── Agent Node: Document Verification ──

def document_agent(state: AgentState, db: Session) -> dict:
    """Agent that verifies and summarizes uploaded documents."""
    company_id = state["company_id"]
    llm = _get_llm()

    docs = (
        db.query(Document)
        .filter(Document.company_id == company_id)
        .all()
    )

    doc_info = []
    for d in docs:
        doc_info.append({
            "filename": d.original_filename,
            "type": d.document_type.value if d.document_type else "other",
            "status": d.processing_status,
            "ocr_used": d.ocr_used,
            "has_text": bool(d.extracted_text),
            "confidence": d.confidence_score,
            "detected_type": d.detected_doc_type,
        })

    if not doc_info:
        return {
            "document_summary": {"status": "no_documents", "count": 0, "details": []},
            "agent_logs": [{"agent": "DocumentAgent", "status": "complete", "message": "No documents found", "timestamp": datetime.utcnow().isoformat()}],
            "current_step": "documents",
        }

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a Document Verification Agent for Indian corporate credit analysis. "
         "Review the uploaded documents and assess completeness for credit appraisal. "
         "Check for: Annual Reports, Balance Sheets, P&L, GST Returns (GSTR-1/2A/2B/3B), "
         "CIBIL/Credit Reports, ITR, Bank Statements, MCA Filings. "
         "Identify what's missing and what needs attention."),
        ("human",
         "Company: {company_name}\n"
         "Documents uploaded:\n{documents}\n\n"
         "Return a JSON with:\n"
         '{{"completeness_score": 0-100, "verified_types": [...], "missing_types": [...], '
         '"recommendations": [...], "overall_assessment": "..."}}'
         ),
    ])

    chain = prompt | llm | StrOutputParser()
    raw = chain.invoke({
        "company_name": state["company_name"],
        "documents": json.dumps(doc_info, indent=2),
    })

    # Parse response
    assessment = _parse_json(raw) or {"completeness_score": 0, "overall_assessment": raw[:500]}
    assessment["count"] = len(doc_info)
    assessment["details"] = doc_info
    assessment["status"] = "verified"

    return {
        "document_summary": assessment,
        "agent_logs": [{
            "agent": "DocumentAgent",
            "status": "complete",
            "message": f"Verified {len(doc_info)} documents. Completeness: {assessment.get('completeness_score', 'N/A')}%",
            "timestamp": datetime.utcnow().isoformat(),
        }],
        "current_step": "documents",
    }


# ── Agent Node: Financial Analysis ──

def financial_agent(state: AgentState, db: Session) -> dict:
    """Agent that analyzes extracted financial data."""
    company_id = state["company_id"]
    llm = _get_llm()

    metrics = (
        db.query(FinancialMetric)
        .filter(FinancialMetric.company_id == company_id)
        .order_by(FinancialMetric.created_at.desc())
        .all()
    )

    if not metrics:
        return {
            "financial_summary": {"status": "no_data", "metrics_count": 0},
            "agent_logs": [{"agent": "FinancialAgent", "status": "complete", "message": "No financial data found. Extract financials first.", "timestamp": datetime.utcnow().isoformat()}],
            "current_step": "financials",
        }

    fin_data = []
    for m in metrics:
        fin_data.append({
            "fiscal_year": m.fiscal_year,
            "revenue": m.revenue,
            "net_profit": m.net_profit,
            "ebitda": m.ebitda,
            "total_assets": m.total_assets,
            "total_debt": m.total_debt,
            "current_ratio": m.current_ratio,
            "debt_ratio": m.debt_ratio,
            "interest_coverage": m.interest_coverage,
            "profit_margin": m.profit_margin,
            "debt_to_equity": m.debt_to_equity,
        })

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a Financial Analysis Agent specialized in Indian corporate credit assessment. "
         "Analyze financial metrics using Ind-AS standards. Evaluate profitability, leverage, "
         "liquidity, and efficiency. Reference Tandon Committee norms for working capital, "
         "RBI guidelines for NPA classification (SMA-0: 1-30 DPD, SMA-1: 31-60, SMA-2: 61-90). "
         "All amounts are in INR (₹), potentially in lakhs/crores."),
        ("human",
         "Company: {company_name} | Industry: {industry}\n"
         "Financial Data:\n{financials}\n\n"
         "Return a JSON with:\n"
         '{{"health_score": 0-100, "strengths": [...], "weaknesses": [...], '
         '"key_ratios_assessment": {{"debt_ratio": "...", "current_ratio": "...", "interest_coverage": "...", "profitability": "..."}}, '
         '"trend_analysis": "...", "red_flags": [...], "overall_assessment": "..."}}'
         ),
    ])

    chain = prompt | llm | StrOutputParser()
    raw = chain.invoke({
        "company_name": state["company_name"],
        "industry": state["industry"],
        "financials": json.dumps(fin_data, indent=2),
    })

    assessment = _parse_json(raw) or {"overall_assessment": raw[:500]}
    assessment["status"] = "analyzed"
    assessment["metrics_count"] = len(fin_data)

    return {
        "financial_summary": assessment,
        "agent_logs": [{
            "agent": "FinancialAgent",
            "status": "complete",
            "message": f"Analyzed {len(fin_data)} financial records. Health: {assessment.get('health_score', 'N/A')}/100",
            "timestamp": datetime.utcnow().isoformat(),
        }],
        "current_step": "financials",
    }


# ── Agent Node: Research Intelligence ──

def research_agent(state: AgentState, db: Session) -> dict:
    """Agent that reviews and synthesizes research findings."""
    company_id = state["company_id"]
    llm = _get_llm()

    findings = (
        db.query(ResearchFinding)
        .filter(ResearchFinding.company_id == company_id)
        .order_by(ResearchFinding.created_at.desc())
        .limit(20)
        .all()
    )

    if not findings:
        return {
            "research_summary": {"status": "no_data", "findings_count": 0},
            "agent_logs": [{"agent": "ResearchAgent", "status": "complete", "message": "No research data. Run research agent first.", "timestamp": datetime.utcnow().isoformat()}],
            "current_step": "research",
        }

    research_data = []
    for f in findings:
        research_data.append({
            "category": f.category,
            "title": f.title,
            "summary": f.summary,
            "sentiment": f.sentiment,
            "relevance": f.relevance_score,
        })

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a Research Intelligence Agent specializing in Indian corporate due diligence. "
         "Synthesize research findings into a credit risk intelligence brief. "
         "Look for: NCLT/DRT cases, SEBI/RBI actions, GST/DGGI issues, MCA defaults, "
         "wilful defaulter status, promoter fraud, sector headwinds, reputational risks. "
         "Classify overall intelligence as favorable/mixed/adverse."),
        ("human",
         "Company: {company_name} | Industry: {industry}\n"
         "Research Findings:\n{research}\n\n"
         "Return a JSON with:\n"
         '{{"intelligence_rating": "favorable/mixed/adverse", "key_concerns": [...], '
         '"positive_signals": [...], "regulatory_exposure": "low/medium/high", '
         '"litigation_status": "...", "media_sentiment": "positive/negative/mixed", '
         '"overall_assessment": "..."}}'
         ),
    ])

    chain = prompt | llm | StrOutputParser()
    raw = chain.invoke({
        "company_name": state["company_name"],
        "industry": state["industry"],
        "research": json.dumps(research_data, indent=2),
    })

    assessment = _parse_json(raw) or {"overall_assessment": raw[:500]}
    assessment["status"] = "synthesized"
    assessment["findings_count"] = len(research_data)

    return {
        "research_summary": assessment,
        "agent_logs": [{
            "agent": "ResearchAgent",
            "status": "complete",
            "message": f"Synthesized {len(research_data)} findings. Rating: {assessment.get('intelligence_rating', 'N/A')}",
            "timestamp": datetime.utcnow().isoformat(),
        }],
        "current_step": "research",
    }


# ── Agent Node: Promoter Verification ──

def promoter_agent(state: AgentState, db: Session) -> dict:
    """Agent that verifies promoter background and risk."""
    company_id = state["company_id"]
    llm = _get_llm()

    promoters = (
        db.query(PromoterAnalysis)
        .filter(PromoterAnalysis.company_id == company_id)
        .all()
    )

    if not promoters:
        return {
            "promoter_summary": {"status": "no_data", "promoter_count": 0},
            "agent_logs": [{"agent": "PromoterAgent", "status": "complete", "message": "No promoter analysis data found.", "timestamp": datetime.utcnow().isoformat()}],
            "current_step": "promoters",
        }

    promoter_data = []
    for p in promoters:
        promoter_data.append({
            "name": p.promoter_name,
            "designation": p.designation,
            "risk_level": p.risk_level.value if p.risk_level else "unknown",
            "bankruptcy_flag": p.bankruptcy_flag,
            "fraud_flag": p.fraud_flag,
            "regulatory_violation": p.regulatory_violation_flag,
            "background": p.background_summary,
            "risk_summary": p.risk_summary,
        })

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a Promoter Due Diligence Agent for Indian corporate credit. "
         "Verify promoter backgrounds for credit character assessment. "
         "Check for: wilful defaulter history, fraud convictions, SEBI debarments, "
         "MCA disqualifications, shell company associations, related party transactions, "
         "and political exposure. Map findings to the 'Character' C of Five Cs."),
        ("human",
         "Company: {company_name}\n"
         "Promoter Profiles:\n{promoters}\n\n"
         "Return a JSON with:\n"
         '{{"character_score": 0-10, "high_risk_promoters": [...], '
         '"flags_summary": {{"bankruptcy": 0, "fraud": 0, "regulatory": 0}}, '
         '"overall_character_assessment": "...", "recommendations": [...]}}'
         ),
    ])

    chain = prompt | llm | StrOutputParser()
    raw = chain.invoke({
        "company_name": state["company_name"],
        "promoters": json.dumps(promoter_data, indent=2),
    })

    assessment = _parse_json(raw) or {"overall_character_assessment": raw[:500]}
    assessment["status"] = "verified"
    assessment["promoter_count"] = len(promoter_data)

    return {
        "promoter_summary": assessment,
        "agent_logs": [{
            "agent": "PromoterAgent",
            "status": "complete",
            "message": f"Verified {len(promoter_data)} promoters. Character: {assessment.get('character_score', 'N/A')}/10",
            "timestamp": datetime.utcnow().isoformat(),
        }],
        "current_step": "promoters",
    }


# ── Agent Node: Warning Detection ──

def warning_agent(state: AgentState, db: Session) -> dict:
    """Agent that aggregates and classifies early warning signals."""
    company_id = state["company_id"]
    llm = _get_llm()

    flags = (
        db.query(RiskFlag)
        .filter(RiskFlag.company_id == company_id)
        .all()
    )

    flag_data = []
    for f in flags:
        flag_data.append({
            "type": f.flag_type,
            "description": f.description,
            "severity": f.severity.value if f.severity else "medium",
            "discrepancy_pct": f.discrepancy_pct,
        })

    # Also include financial and research context for cross-referencing
    fin_summary = state.get("financial_summary", {})
    research_summary = state.get("research_summary", {})

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an Early Warning Signal Agent for Indian bank lending. "
         "Analyze risk flags and cross-reference with financial and research data. "
         "Apply RBI IRAC norms: SMA-0 (1-30 DPD), SMA-1 (31-60), SMA-2 (61-90). "
         "Look for: revenue-GST mismatches, DPD indicators, deteriorating ratios, "
         "adverse media, regulatory non-compliance, related party red flags."),
        ("human",
         "Company: {company_name}\n"
         "Risk Flags ({flag_count}):\n{flags}\n"
         "Financial Health: {fin_health}\n"
         "Research Intelligence: {research_intel}\n\n"
         "Return a JSON with:\n"
         '{{"sma_classification": "none/SMA-0/SMA-1/SMA-2", "warning_level": "green/yellow/orange/red", '
         '"critical_warnings": [...], "moderate_warnings": [...], '
         '"cross_reference_issues": [...], "overall_assessment": "..."}}'
         ),
    ])

    chain = prompt | llm | StrOutputParser()
    raw = chain.invoke({
        "company_name": state["company_name"],
        "flag_count": len(flag_data),
        "flags": json.dumps(flag_data, indent=2) if flag_data else "No risk flags detected",
        "fin_health": fin_summary.get("overall_assessment", "Not analyzed"),
        "research_intel": research_summary.get("overall_assessment", "Not available"),
    })

    assessment = _parse_json(raw) or {"overall_assessment": raw[:500]}
    assessment["status"] = "assessed"
    assessment["total_flags"] = len(flag_data)

    return {
        "warning_summary": assessment,
        "agent_logs": [{
            "agent": "WarningAgent",
            "status": "complete",
            "message": f"Assessed {len(flag_data)} flags. Level: {assessment.get('warning_level', 'N/A')}",
            "timestamp": datetime.utcnow().isoformat(),
        }],
        "current_step": "warnings",
    }


# ── Agent Node: Final Risk Verdict ──

def risk_verdict_agent(state: AgentState, db: Session) -> dict:
    """Final agent that synthesizes all previous agent outputs into a credit verdict."""
    llm = _get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are the Senior Credit Decision Agent at an Indian bank. "
         "You receive analysis from 5 specialist agents and must produce a final credit verdict. "
         "Apply the Five Cs framework, RBI IRAC norms, and bank-level underwriting standards. "
         "Your decision must be defensible and walk through the reasoning step-by-step."),
        ("human",
         "Company: {company_name} | Industry: {industry}\n\n"
         "=== DOCUMENT AGENT REPORT ===\n{doc_report}\n\n"
         "=== FINANCIAL AGENT REPORT ===\n{fin_report}\n\n"
         "=== RESEARCH AGENT REPORT ===\n{research_report}\n\n"
         "=== PROMOTER AGENT REPORT ===\n{promoter_report}\n\n"
         "=== WARNING AGENT REPORT ===\n{warning_report}\n\n"
         "Return a JSON with:\n"
         '{{"credit_verdict": "approve/approve_with_conditions/reject", '
         '"confidence_level": 0-100, '
         '"risk_rating": "low/medium/high/critical", '
         '"five_cs_summary": {{"character": "...", "capacity": "...", "capital": "...", "collateral": "...", "conditions": "..."}}, '
         '"key_strengths": [...], "key_concerns": [...], '
         '"conditions_if_approved": [...], '
         '"reasoning_walkthrough": "Step-by-step explanation of the decision..."}}'
         ),
    ])

    chain = prompt | llm | StrOutputParser()
    raw = chain.invoke({
        "company_name": state["company_name"],
        "industry": state["industry"],
        "doc_report": json.dumps(state.get("document_summary", {}), indent=2, default=str),
        "fin_report": json.dumps(state.get("financial_summary", {}), indent=2, default=str),
        "research_report": json.dumps(state.get("research_summary", {}), indent=2, default=str),
        "promoter_report": json.dumps(state.get("promoter_summary", {}), indent=2, default=str),
        "warning_report": json.dumps(state.get("warning_summary", {}), indent=2, default=str),
    })

    verdict = _parse_json(raw) or {"credit_verdict": "reject", "reasoning_walkthrough": raw[:500]}
    verdict["status"] = "complete"

    return {
        "risk_summary": verdict,
        "agent_logs": [{
            "agent": "RiskVerdictAgent",
            "status": "complete",
            "message": f"Verdict: {verdict.get('credit_verdict', 'N/A').upper()} | Confidence: {verdict.get('confidence_level', 'N/A')}%",
            "timestamp": datetime.utcnow().isoformat(),
        }],
        "current_step": "risk_verdict",
    }


# ── Graph Builder ──

def build_agent_graph(db: Session) -> StateGraph:
    """Build the LangGraph agent pipeline."""

    graph = StateGraph(AgentState)

    # Wrap nodes to pass db session
    graph.add_node("document_agent", lambda state: document_agent(state, db))
    graph.add_node("financial_agent", lambda state: financial_agent(state, db))
    graph.add_node("research_agent", lambda state: research_agent(state, db))
    graph.add_node("promoter_agent", lambda state: promoter_agent(state, db))
    graph.add_node("warning_agent", lambda state: warning_agent(state, db))
    graph.add_node("risk_verdict_agent", lambda state: risk_verdict_agent(state, db))

    # Sequential pipeline: each agent feeds into the next
    graph.set_entry_point("document_agent")
    graph.add_edge("document_agent", "financial_agent")
    graph.add_edge("financial_agent", "research_agent")
    graph.add_edge("research_agent", "promoter_agent")
    graph.add_edge("promoter_agent", "warning_agent")
    graph.add_edge("warning_agent", "risk_verdict_agent")
    graph.add_edge("risk_verdict_agent", END)

    return graph.compile()


# ── Orchestrator Service ──

class AgentOrchestrator:
    """Runs the full LangGraph agent pipeline for credit analysis."""

    def run_full_pipeline(
        self, company_id: str, db: Session
    ) -> Dict[str, Any]:
        """Execute all agents in sequence and return the aggregated result."""
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"Company {company_id} not found")

        logger.info(f"Starting agent pipeline for {company.name}")

        graph = build_agent_graph(db)

        initial_state: AgentState = {
            "company_id": company_id,
            "company_name": company.name,
            "industry": company.industry or "general",
            "agent_logs": [],
            "document_summary": {},
            "financial_summary": {},
            "research_summary": {},
            "promoter_summary": {},
            "warning_summary": {},
            "risk_summary": {},
            "errors": [],
            "current_step": "starting",
        }

        try:
            final_state = graph.invoke(initial_state)
        except Exception as e:
            logger.error(f"Agent pipeline failed: {e}")
            final_state = {
                **initial_state,
                "errors": [str(e)],
                "agent_logs": [{"agent": "Orchestrator", "status": "error", "message": str(e), "timestamp": datetime.utcnow().isoformat()}],
            }

        logger.info(f"Agent pipeline complete for {company.name}: {len(final_state.get('agent_logs', []))} agent logs")

        return {
            "company_id": company_id,
            "company_name": company.name,
            "agent_logs": final_state.get("agent_logs", []),
            "document_summary": final_state.get("document_summary", {}),
            "financial_summary": final_state.get("financial_summary", {}),
            "research_summary": final_state.get("research_summary", {}),
            "promoter_summary": final_state.get("promoter_summary", {}),
            "warning_summary": final_state.get("warning_summary", {}),
            "risk_summary": final_state.get("risk_summary", {}),
            "errors": final_state.get("errors", []),
        }

    def run_single_agent(
        self, agent_name: str, company_id: str, db: Session
    ) -> Dict[str, Any]:
        """Run a single agent independently."""
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"Company {company_id} not found")

        state: AgentState = {
            "company_id": company_id,
            "company_name": company.name,
            "industry": company.industry or "general",
            "agent_logs": [],
            "document_summary": {},
            "financial_summary": {},
            "research_summary": {},
            "promoter_summary": {},
            "warning_summary": {},
            "risk_summary": {},
            "errors": [],
            "current_step": agent_name,
        }

        agent_map = {
            "documents": document_agent,
            "financials": financial_agent,
            "research": research_agent,
            "promoters": promoter_agent,
            "warnings": warning_agent,
            "risk": risk_verdict_agent,
        }

        agent_fn = agent_map.get(agent_name)
        if not agent_fn:
            raise ValueError(f"Unknown agent: {agent_name}")

        try:
            result = agent_fn(state, db)
            state.update(result)
        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {e}")
            state["errors"] = [str(e)]
            state["agent_logs"] = [{"agent": agent_name, "status": "error", "message": str(e), "timestamp": datetime.utcnow().isoformat()}]

        return state


def _parse_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from LLM output."""
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}') + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return None


agent_orchestrator = AgentOrchestrator()
