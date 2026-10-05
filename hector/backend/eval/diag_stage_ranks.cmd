@echo off
setlocal
set PYTHONIOENCODING=utf-8
title HECTOR round4 stage diagnosis
echo ============================================
echo  Round 4 - stage ranks for always-refused
echo  output tee'd to results\diag_stage_ranks.log
echo ============================================
powershell -NoProfile -Command "& 'D:\Vs Code\VS code\Hector\.venv\Scripts\python.exe' -u 'D:\Vs Code\VS code\Hector\hector\backend\eval\diag_stage_ranks.py' 2>&1 | Tee-Object -FilePath 'D:\Vs Code\VS code\Hector\hector\backend\eval\results\diag_stage_ranks.log'"
echo.
echo [diag finished] exit=%errorlevel%
pause
