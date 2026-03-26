"""
Intelli-Credit - AI Powered Corporate Credit Decisioning Platform
Main FastAPI Application
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings, configure_langsmith
from app.core.database import engine, Base
from app.api.routes import router

# Configure LangSmith tracing early
configure_langsmith()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Intelli-Credit API",
    description="AI Powered Corporate Credit Decisioning Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware — restrict methods/headers to what the frontend actually needs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Initialize database tables and directories on startup."""
    logger.info("Starting Intelli-Credit API...")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified.")

    # Create required directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.reports_dir, exist_ok=True)
    logger.info("Upload and reports directories ready.")

    logger.info(f"Intelli-Credit API started on {settings.app_host}:{settings.app_port}")

    # Log LangSmith status
    if settings.langchain_api_key:
        logger.info(f"LangSmith tracing enabled for project: {settings.langchain_project}")
    else:
        logger.warning("LangSmith API key not set — tracing disabled.")


@app.get("/")
def root():
    return {
        "name": "Intelli-Credit API",
        "version": "1.0.0",
        "description": "AI Powered Corporate Credit Decisioning Platform",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
