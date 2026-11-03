"""
FastAPI Application Entry Point.
Enterprise Real-Time Data Intelligence Platform.
Serves both the REST API endpoints and the unified React + TypeScript Dashboard.
"""
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router (MUST be included before mounting root static files)
app.include_router(router)

# Mount compiled React frontend if present
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
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
