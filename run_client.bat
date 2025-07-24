@echo off
echo Starting MCP Scout Client with vLLM...
echo.

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not available in PATH
    echo Please ensure Python is installed and added to PATH
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import scout.client" >nul 2>&1
if errorlevel 1 (
    echo Error: Required packages not found
    echo Please run: pip install -e .
    pause
    exit /b 1
)

REM Run the client
echo Starting MCP Scout Client...
echo.
python -m scout.client

echo.
echo MCP Scout Client has exited.
pause
