@echo off
echo ==================================================
echo Starting MindSense (Multimodal Emotion-Aware System)
echo ==================================================

echo.
echo [1/2] Setting up Backend...
cd backend

IF NOT EXIST "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -r requirements.txt

echo Initializing local database...
set FLASK_APP=run.py
set FLASK_ENV=development
:: We skip migration for first run if the db doesn't exist to prevent errors, we just let SQLAlchemy create it on first request, or we can use db.create_all()
:: For the scaffold, it's safer to just run it.

echo Starting Flask Server in a new window...
start "MindSense Backend" cmd /c "call venv\Scripts\activate.bat && python run.py"

cd ..

echo.
echo [2/2] Setting up Frontend...
cd frontend

IF NOT EXIST "node_modules" (
    echo Installing NPM dependencies...
    npm install
)

echo Starting Vite React Server in a new window...
start "MindSense Frontend" cmd /c "npm run dev"

echo.
echo ==================================================
echo Success! Both servers are starting up.
echo - The backend terminal window should show it running on http://localhost:5000
echo - The frontend terminal window should show it running on http://localhost:5173
echo.
echo You can now open your browser and navigate to:
echo http://localhost:5173
echo ==================================================
pause
