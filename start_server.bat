@echo off
title Enterprise Real-Time Data Intelligence Platform
echo ========================================================
echo  Enterprise Real-Time Data Intelligence Platform
echo  Serving at: http://localhost:8000
echo  FastAPI Docs at: http://localhost:8000/docs
echo ========================================================
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
pause

