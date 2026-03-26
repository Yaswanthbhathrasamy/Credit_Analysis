"""
FastAPI API Routes
All endpoints for the Intelli-Credit platform.
"""

import os
import uuid
import logging
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Path
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.models.models import (
    Company, Document, DocumentType, FinancialMetric,
    RiskFlag, ResearchFinding, PromoterAnalysis, RiskScore, SWOTAnalysis,
)
from app.schemas.schemas import (
    CompanyCreate, CompanyResponse, DocumentResponse,
    FinancialExtractionRequest, FinancialMetricResponse,
    ResearchRequest, ResearchFindingResponse,
    PromoterAnalysisRequest, PromoterAnalysisResponse,
    RiskScoreRequest, RiskScoreResponse, RiskFlagResponse,
    EarlyWarningRequest, EarlyWarningResponse,
    DueDiligenceUpdate, StatusResponse, CAMReportRequest,
    ClassificationApproval, SchemaMapping,
    SWOTRequest, SWOTResponse,
)
from app.services.document_service import document_processor
from app.services.extraction_service import financial_extraction_service
from app.services.validation_service import financial_validation_service
from app.services.research_service import research_intelligence_service
from app.services.promoter_service import promoter_risk_service
from app.services.risk_scoring_service import risk_scoring_service
from app.services.cam_report_service import cam_report_service
from app.services.crew_research_service import crew_research_service
from app.services.agent_orchestrator import agent_orchestrator
from app.services.swot_service import swot_analysis_service

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


def _validate_uuid(value: str, field_name: str = "company_id") -> str:
    """Validate that a string is a valid UUID format."""
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name} format")
    return value


# ─── Company Endpoints ───

@router.post("/companies", response_model=CompanyResponse)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    """Create a new company for credit analysis."""
    db_company = Company(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company


@router.get("/companies", response_model=List[CompanyResponse])
def list_companies(db: Session = Depends(get_db)):
    """List all companies."""
    return db.query(Company).order_by(Company.created_at.desc()).all()


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: str, db: Session = Depends(get_db)):
    """Get company details."""
    _validate_uuid(company_id)
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


# ─── Document Upload Endpoints ───

@router.post("/upload-documents", response_model=List[DocumentResponse])
async def upload_documents(
    company_id: str = Form(...),
    document_type: str = Form("other"),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload company documents for processing."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB per file

    os.makedirs(settings.upload_dir, exist_ok=True)
    uploaded_docs = []

    for file in files:
        # Validate file extension
        ext = os.path.splitext(file.filename or "document.pdf")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{ext}' not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        # Generate safe filename (prevents path traversal)
        safe_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(settings.upload_dir, safe_filename)

        # Read and validate file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' exceeds maximum size of 50 MB.",
            )

        # Save file
        with open(file_path, "wb") as f:
            f.write(content)

        # Process document
        try:
            doc_type = DocumentType(document_type)
        except ValueError:
            doc_type = DocumentType.OTHER

        # Extract text
        try:
            result = document_processor.extract_text_from_pdf(file_path)
            processing_status = "processed"
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            result = {"text": "", "ocr_used": False, "page_count": 0}
            processing_status = "failed"

        doc_record = Document(
            company_id=company_id,
            filename=safe_filename,
            original_filename=file.filename or "unknown",
            document_type=doc_type,
            file_path=file_path,
            file_size=len(content),
            extracted_text=result["text"],
            processing_status=processing_status,
            ocr_used=result["ocr_used"],
            confidence_score=result.get("confidence"),
            detected_doc_type=result.get("detected_doc_type"),
        )
        db.add(doc_record)
        uploaded_docs.append(doc_record)

    db.commit()
    for doc in uploaded_docs:
        db.refresh(doc)

    return uploaded_docs


# ─── Financial Extraction Endpoints ───

