# Secret Values Rotation Guide

## 🚨 CRITICAL: Why Rotate Secret Values?

The age encryption key was compromised, which means anyone with access to the old key can:

1. ✅ Decrypt the old encrypted files (even if you re-encrypt them)
2. ✅ Read all the passwords, API keys, and tokens
3. ✅ Use those credentials to access your services

**Re-encrypting with a new key is NOT enough!** You must rotate the actual secret values.

## 📋 Secrets That Need Rotation

Based on `infra/secrets/secrets.enc.json`:

### 1. GLM (Language Model API)

- **ApiKey** - OpenAI/GLM API Key
- **Action**: Generate new API key from provider dashboard
- **Where**: OpenAI platform or GLM provider

### 2. GitHub

- **Token** - GitHub Personal Access Token or App token
- **Action**: Revoke old token, generate new one
- **Where**: <https://github.com/settings/tokens>

### 3. Services

Various service credentials (n8n, Gateway, etc.)

- **Action**: Generate new passwords/tokens for each service

---

## 🛠️ Step-by-Step Rotation Process

### Step 1: Decrypt Current Secrets (Using OLD Key)

```bash
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub

# View current secrets structure (values redacted)
SOPS_AGE_KEY_FILE=.sops/age.key.backup.20251031_101650 \
  sops decrypt infra/secrets/secrets.enc.json | \
  jq 'walk(if type == "string" and (. | length > 10) then "***" else . end)'

# Or edit to see full values (if you need to know what to rotate)
SOPS_AGE_KEY_FILE=.sops/age.key.backup.20251031_101650 \
  sops infra/secrets/secrets.enc.json
```

### Step 2: Generate New Secrets

For each secret, generate a NEW value:

#### GLM API Key

1. Go to your LLM provider dashboard (OpenAI, etc.)
2. Revoke the old API key
3. Generate a new API key
4. Copy the new key

#### GitHub Token

1. Go to: <https://github.com/settings/tokens>
2. Find and delete the old token
3. Generate new token with same scopes
4. Copy the new token

#### Service Passwords/Tokens

Generate secure random passwords:

```bash
# Generate a secure password
openssl rand -base64 32

# Or use a password manager
```

### Step 3: Create New Secrets File

Option A - Edit directly with SOPS (using NEW key):

```bash
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub

# This will use the NEW age key (.sops/age.key)
sops infra/secrets/secrets.enc.json
```

Option B - Decrypt old, modify, encrypt with new:

```bash
# Decrypt with OLD key
SOPS_AGE_KEY_FILE=.sops/age.key.backup.20251031_101650 \
  sops decrypt infra/secrets/secrets.enc.json > /tmp/secrets.json

# Edit the file manually
nano /tmp/secrets.json
# or
code /tmp/secrets.json

# Encrypt with NEW key
sops encrypt /tmp/secrets.json > infra/secrets/secrets.enc.json

# Clean up
rm /tmp/secrets.json
```

### Step 4: Update mac-mini.enc.yaml

```bash
# Decrypt with OLD key (dotenv format)
SOPS_AGE_KEY_FILE=.sops/age.key.backup.20251031_101650 \
  sops decrypt --input-type dotenv --output-type dotenv \
  infra/secrets/mac-mini.enc.yaml > /tmp/mac-mini.env

# Edit with new values
nano /tmp/mac-mini.env

# Encrypt with NEW key
sops encrypt --input-type dotenv --output-type dotenv \
  /tmp/mac-mini.env > infra/secrets/mac-mini.enc.yaml

# Clean up
rm /tmp/mac-mini.env
```

### Step 5: Update config.json (if needed)

`infra/secrets/config.json` is NOT encrypted, so check if it contains any sensitive data:

```bash
cat infra/secrets/config.json
```

If it contains sensitive data, it should be encrypted or moved to the encrypted files.

### Step 6: Test Decryption with NEW Key

```bash
# Should work with NEW key (default .sops/age.key)
sops decrypt infra/secrets/secrets.enc.json | jq 'keys'

# Should show your NEW secrets
sops decrypt --input-type dotenv --output-type dotenv \
  infra/secrets/mac-mini.enc.yaml
```

### Step 7: Update Services

After rotating secrets:

1. **Update CI/CD secrets**
   - Update GitHub Actions secrets
   - Update any other CI/CD pipelines

2. **Update running services**

   ```bash
   # Regenerate .env from new secrets
   task infra:setup

   # Restart services with new credentials
   task infra:restart
   ```

3. **Test services**

   ```bash
   task infra:status
   ```

---

## 📋 Checklist

- [ ] Identified all secrets that need rotation
- [ ] Generated new API keys from providers
- [ ] Revoked/deleted old API keys
- [ ] Generated new service passwords/tokens
- [ ] Updated `secrets.enc.json` with new values
- [ ] Updated `mac-mini.enc.yaml` with new values
- [ ] Tested decryption with NEW key
- [ ] Updated CI/CD secrets
- [ ] Restarted services with new credentials
- [ ] Verified services are working
- [ ] Deleted temporary decrypted files
- [ ] Securely deleted old backed-up keys after verification

---

## 🔒 Security Best Practices

1. **Never commit decrypted files**
   - Always work in `/tmp/` or similar
   - Delete immediately after use

2. **Verify no sensitive data in plaintext**

   ```bash
   # Check git for plaintext secrets
   git grep -i "password\|secret\|key\|token" --cached
   ```

3. **Rotate all secrets, not just some**
   - Even if you think a secret wasn't critical, rotate it

4. **Monitor for unauthorized access**
   - Check logs for unusual activity
   - Review API usage from your providers

5. **Document what was rotated**
   - Keep a record (not in git) of when secrets were rotated
   - Note which services were updated

---

## 🆘 If You Need Help

```bash
# Check SOPS configuration
task sops:info

# Edit encrypted file (uses new key automatically)
task sops:edit

# View decrypted content
task sops:decrypt
```

## ⚠️ After Rotation

Once you've rotated all secret values:

1. ✅ Commit the newly encrypted files
2. ✅ Update CI/CD with new credentials
3. ✅ Delete old backup keys after confirming everything works
4. ✅ Clean git history of old compromised key
5. ✅ Monitor services for issues

Remember: **The goal is not just to re-encrypt, but to make the old secret values useless!**
