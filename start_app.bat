@echo off
echo ============================================================
echo   Face Authentication System - Desktop App
echo ============================================================
echo.
echo Activating conda environment...
call C:\Users\Rishabh\anaconda3\condabin\conda.bat activate face_auth
echo.
echo Starting desktop application...
echo Make sure the backend server is running first!
echo.
python run_app.py
pause
