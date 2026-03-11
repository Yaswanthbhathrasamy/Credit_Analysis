# Intelli-Credit AI Platform — Project Guidelines

## Overview
AI-powered Corporate Credit Decisioning Engine for Indian mid-sized corporates. Automates preparation of Credit Appraisal Memos (CAM) by ingesting multi-source data, performing web-scale research, and producing ML-based lending recommendations.

## Architecture
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL (Docker). Entry point: `backend/main.py`
- **Frontend**: React 18 + Vite + Tailwind CSS + Recharts. Entry point: `frontend/src/App.jsx`
- **AI/ML**: OpenAI GPT-4o-mini via LangChain, scikit-learn ensemble (RF/LR/GBT) with SHAP explainability
- **Document Processing**: PyMuPDF (fitz) + PaddleOCR (Hindi + English)
- **Web Research**: SerpAPI + BeautifulSoup
- **Reports**: python-docx for CAM generation

## Three Pillars
1. **Data Ingestor** — `document_service.py`, `extraction_service.py`, `validation_service.py`
2. **Research Agent** — `research_service.py`, `promoter_service.py`
3. **Recommendation Engine** — `risk_scoring_service.py`, `cam_report_service.py`

## Indian Context (Critical)
- All financial amounts in ₹ (INR), often expressed in lakhs/crores
- Fiscal year: April–March (e.g., FY 2024-25)
- GST specifics: GSTR-1, GSTR-2A, GSTR-2B, GSTR-3B — each has distinct meaning
- CIBIL Commercial reports (score + rank 1-10)
- RBI IRAC norms for NPA classification: SMA-0 (1-30 DPD), SMA-1 (31-60), SMA-2 (61-90)
- Ind-AS accounting standards, not US GAAP
- Regulatory bodies: RBI, SEBI, MCA/ROC, NCLT, DGGI, NGT, SFIO

## Build & Run
```bash
docker-compose up --build        # Full stack
cd backend && pip install -r requirements.txt  # Backend only
cd frontend && npm install && npm run dev      # Frontend only
```

## Evaluation Criteria
1. **Extraction Accuracy** — messy, scanned Indian-context PDFs
2. **Research Depth** — local news, regulatory filings beyond provided files
3. **Explainability** — AI must "walk the judge through" its logic
4. **Indian Context Sensitivity** — GSTR-2A vs 3B, CIBIL, RBI norms
