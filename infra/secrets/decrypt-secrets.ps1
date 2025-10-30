# Decrypt secrets.enc.json for local use
# Usage: .\decrypt-secrets.ps1

$ErrorActionPreference = "Stop"

# Ensure SOPS_AGE_KEY_FILE is set
$keyFile = Join-Path $env:USERPROFILE ".config\sops\age\keys.txt"
if (-not (Test-Path $keyFile)) {
    Write-Error "❌ Age key not found. You need the private key to decrypt."
    exit 1
}

$env:SOPS_AGE_KEY_FILE = $keyFile

# Paths
$secretsEncFile = "secrets.enc.json"
$secretsFile = "secrets.json"

# Check if secrets.enc.json exists
if (-not (Test-Path $secretsEncFile)) {
    Write-Error "❌ Encrypted secrets.enc.json not found at: $secretsEncFile"
    exit 1
}

# Decrypt
Write-Host "🔓 Decrypting secrets.enc.json..."

# Change to repo root to run SOPS (where .sops.yaml is located)
$originalLocation = Get-Location
try {
    Set-Location "../.."

    # Verify .sops.yaml exists in repo root
    if (-not (Test-Path ".sops.yaml")) {
        throw ".sops.yaml not found in repo root"
    }

    # Run SOPS from repo root with relative path
    $secretsEncPath = "infra\secrets\$secretsEncFile"
    $secretsPath = "infra\secrets\$secretsFile"

    sops decrypt $secretsEncPath | Out-File -Encoding utf8 $secretsPath
} finally {
    Set-Location $originalLocation
}

Write-Host "✅ Decrypted: $secretsFile"
Write-Host ""
Write-Host "⚠️  Remember: secrets.json is gitignored (do not commit it)"
Write-Host ""
Write-Host "🐳 To generate .env for Docker:"
Write-Host "  .\json-to-env.ps1"
