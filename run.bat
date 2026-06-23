@echo off
echo Starting FastAPI Backend...
start cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000"

echo Starting Vite Frontend...
cd frontend
start cmd /k "npm run dev"
