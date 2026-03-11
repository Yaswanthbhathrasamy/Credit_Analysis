"""
LLM Financial Extraction Service
Uses OpenAI GPT via LangChain to extract structured financial data from text.
Enhanced with deep Indian-context awareness: Ind-AS, GSTR, CIBIL, ITR, MCA formats.
"""

import json
import re
import logging
from typing import Optional, Dict, Any

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ExtractedFinancials(BaseModel):
    """Structured financial data extracted from documents."""
    fiscal_year: Optional[str] = Field(None, description="Fiscal year or period (e.g., FY 2023-24, AY 2024-25)")
    revenue: Optional[float] = Field(None, description="Total revenue/turnover in currency units")
    net_profit: Optional[float] = Field(None, description="Net profit after tax")
    gross_profit: Optional[float] = Field(None, description="Gross profit")
    ebitda: Optional[float] = Field(None, description="EBITDA")
    total_assets: Optional[float] = Field(None, description="Total assets")
    total_liabilities: Optional[float] = Field(None, description="Total liabilities")
    total_debt: Optional[float] = Field(None, description="Total debt (long-term + short-term borrowings)")
    current_assets: Optional[float] = Field(None, description="Current assets")
    current_liabilities: Optional[float] = Field(None, description="Current liabilities")
    shareholders_equity: Optional[float] = Field(None, description="Shareholders equity / net worth")
    cash_flow_operations: Optional[float] = Field(None, description="Cash flow from operations")
    interest_expense: Optional[float] = Field(None, description="Interest expense / finance costs")
    director_names: Optional[List[str]] = Field(default_factory=list, description="Names of directors/promoters/KMPs")
    legal_mentions: Optional[List[str]] = Field(default_factory=list, description="Mentions of legal cases, lawsuits, regulatory actions, show cause notices")

    # Indian-specific fields
    gst_turnover: Optional[float] = Field(None, description="Turnover as reported in GST returns")
    gstr3b_tax_liability: Optional[float] = Field(None, description="Total tax liability from GSTR-3B")
    gstr2a_itc_claimed: Optional[float] = Field(None, description="Input Tax Credit from GSTR-2A/2B")
    gstr3b_itc_claimed: Optional[float] = Field(None, description="ITC claimed in GSTR-3B")
    gst_filings_count: Optional[int] = Field(None, description="Number of GST return filings found (0-12)")
    cibil_score: Optional[int] = Field(None, description="CIBIL/TransUnion credit score")
    cibil_rank: Optional[int] = Field(None, description="CIBIL Commercial Rank (1-10)")
    dpd_instances: Optional[int] = Field(None, description="Days Past Due instances from credit report")
    npa_classification: Optional[str] = Field(None, description="NPA/SMA classification: standard, SMA-0, SMA-1, SMA-2, substandard, doubtful, loss")
    related_party_transactions: Optional[float] = Field(None, description="Total related party transactions value")
    contingent_liabilities: Optional[float] = Field(None, description="Contingent liabilities from notes to accounts")
    auditor_qualifications: Optional[List[str]] = Field(default_factory=list, description="Auditor qualifications or emphasis of matter")


