@echo off
echo Starting Product Checker Development Environment
echo ================================================
echo.

echo [1/3] Starting Backend API on port 8080...
start "Backend API" cmd /k "cd backend && venv\Scripts\activate && python run.py"

timeout /t 3 /nobreak >nul

echo [2/3] Starting Frontend on port 3000...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo [3/3] Services starting...
echo.
echo Backend API: http://localhost:8080/docs
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit (this will NOT stop the services)
pause >nul
