@echo off
setlocal
title Market Anomaly Detection Launcher

echo ==============================================================================
echo 🚀 MARKET ANOMALY DETECTION - AUTO LAUNCHER
echo ==============================================================================
echo.

:: 1. CHECK DOCKER
echo [1/5] Checking Docker status...
docker info >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: Docker is NOT running.
    echo    Please start Docker Desktop and try again.
    pause
    exit /b
)
echo    ✅ Docker is running.

:: 2. START INFRASTRUCTURE
echo [2/5] Starting Infrastructure (Kafka, Zookeeper, Jupyter)...
docker-compose up -d
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to start docker-compose services.
    pause
    exit /b
)
echo    ✅ Infrastructure up.

:: 3. INSTALL REQUIREMENTS
echo.
echo [3/5] Installing Python Dependencies inside Container...
echo    (This ensures kafka-python, streamlit, etc. are available)
timeout /t 5 >nul
docker exec jupyter pip install -r work/requirements.txt
echo    ✅ Dependencies installed.

:: 4. LAUNCH COMPONENTS
echo.
echo [4/5] Launching Systems in Parallel...

:: Launch Producer
echo    - Starting PRODUCER (Fetching Binance Data)...
start "1. PRODUCER (Binance -> Kafka)" cmd /k "docker exec -it jupyter python work/src/kafka_producer.py"

:: Wait a moment for producer to init
timeout /t 3 >nul

:: Launch Consumer
echo    - Starting CONSUMER (Spark Streaming)...
start "2. CONSUMER (Spark Analysis)" cmd /k "docker exec -it jupyter spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 work/src/spark_consumer.py"

:: Launch Dashboard
echo    - Starting DASHBOARD (Streamlit UI)...
start "3. DASHBOARD (Web UI)" cmd /k "docker exec -it jupyter streamlit run work/src/dashboard.py"

:: 5. FINISH
echo.
echo ==============================================================================
echo ✅ PIPELINE FULLY OPERATIONAL
echo ==============================================================================
echo.
echo    📊 Dashboard: http://localhost:8501
echo    👀 Kafka UI:  http://localhost:8080
echo.
echo    (Don't close the popped-up terminal windows!)
echo.
pause
