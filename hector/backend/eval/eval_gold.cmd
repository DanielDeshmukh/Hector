@echo off
setlocal
set PYTHONIOENCODING=utf-8
title HECTOR gold-eval %*
echo ============================================
echo  HECTOR gold-set eval - phase: %*
echo  live output ALSO tee'd to results\*.log
echo ============================================
"D:\Vs Code\VS code\Hector\.venv\Scripts\python.exe" "D:\Vs Code\VS code\Hector\hector\backend\eval\run_gold_eval.py" %*
echo.
echo [phase finished] exit=%errorlevel%
pause
