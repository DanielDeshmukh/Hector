# Launcher for judged run B - BNS gold, 200-question sample (results\bns1).
#
# Same machinery as run_iter4.ps1: run_gold_eval.py reads PINECONE_API_KEY
# straight from os.environ (it does NOT load .env itself) and key values must
# never appear on a command line or in a log, so .env is parsed here at
# runtime into this process before python starts.
#
# Why run B exists: iter4 measured IPC gates green BEFORE today's retriever
# changes (citation injection, injection floor, injection-only blend,
# raw_query attribution). This afternoon's sweeps measured all three
# retrieval sets at 1.0000 on the new code (BNS 193/193, IPC 198/198,
# compare 162/162); run B is the judged pass (generation + grounded +
# fabricated gates) for BNS on the same code the API will ship.
#
# Gold: gold_bns_iteration1.jsonl (740 rows = 358 sections x2 phrasings +
# 24 carried false-premise rows, seed 20261013). Sample 200 with seed
# 20261013 matches the gate sampling convention used by iter1/iter2/iter4.
#
# Thresholds are unchanged (0.98 / 0.99 / 0.991), live in report_gates.py as
# documented references only, and appear in NO code in this repo.

$Host.UI.RawUI.WindowTitle = "GOLD EVAL run B (BNS judged, 200q)"

$root = "D:\Vs Code\VS code\Hector"
$eval = Join-Path $root "hector\backend\eval"
$results = Join-Path $eval "results\bns1"
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
$env:HECTOR_GOLD_PATH   = Join-Path $eval "gold_bns_iteration1.jsonl"
$env:HECTOR_EVAL_RESULTS = $results
$env:HECTOR_EVAL_SEEDS  = "20260930"
$env:HECTOR_EVAL_WORKERS = "3"
$env:PYTHONUNBUFFERED   = "1"

Write-Host "index=$($env:HECTOR_EVAL_INDEX) gold=$($env:HECTOR_GOLD_PATH)"
Write-Host "results=$($env:HECTOR_EVAL_RESULTS) seeds=$($env:HECTOR_EVAL_SEEDS)"

Set-Location $eval
$runLog = Join-Path $results "run.log"
$sw = [Diagnostics.Stopwatch]::StartNew()
# -u + Tee => progress lines land in run.log as they are produced (the
# block-buffered redirect problem that made sweep logs look frozen).
& $python -u run_gold_eval.py all --sample 200 --sample-seed 20261013 2>&1 |
    Tee-Object -FilePath $runLog
Write-Host "python exit=$LASTEXITCODE after $([math]::Round($sw.Elapsed.TotalSeconds))s"