@router.post("/extract-financial-data", response_model=StatusResponse)
def extract_financial_data(
    request: FinancialExtractionRequest,
    db: Session = Depends(get_db),
):
    """Extract structured financial data from uploaded documents using AI."""
    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get documents to process
    query = db.query(Document).filter(
        Document.company_id == request.company_id,
        Document.processing_status == "processed",
    )
    if request.document_ids:
        query = query.filter(Document.id.in_(request.document_ids))

    documents = query.all()
    if not documents:
        raise HTTPException(status_code=404, detail="No processed documents found")

    extracted_count = 0
    for doc in documents:
        if not doc.extracted_text:
            continue

        try:
            # Pass document type for context-aware extraction
            doc_type_hint = doc.detected_doc_type or (doc.document_type.value if doc.document_type else None)
            data = financial_extraction_service.extract_financial_data(doc.extracted_text, document_type=doc_type_hint)

            metric = FinancialMetric(
                company_id=str(request.company_id),
                source_document_id=str(doc.id),
                fiscal_year=data.get("fiscal_year"),
                revenue=data.get("revenue"),
                net_profit=data.get("net_profit"),
                gross_profit=data.get("gross_profit"),
                ebitda=data.get("ebitda"),
                total_assets=data.get("total_assets"),
                total_liabilities=data.get("total_liabilities"),
                total_debt=data.get("total_debt"),
                current_assets=data.get("current_assets"),
                current_liabilities=data.get("current_liabilities"),
                shareholders_equity=data.get("shareholders_equity"),
                cash_flow_operations=data.get("cash_flow_operations"),
                interest_expense=data.get("interest_expense"),
                debt_ratio=data.get("debt_ratio"),
                current_ratio=data.get("current_ratio"),
                debt_to_equity=data.get("debt_to_equity"),
                interest_coverage=data.get("interest_coverage"),
                profit_margin=data.get("profit_margin"),
                return_on_assets=data.get("return_on_assets"),
                return_on_equity=data.get("return_on_equity"),
                director_names=data.get("director_names"),
                legal_mentions=data.get("legal_mentions"),
                raw_extraction=data,
            )
            db.add(metric)
            extracted_count += 1
        except Exception as e:
            logger.error(f"Extraction failed for document {doc.id}: {e}")

    db.commit()

    # Run validation after extraction
    flags = financial_validation_service.validate_financials(str(request.company_id), db)

    return StatusResponse(
        status="success",
        message=f"Extracted financial data from {extracted_count} documents. Found {len(flags)} risk flags.",
        data={"documents_processed": extracted_count, "risk_flags": len(flags)},
    )


@router.get("/companies/{company_id}/financials", response_model=List[FinancialMetricResponse])
def get_financials(company_id: str, db: Session = Depends(get_db)):
    """Get extracted financial metrics for a company."""
    _validate_uuid(company_id)
    metrics = (
        db.query(FinancialMetric)
        .filter(FinancialMetric.company_id == company_id)
        .order_by(FinancialMetric.created_at.desc())
        .all()
    )
    return metrics


# ─── Research Intelligence Endpoints ───

@router.post("/run-research-agent", response_model=StatusResponse)
def run_research_agent(
    request: ResearchRequest,
    db: Session = Depends(get_db),
):
    """Run web research intelligence agent for a company."""
    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    findings = research_intelligence_service.run_research(
        company_name=company.name,
        company_id=str(request.company_id),
        db=db,
    )

    return StatusResponse(
        status="success",
        message=f"Research completed. Found {len(findings)} intelligence items.",
        data={"findings_count": len(findings)},
    )


@router.get("/companies/{company_id}/research", response_model=List[ResearchFindingResponse])
def get_research(company_id: str, db: Session = Depends(get_db)):
    """Get research findings for a company."""
    _validate_uuid(company_id)
    return (
        db.query(ResearchFinding)
        .filter(ResearchFinding.company_id == company_id)
        .order_by(ResearchFinding.created_at.desc())
        .all()
    )


@router.post("/run-crew-research", response_model=StatusResponse)
def run_crew_research(
    request: ResearchRequest,
    db: Session = Depends(get_db),
):
    """Run CrewAI multi-agent research for news, regulatory, and sector intelligence."""
    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    result = crew_research_service.run_crew_research(
        company_name=company.name,
        industry=company.industry or "",
        company_id=str(request.company_id),
        db=db,
    )

    return StatusResponse(
        status="success",
        message=f"CrewAI research completed. Found {len(result.get('findings', []))} intelligence items.",
        data={
            "findings_count": len(result.get("findings", [])),
            "synthesis": result.get("synthesis"),
        },
    )


