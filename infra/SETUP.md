# 🚀 Infrastructure Setup Guide

**Complete guide for setting up Letta, Qdrant, n8n, and Gateway on Mac Mini**

## 📋 What We Built

✅ **Ansible Automation** - One-command setup for Mac Mini
✅ **JSON Configuration** - Following your `giantcroissant-lunar-ai` pattern
✅ **SOPS Encryption** - Secure secrets management with age
✅ **Docker Compose** - All services pre-configured
✅ **PowerShell Scripts** - Windows workflow automation

## 🎯 Architecture

```
Windows (Development)          Mac Mini (Infrastructure)
├─ VS Code + AI Agents    ←→  ├─ Letta (Memory) :5055
├─ secrets.json (local)        ├─ Qdrant (RAG) :6333
└─ Tailscale                   ├─ n8n (Automation) :5678
                               └─ Gateway (API) :5057
```

**Communication:** Windows ←→ Mac Mini via Tailscale VPN

## 🔐 Step 1: Create Secrets Configuration

### 1a. Generate Gateway Token

```powershell
# Open PowerShell
[System.Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

**Save this token** - you'll need it for secrets.json

### 1b. Get Your GLM-4.6 API Key

1. Login to <https://open.bigmodel.cn/>
2. Go to API Keys section
3. Copy your JWT token (long string starting with `eyJ...`)

### 1c. Create secrets.json

```powershell
cd D:\lunar-snake\lunar-snake-hub\infra\secrets

# Copy template
copy secrets.template.json secrets.json

# Edit with your values
notepad secrets.json
```

**Edit these fields in secrets.json:**

```json
{
  "GLM": {
    "ApiKey": "eyJhbGci... YOUR_ACTUAL_GLM_JWT_TOKEN",
  },
  "Services": {
    "Gateway": {
      "Token": "YOUR_GENERATED_TOKEN_FROM_STEP_1A"
    },
    "N8n": {
      "Password": "CHOOSE_A_STRONG_PASSWORD"
    }
  },
  "GitHub": {
    "PersonalAccessToken": "OPTIONAL_ghp_xxxx"
  }
}
```

### 1d. Encrypt secrets.json

```powershell
# Still in infra\secrets\
.\encrypt-secrets.ps1
```

**Output:** `secrets.enc.json` (safe to commit)

### 1e. Generate .env for Docker

```powershell
.\json-to-env.ps1 -Encrypted
```

**Output:** `../docker/.env` (gitignored, for Docker Compose)

## 📦 Step 2: Commit Infrastructure Files

```powershell
cd D:\lunar-snake\lunar-snake-hub

# Check what we're committing
git status

# Should see:
# - infra/ansible/ (all files)
# - infra/docker/docker-compose.yml
# - infra/docker/.env.template
# - infra/secrets/secrets.enc.json ← ENCRYPTED (safe)
# - infra/secrets/*.ps1 (scripts)
# - .sops.yaml

# Stage all infrastructure
git add infra/
git add .sops.yaml

# Verify secrets.json is NOT staged (should be gitignored)
git status | grep "secrets.json"
# Should output nothing

# Commit
git commit -m "feat: add Ansible infrastructure with JSON secrets

- Ansible playbook for Mac Mini setup
- Docker Compose for Letta/Qdrant/n8n/Gateway
- SOPS encryption with age keys
- JSON-based secrets management
- PowerShell automation scripts"

# Push
git push origin main
```

## 🍎 Step 3: Setup Mac Mini

### 3a. Transfer age Key to Mac

**On Windows:**

```powershell
# Display your age key
cat $env:USERPROFILE\.config\sops\age\keys.txt
```

**On Mac Mini:**

```bash
# Create directory
mkdir -p ~/.config/sops/age

# Paste the key contents (entire file, all 3 lines)
nano ~/.config/sops/age/keys.txt
# Paste → Ctrl+X → Y → Enter

# Set permissions
chmod 600 ~/.config/sops/age/keys.txt

# Verify
cat ~/.config/sops/age/keys.txt
```

### 3b. Clone Repository

```bash
cd ~/repos
git clone https://github.com/GiantCroissant-Lunar/lunar-snake-hub.git
cd lunar-snake-hub
```

### 3c. Run Ansible Playbook

```bash
cd infra/ansible
ansible-playbook -i inventory/hosts.yml playbook.yml
```

**This will:**

1. ✅ Install Homebrew packages (Docker, SOPS, age, gh, yq, task)
2. ✅ Verify age keys are configured
3. ✅ Decrypt secrets and generate .env
4. ✅ Start Docker services (Letta, Qdrant, n8n)
5. ✅ Setup GitHub CLI (if you provided PAT)

**Expected output:**

```
PLAY RECAP *****************************************
localhost : ok=25  changed=12  unreachable=0  failed=0
```

### 3d. Verify Services

```bash
# Check Docker services
cd ~/repos/lunar-snake-hub/infra/docker
docker compose ps

