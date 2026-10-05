# Launcher for the phase-2 gold re-measure (results\iter2).
#
# Why this file exists: run_gold_eval.py reads PINECONE_API_KEY straight from
# os.environ (it does NOT load .env itself), and the API key value must never
# appear on a command line or in a log. So the .env is parsed here at runtime
# and exported into this process before python starts - no key is embedded in
# this script or in the Start-Process invocation.
#
# Scope of this run: IPC + BNS corpus (945 records) on index `hector`.
# Same gold file and same sample size as iter1, so the three gate numbers are
# directly comparable to the iter1 baseline.

$Host.UI.RawUI.WindowTitle = "GOLD EVAL iter2 (IPC+BNS)"

$root = "D:\Vs Code\VS code\Hector"
$eval = Join-Path $root "hector\backend\eval"
$results = Join-Path $eval "results\iter2"
if (-not (Test-Path $results)) { New-Item -ItemType Directory -Path $results -Force | Out-Null }
# The launcher window is invisible from the agent, so everything it prints is
# also captured here to make failures readable after the fact.
Start-Transcript -Path (Join-Path $results "launcher.log") -Force

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

# Pin the interpreter: bare `python` on this machine resolves to
# D:\Vs Code\themis\venv\Scripts\python.exe (a different project's venv), which
# dies on the first import and writes nothing.
$python = "D:\Vs Code\VS code\Hector\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "missing venv interpreter: $python" }
Write-Host "python = $python"
Write-Host "cwd    = $eval"

$env:HECTOR_EVAL_CORPUS = Join-Path $root "hector\backend\ingest_v2\output\eval_corpus.jsonl"
$env:HECTOR_EVAL_INDEX  = "hector"
$env:HECTOR_GOLD_PATH   = Join-Path $eval "gold_iteration1.jsonl"
$env:HECTOR_EVAL_RESULTS = $results
$env:HECTOR_EVAL_SEEDS  = "20260930"   # 1 seed, matching iter1
$env:HECTOR_EVAL_WORKERS = "3"         # measured best: p50 5012ms vs 8 workers 10732ms

Write-Host "index=$($env:HECTOR_EVAL_INDEX) corpus=$($env:HECTOR_EVAL_CORPUS)"
Write-Host "gold=$($env:HECTOR_GOLD_PATH) results=$($env:HECTOR_EVAL_RESULTS)"
Write-Host "seeds=$($env:HECTOR_EVAL_SEEDS) workers=$($env:HECTOR_EVAL_WORKERS)"

Set-Location $eval
$sw = [Diagnostics.Stopwatch]::StartNew()
& $python -u run_gold_eval.py all --sample 200 --sample-seed 20261013
Write-Host "python exit=$LASTEXITCODE after $($sw.Elapsed.TotalSeconds)s"
Stop-Transcript
