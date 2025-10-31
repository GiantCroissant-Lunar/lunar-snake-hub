# Specific Secrets to Rotate

## 📋 Exact List of Compromised Secrets

Based on your encrypted files, here are **ALL** the secrets that need new values:

---

## 1. GLM API Key (`secrets.enc.json`)

**What it is:** API key for GLM (Zhipu AI) language model service

**Location in file:** `GLM.ApiKey`

**Where to rotate:**

1. Go to: <https://open.bigmodel.cn/usercenter/apikeys> (or your GLM dashboard)
2. Find your current API key
3. **Delete/Revoke** the old key
4. **Generate** a new API key
5. Copy the new key

**Also in:** `mac-mini.enc.yaml` as `OPENAI_API_KEY` (yes, confusingly named - it's actually your GLM key)

---

## 2. GitHub Personal Access Token (`secrets.enc.json`)

**What it is:** Token for GitHub API access (for automation, CI/CD, etc.)

**Location in file:** `GitHub.PersonalAccessToken`

**Where to rotate:**

1. Go to: <https://github.com/settings/tokens>
2. Find the token (look for one created around the same time as your hub setup)
3. **Delete** the old token
4. Click "Generate new token" (classic or fine-grained)
5. Select the same scopes/permissions as before:
   - Likely: `repo`, `workflow`, `read:org` (check your usage to confirm)
6. Copy the new token

**Note:** If `GitHub.Enabled: false` in config, this might not be actively used, but rotate it anyway!

---

## 3. GitHub Webhook Secret (`secrets.enc.json`)

**What it is:** Secret for validating GitHub webhook payloads

**Location in file:** `GitHub.WebhookSecret`

**Where to rotate:**

1. Generate a new random secret:

   ```bash
   openssl rand -hex 32
   ```

2. Update in your GitHub webhook settings if you have webhooks configured
3. Use the new secret in the encrypted file

---

## 4. Gateway Token (`secrets.enc.json` and `mac-mini.enc.yaml`)

**What it is:** Authentication token for your Gateway service (port 5057)

**Location in files:**

- `Services.Gateway.Token` in secrets.enc.json
- `GATEWAY_TOKEN` in mac-mini.enc.yaml

**Where to rotate:**
This is a custom token for your own Gateway service. Generate a new random token:

```bash
# Generate a secure random token
openssl rand -base64 32
```

Use the same new value in **both** files.

---

## 5. N8n Password (`secrets.enc.json`)

**What it is:** Password for n8n workflow automation tool (admin user)

**Location in file:** `Services.N8n.Password`

**Service details:**

- Port: 5678
- User: admin (from config.json)
- URL: <http://juis-mac-mini:5678>

**Where to rotate:**
Generate a new strong password:

```bash
# Generate a secure password
openssl rand -base64 24
```

**After updating:** You'll need to log into n8n with the new password after restarting the service.

---

## 6. OpenAI Base URL (`mac-mini.enc.yaml`)

**What it is:** API endpoint URL for GLM service

**Location in file:** `OPENAI_BASE_URL`

**Current value:** `https://api.z.ai/api/coding/paas/v4` (from config.json)

**Action:** This is probably **NOT** a secret (just a URL), but it's encrypted. You can keep the same value or verify it's correct.

---

## 🎯 Summary Checklist

Here's what you need to do:

- [ ] **GLM API Key** - Get new key from GLM dashboard (use in both files)
- [ ] **GitHub Personal Access Token** - Revoke old, generate new from GitHub settings
- [ ] **GitHub Webhook Secret** - Generate new random hex string
- [ ] **Gateway Token** - Generate new random token (use in both files)
- [ ] **N8n Password** - Generate new password for admin user

---

## 🛠️ How to Update

### Option 1: Edit with SOPS directly (Recommended)

```bash
# Edit secrets.enc.json (SOPS handles encryption)
sops infra/secrets/secrets.enc.json

# For mac-mini.enc.yaml, use the helper script
./rotate-secret-values.sh
```

### Option 2: Manual process

```bash
# 1. Decrypt
SOPS_AGE_KEY_FILE=.sops/age.key.backup.20251031_101650 \
  sops decrypt infra/secrets/secrets.enc.json > /tmp/secrets.json

# 2. Edit (replace all the values)
nano /tmp/secrets.json

# 3. Encrypt with NEW key
sops encrypt /tmp/secrets.json > infra/secrets/secrets.enc.json

# 4. Clean up
rm /tmp/secrets.json
```

---

## 📝 Example: What the files look like

### secrets.enc.json structure

```json
{
  "$schema": "./schemas/config.schema.json",
  "GLM": {
    "ApiKey": "YOUR_NEW_GLM_API_KEY_HERE"
  },
  "GitHub": {
    "PersonalAccessToken": "ghp_YOUR_NEW_GITHUB_TOKEN_HERE",
    "WebhookSecret": "NEW_RANDOM_HEX_STRING_HERE"
  },
  "Services": {
    "Gateway": {
      "Token": "NEW_RANDOM_TOKEN_HERE"
    },
    "N8n": {
      "Password": "NEW_STRONG_PASSWORD_HERE"
    }
  }
}
```

### mac-mini.enc.yaml content

```env
OPENAI_API_KEY=YOUR_NEW_GLM_API_KEY_HERE
OPENAI_BASE_URL=https://api.z.ai/api/coding/paas/v4
GATEWAY_TOKEN=NEW_RANDOM_TOKEN_HERE
```

**Important:** Use the **SAME** GLM API key and Gateway token in both files!

---

## ⚠️ After Rotation

1. Update services:

   ```bash
   task infra:setup
   task infra:restart
   ```

2. Test services:

   ```bash
   task infra:status
   ```

3. Update CI/CD secrets with:
   - New private age key (`.sops/age.key`)
   - Any other secrets your CI/CD uses

---

## 🔗 Quick Links

- GLM Dashboard: <https://open.bigmodel.cn/usercenter/apikeys>
- GitHub Tokens: <https://github.com/settings/tokens>
- Generate passwords: `openssl rand -base64 24`
- Generate tokens: `openssl rand -base64 32`
- Generate webhook secret: `openssl rand -hex 32`
