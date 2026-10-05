# Iter3 verification run: 60 questions with all three grounding fixes live.
#
#   1. gate denominator = n_assertive (authorized 2026-10-03, threshold 0.99
#      unchanged) - stops honest "the sources do not contain Section X"
#      abstentions being counted against the answer
#   2. generator prompt rule 7 - no section number unless its text is in the
#      retrieved sources (kills the 28 out-of-context cross-references)
#   3. verifier Round 6 markers - "(not in sources)" / "but not Section N"
#      classify as negated instead of assertive-and-ungrounded
#
# Model is ultra-550b (the default in run_gold_eval.py); the nano A/B showed
# swapping models neither helps the gate nor speeds anything up.
#
# Why 60 first: direction check in ~12 min and far less egress from the fresh
# 1GB quota. The sample seed draws a DIFFERENT subset than the 200, so this is
# directional, not a paired comparison - commit to a full 200 only if it
# clears 0.99.

$Host.UI.RawUI.WindowTitle = "GOLD EVAL iter3 fix-check (60q)"

$root = "D:\Vs Code\VS code\Hector"
$eval = Join-Path $root "hector\backend\eval"
$results = Join-Path $eval "results\iter3_fix60"
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
$env:HECTOR_EVAL_WORKERS = "2"

Write-Host "model =nvidia/nemotron-3-ultra-550b-a55b (default)"
Write-Host "fixes =denominator n_assertive + prompt rule 7 + Round 6 markers"
Write-Host "index =$($env:HECTOR_EVAL_INDEX)  workers=$($env:HECTOR_EVAL_WORKERS)"
Write-Host "results=$($env:HECTOR_EVAL_RESULTS)"

Set-Location $eval
$sw = [Diagnostics.Stopwatch]::StartNew()
& $python -u run_gold_eval.py all --sample 60 --sample-seed 20261013
Write-Host "python exit=$LASTEXITCODE after $($sw.Elapsed.TotalSeconds)s"
Stop-Transcript
