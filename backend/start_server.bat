@echo off
echo Starting Tour Booking API Server...
echo.

REM Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please create it first:
    echo python -m venv .venv
    echo .venv\Scripts\activate
    echo pip install -r requirements.txt
    pause
    exit /b 1
)

REM Start the FastAPI server
echo Starting FastAPI server on http://localhost:8000
echo.
echo Available endpoints:
echo - API Documentation: http://localhost:8000/docs
echo - Alternative API Docs: http://localhost:8000/redoc
echo - Health Check: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
