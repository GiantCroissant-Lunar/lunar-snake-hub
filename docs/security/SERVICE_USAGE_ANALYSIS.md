# Service Usage Analysis

## Summary: Which Secrets Are Actually Being Used?

Based on analysis of your lunar-snake-hub infrastructure:

---

## ✅ ACTIVELY USED

### 1. GLM API Key

- **Status:** ✅ **REQUIRED** - Actively used
- **Used by:**
  - Letta service (Docker container)
  - Gateway service (Docker container)
- **Environment variable:** `OPENAI_API_KEY`
- **Conclusion:** **Keep this - it's essential**

### 2. N8n Password

- **Status:** ✅ **REQUIRED** - Actively used
- **Used by:** n8n workflow automation service (Docker container)
- **Environment variable:** `N8N_PASSWORD`
- **Login:** `admin` / `[password]` at <http://juis-mac-mini:5678>
- **Conclusion:** **Keep this - it's essential**

---

## ⚠️ PLANNED BUT NOT YET IMPLEMENTED

### 3. Gateway Token

- **Status:** ⚠️ **PLANNED** (Phase 2)
- **Intended use:** Authentication for the Gateway FastAPI service
- **Docker service:** `gateway` (port 5057)
- **Current state:**
  - Service is defined in `docker-compose.yml`
  - Gateway code needs to be built (`./gateway/Dockerfile`)
  - Not currently running (Phase 2 feature)
- **Conclusion:** **OPTIONAL** - Can be removed if you're not implementing the Gateway service soon

### 4. GitHub Personal Access Token

- **Status:** ⚠️ **OPTIONAL** - Not actively used
- **Config shows:** `"GitHub": { "Enabled": false }`
- **Intended use:** GitHub API access (automation, CI/CD)
- **Current state:** GitHub integration is disabled
- **Conclusion:** **OPTIONAL** - Can be removed or kept for future use

### 5. GitHub Webhook Secret  

- **Status:** ⚠️ **OPTIONAL** - Not actively used
- **Config shows:** `"GitHub": { "Enabled": false }`
- **Intended use:** Validating GitHub webhook payloads (for n8n workflows)
- **Planned for:** Automatic repo sync when code changes
- **Current state:** Not configured, no webhooks set up
- **Conclusion:** **OPTIONAL** - Only needed if you set up GitHub webhooks with n8n

---

## 📊 Running Services Analysis

From `docker-compose.yml`, these services are defined:

| Service | Status | Port | Requires Secrets? |
|---------|--------|------|-------------------|
| **Letta** | ✅ Running | 5055 | ✅ GLM API Key |
| **Qdrant** | ✅ Running | 6333, 6334 | ❌ No |
| **n8n** | ✅ Running | 5678 | ✅ N8n Password |
| **Gateway** | ⚠️ Phase 2 | 5057 | ⚠️ Gateway Token (when implemented) |

---

## 🎯 Recommendations

### Minimal Configuration (What You Need Now)

If you want to simplify and only keep what's actively used:

```json
{
  "$schema": "./schemas/config.schema.json",
  "GLM": {
    "ApiKey": "<REDACTED>"
  },
  "Services": {
    "N8n": {
      "Password": "<REDACTED>"
    }
  }
}
```

**Remove:**

- `GitHub.PersonalAccessToken` (not used, GitHub disabled)
- `GitHub.WebhookSecret` (not used, no webhooks configured)
- `Services.Gateway.Token` (Phase 2, not implemented yet)

### Full Configuration (What You Have Now)

Keep all secrets if you plan to:

- Implement the Gateway service (Phase 2)
- Enable GitHub integration
- Set up GitHub webhooks for n8n automation

---

## 🔧 How to Simplify

### Option 1: Remove Unused Secrets Now

```bash
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub

# Create minimal secrets file
cat > /tmp/secrets-minimal.json << 'EOF'
{
  "$schema": "./schemas/config.schema.json",
  "GLM": {
    "ApiKey": "<REDACTED>"
  },
  "Services": {
    "N8n": {
      "Password": "<REDACTED>"
    }
  }
}
EOF

# Encrypt it
sops --encrypt /tmp/secrets-minimal.json > infra/secrets/secrets.enc.json
rm /tmp/secrets-minimal.json
```

**Note:** This will break the JSON schema validation since it expects `Gateway` to be present.

### Option 2: Keep All Secrets (Recommended)

Keep the current configuration as-is. The unused secrets don't hurt anything, and you might need them when you implement Phase 2/3 features.

**Pros:**

- ✅ Ready for future features
- ✅ No schema changes needed
- ✅ All secrets already rotated with new secure values

**Cons:**

- More secrets to manage (but they're already managed)

---

## 🛠️ Schema Changes Needed for Option 1

If you want to make Gateway and GitHub optional in the schema:

```json
{
  "Services": {
    "type": "object",
    "required": ["N8n"],  // Remove "Gateway" from required
    "properties": {
      "Gateway": {
        // Keep definition but not required
      },
      "N8n": {
        // Required
      }
    }
  },
  "GitHub": {
    // Already optional (not in required array)
  }
}
```

---

## ✅ My Recommendation

**Keep all the secrets you just rotated.** Here's why:

1. ✅ **They're already rotated** - Work is done
2. ✅ **Secure new values** - All freshly generated
3. ✅ **Future-ready** - Gateway and GitHub features are planned
4. ✅ **No harm** - Having extra encrypted secrets doesn't create risk
5. ✅ **Schema compliant** - Current schema expects Gateway token

**Just proceed with committing the current `secrets.enc.json` as-is.**

---

## 📋 Next Steps

1. **Commit the changes** (all secrets included)
2. **Update CI/CD** with new age private key
3. **Clean git history** to remove old compromised key
4. **Test services:**

   ```bash
   task infra:setup
   task infra:restart
   task infra:status
   ```

5. **When you implement Gateway/GitHub features**, the secrets are already there!

---

## 🎯 TL;DR

**Currently Active:**

- ✅ GLM API Key (essential)
- ✅ N8n Password (essential)

**Currently Unused but Kept:**

- ⚠️ Gateway Token (Phase 2 - planned)
- ⚠️ GitHub Token (optional - disabled)
- ⚠️ GitHub Webhook Secret (optional - not configured)

**Recommendation:** Keep everything. It's already secured and ready for future use.
