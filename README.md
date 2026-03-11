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
