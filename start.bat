@echo off
echo ============================================
echo Ubique Product Checker - Quick Start
echo ============================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [1/5] Docker found!
echo.

REM Check if .env exists
if not exist .env (
    echo [2/5] Creating .env file from template...
    copy .env.example .env >nul
    echo .env file created successfully!
) else (
    echo [2/5] .env file already exists
)
echo.

REM Stop any existing containers
echo [3/5] Stopping existing containers...
docker-compose down >nul 2>&1
echo.

REM Start services
echo [4/5] Starting services (this may take a few minutes)...
echo This includes: MongoDB, Backend API, and Frontend
docker-compose up -d

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start services
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo [5/5] Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo.
echo ============================================
echo SUCCESS! Application is starting...
echo ============================================
echo.
echo Services:
echo   - Frontend:  http://localhost:3000
echo   - Backend:   http://localhost:8000
echo   - API Docs:  http://localhost:8000/docs
echo.
echo Please wait 1-2 minutes for all services to fully start.
echo Then open http://localhost:3000 in your browser.
echo.
echo To stop the application, run: docker-compose down
echo To view logs, run: docker-compose logs -f
echo.
pause
