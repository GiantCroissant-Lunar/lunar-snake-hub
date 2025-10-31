# Encrypt secrets.json for safe storage in git
# Usage: .\encrypt-secrets.ps1

$ErrorActionPreference = "Stop"

# Verify project-scoped age key exists
$projectRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$keyFile = Join-Path $projectRoot ".sops\age.key"

if (-not (Test-Path $keyFile)) {
    Write-Error "❌ Age key not found at $keyFile. Run .\generate-age-key.ps1 first"
    exit 1
}

# No need to set env var - .sops.yaml references key file directly via key_file directive

# Paths
$secretsFile = "secrets.json"
$secretsEncFile = "secrets.enc.json"

# Check if secrets.json exists
if (-not (Test-Path $secretsFile)) {
    Write-Host "⚠️  secrets.json not found!"
    Write-Host ""
    Write-Host "Please create $secretsFile from secrets.template.json:"
    Write-Host "  1. Copy secrets.template.json to secrets.json"
    Write-Host "  2. Fill in your actual values (GLM API key, tokens, passwords)"
    Write-Host "  3. Run this script again"
    Write-Host ""
    exit 1
}

# Validate JSON
try {
    $config = Get-Content $secretsFile | ConvertFrom-Json
    Write-Host "✅ JSON validation passed"
} catch {
    Write-Error "❌ Invalid JSON in secrets.json: $_"
    exit 1
}

# Check for placeholder values
$hasPlaceholders = $false
if ($config.GLM.ApiKey -like "REPLACE_*" -or $config.GLM.ApiKey -eq "") {
    Write-Warning "⚠️  GLM.ApiKey contains placeholder or is empty"
    $hasPlaceholders = $true
}
if ($config.Services.Gateway.Token -like "*GENERATE*" -or $config.Services.Gateway.Token -eq "") {
    Write-Warning "⚠️  Services.Gateway.Token contains placeholder or is empty"
    $hasPlaceholders = $true
}
if ($config.Services.N8n.Password -like "*CHANGE*" -or $config.Services.N8n.Password -eq "CHANGE_ME_PLEASE") {
    Write-Warning "⚠️  Services.N8n.Password contains placeholder"
    $hasPlaceholders = $true
}

if ($hasPlaceholders) {
    Write-Host ""
    $continue = Read-Host "Continue with encryption anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "Aborted."
        exit 0
    }
}

# Encrypt
Write-Host ""
Write-Host "🔐 Encrypting secrets.json..."

# Change to repo root to run SOPS (where .sops.yaml is located)
$originalLocation = Get-Location
try {
    Set-Location "../.."

    # Verify .sops.yaml exists in repo root
    if (-not (Test-Path ".sops.yaml")) {
        throw ".sops.yaml not found in repo root"
    }

    # Run SOPS from repo root with relative path to secrets file
    $secretsPath = "infra\secrets\$secretsFile"
    $secretsEncPath = "infra\secrets\$secretsEncFile"

    # Encrypt and write without BOM (UTF8 without BOM)
    $encrypted = sops encrypt $secretsPath
    # Convert to absolute path for WriteAllText
    $secretsEncPathAbs = (Resolve-Path -Path $secretsEncPath -Relative:$false -ErrorAction SilentlyContinue).Path
    if (-not $secretsEncPathAbs) {
        # If file doesn't exist yet, construct absolute path
        $secretsEncPathAbs = Join-Path (Get-Location).Path $secretsEncPath
    }
    [System.IO.File]::WriteAllText($secretsEncPathAbs, $encrypted, (New-Object System.Text.UTF8Encoding $false))
} finally {
    Set-Location $originalLocation
}

Write-Host "✅ Encrypted: $secretsEncFile"
Write-Host ""
Write-Host "⚠️  IMPORTANT:"
Write-Host "1. ✅ COMMIT secrets.enc.json (encrypted, safe)"
Write-Host "2. ❌ NEVER commit secrets.json (unencrypted)"
Write-Host "3. ✅ secrets.json is already in .gitignore"
Write-Host ""
Write-Host "📝 Next steps:"
Write-Host "  git add secrets.enc.json"
Write-Host "  git commit -m 'Add encrypted secrets configuration'"
Write-Host ""
Write-Host "🐳 To generate .env for Docker:"
Write-Host "  .\json-to-env.ps1 -Encrypted"
