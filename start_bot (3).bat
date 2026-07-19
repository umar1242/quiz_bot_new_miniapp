@echo off
chcp 65001 >nul
title Quiz Bot

echo.
echo  =========================================
echo   Quiz Bot - Setup and Start
echo  =========================================
echo.

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Docker not found!
    echo  Download and install Docker Desktop:
    echo  https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)
echo  [OK] Docker found

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Docker is not running!
    echo  Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)
echo  [OK] Docker is running

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo.
        echo  [!] .env file created from example.
        echo  Opening .env - paste your BOT_TOKEN and save the file.
        echo.
        notepad .env
        echo  Press any key after saving .env ...
        pause >nul
    ) else (
        echo  [ERROR] .env file not found!
        pause
        exit /b 1
    )
) else (
    echo  [OK] .env found
)

findstr /r /c:"BOT_TOKEN=." .env >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] BOT_TOKEN is empty in .env!
    echo  Opening .env - paste your token from @BotFather.
    notepad .env
    pause
    exit /b 1
)
echo  [OK] BOT_TOKEN is set

echo.
echo  Stopping old containers...
docker compose down

echo.
echo  Starting containers...
echo.

docker compose up -d

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Failed to start. See log above.
    pause
    exit /b 1
)

echo.
echo  =========================================
echo   Bot started successfully!
echo  =========================================
echo.
echo  Stop:      docker compose down
echo  Logs:      docker compose logs -f bot
echo  Restart:   docker compose restart bot
echo.
echo  Showing bot logs... (Ctrl+C to close logs, bot keeps running)
echo.
timeout /t 3 /nobreak >nul

docker compose logs -f bot