# Launcher for IPC re-run A2 - IPC gold, 200-question sample (results\ipc2).
#
# Same machinery as run_bns1.ps1 (see that file for the .env-in-process rule
# and the -u + Tee progress rule). Differences: IPC gold (gold_iteration1,
# 1185 rows) instead of BNS, results go to results\ipc2.
#
# Why A2 exists: iter4 measured IPC gates green BEFORE today's retriever
# changes (citation injection, injection floor, injection-only blend,
# raw_query attribution). sweep_ipc3.log measured retrieval at 198/198 =
# 1.0000 on the new code; A2 is the judged pass (generation + grounded +
# fabricated gates) for IPC on the same code the API will ship.
#
# Thresholds unchanged (0.98 / 0.99 / 0.991), live in report_gates.py only.

try { $Host.UI.RawUI.WindowTitle = "GOLD EVAL run A2 (IPC judged, 200q)" } catch { }

$root = "D:\Vs Code\VS code\Hector"
$eval = Join-Path $root "hector\backend\eval"
$results = Join-Path $eval "results\ipc2"
if (-not (Test-Path $results)) { New-Item -ItemType Directory -Path $results -Force | Out-Null }

$envFile = Join-Path $root ".env"
if (-not (Test-Path $envFile)) { throw "missing $envFile" }
foreach ($line in Get-Content $envFile) {
    $s = $line.Trim()
    if (-not $s -or $s.StartsWith("#") -or -not $s.Contains("=")) { continue }
    $i = $s.IndexOf("=")
    $k = $s.Substring(0, $i).Trim()
    $v = $s.Substring($i + 1).Trim().Trim('"').Trim("'")
    if ($k) { Set-Item -Path "env:$k" -Value $v }
}
if (-not $env:PINECONE_API_KEY) { throw "PINECONE_API_KEY missing from .env" }

$python = "D:\Vs Code\VS code\Hector\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "missing venv interpreter: $python" }
Write-Host "python = $python"

$env:HECTOR_EVAL_CORPUS = Join-Path $root "hector\backend\ingest_v2\output\eval_corpus.jsonl"
$env:HECTOR_EVAL_INDEX  = "hector"
$env:HECTOR_GOLD_PATH   = Join-Path $eval "gold_iteration1.jsonl"
$env:HECTOR_EVAL_RESULTS = $results
$env:HECTOR_EVAL_SEEDS  = "20260930"
$env:HECTOR_EVAL_WORKERS = "3"
$env:PYTHONUNBUFFERED   = "1"

Write-Host "index=$($env:HECTOR_EVAL_INDEX) gold=$($env:HECTOR_GOLD_PATH)"
Write-Host "results=$($env:HECTOR_EVAL_RESULTS) seeds=$($env:HECTOR_EVAL_SEEDS)"

Set-Location $eval
$runLog = Join-Path $results "run.log"
$sw = [Diagnostics.Stopwatch]::StartNew()
& $python -u run_gold_eval.py all --sample 200 --sample-seed 20261013 2>&1 |
    Tee-Object -FilePath $runLog
Write-Host "python exit=$LASTEXITCODE after $([math]::Round($sw.Elapsed.TotalSeconds))s"