# ─── Promoter Analysis Endpoints ───

@router.post("/run-promoter-analysis", response_model=StatusResponse)
def run_promoter_analysis(
    request: PromoterAnalysisRequest,
    db: Session = Depends(get_db),
):
    """Run promoter risk analysis."""
    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    results = promoter_risk_service.analyze_promoters(
        company_id=str(request.company_id),
        company_name=company.name,
        promoter_names=request.promoter_names or [],
        db=db,
    )

    return StatusResponse(
        status="success",
        message=f"Promoter analysis completed for {len(results)} promoters.",
        data={"promoters_analyzed": len(results)},
    )


@router.get("/companies/{company_id}/promoters", response_model=List[PromoterAnalysisResponse])
def get_promoter_analyses(company_id: str, db: Session = Depends(get_db)):
    """Get promoter analyses for a company."""
    _validate_uuid(company_id)
    return (
        db.query(PromoterAnalysis)
        .filter(PromoterAnalysis.company_id == company_id)
        .order_by(PromoterAnalysis.created_at.desc())
        .all()
    )


# ─── Early Warning Detection ───

@router.post("/detect-early-warning", response_model=EarlyWarningResponse)
def detect_early_warning(
    request: EarlyWarningRequest,
    db: Session = Depends(get_db),
):
    """Detect early warning signals based on financial validation."""
    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get existing risk flags
    flags = (
        db.query(RiskFlag)
        .filter(RiskFlag.company_id == str(request.company_id))
        .all()
    )

    critical_count = sum(
        1 for f in flags if f.severity and f.severity.value in ("high", "critical")
    )

    return EarlyWarningResponse(
        company_id=request.company_id,
        warnings=[RiskFlagResponse.model_validate(f) for f in flags],
        total_flags=len(flags),
        critical_flags=critical_count,
    )


@router.get("/companies/{company_id}/risk-flags", response_model=List[RiskFlagResponse])
def get_risk_flags(company_id: str, db: Session = Depends(get_db)):
    """Get all risk flags for a company."""
    _validate_uuid(company_id)
    return (
        db.query(RiskFlag)
        .filter(RiskFlag.company_id == company_id)
        .all()
    )


# ─── Risk Scoring Endpoints ───

