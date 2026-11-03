"""
FastAPI Application Entry Point.
Enterprise Real-Time Data Intelligence Platform.
"""
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure platform root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.core.config import settings
from backend.app.api.routes import router

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Enterprise-Scale Real-Time Data Intelligence Platform API powering analytical dashboards, streaming metrics, and data pipeline orchestration.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(router)


@app.get("/")
def root():
    return {
        "platform": settings.app_name,
        "version": "1.0.0",
        "status": "OPERATIONAL",
        "docs": "/docs",
        "api_endpoints": {
            "health": "/api/health",
            "kpis": "/api/kpis",
            "revenue": "/api/revenue",
            "orders": "/api/orders",
            "customers": "/api/customers",
            "products": "/api/products",
            "pipelines": "/api/pipelines",
            "streaming": "/api/streaming/status",
            "data_quality": "/api/data-quality",
            "metrics": "/api/metrics",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.host, port=settings.port, reload=True)
