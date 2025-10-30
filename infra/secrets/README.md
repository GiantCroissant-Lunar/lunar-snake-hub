# 🔐 Secrets Management for lunar-snake-hub

This directory contains scripts for managing encrypted secrets using SOPS and age.

## 📋 Overview

**Security Model:**

- **age** provides encryption keys (public/private key pair)
- **SOPS** encrypts files using age keys
- **Encrypted files** (`.enc.*`) are safe to commit to git
- **Unencrypted files** must NEVER be committed

## 🚀 Quick Start

### Windows (First Time Setup)

```powershell
# 1. Install prerequisites (if not already installed)
winget install Mozilla.Sops
winget install FiloSottile.age

# 2. Generate age key
cd infra\secrets
.\generate-age-key.ps1

# 3. Create secrets.json from template
cp secrets.template.json secrets.json
# Edit secrets.json with your actual values:
# - GLM.ApiKey: Your GLM-4.6 JWT token
# - Services.Gateway.Token: Generate with: [System.Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
# - Services.N8n.Password: Choose a strong password
notepad secrets.json

# 4. Encrypt secrets.json
.\encrypt-secrets.ps1

# 5. Generate .env for Docker Compose
.\json-to-env.ps1 -Encrypted

# 6. Commit only the encrypted file
git add secrets.enc.json
git commit -m "Add encrypted secrets configuration"
```

### Mac Mini (First Time Setup)

The Ansible playbook will handle most of this automatically, but manual steps:

```bash
# 1. Prerequisites installed via Ansible (homebrew)
# brew install sops age

# 2. Copy your age key from Windows
# Or generate a new one: age-keygen -o ~/.config/sops/age/keys.txt

# 3. Clone the repo
cd ~/repos
git clone https://github.com/GiantCroissant-Lunar/lunar-snake-hub.git
cd lunar-snake-hub

# 4. Run Ansible playbook (sets up everything)
cd infra/ansible
ansible-playbook -i inventory/hosts.yml playbook.yml

# 5. Decrypt .env for Docker Compose
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
sops decrypt infra/docker/.env.enc > infra/docker/.env

# 6. Start services
cd ../docker
docker compose up -d
```

## 🔑 age Key Management

### Key Locations

- **Windows**: `%USERPROFILE%\.config\sops\age\keys.txt`
- **Mac/Linux**: `~/.config/sops/age/keys.txt`

### Key Structure

The `keys.txt` file contains both keys:

```
# created: 2025-10-30T12:34:56Z
# public key: age1abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567890
AGE-SECRET-KEY-1QWERTYUIOP1234567890ASDFGHJKLZXCVBNM1234567890
```

- **Line 1**: Comment with creation timestamp
- **Line 2**: Public key (for encryption - safe to share)
- **Line 3**: Private key (for decryption - KEEP SECRET)

### Sharing Keys Between Machines

**Option 1: Manual Copy (Recommended for security)**

1. On Windows, copy the entire contents of `%USERPROFILE%\.config\sops\age\keys.txt`
2. On Mac Mini, paste into `~/.config/sops/age/keys.txt`
3. Set permissions: `chmod 600 ~/.config/sops/age/keys.txt`

**Option 2: Via GitHub Secret (for CI/CD)**

1. Copy the entire `keys.txt` contents
2. Add as GitHub secret: `SOPS_AGE_KEY`
3. GitHub Actions can decrypt files using this secret

## 🔐 SOPS Configuration

The `.sops.yaml` file in the repo root defines encryption rules:

```yaml
creation_rules:
  - path_regex: infra/secrets/.*\.enc\..*$
    age: >-
      age1abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567890

  - path_regex: infra/docker/\.env\.enc$
    age: >-
      age1abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567890
```

This tells SOPS:

- Which files to encrypt (matching the regex pattern)
- Which age public key to use for encryption

## 📝 Scripts Reference

### `generate-age-key.ps1` (Windows)

Generates a new age key pair if one doesn't exist.

**Usage:**

```powershell
.\generate-age-key.ps1
```

**Output:**

- Creates `~/.config/sops/age/keys.txt`
- Displays public key for `.sops.yaml`
- Sets `$env:SOPS_AGE_KEY_FILE`

### `encrypt-secrets.ps1` (Windows)

Encrypts `secrets.json` for safe storage in git.

**Usage:**

```powershell
.\encrypt-secrets.ps1
```

**Input:** `secrets.json` (unencrypted, from `secrets.template.json`)
**Output:** `secrets.enc.json` (encrypted, safe to commit)

**Features:**

- Validates JSON syntax
- Checks for placeholder values
- Prompts before encrypting if placeholders detected

### `decrypt-secrets.ps1` (Windows)

Decrypts `secrets.enc.json` for local editing.

**Usage:**

```powershell
.\decrypt-secrets.ps1
```

**Input:** `secrets.enc.json` (from git)
**Output:** `secrets.json` (unencrypted, DO NOT COMMIT)

### `json-to-env.ps1` (Windows)

Converts `secrets.json` (or `secrets.enc.json`) to Docker Compose `.env` file.

**Usage:**

```powershell
# From unencrypted secrets.json
.\json-to-env.ps1

# From encrypted secrets.enc.json (decrypts automatically)
.\json-to-env.ps1 -Encrypted
```

**Output:** `../docker/.env` (for Docker Compose)

**Note:** Docker Compose doesn't support JSON directly, so we convert JSON → .env at runtime.

## 🔒 Security Best Practices

### ✅ DO

- ✅ Commit `.env.enc` (encrypted files)
- ✅ Keep `keys.txt` private (600 permissions)
- ✅ Use different keys for different environments
- ✅ Rotate keys periodically (every 90 days)
- ✅ Backup your private key securely

### ❌ DON'T

- ❌ Never commit `.env` (unencrypted files)
- ❌ Never share private keys in chat/email
- ❌ Never commit `keys.txt` to git
- ❌ Never store keys in cloud drives without encryption

## 🔄 Rotating Keys

When rotating keys:

1. Generate a new age key
2. Re-encrypt all secrets with the new key
3. Update `.sops.yaml` with new public key
4. Update GitHub secret `SOPS_AGE_KEY` with new private key
5. Distribute new private key to team members securely
6. Revoke old key

## 🆘 Troubleshooting

### Error: "age key not found"

**Solution:**

```powershell
# Windows
.\generate-age-key.ps1

# Mac
age-keygen -o ~/.config/sops/age/keys.txt
```

### Error: "failed to decrypt"

**Possible causes:**

- Using wrong private key
- `.env.enc` was encrypted with a different public key
- `SOPS_AGE_KEY_FILE` environment variable not set

**Solution:**

```powershell
# Windows
$env:SOPS_AGE_KEY_FILE = "$env:USERPROFILE\.config\sops\age\keys.txt"

# Mac/Linux
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
```

### Error: "sops: command not found"

**Solution:**

```powershell
# Windows
winget install Mozilla.Sops

# Mac
brew install sops
```

## 📚 References

- **SOPS**: <https://github.com/getsops/sops>
- **age**: <https://github.com/FiloSottile/age>
- **age Key Format**: <https://github.com/C2SP/C2SP/blob/main/age.md>

---

**Security Note:** This documentation is safe to commit to git. It contains no secrets, only instructions for managing secrets.
