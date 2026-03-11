from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ─── Company Schemas ───

class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    incorporation_date: Optional[str] = None
    registered_address: Optional[str] = None
    cin: Optional[str] = None
    pan: Optional[str] = None
    gst_number: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    loan_amount_requested: Optional[float] = None
    loan_purpose: Optional[str] = None
    loan_type: Optional[str] = None
    loan_tenure_months: Optional[int] = None
    proposed_interest_rate: Optional[float] = None
    annual_turnover: Optional[float] = None


class CompanyResponse(BaseModel):
    id: UUID
    name: str
    industry: Optional[str]
    incorporation_date: Optional[str]
    registered_address: Optional[str]
    cin: Optional[str]
    pan: Optional[str]
    gst_number: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    loan_amount_requested: Optional[float]
    loan_purpose: Optional[str]
    loan_type: Optional[str]
    loan_tenure_months: Optional[int]
    proposed_interest_rate: Optional[float]
    annual_turnover: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Document Schemas ───

class DocumentResponse(BaseModel):
    id: UUID
    company_id: UUID
    filename: str
    original_filename: str
    document_type: str
    processing_status: str
    ocr_used: bool
    file_size: Optional[int]
    confidence_score: Optional[float] = None
    detected_doc_type: Optional[str] = None
    classification_approved: Optional[bool] = False
    user_corrected_type: Optional[str] = None
    extraction_schema: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Financial Metrics Schemas ───

class FinancialMetricResponse(BaseModel):
    id: UUID
    company_id: UUID
    fiscal_year: Optional[str]
    revenue: Optional[float]
    net_profit: Optional[float]
    gross_profit: Optional[float]
    ebitda: Optional[float]
    total_assets: Optional[float]
    total_liabilities: Optional[float]
    total_debt: Optional[float]
    current_assets: Optional[float]
    current_liabilities: Optional[float]
    shareholders_equity: Optional[float]
    cash_flow_operations: Optional[float]
    interest_expense: Optional[float]
    debt_ratio: Optional[float]
    current_ratio: Optional[float]
    debt_to_equity: Optional[float]
    interest_coverage: Optional[float]
    profit_margin: Optional[float]
    return_on_assets: Optional[float]
    return_on_equity: Optional[float]
    director_names: Optional[List[str]]
    legal_mentions: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


class FinancialExtractionRequest(BaseModel):
    company_id: UUID
    document_ids: Optional[List[UUID]] = None


# ─── Risk Flags Schemas ───

class RiskFlagResponse(BaseModel):
    id: UUID
    company_id: UUID
    flag_type: str
    description: str
    severity: str
    source_a: Optional[str]
    source_b: Optional[str]
    value_a: Optional[float]
    value_b: Optional[float]
    discrepancy_pct: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Research Schemas ───

class ResearchRequest(BaseModel):
    company_id: UUID


class ResearchFindingResponse(BaseModel):
    id: UUID
    company_id: UUID
    category: Optional[str]
    title: Optional[str]
    summary: Optional[str]
    source_url: Optional[str]
    sentiment: Optional[str]
    relevance_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Promoter Analysis Schemas ───

class PromoterAnalysisRequest(BaseModel):
    company_id: UUID
    promoter_names: Optional[List[str]] = None


class PromoterAnalysisResponse(BaseModel):
    id: UUID
    company_id: UUID
    promoter_name: str
    designation: Optional[str]
    background_summary: Optional[str]
    bankruptcy_flag: bool
    fraud_flag: bool
    regulatory_violation_flag: bool
    associated_companies: Optional[List[str]]
    risk_summary: Optional[str]
    risk_level: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Risk Score Schemas ───

class RiskScoreRequest(BaseModel):
    company_id: UUID


class RiskScoreResponse(BaseModel):
    id: UUID
    company_id: UUID
    probability_of_default: float
    risk_level: Optional[str]
    model_version: Optional[str]
    decision: Optional[str]
    recommended_loan_limit: Optional[float]
    suggested_interest_rate: Optional[float]
    shap_values: Optional[Dict[str, Any]]
    positive_factors: Optional[List[str]]
    negative_factors: Optional[List[str]]
    feature_importance: Optional[Dict[str, float]]
    five_cs_evaluation: Optional[Dict[str, Any]]
    reasoning_narrative: Optional[str] = None
    due_diligence_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DueDiligenceUpdate(BaseModel):
    company_id: UUID
    notes: str


# ─── Early Warning Schemas ───

class EarlyWarningRequest(BaseModel):
    company_id: UUID


class EarlyWarningResponse(BaseModel):
    company_id: UUID
    warnings: List[RiskFlagResponse]
    total_flags: int
    critical_flags: int


# ─── CAM Report Schemas ───

class CAMReportRequest(BaseModel):
    company_id: UUID


# ─── Generic Responses ───

class StatusResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


# ─── Document Classification Schemas ───

class ClassificationApproval(BaseModel):
    document_id: UUID
    approved: bool
    corrected_type: Optional[str] = None


class SchemaMapping(BaseModel):
    document_id: UUID
    schema: Dict[str, Any]  # User-defined extraction schema


# ─── SWOT Analysis Schemas ───

class SWOTRequest(BaseModel):
    company_id: UUID


class SWOTResponse(BaseModel):
    id: UUID
    company_id: UUID
    strengths: Optional[List[str]]
    weaknesses: Optional[List[str]]
    opportunities: Optional[List[str]]
    threats: Optional[List[str]]
    summary: Optional[str]
    data_sources: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True
