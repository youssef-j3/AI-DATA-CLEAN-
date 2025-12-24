@echo off
echo ==========================================
echo Starting Transport Analysis System
echo ==========================================
echo.

echo Starting Backend (FastAPI)...
echo.
cd /d C:\Users\mahmo\OneDrive\Desktop\AI_Project\AI_Project
start "Backend" cmd /k "python scripts/rebuild_outputs.py && uvicorn src.transport_analysis.api:app --reload --host 0.0.0.0 --port 8000"

echo.
echo Waiting 5 seconds...
timeout /t 5

echo Starting Frontend (Angular)...
echo.
cd /d C:\Users\mahmo\OneDrive\Desktop\AI_Project\AI_Project\frontend
start "Frontend" cmd /k npm start

echo.
echo ==========================================
echo System Starting:
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:4200
echo ==========================================
