# Launcher for judged run C - compare gold, full 102-question set (results\cmp1).
#
# Same machinery as run_bns1.ps1 (see that file for the .env-in-process rule
# and the -u + Tee progress rule). Differences: compare gold has 102 rows, so
# --sample 200 draws the WHOLE set (load_gold only samples when
# GOLD_SAMPLE < len(gold)); results go to results\cmp1.
#
# Phase param (2026-10-06): "run" stops after generation (gates only:
# report_gates.py needs raw_runs only); default "all" also judges + metrics.
#
# Why run C exists: the compare retrieval sweep (sweep_cmp4.log) measured
# 162/162 = 1.0000 on today's fixed code, but the judged gates (generation +
# grounded + fabricated) have not been measured on this code since the fix.
#
# Gold: gold_compare_iteration1.jsonl (102 rows, seed 20261013).
# Thresholds unchanged (0.98 / 0.99 / 0.991), live in report_gates.py only.

param([string]$Phase = "all")

try { $Host.UI.RawUI.WindowTitle = "GOLD EVAL run C (compare judged, 102q)" } catch { }

$root = "D:\Vs Code\VS code\Hector"
$eval = Join-Path $root "hector\backend\eval"
$results = Join-Path $eval "results\cmp1"
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
$env:HECTOR_GOLD_PATH   = Join-Path $eval "gold_compare_iteration1.jsonl"
$env:HECTOR_EVAL_RESULTS = $results
$env:HECTOR_EVAL_SEEDS  = "20260930"
$env:HECTOR_EVAL_WORKERS = "3"
$env:PYTHONUNBUFFERED   = "1"

Write-Host "index=$($env:HECTOR_EVAL_INDEX) gold=$($env:HECTOR_GOLD_PATH)"
Write-Host "results=$($env:HECTOR_EVAL_RESULTS) seeds=$($env:HECTOR_EVAL_SEEDS)"

Set-Location $eval
$runLog = Join-Path $results "run.log"
$sw = [Diagnostics.Stopwatch]::StartNew()
# No PS-side Tee here: run_gold_eval's setup_phase_log already tees stdout+stderr
# into run.log itself, and a second writer on the same file races its handle
# (fails intermittently with "being used by another process" under WMI).
& $python -u run_gold_eval.py $Phase --sample 200 --sample-seed 20261013
Write-Host "python exit=$LASTEXITCODE after $([math]::Round($sw.Elapsed.TotalSeconds))s"
