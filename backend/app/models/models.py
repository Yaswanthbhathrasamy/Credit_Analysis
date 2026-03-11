import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Text, DateTime, Boolean, Integer,
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class DocumentType(str, enum.Enum):
    ANNUAL_REPORT = "annual_report"
    FINANCIAL_STATEMENT = "financial_statement"
    BANK_STATEMENT = "bank_statement"
    GST_RETURN = "gst_return"
    LEGAL_NOTICE = "legal_notice"
    RATING_REPORT = "rating_report"
    ITR_FORM = "itr_form"
    CIBIL_REPORT = "cibil_report"
    MCA_FILING = "mca_filing"
    ALM = "alm"
    SHAREHOLDING_PATTERN = "shareholding_pattern"
    BORROWING_PROFILE = "borrowing_profile"
    PORTFOLIO_PERFORMANCE = "portfolio_performance"
    OTHER = "other"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LoanDecision(str, enum.Enum):
    APPROVE = "approve"
    APPROVE_WITH_CONDITIONS = "approve_with_conditions"
    REJECT = "reject"


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    industry = Column(String(255))
    incorporation_date = Column(String(50))
    registered_address = Column(Text)
    cin = Column(String(50))
    pan = Column(String(20))
    gst_number = Column(String(20))
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    loan_amount_requested = Column(Float)
    loan_purpose = Column(Text)
    loan_type = Column(String(100))  # Term Loan, Working Capital, CC/OD, etc.
    loan_tenure_months = Column(Integer)
    proposed_interest_rate = Column(Float)
    annual_turnover = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("Document", back_populates="company", cascade="all, delete-orphan")
    financial_metrics = relationship("FinancialMetric", back_populates="company", cascade="all, delete-orphan")
    risk_flags = relationship("RiskFlag", back_populates="company", cascade="all, delete-orphan")
    research_findings = relationship("ResearchFinding", back_populates="company", cascade="all, delete-orphan")
    promoter_analyses = relationship("PromoterAnalysis", back_populates="company", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="company", cascade="all, delete-orphan")
    swot_analyses = relationship("SWOTAnalysis", back_populates="company", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    document_type = Column(SQLEnum(DocumentType), default=DocumentType.OTHER)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)
    extracted_text = Column(Text)
    processing_status = Column(String(50), default="pending")
    ocr_used = Column(Boolean, default=False)
    confidence_score = Column(Float)
    detected_doc_type = Column(String(50))
    classification_approved = Column(Boolean, default=False)
    user_corrected_type = Column(String(50))  # If user overrides auto-classification
    extraction_schema = Column(JSON)  # User-defined or default extraction schema
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="documents")


class FinancialMetric(Base):
    __tablename__ = "financial_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    fiscal_year = Column(String(20))
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)

    revenue = Column(Float)
    net_profit = Column(Float)
    gross_profit = Column(Float)
    ebitda = Column(Float)
    total_assets = Column(Float)
    total_liabilities = Column(Float)
    total_debt = Column(Float)
    current_assets = Column(Float)
    current_liabilities = Column(Float)
    shareholders_equity = Column(Float)
    cash_flow_operations = Column(Float)
    interest_expense = Column(Float)

    # Ratios
    debt_ratio = Column(Float)
    current_ratio = Column(Float)
    debt_to_equity = Column(Float)
    interest_coverage = Column(Float)
    profit_margin = Column(Float)
    return_on_assets = Column(Float)
    return_on_equity = Column(Float)

    # Additional fields
    director_names = Column(JSON)
    legal_mentions = Column(JSON)
    raw_extraction = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="financial_metrics")


class RiskFlag(Base):
    __tablename__ = "risk_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    flag_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(SQLEnum(RiskLevel), default=RiskLevel.MEDIUM)
    source_a = Column(String(255))
    source_b = Column(String(255))
    value_a = Column(Float)
    value_b = Column(Float)
    discrepancy_pct = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="risk_flags")


class ResearchFinding(Base):
    __tablename__ = "research_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    category = Column(String(100))  # litigation, regulatory, industry, reputation
    title = Column(String(500))
    summary = Column(Text)
    source_url = Column(String(1000))
    sentiment = Column(String(50))  # positive, negative, neutral
    relevance_score = Column(Float)
    raw_content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="research_findings")


class PromoterAnalysis(Base):
    __tablename__ = "promoter_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    promoter_name = Column(String(255), nullable=False)
    designation = Column(String(100))
    background_summary = Column(Text)
    bankruptcy_flag = Column(Boolean, default=False)
    fraud_flag = Column(Boolean, default=False)
    regulatory_violation_flag = Column(Boolean, default=False)
    associated_companies = Column(JSON)
    risk_summary = Column(Text)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)
    sources = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="promoter_analyses")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    probability_of_default = Column(Float, nullable=False)
    risk_level = Column(SQLEnum(RiskLevel))
    model_version = Column(String(50))

    # Decision
    decision = Column(SQLEnum(LoanDecision))
    recommended_loan_limit = Column(Float)
    suggested_interest_rate = Column(Float)

    # SHAP Explanations
    shap_values = Column(JSON)
    positive_factors = Column(JSON)
    negative_factors = Column(JSON)
    feature_importance = Column(JSON)

    # Five Cs evaluation
    five_cs_evaluation = Column(JSON)

    # Explainability: full reasoning narrative
    reasoning_narrative = Column(Text)

    due_diligence_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="risk_scores")


class SWOTAnalysis(Base):
    __tablename__ = "swot_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    strengths = Column(JSON)  # List of strength items
    weaknesses = Column(JSON)  # List of weakness items
    opportunities = Column(JSON)  # List of opportunity items
    threats = Column(JSON)  # List of threat items
    summary = Column(Text)
    data_sources = Column(JSON)  # Which data was used for triangulation
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="swot_analyses")
