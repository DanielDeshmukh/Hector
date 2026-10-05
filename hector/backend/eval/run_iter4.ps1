# Launcher for the full 200-question re-measure (results\iter4).
#
# Why this file exists: run_gold_eval.py reads PINECONE_API_KEY straight from
# os.environ (it does NOT load .env itself), and the API key value must never
# appear on a command line or in a log. So the .env is parsed here at runtime
# and exported into this process before python starts - no key is embedded in
# this script or in the Start-Process invocation.
#
# Scope: IPC + BNS corpus (945 records) on index `hector`. Same gold file and
# same sample size as iter1/iter2, so the three gate numbers are directly
# comparable to both baselines.
#
# What changed since iter2 (measured before this run was launched):
#
#   retrieval - section_recall@10 0.9545 -> 1.0000, measured 198/198 on this
#     exact sample by sweep_recall.py before spending any generation tokens.
#     Three root causes, all fixed in this build:
#       1. query_expander.expand() appended 30-50 tokens of OTHER sections to
#          queries that already cite one ("Section 275 IPC" also became
#          "section 106 ... section 115"), pushing the target out of dense
#          top-30 entirely. Section-citing queries now pass through unchanged.
#       2. the same table injected cross-act citations ("murder" -> "section
#          101 bns"), which _parse_query read as a two-act comparison query.
#          Synonyms may no longer introduce an act the question never named.
#       3. hybrid_retriever._apply_same_act_floor() reserves 5 of the top-10
#          slots for the named act. Promotion only. Needed because paired
#          provisions (BNS 103 vs IPC 300) legitimately outscore each other
#          and a pure cross-encoder ranking filled top-10 with 100% BNS for an
#          IPC question.
#     Also fixed: _infer_act() now maps "The Indian Penal Code, 1860" -> "IPC"
#     instead of uppercasing it, so the pre-existing act-match boost fires.
#
#   generation - prompt SECTION-NUMBER RULE (rule 1) + verifier Round 6
#     abstention markers. iter3 60q measured citation_grounded_ratio 1.0000
#     and fabricated_free_rate 1.0000 with these live.
#
#   gate math - denominator is n_assertive (authorized 2026-10-03); thresholds
#     are unchanged (0.98 / 0.99 / 0.991) and appear in NO code.
#
# Model: nvidia/nemotron-3-ultra-550b-a55b (the default; the nano A/B showed
# swapping models helps neither the gate nor latency at eval scale).

$Host.UI.RawUI.WindowTitle = "GOLD EVAL iter4 (IPC+BNS, all fixes)"

$root = "D:\Vs Code\VS code\Hector"
$eval = Join-Path $root "hector\backend\eval"
$results = Join-Path $eval "results\iter4"
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
# D:\Vs Code\themis\venv\Scripts\python.exe (a different project's venv),
# which dies on the first import and writes nothing.
$python = "D:\Vs Code\VS code\Hector\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "missing venv interpreter: $python" }
Write-Host "python = $python"
Write-Host "cwd    = $eval"

$env:HECTOR_EVAL_CORPUS = Join-Path $root "hector\backend\ingest_v2\output\eval_corpus.jsonl"
$env:HECTOR_EVAL_INDEX  = "hector"
$env:HECTOR_GOLD_PATH   = Join-Path $eval "gold_iteration1.jsonl"
$env:HECTOR_EVAL_RESULTS = $results
$env:HECTOR_EVAL_SEEDS  = "20260930"   # 1 seed, matching iter1/iter2
$env:HECTOR_EVAL_WORKERS = "3"         # measured best: p50 5012ms vs 8 workers 10732ms

Write-Host "index=$($env:HECTOR_EVAL_INDEX) corpus=$($env:HECTOR_EVAL_CORPUS)"
Write-Host "gold=$($env:HECTOR_GOLD_PATH) results=$($env:HECTOR_EVAL_RESULTS)"
Write-Host "seeds=$($env:HECTOR_EVAL_SEEDS) workers=$($env:HECTOR_EVAL_WORKERS)"

Set-Location $eval
$sw = [Diagnostics.Stopwatch]::StartNew()
& $python -u run_gold_eval.py all --sample 200 --sample-seed 20261013
Write-Host "python exit=$LASTEXITCODE after $($sw.Elapsed.TotalSeconds)s"
Stop-Transcript
