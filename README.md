# Intelli-Credit: AI Powered Corporate Credit Decisioning Platform

A full-stack AI platform that automates corporate credit appraisal and generates professional Credit Appraisal Memo (CAM) reports for loan decisioning.

## Architecture

```
User → React Dashboard → FastAPI Backend → PostgreSQL
                              ↓
         ┌──────────────────────────────────────┐
         │  Document Processing (PyMuPDF + OCR) │
         │  LLM Extraction (GPT + LangChain)    │
         │  Financial Validation Engine          │
         │  Web Intelligence (SerpAPI + BS4)     │
         │  Promoter Risk Analysis               │
         │  ML Risk Scoring (Scikit-learn)       │
         │  SHAP Explainability                  │
         │  CAM Report Generator (python-docx)   │
         └──────────────────────────────────────┘
```

### System Architecture Diagram — Image Generation Prompt

> **Use the prompt below with any AI image generator (Midjourney, DALL·E, Figma AI, Excalidraw AI, etc.) to produce a professional system architecture diagram for Intelli-Credit.**

```text
Create a detailed, professional system architecture diagram for "Intelli-Credit — AI-Powered Corporate Credit Decisioning Platform". Use a clean, modern tech blueprint style with a dark navy (#0f172a) or white background, neon-accent connecting lines, and clearly labeled component boxes with rounded corners and subtle drop shadows. Use a left-to-right or top-to-bottom data flow layout.

LAYER 1 — CLIENT LAYER (top / left):
- "React 18 + Vite + Tailwind CSS" frontend box.
  - Sub-components inside: HomePage (Company Listing), CompanyPage (New Company Form), DashboardPage (Analysis Dashboard with Recharts charts), AnalyzerPage, AboutPage, TeamPage, ContactPage.
  - Arrow labeled "REST API (Axios)" pointing to the backend.

LAYER 2 — API GATEWAY (middle):
- "FastAPI Backend" large box (Python).
  - Show "routes.py" as the single entry router.
  - Inside list key endpoints vertically: POST /upload-documents, POST /extract-financial-data, POST /run-research-agent, POST /run-crew-research, POST /run-promoter-analysis, POST /detect-early-warning, POST /calculate-risk-score, GET /generate-cam-report, GET /dashboard-summary.
  - Arrow down to "PostgreSQL 14+" database cylinder, labeled "SQLAlchemy ORM".
  - Database tables listed on/next to the cylinder: Company, Document, FinancialMetric, RiskFlag, ResearchFinding, PromoterAnalysis, RiskScore.

LAYER 3 — THREE PILLARS (center, side by side):

  PILLAR 1 — "Data Ingestor":
    Box 1: "DocumentProcessor" — icons/labels: PyMuPDF (fitz) text extraction, PaddleOCR (Hindi + English bilingual), image preprocessing (contrast, sharpen, autocontrast), smart OCR detection (garbled text, image ratio, word density), Indian doc-type detection (GSTR, CIBIL, Annual Report, ITR, Bank Statement, MCA Filing), table extraction.
    Box 2: "FinancialExtractionService" — icons/labels: OpenAI GPT-4o-mini via LangChain, document-type-aware prompts, 30+ Pydantic financial fields, Indian amount normalization (lakh/crore), ratio computation (DSCR, current ratio, debt-to-equity), extraction reasoning audit trail.
    Box 3: "FinancialValidationService" — icons/labels: cross-source revenue/profit discrepancy check (15% threshold), balance sheet sanity (Assets ≥ Liabilities + Equity), ratio anomaly detection, GST reconciliation (GSTR-2A vs 3B ITC mismatch), CIBIL flag check (score < 650, DPD > 0, wilful defaulter), RBI SMA/NPA classification (SMA-0/1/2), auditor qualification flags, RBI prudential norms check. Output: RiskFlag objects with severity levels (low/medium/high/critical).

  PILLAR 2 — "Research Agent":
    Box 1: "ResearchIntelligenceService" — icons/labels: SerpAPI (gl=in, hl=en India-focused), BeautifulSoup web scraping (10KB page limit), GPT sentiment + relevance scoring (0.0–1.0 scale), query categories: litigation, regulatory, GST compliance, NPA/default, environmental.
    Box 2: "CrewAIResearchService" — icons/labels: LangChain multi-chain orchestration, 3 specialized analyst agents (News Analyst → ET, Moneycontrol, Business Standard; Regulatory Analyst → SEBI, RBI, NCLT, DRT; Sector Analyst → industry outlook, commodity/macro impact), Synthesis chain → Five Cs credit risk mapping.
    Box 3: "PromoterRiskService" — icons/labels: director-level web search, GPT risk assessment, flags: bankruptcy, fraud, regulatory, criminal; risk_level classification output.

  PILLAR 3 — "Recommendation Engine":
    Box 1: "RiskScoringService" — icons/labels: scikit-learn ML ensemble (Random Forest, Logistic Regression, Gradient Boosting), 12-feature vector (revenue, profit margin, debt ratio, current ratio, GST filings, litigation flags, sector growth, promoter risk, years in business, interest coverage, revenue growth, cash flow status), best model auto-selected by AUC-ROC, SHAP explainability (positive/negative factor breakdown), Five Cs evaluation (Character, Capacity, Capital, Collateral, Conditions), decision output: Approve / Reject / Conditional + loan limit + interest rate, reasoning narrative ("walk the judge through the logic").
    Box 2: "CAMReportService" — icons/labels: python-docx .docx generation, sections: executive summary, company profile, financial analysis, research findings, promoter analysis, risk assessment, SHAP explanation, loan recommendation, terms & conditions.

LAYER 4 — EXTERNAL SERVICES (bottom / right):
  - "OpenAI GPT-4o-mini" cloud icon with LangChain connector.
  - "SerpAPI" cloud icon (Indian web search).
  - "PaddleOCR Engine" icon (Hindi + English).
  - "PostgreSQL" database cylinder.

LAYER 5 — INFRASTRUCTURE:
  - "Docker Compose" wrapping the entire stack.
  - Container boxes: frontend (port 3000), backend (port 8000), postgres (port 5432).
  - Arrows showing container networking.

ADDITIONAL DETAILS:
  - Show data flow arrows with labels: "PDF/Scanned Docs" → Document Processor → "Extracted Text" → Financial Extraction → "Structured JSON" → Validation → "Risk Flags" → Risk Scoring → "ML Prediction + SHAP" → CAM Report → "Downloadable .docx".
  - Color-code the three pillars: Data Ingestor (blue/cyan), Research Agent (green/emerald), Recommendation Engine (orange/amber).
  - Indian context badge/icon near relevant components showing: ₹ INR (lakhs/crores), FY April–March, GST (GSTR-1/2A/2B/3B), CIBIL, RBI IRAC norms, Ind-AS, MCA/ROC filings.
  - Include a legend box explaining the color coding and arrow types.
  - Style: flat design, no 3D effects, sans-serif fonts (Inter or similar), high contrast for readability, suitable for printing on A3 paper or embedding in a presentation.
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React.js, Tailwind CSS, Recharts |
| Backend | FastAPI (Python) |
| Document Processing | PyMuPDF, PaddleOCR |
| LLM | OpenAI GPT via LangChain |
| Web Intelligence | SerpAPI, BeautifulSoup |
| ML | Scikit-learn, SHAP |
| Database | PostgreSQL |
| Reports | python-docx |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Docker & Docker Compose (optional)

### Environment Variables

Create `backend/.env`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/intelli_credit
OPENAI_API_KEY=your-openai-api-key
SERPAPI_API_KEY=your-serpapi-key
```

