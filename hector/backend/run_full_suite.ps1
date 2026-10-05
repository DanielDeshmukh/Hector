$ErrorActionPreference = "Continue"
$wd = "D:\Vs Code\VS code\Hector\hector\backend"
$log = Join-Path $wd "tests\full_suite5.log"
$exit = Join-Path $wd "tests\full_suite5.exit.txt"
Remove-Item $log, $exit -ErrorAction SilentlyContinue
Set-Location $wd
& "D:\Vs Code\VS code\Hector\.venv\Scripts\python.exe" -u -m pytest tests eval `
    --ignore=tests/test_act_coverage.py `
    --ignore=tests/test_pinecone_query.py `
    --ignore=tests/test_quick_semantic.py `
    -v --tb=short 2>&1 | Tee-Object -FilePath $log
"EXITCODE=$LASTEXITCODE FINISHED=$(Get-Date -Format o)" | Tee-Object -FilePath $exit
