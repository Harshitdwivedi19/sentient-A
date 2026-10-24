@echo off
title Sentiment & Emotional Trajectory Studio
echo ======================================================================
echo Launching Sentiment & Emotional Trajectory Studio (Desktop Edition)...
echo ======================================================================

if exist "dist\SentimentTrajectoryStudio\SentimentTrajectoryStudio.exe" (
    echo Starting compiled binary...
    start "" "dist\SentimentTrajectoryStudio\SentimentTrajectoryStudio.exe"
    exit /b 0
)

if exist ".venv\Scripts\python.exe" (
    echo Starting from Python virtual environment...
    start "" ".venv\Scripts\pythonw.exe" "src\desktop_app.py"
    exit /b 0
)

echo Python environment not found. Please run installer first.
pause