### Option 1: Docker Compose (Recommended)

```bash
# Set API keys
export OPENAI_API_KEY=your-key
export SERPAPI_API_KEY=your-key

# Start all services
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

**Database:**
```bash
# Create PostgreSQL database
createdb intelli_credit
```

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Train ML model
python -m app.ml.train_model

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/companies` | Create a new company |
| GET | `/api/companies` | List all companies |
| POST | `/api/upload-documents` | Upload company documents |
| POST | `/api/extract-financial-data` | AI financial data extraction |
| POST | `/api/run-research-agent` | Run web research intelligence |
| POST | `/api/run-promoter-analysis` | Analyze promoter risk |
| POST | `/api/detect-early-warning` | Detect early warning signals |
| POST | `/api/calculate-risk-score` | ML credit risk scoring |
| GET | `/api/generate-cam-report` | Generate & download CAM report |

## System Workflow

1. **Document Upload** → Upload annual reports, financial statements, bank statements, GST returns
2. **Document Processing** → PyMuPDF text extraction + PaddleOCR for scanned documents
3. **AI Financial Extraction** → GPT extracts revenue, profit, assets, liabilities, ratios
4. **Financial Validation** → Cross-verify data across sources, detect discrepancies
5. **Research Intelligence** → Web search for litigation, regulatory issues, industry conditions
6. **Promoter Risk Analysis** → Background checks on directors/promoters
7. **ML Risk Scoring** → Random Forest/Gradient Boosting predicts probability of default
8. **SHAP Explainability** → Transparent explanations of risk factors
9. **Decision Engine** → Approve/Reject/Conditional with loan limits and interest rates
10. **CAM Report** → Professional Word document with complete credit analysis

## ML Model

The credit risk model uses:
- **Random Forest** classifier
- **Gradient Boosting** classifier
- **Logistic Regression** classifier

Features: revenue, profit margin, debt ratio, current ratio, GST filings, litigation flags, sector growth, promoter risk, years in business, interest coverage, revenue growth, cash flow status.

The best model is automatically selected based on AUC-ROC score.

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/routes.py          # FastAPI endpoints
│   │   ├── core/
│   │   │   ├── config.py          # Settings & environment
│   │   │   └── database.py        # PostgreSQL connection
│   │   ├── models/models.py       # SQLAlchemy ORM models
│   │   ├── schemas/schemas.py     # Pydantic schemas
│   │   ├── services/
│   │   │   ├── document_service.py    # PDF parsing + OCR
│   │   │   ├── extraction_service.py  # GPT financial extraction
│   │   │   ├── validation_service.py  # Financial validation
│   │   │   ├── research_service.py    # Web intelligence
│   │   │   ├── promoter_service.py    # Promoter risk analysis
│   │   │   ├── risk_scoring_service.py # ML + SHAP
│   │   │   └── cam_report_service.py  # CAM report generation
│   │   └── ml/
│   │       ├── generate_data.py       # Synthetic training data
│   │       └── train_model.py         # Model training
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/Layout.jsx
│   │   ├── pages/
│   │   │   ├── HomePage.jsx       # Company listing
│   │   │   ├── CompanyPage.jsx    # New company form
│   │   │   └── DashboardPage.jsx  # Analysis dashboard
│   │   ├── services/api.js        # API client
│   │   └── styles/index.css
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```