@router.post("/calculate-risk-score", response_model=StatusResponse)
def calculate_risk_score(
    request: RiskScoreRequest,
    db: Session = Depends(get_db),
):
    """Calculate ML-based credit risk score with SHAP explanations."""
    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    try:
        result = risk_scoring_service.calculate_risk_score(
            company_id=str(request.company_id), db=db
        )
        return StatusResponse(
            status="success",
            message=f"Risk score calculated: {result['probability_of_default']:.2%} ({result['risk_level']})",
            data=result,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/companies/{company_id}/risk-score")
def get_risk_score(company_id: str, db: Session = Depends(get_db)):
    """Get the latest risk score for a company. Returns null if none calculated."""
    _validate_uuid(company_id)
    score = (
        db.query(RiskScore)
        .filter(RiskScore.company_id == company_id)
        .order_by(RiskScore.created_at.desc())
        .first()
    )
    if not score:
        return None
    return RiskScoreResponse.model_validate(score)


# ─── Due Diligence Notes ───

@router.post("/companies/{company_id}/due-diligence", response_model=StatusResponse)
def update_due_diligence(
    company_id: str,
    update: DueDiligenceUpdate,
    db: Session = Depends(get_db),
):
    """Update due diligence notes for a company's risk score."""
    _validate_uuid(company_id)
    score = (
        db.query(RiskScore)
        .filter(RiskScore.company_id == company_id)
        .order_by(RiskScore.created_at.desc())
        .first()
    )
    if not score:
        raise HTTPException(status_code=404, detail="No risk score found")

    score.due_diligence_notes = update.notes
    db.commit()

    return StatusResponse(
        status="success",
        message="Due diligence notes updated.",
    )


# ─── CAM Report Generation ───

@router.get("/generate-cam-report")
def generate_cam_report(company_id: str, db: Session = Depends(get_db)):
    """Generate and download the Credit Appraisal Memo (CAM) report."""
    _validate_uuid(company_id)
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    try:
        filepath = cam_report_service.generate_report(
            company_id=company_id, db=db
        )
        filename = os.path.basename(filepath)
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        logger.error(f"CAM report generation failed: {e}")
        raise HTTPException(status_code=500, detail="Report generation failed. Check server logs for details.")


# ─── Dashboard Summary ───

@router.get("/companies/{company_id}/dashboard-summary")
def get_dashboard_summary(company_id: str, db: Session = Depends(get_db)):
    """Get a complete dashboard summary for a company."""
    _validate_uuid(company_id)
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    documents = db.query(Document).filter(Document.company_id == company_id).all()
    metrics = (
        db.query(FinancialMetric)
        .filter(FinancialMetric.company_id == company_id)
        .order_by(FinancialMetric.created_at.desc())
        .first()
    )
    flags = db.query(RiskFlag).filter(RiskFlag.company_id == company_id).all()
    research = db.query(ResearchFinding).filter(ResearchFinding.company_id == company_id).all()
    promoters = db.query(PromoterAnalysis).filter(PromoterAnalysis.company_id == company_id).all()
    risk_score = (
        db.query(RiskScore)
        .filter(RiskScore.company_id == company_id)
        .order_by(RiskScore.created_at.desc())
        .first()
    )

    return {
        "company": CompanyResponse.model_validate(company),
        "documents_count": len(documents),
        "documents_processed": sum(1 for d in documents if d.processing_status == "processed"),
        "has_financials": metrics is not None,
        "risk_flags_count": len(flags),
        "critical_flags_count": sum(1 for f in flags if f.severity and f.severity.value in ("high", "critical")),
        "research_findings_count": len(research),
        "promoters_analyzed": len(promoters),
        "has_risk_score": risk_score is not None,
        "risk_score": {
            "probability_of_default": risk_score.probability_of_default if risk_score else None,
            "risk_level": risk_score.risk_level.value if risk_score and risk_score.risk_level else None,
            "decision": risk_score.decision.value if risk_score and risk_score.decision else None,
        } if risk_score else None,
    }


# ─── Document Classification Endpoints ───

@router.get("/companies/{company_id}/documents", response_model=List[DocumentResponse])
def get_documents(company_id: str, db: Session = Depends(get_db)):
    """Get all documents for a company."""
    _validate_uuid(company_id)
    return (
        db.query(Document)
        .filter(Document.company_id == company_id)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.post("/approve-classification", response_model=StatusResponse)
def approve_classification(
    request: ClassificationApproval,
    db: Session = Depends(get_db),
):
    """Approve or correct the auto-classification of a document."""
    doc = db.query(Document).filter(Document.id == request.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.classification_approved = request.approved
    if request.corrected_type:
        try:
            new_type = DocumentType(request.corrected_type)
            doc.document_type = new_type
            doc.user_corrected_type = request.corrected_type
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid document type: {request.corrected_type}")

    db.commit()
    db.refresh(doc)

    return StatusResponse(
        status="success",
        message=f"Classification {'approved' if request.approved else 'corrected'} for document {doc.original_filename}",
    )


@router.post("/set-extraction-schema", response_model=StatusResponse)
def set_extraction_schema(
    request: SchemaMapping,
    db: Session = Depends(get_db),
):
    """Set a custom extraction schema for a document."""
    doc = db.query(Document).filter(Document.id == request.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.extraction_schema = request.schema
    db.commit()

    return StatusResponse(
        status="success",
        message=f"Extraction schema set for document {doc.original_filename}",
        data={"schema": request.schema},
    )


@router.get("/default-schemas")
def get_default_schemas():
    """Get default extraction schemas for each document type."""
    schemas = {
        "annual_report": {
            "fields": ["revenue", "net_profit", "gross_profit", "ebitda", "total_assets", "total_liabilities",
                       "total_debt", "shareholders_equity", "cash_flow_operations", "interest_expense",
                       "director_names", "auditor_qualifications"],
            "description": "Annual Report / Financial Statements (P&L, Balance Sheet, Cash Flow)"
        },
        "alm": {
            "fields": ["asset_maturity_buckets", "liability_maturity_buckets", "cumulative_gap",
                       "interest_rate_sensitivity", "liquidity_coverage_ratio", "net_stable_funding_ratio"],
            "description": "Asset-Liability Management Statement"
        },
        "shareholding_pattern": {
            "fields": ["promoter_holding_pct", "institutional_holding_pct", "public_holding_pct",
                       "pledged_shares_pct", "top_shareholders", "change_in_holding"],
            "description": "Shareholding Pattern"
        },
        "borrowing_profile": {
            "fields": ["total_borrowings", "secured_loans", "unsecured_loans", "working_capital_limit",
                       "term_loans", "lender_names", "repayment_schedule", "interest_rates",
                       "collateral_details", "guarantee_details"],
            "description": "Borrowing Profile / Debt Schedule"
        },
        "portfolio_performance": {
            "fields": ["portfolio_value", "asset_allocation", "sector_exposure",
                       "top_holdings", "returns_ytd", "npa_ratio", "provision_coverage",
                       "concentration_risk"],
            "description": "Portfolio Cuts / Performance Data"
        },
        "gst_return": {
            "fields": ["gst_turnover", "gstr_3b_tax_liability", "gstr_2a_itc",
                       "gstr_1_outward_supply", "filing_count", "late_filings"],
            "description": "GST Returns (GSTR-1/2A/2B/3B)"
        },
        "cibil_report": {
            "fields": ["cibil_score", "cibil_rank", "dpd_instances", "npa_classification",
                       "wilful_defaulter", "suit_filed_cases", "written_off_amount"],
            "description": "CIBIL / Credit Report"
        },
    }
    return schemas


# ─── SWOT Analysis Endpoints ───

@router.post("/generate-swot", response_model=StatusResponse)
def generate_swot(
    request: SWOTRequest,
    db: Session = Depends(get_db),
):
    """Generate AI-powered SWOT analysis triangulating all data sources."""
    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    try:
        result = swot_analysis_service.generate_swot(
            company_id=str(request.company_id), db=db
        )
        return StatusResponse(
            status="success",
            message="SWOT analysis generated successfully.",
            data=result,
        )
    except Exception as e:
        logger.error(f"SWOT generation failed: {e}")
        raise HTTPException(status_code=500, detail="SWOT generation failed. Check server logs for details.")


@router.get("/companies/{company_id}/swot", response_model=List[SWOTResponse])
def get_swot(company_id: str, db: Session = Depends(get_db)):
    """Get SWOT analyses for a company."""
    _validate_uuid(company_id)
    return (
        db.query(SWOTAnalysis)
        .filter(SWOTAnalysis.company_id == company_id)
        .order_by(SWOTAnalysis.created_at.desc())
        .all()
    )


# ─── Agent Orchestrator Endpoints ───

@router.post("/run-agent-pipeline", response_model=StatusResponse)
def run_agent_pipeline(
    request: ResearchRequest,
    db: Session = Depends(get_db),
):
    """Run the full LangGraph agent pipeline (all 6 agents in sequence)."""
    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    try:
        result = agent_orchestrator.run_full_pipeline(
            company_id=str(request.company_id), db=db
        )
        return StatusResponse(
            status="success",
            message=f"Agent pipeline complete. {len(result.get('agent_logs', []))} agents executed.",
            data=result,
        )
    except Exception as e:
        logger.error(f"Agent pipeline failed: {e}")
        raise HTTPException(status_code=500, detail="Agent pipeline failed. Check server logs for details.")


@router.post("/run-single-agent", response_model=StatusResponse)
def run_single_agent(
    request: ResearchRequest,
    agent_name: str = "documents",
    db: Session = Depends(get_db),
):
    """Run a single agent (documents, financials, research, promoters, warnings, risk)."""
    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    try:
        result = agent_orchestrator.run_single_agent(
            agent_name=agent_name,
            company_id=str(request.company_id),
            db=db,
        )
        return StatusResponse(
            status="success",
            message=f"Agent '{agent_name}' complete.",
            data=result,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Single agent '{agent_name}' failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent '{agent_name}' failed. Check server logs for details.")
