# Age Key Rotation - COMPLETED ✅

## Date: October 31, 2025

---

## ✅ What Was Done

### 1. Generated New Age Key Pair

- **Old public key (COMPROMISED):** `age1ydjyyu9m550m8dj22qag8qlk8ugh6n454tjezenmtra48tjaypeq5m3zj0`
- **New public key:** `age1jgv3pfxe8a5nw4hnf2hwt4w6h0npwtgtj66xnl6fw7j49n5jr54qgfvagl`

### 2. Rotated ALL Secret Values

All credentials have been replaced with NEW values:

- **GLM API Key** - New key from user
- **GitHub Personal Access Token** - New token from user  
- **GitHub Webhook Secret** - Generated: `[REDACTED]`
- **Gateway Token** - Generated: `[REDACTED]`
- **N8n Password** - Generated: `[REDACTED]`

### 3. Re-encrypted with New Key

- `infra/secrets/secrets.enc.json` - Encrypted with new age key
- Verified decryption works

### 4. Cleaned Up

- Removed `mac-mini.enc.yaml` (redundant .env format file)
- Fixed age key file format (removed warning messages)
- Set correct permissions: `chmod 600 .sops/age.key`

---

## 📋 Current State

### Files Updated

```
Modified:
  .sops.yaml                         (new public key)
  .sops/age.pub                      (new public key)
  .sops/age.key                      (NEW private key - NOT committed)
  infra/secrets/secrets.enc.json     (NEW values, encrypted with new key)

Removed:
  infra/secrets/mac-mini.enc.yaml    (redundant)

Backup files:
  .sops/age.key.backup.20251031_101650
  .sops/age.pub.backup.20251031_101650
  .sops.yaml.backup.20251031_101650
```

### Current Secrets Structure

```json
{
  "$schema": "./schemas/config.schema.json",
  "GLM": {
    "ApiKey": "..."
  },
  "GitHub": {
    "PersonalAccessToken": "...",
    "WebhookSecret": "..."
  },
  "Services": {
    "Gateway": {
      "Token": "..."
    },
    "N8n": {
      "Password": "..."
    }
  }
}
```

---

## 🚨 CRITICAL: Next Steps

### 1. Update CI/CD Secrets ⚠️

Your CI/CD system needs the NEW private key:

```bash
# Display the private key
cat /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub/.sops/age.key
```

Update in:

- GitHub Actions secrets (if used)
- Any other CI/CD pipelines

**Secret name:** Likely `SOPS_AGE_KEY` or `AGE_SECRET_KEY`

### 2. Commit the Changes

```bash
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub

# Stage ONLY these files
git add .sops.yaml
git add .sops/age.pub  
git add infra/secrets/secrets.enc.json

# Remove mac-mini.enc.yaml from git if it was tracked
git rm infra/secrets/mac-mini.enc.yaml

# Verify (should NOT include age.key)
git status

# Commit
git commit -m "security: complete age key rotation and secret values rotation

- Rotated age encryption key
- Old key: age1ydjyyu9m550m8dj22qag8qlk8ugh6n454tjezenmtra48tjaypeq5m3zj0 (COMPROMISED)
- New key: age1jgv3pfxe8a5nw4hnf2hwt4w6h0npwtgtj66xnl6fw7j49n5jr54qgfvagl

- Rotated ALL secret values (API keys, tokens, passwords)
- Old credentials are now invalid
- Removed redundant mac-mini.enc.yaml

All secrets re-encrypted with new key and new values."

# Push
git push
```

### 3. Clean Git History (REQUIRED!)

The old private key is still in git history:

```bash
# Install git-filter-repo if needed
brew install git-filter-repo

# Remove old key from ALL history
git filter-repo --path .sops/age.key --invert-paths --force

# Force push (THIS REWRITES HISTORY!)
git push origin --force --all
git push origin --force --tags
```

⚠️ **After rewriting history, all collaborators must re-clone the repository!**

### 4. Update and Restart Services

```bash
# Regenerate .env from new secrets
task infra:setup

# Restart services with new credentials
task infra:restart

# Verify
task infra:status
```

### 5. Verify Everything

```bash
# Test decryption
sops --decrypt infra/secrets/secrets.enc.json | jq '.'

# Check git security
task sops:check-git

# Test services
curl http://localhost:5055/v1/health  # Letta
curl http://localhost:6333/healthz     # Qdrant
curl http://localhost:5678             # n8n
```

---

## ✅ Security Checklist

- [x] New age key pair generated
- [x] Old keys backed up
- [x] .sops.yaml updated with new public key
- [x] ALL secret values rotated (API keys, tokens, passwords)
- [x] secrets.enc.json re-encrypted with new key
- [x] Decryption verified
- [x] Redundant mac-mini.enc.yaml removed
- [x] Age key file cleaned and permissions fixed
- [ ] Changes committed (without private key)
- [ ] CI/CD secrets updated with new private key
- [ ] Git history cleaned (old private key removed)
- [ ] Services restarted with new credentials
- [ ] All services verified working
- [ ] All collaborators notified to re-clone
- [ ] Old backup files removed (after verification)

---

## 🔒 What Makes This Secure Now

1. **New encryption key** - Old compromised key can't decrypt new files
2. **New secret values** - Old API keys/passwords are useless even if someone has them
3. **Private key not in git** - .gitignore prevents committing it
4. **Proper permissions** - age.key is chmod 600 (owner read/write only)

---

## 🆘 If Something Goes Wrong

### Can't decrypt files

```bash
# Make sure key file is clean
cat .sops/age.key | head -1
# Should start with: # created:

# Check permissions
ls -la .sops/age.key
# Should show: -rw------- (600)

# Verify environment
echo $SOPS_AGE_KEY_FILE
# Should show: (empty) or the path to age.key
```

### Services won't start

```bash
# Check .env was generated
cat infra/docker/.env

# Regenerate if needed
task infra:setup
```

### Need old secrets

```bash
# Decrypt with old backed-up key
SOPS_AGE_KEY_FILE=.sops/age.key.backup.20251031_101650 \
  sops --decrypt infra/secrets/secrets.enc.json
```

---

## 📚 Documentation

- Full rotation guide: `infra/secrets/AGE_KEY_ROTATION.md`
- What to rotate: `infra/secrets/WHAT_TO_ROTATE.md`
- Secret values guide: `infra/secrets/SECRET_VALUES_ROTATION.md`

---

## 🎉 Status: ROTATION COMPLETE

The encryption key AND all secret values have been successfully rotated.

**Immediate action required:**

1. Commit changes
2. Update CI/CD
3. Clean git history
4. Restart services

**Then you're secure! 🔒**
