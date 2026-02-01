@echo off
echo ============================================================
echo   Face Authentication System - Backend Server
echo ============================================================
echo.
echo Activating conda environment...
call C:\Users\Rishabh\anaconda3\condabin\conda.bat activate face_auth
echo.
echo Starting backend server...
python run_backend.py
pause
