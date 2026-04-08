@echo off
echo Starting Product Checker Development Environment
echo ================================================
echo.

REM Check if Docker Desktop is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Desktop is not running.
    echo Please start Docker Desktop and wait for it to fully load,
    echo then run this script again.
    pause
    exit /b 1
)

echo [1/3] Starting MongoDB (Docker)...
REM Try to start existing container first
docker start ubique-mongo >nul 2>&1
if %errorlevel% neq 0 (
    REM Container doesn't exist yet, create it
    docker run -d --name ubique-mongo -p 27017:27017 -e MONGO_INITDB_DATABASE=ubique_product_checker mongo:7.0 >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create MongoDB container.
        pause
        exit /b 1
    )
    echo MongoDB container created and started.
) else (
    echo MongoDB container started.
)
echo.

timeout /t 3 /nobreak >nul

echo [2/3] Starting Backend API on port 8080...
start "Backend API" cmd /k "cd backend && conda activate product-checker && python run.py"

timeout /t 3 /nobreak >nul

echo [3/3] Starting Frontend on port 3000...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Services starting...
echo.
echo Backend API: http://localhost:8080/docs
echo Frontend:    http://localhost:3000
echo.
echo Press any key to exit (this will NOT stop the services)
pause >nul
