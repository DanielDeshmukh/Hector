# A/B probe: answer "would nano-omni score better AND run faster than
# ultra-550b?" with a measured sample instead of a guess.
#
# Runs the exact same gold file, seed and pipeline as run_iter2.ps1 but:
#   - HECTOR_EVAL_LIVE_MODEL=nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
#     (run_gold_eval.py honours this, so the file needs no edit mid-run)
#   - --sample 40  -> ~10 min instead of ~2.3h, enough to see the direction
#   - workers 1    -> keeps CPU off the in-flight ultra run, which owns 3
#   - its own results dir, so it can never touch results\iter2
#
# Compare afterwards: citation_grounded_ratio (the gate) + gen_ms/total_ms.

$Host.UI.RawUI.WindowTitle = "A/B probe nano-omni (40q)"

$root = "D:\Vs Code\VS code\Hector"
$eval = Join-Path $root "hector\backend\eval"
$results = Join-Path $eval "results\iter2_nano_probe"
if (-not (Test-Path $results)) { New-Item -ItemType Directory -Path $results -Force | Out-Null }
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

$python = "D:\Vs Code\VS code\Hector\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "missing venv interpreter: $python" }

$env:HECTOR_EVAL_CORPUS = Join-Path $root "hector\backend\ingest_v2\output\eval_corpus.jsonl"
$env:HECTOR_EVAL_INDEX  = "hector"
$env:HECTOR_GOLD_PATH   = Join-Path $eval "gold_iteration1.jsonl"
$env:HECTOR_EVAL_RESULTS = $results
$env:HECTOR_EVAL_SEEDS  = "20260930"
$env:HECTOR_EVAL_WORKERS = "1"
$env:HECTOR_EVAL_LIVE_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"

Write-Host "model =$($env:HECTOR_EVAL_LIVE_MODEL)"
Write-Host "index =$($env:HECTOR_EVAL_INDEX)  workers=$($env:HECTOR_EVAL_WORKERS)"
Write-Host "results=$($env:HECTOR_EVAL_RESULTS)"

Set-Location $eval
$sw = [Diagnostics.Stopwatch]::StartNew()
& $python -u run_gold_eval.py all --sample 40 --sample-seed 20261013
Write-Host "python exit=$LASTEXITCODE after $($sw.Elapsed.TotalSeconds)s"
Stop-Transcript