# Should show:
# lunar-letta    running   5055/tcp
# lunar-qdrant   running   6333/tcp, 6334/tcp
# lunar-n8n      running   5678/tcp
# lunar-gateway  running   5057/tcp (Phase 2)

# Test Letta
curl http://localhost:5055/v1/health
# Should return: {"status":"ok"}
```

## 🪟 Step 4: Test from Windows

```powershell
# Test Tailscale connectivity
ping juis-mac-mini

# Test Letta via Tailscale
curl http://juis-mac-mini:5055/v1/health

# Should return: {"status":"ok"}
```

✅ **If you see `{"status":"ok"}`, Letta is working!**

## 🔌 Step 5: Configure Letta MCP Tool (VS Code)

### Option A: HTTP MCP Tool (Simplest)

Add to your MCP configuration (`.vscode/settings.json` or Cline settings):

```json
{
  "mcpServers": {
    "letta-memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"],
      "env": {
        "LETTA_URL": "http://juis-mac-mini:5055"
      }
    }
  }
}
```

### Option B: Custom MCP Server (More Features)

Create `mcp-servers/letta/index.js`:

```javascript
#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

const LETTA_URL = process.env.LETTA_URL || "http://juis-mac-mini:5055";

const server = new McpServer({
  name: "letta",
  version: "1.0.0"
});

server.tool("letta_memory_put", {
  description: "Store a decision or memory in Letta",
  inputSchema: {
    type: "object",
    properties: {
      key: { type: "string", description: "Memory key (e.g., 'project/decision/auth')" },
      value: { type: "object", description: "Memory value (any JSON object)" }
    },
    required: ["key", "value"]
  }
}, async ({key, value}) => {
  const response = await fetch(`${LETTA_URL}/v1/memory`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ op: "put", key, value })
  });
  return await response.json();
});

server.tool("letta_memory_get", {
  description: "Retrieve a memory from Letta",
  inputSchema: {
    type: "object",
    properties: {
      key: { type: "string", description: "Memory key to retrieve" }
    },
    required: ["key"]
  }
}, async ({key}) => {
  const response = await fetch(`${LETTA_URL}/v1/memory/${key}`);
  return await response.json();
});

server.start();
```

Then in MCP config:

```json
{
  "mcpServers": {
    "letta": {
      "command": "node",
      "args": ["D:/lunar-snake/lunar-snake-hub/mcp-servers/letta/index.js"],
      "env": {
        "LETTA_URL": "http://juis-mac-mini:5055"
      }
    }
  }
}
```

## ✅ Step 6: Test End-to-End

### Test 1: Store a Memory

In VS Code with Cline:

> "Store this decision: We're using Repository pattern for data access because it provides better testability and separation of concerns."

Agent should use the `letta_memory_put` tool.

### Test 2: Recall Memory

Restart VS Code, then ask:

> "What pattern did we decide to use for data access?"

Agent should use `letta_memory_get` and recall the decision.

## 🎉 Success Criteria

✅ Letta responds to health checks from Windows
✅ Agent can store memories via MCP tool
✅ Agent can retrieve memories after restart
✅ Memories persist across IDE sessions

## 🔧 Troubleshooting

### Services won't start on Mac

```bash
# Check if ports are available
lsof -i :5055  # Should be empty

# Check Docker
docker info

# Restart Docker Desktop
killall Docker && open -a Docker

# Re-run Ansible
cd ~/repos/lunar-snake-hub/infra/ansible
ansible-playbook -i inventory/hosts.yml playbook.yml
```

### Can't access from Windows

```bash
# On Mac Mini: Check Tailscale
tailscale status

# On Windows: Test connectivity
ping juis-mac-mini
curl http://100.79.159.89:5055/v1/health  # Use IP directly
```

### Secrets won't decrypt

```bash
# Verify age key exists
ls -la ~/.config/sops/age/keys.txt

# Set environment variable
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt

# Test decrypt
cd ~/repos/lunar-snake-hub/infra/secrets
sops decrypt secrets.enc.json
```

## 📚 Next Steps (Phase 2)

After Phase 1 is working:

1. **Add Qdrant** - Vector database for RAG
2. **Build Context Gateway** - HTTP API for /ask, /memory, /notes
3. **Index Repositories** - Embed code for semantic search
4. **Test RAG Queries** - "Show me authentication examples"

See: `docs/architecture/YOUR_DECISIONS_SUMMARY.md` for Phase 2 details.

## 📖 Reference Documentation

- [Infrastructure Overview](README.md)
- [Secrets Management](secrets/README.md)
- [Ansible Playbook Details](ansible/README.md)
- [Docker Services](docker/docker-compose.yml)

---

**Status:** Phase 1 Ready
**Last Updated:** 2025-10-30
**Owner:** lunar-snake