class FinancialExtractionService:
    """Uses LLM to extract structured financial metrics from document text.
    Enhanced with Indian regulatory context awareness."""

    def __init__(self):
        self._llm = None
        self.parser = PydanticOutputParser(pydantic_object=ExtractedFinancials)

    @property
    def llm(self):
        if self._llm is None:
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                api_key=settings.openai_api_key,
            )
        return self._llm

    def extract_financial_data(self, text: str, document_type: str = None) -> Dict[str, Any]:
        """
        Extract structured financial data from unstructured document text.
        Uses document-type-specific prompts for better accuracy.
        """
        # Choose specialized prompt based on document type
        system_prompt = self._get_extraction_prompt(document_type)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """Extract all financial metrics from the following document text:

{document_text}"""),
        ])

        formatted_prompt = prompt.format_messages(
            format_instructions=self.parser.get_format_instructions(),
            document_text=text[:15000],
        )

        try:
            response = self.llm.invoke(formatted_prompt)
            extracted = self.parser.parse(response.content)
            data = extracted.model_dump()
            data = self._compute_ratios(data)
            data = self._normalize_indian_amounts(data, text)
            data["_extraction_reasoning"] = self._generate_extraction_reasoning(data, document_type)
            return data
        except Exception as e:
            logger.error(f"Financial extraction failed: {e}")
            return self._fallback_extraction(text)

    def _get_extraction_prompt(self, document_type: str = None) -> str:
        """Get document-type-specific extraction prompt with Indian context."""
        base_prompt = """You are an expert Indian financial analyst specializing in corporate credit analysis.
You have deep knowledge of Indian accounting standards (Ind-AS / Indian GAAP), RBI regulations,
GST framework, Companies Act 2013, and SEBI guidelines.

Extract structured financial data from the provided document text.

CRITICAL INDIAN CONTEXT RULES:
1. **Amount Units**: Indian financials use Lakhs (1L = 100,000) and Crores (1Cr = 10,000,000).
   - ALWAYS note if amounts are in Lakhs, Crores, or absolute Rupees.
   - Convert all amounts to the same unit as present in the document. Note the unit used.
   - "Rs. 1,23,45,678" follows Indian numbering (1 crore 23 lakh 45 thousand 678).

2. **Fiscal Year**: Indian fiscal year runs April to March.
   - "FY 2023-24" = April 2023 to March 2024
   - "AY 2024-25" = Assessment Year for FY 2023-24

3. **GST Returns**: Understand the distinction:
   - GSTR-1: Outward supplies (sales reported by company)
   - GSTR-2A/2B: Auto-populated inward supplies (purchases reported by suppliers)
   - GSTR-3B: Summary return with self-declared tax liability and ITC claims
   - DISCREPANCY between GSTR-2A ITC and GSTR-3B ITC = potential tax risk
   - DISCREPANCY between GSTR-1 turnover and books turnover = revenue manipulation risk

4. **CIBIL/Credit Reports**: Extract:
   - CIBIL Score (300-900) or CIBIL Rank (1-10, 1=best for commercial)
   - DPD (Days Past Due) entries — any DPD > 0 is a red flag
   - SMA classification: SMA-0 (1-30 days), SMA-1 (31-60 days), SMA-2 (61-90 days)
   - NPA classification if mentioned

5. **Ind-AS Specifics**:
   - "Other Comprehensive Income" should be noted separately from P&L profit
   - Fair value gains/losses may inflate balance sheet
   - Look for deferred tax assets/liabilities
   - Related Party Transactions (Ind-AS 24) — extract total value
   - Contingent Liabilities (Ind-AS 37) — extract from notes to accounts

6. **Auditor's Report**: Flag:
   - Qualified opinions, disclaimers, adverse opinions
   - Emphasis of Matter paragraphs
   - CARO (Companies Auditor's Report Order) observations
   - Going concern qualifications

7. **Directors/KMPs**: Extract Key Managerial Personnel including:
   - Managing Director, Whole-time Directors
   - CFO, Company Secretary
   - Independent Directors

If a value is not found in the text, return null for that field.
Only extract data that is explicitly stated or can be directly calculated from the text.

{format_instructions}"""

        # Add specialized context for specific document types
        type_additions = {
            "gst_return": """

ADDITIONAL GST-SPECIFIC EXTRACTION:
- Extract GSTIN, Tax Period, Place of Supply
- Extract Taxable Value, IGST, CGST, SGST amounts separately
- For GSTR-3B: Extract Table 3.1 (outward supplies), Table 4 (ITC), Table 6 (payment)
- For GSTR-2A: Extract total ITC available from suppliers
- Flag if late filing fee is present (indicates delayed filing)
- Count the number of filing periods visible""",

            "cibil_report": """

ADDITIONAL CIBIL-SPECIFIC EXTRACTION:
- Extract the Credit Score (300-900 range)
- For Commercial reports: Extract CIBIL Rank (1-10) and Credit Rating
- List all credit facilities with DPD status
- Note any "Written Off" or "Settled" accounts (red flags)
- Extract total outstanding, total overdue amounts
- Note suit-filed / wilful defaulter status if present
- Extract the number of enquiries in last 6 months (high enquiries = credit hungry)""",

            "annual_report": """

ADDITIONAL ANNUAL REPORT EXTRACTION:
- Extract from Board's Report: dividend declared, CSR spend, material changes
- From Auditor's Report: qualification matters, CARO observations
- From Notes: Related Party Transactions, Contingent Liabilities, Commitments
- Segment-wise revenue if available
- Employee count / key ratios from Business Responsibility Report""",

            "financial_statement": """

ADDITIONAL FINANCIAL STATEMENT EXTRACTION:
- Follow Ind-AS / Schedule III format
- Extract both standalone and consolidated figures (prefer consolidated)
- Note if prepared under Ind-AS or Indian GAAP
- Extract exceptional items separately
- Deferred tax assets/liabilities from balance sheet
- Trade receivables aging (> 6 months is a red flag)
- Inventory valuation method""",
        }

        if document_type and document_type in type_additions:
            return base_prompt + type_additions[document_type]
        return base_prompt

    def _normalize_indian_amounts(self, data: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        """Detect and normalize amount units (lakhs/crores) for consistency."""
        # Detect prevalent unit from text
        text_lower = raw_text[:5000].lower()
        in_crores = bool(re.search(r'(?:in\s+)?(?:₹|rs\.?|inr)?\s*(?:in\s+)?crore', text_lower))
        in_lakhs = bool(re.search(r'(?:in\s+)?(?:₹|rs\.?|inr)?\s*(?:in\s+)?lakh', text_lower))

        if in_crores or in_lakhs:
            data["_amount_unit"] = "crores" if in_crores else "lakhs"
        else:
            data["_amount_unit"] = "absolute"

        return data

    def _generate_extraction_reasoning(self, data: Dict[str, Any], doc_type: str = None) -> str:
        """Generate human-readable reasoning for extraction decisions."""
        reasoning_parts = []

        if doc_type:
            reasoning_parts.append(f"Document identified as: {doc_type}")

        unit = data.get("_amount_unit", "absolute")
        if unit != "absolute":
            reasoning_parts.append(f"Amounts appear to be in {unit}")

        if data.get("fiscal_year"):
            reasoning_parts.append(f"Fiscal year identified: {data['fiscal_year']}")

        # GST reconciliation flags
        if data.get("gstr2a_itc_claimed") and data.get("gstr3b_itc_claimed"):
            itc_2a = data["gstr2a_itc_claimed"]
            itc_3b = data["gstr3b_itc_claimed"]
            if itc_3b > itc_2a * 1.1:
                reasoning_parts.append(
                    f"WARNING: GSTR-3B ITC (₹{itc_3b:,.0f}) exceeds GSTR-2A ITC (₹{itc_2a:,.0f}) "
                    f"by {((itc_3b/itc_2a - 1)*100):.1f}%. Possible excess ITC claim."
                )

        # CIBIL flags
        if data.get("cibil_score") and data["cibil_score"] < 650:
            reasoning_parts.append(f"CIBIL score {data['cibil_score']} is below acceptable threshold (650)")

        if data.get("dpd_instances") and data["dpd_instances"] > 0:
            reasoning_parts.append(f"Found {data['dpd_instances']} Days Past Due instances — credit discipline concern")

        if data.get("npa_classification") and data["npa_classification"] != "standard":
            reasoning_parts.append(f"Account classified as {data['npa_classification']} — significant credit risk")

        if data.get("contingent_liabilities"):
            reasoning_parts.append(f"Contingent liabilities of ₹{data['contingent_liabilities']:,.0f} noted")

        if data.get("auditor_qualifications"):
            reasoning_parts.append(f"Auditor qualifications found: {'; '.join(data['auditor_qualifications'][:3])}")

        extracted_fields = sum(1 for v in data.values() if v is not None and v != [] and v != 0)
        reasoning_parts.append(f"Successfully extracted {extracted_fields} data fields")

        return " | ".join(reasoning_parts)

    def _compute_ratios(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute financial ratios from extracted metrics."""
        try:
            if data.get("total_debt") and data.get("total_assets"):
                data["debt_ratio"] = round(data["total_debt"] / data["total_assets"], 4)

            if data.get("current_assets") and data.get("current_liabilities"):
                if data["current_liabilities"] > 0:
                    data["current_ratio"] = round(data["current_assets"] / data["current_liabilities"], 4)

            if data.get("total_debt") and data.get("shareholders_equity"):
                if data["shareholders_equity"] > 0:
                    data["debt_to_equity"] = round(data["total_debt"] / data["shareholders_equity"], 4)

            if data.get("ebitda") and data.get("interest_expense"):
                if data["interest_expense"] > 0:
                    data["interest_coverage"] = round(data["ebitda"] / data["interest_expense"], 4)

            if data.get("net_profit") and data.get("revenue"):
                if data["revenue"] > 0:
                    data["profit_margin"] = round(data["net_profit"] / data["revenue"], 4)

            if data.get("net_profit") and data.get("total_assets"):
                if data["total_assets"] > 0:
                    data["return_on_assets"] = round(data["net_profit"] / data["total_assets"], 4)

            if data.get("net_profit") and data.get("shareholders_equity"):
                if data["shareholders_equity"] > 0:
                    data["return_on_equity"] = round(data["net_profit"] / data["shareholders_equity"], 4)

            # DSCR (Debt Service Coverage Ratio) — important for Indian lending
            if data.get("ebitda") and data.get("interest_expense") and data.get("total_debt"):
                annual_debt_service = data["interest_expense"] + (data["total_debt"] * 0.1)  # Approximate principal repayment
                if annual_debt_service > 0:
                    data["dscr"] = round(data["ebitda"] / annual_debt_service, 4)

        except (ZeroDivisionError, TypeError):
            pass

        return data

    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Enhanced regex-based fallback extraction for Indian documents."""
        data = {}

        # Indian-format number: 1,23,45,678.00 or 12,34,567
        indian_num = r'[\d,]+\.?\d*'

        patterns = {
            "revenue": rf"(?:revenue|turnover|sales|total\s+income)[\s:]*(?:Rs\.?|INR|₹)?\s*({indian_num})",
            "net_profit": rf"(?:net\s*profit|PAT|profit\s*after\s*tax)[\s:]*(?:Rs\.?|INR|₹)?\s*({indian_num})",
            "total_assets": rf"(?:total\s*assets)[\s:]*(?:Rs\.?|INR|₹)?\s*({indian_num})",
            "total_liabilities": rf"(?:total\s*liabilities)[\s:]*(?:Rs\.?|INR|₹)?\s*({indian_num})",
            "total_debt": rf"(?:total\s*debt|total\s*borrowings)[\s:]*(?:Rs\.?|INR|₹)?\s*({indian_num})",
            "ebitda": rf"(?:EBITDA|earnings\s+before)[\s:]*(?:Rs\.?|INR|₹)?\s*({indian_num})",
            "shareholders_equity": rf"(?:shareholders?\s*equity|net\s*worth)[\s:]*(?:Rs\.?|INR|₹)?\s*({indian_num})",
            "interest_expense": rf"(?:interest\s*(?:expense|cost)|finance\s*cost)[\s:]*(?:Rs\.?|INR|₹)?\s*({indian_num})",
        }

        # CIBIL score extraction
        cibil_match = re.search(r'(?:CIBIL|credit)\s*score[\s:]*(\d{3})', text, re.IGNORECASE)
        if cibil_match:
            data["cibil_score"] = int(cibil_match.group(1))

        # CIBIL Rank extraction
        rank_match = re.search(r'CIBIL\s*(?:commercial\s*)?rank[\s:]*(\d{1,2})', text, re.IGNORECASE)
        if rank_match:
            data["cibil_rank"] = int(rank_match.group(1))

        # GST filings count
        gst_periods = re.findall(r'(?:tax\s+period|return\s+period)[\s:]*\w+[\s-]\d{4}', text, re.IGNORECASE)
        if gst_periods:
            data["gst_filings_count"] = len(set(gst_periods))

        # NPA/SMA classification
        sma_match = re.search(r'(SMA-[012]|substandard|doubtful|loss\s+asset|NPA)', text, re.IGNORECASE)
        if sma_match:
            data["npa_classification"] = sma_match.group(1).lower()

        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    data[field] = float(match.group(1).replace(",", ""))
                except ValueError:
                    pass

        return data

    def summarize_financials(self, data: Dict[str, Any]) -> str:
        """Generate a natural language summary of financial metrics with Indian context."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior Indian credit analyst preparing a financial summary for a
Credit Appraisal Memo (CAM). Reference Indian benchmarks and RBI norms where relevant.
Mention any GST or CIBIL observations. Provide a concise 3-4 paragraph financial summary."""),
            ("human", "Summarize these financial metrics for a credit appraisal:\n{data}"),
        ])

        formatted = prompt.format_messages(data=json.dumps(data, indent=2, default=str))
        response = self.llm.invoke(formatted)
        return response.content


financial_extraction_service = FinancialExtractionService()
