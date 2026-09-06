@echo off
setlocal
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 (
        echo Python 3.11+ is required.
        pause
        exit /b 1
    )
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

echo.
echo === Building PriceMonitor ===
pyinstaller --noconfirm --clean --windowed --name PriceMonitor ^
 --icon resources\app.ico ^
 --collect-all tzdata ^
 main.py
if errorlevel 1 goto :fail

echo.
echo === Building MarketCollector ===
pyinstaller --noconfirm --clean --onefile --console --name MarketCollector ^
 --collect-all playwright ^
 collector\market_collector_v14.py
if errorlevel 1 goto :fail

echo.
echo === Copying runtime files ===
if not exist "dist\PriceMonitor\resources" mkdir "dist\PriceMonitor\resources"
if not exist "dist\PriceMonitor\data" mkdir "dist\PriceMonitor\data"
if not exist "dist\PriceMonitor\collector" mkdir "dist\PriceMonitor\collector"
if not exist "dist\PriceMonitor\logs" mkdir "dist\PriceMonitor\logs"
if not exist "dist\PriceMonitor\backups" mkdir "dist\PriceMonitor\backups"

xcopy /E /I /Y "resources\*" "dist\PriceMonitor\resources\" >nul
copy /Y "data\prices.db" "dist\PriceMonitor\data\prices.db" >nul
copy /Y "dist\MarketCollector.exe" "dist\PriceMonitor\collector\MarketCollector.exe" >nul

powershell -NoProfile -Command "$s=Get-Content 'settings.json' -Raw | ConvertFrom-Json; $s.collector_path='collector/MarketCollector.exe'; $json=$s | ConvertTo-Json -Depth 10; [System.IO.File]::WriteAllText((Join-Path (Get-Location) 'dist/PriceMonitor/settings.json'), $json, (New-Object System.Text.UTF8Encoding($false)))"

echo.
echo Build completed successfully.
echo Final folder: dist\PriceMonitor\
echo Run: dist\PriceMonitor\PriceMonitor.exe
pause
exit /b 0

:fail
echo.
echo BUILD FAILED.
pause
exit /b 1
