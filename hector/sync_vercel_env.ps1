$ErrorActionPreference = "Continue"
Set-Location "D:\Vs Code\VS code\Hector\hector"
$rootEnv = "D:\Vs Code\VS code\Hector\.env"
$vars = @(
    "PINECONE_API_KEY", "HECTOR_API_KEY", "HECTOR_JWT_SECRET",
    "GROQ_API_KEY", "NIM_API_KEY", "NIM_BASE_URL",
    "NVIDIA_API_KEY", "GEMINI_API_KEY",
    "NEXT_PUBLIC_HECTOR_API_KEY", "NEXT_PUBLIC_HECTOR_API_URL"
)
$lines = Get-Content -LiteralPath $rootEnv
foreach ($name in $vars) {
    $line = $lines | Where-Object { $_ -match "^$name=" } | Select-Object -First 1
    if (-not $line) { Write-Output "$name : MISSING in .env - skipped"; continue }
    $value = ($line -split '=', 2)[1]
    # remove existing entry (may not exist)
    & vercel env rm $name production -y 2>&1 | Out-Null
    # pipe value via stdin - never printed to console
    $value | & vercel env add $name production 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Output "$name : synced" }
    else { Write-Output "$name : FAILED exit=$LASTEXITCODE" }
}
