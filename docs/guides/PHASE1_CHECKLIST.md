---
doc_id: DOC-2025-00014
title: Phase 1 Implementation Checklist
doc_type: guide
status: active
canonical: true
created: 2025-10-30
tags: [phase1, checklist, implementation, step-by-step]
summary: Step-by-step implementation checklist for Phase 1 hub setup (4 hours target)
related: [DOC-2025-00004, DOC-2025-00015]
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# Phase 1 Implementation Checklist

**Target:** 4 hours | **Pilot:** lablab-bean | **Hub:** lunar-snake-hub

---

## ☑️ Before You Start

- [ ] Read `YOUR_DECISIONS_SUMMARY.md`
- [ ] Mac Mini is on and Tailscale connected
- [ ] You have 4 uninterrupted hours
- [ ] GitHub org access confirmed: `GiantCroissant-Lunar`

---

## 📋 Step-by-Step Checklist

### 1️⃣ Create Hub Repo (30 min)

**GitHub:**

- [ ] Go to <https://github.com/organizations/GiantCroissant-Lunar/repositories/new>
- [ ] Name: `lunar-snake-hub`
- [ ] Visibility: **Public**
- [ ] Initialize with README
- [ ] Create

**Local setup:**

```bash
cd C:\lunar-snake\personal-work\
git clone https://github.com/GiantCroissant-Lunar/lunar-snake-hub.git
cd lunar-snake-hub
```

**Create structure:**

```bash
mkdir -p .agent/rules .agent/prompts .agent/adapters
mkdir -p nuke specs precommit/hooks infra/secrets docs
touch .gitignore README.md
```

**`.gitignore`:**

```
# Secrets (use SOPS encrypted versions)
*.env
!*.enc.yaml

# Local
.DS_Store
.vscode/
.idea/
```

**Commit:**

```bash
git add .
git commit -m "feat: initial hub structure"
git push
```

---

### 2️⃣ Extract Agent Rules from lablab-bean (45 min)

**Explore current structure:**

```bash
cd D:\lunar-snake\personal-work\yokan-projects\lablab-bean\.agent
ls -la
# You have: adapters, agents, base, integrations, meta, scripts, specs
```

**Copy to hub:**

```bash
cd C:\lunar-snake\personal-work\lunar-snake-hub

# Copy base rules
cp -r ../yokan-projects/lablab-bean/.agent/base/* .agent/rules/

# Copy agent prompts
cp -r ../yokan-projects/lablab-bean/.agent/agents/* .agent/prompts/

# Copy adapters
cp -r ../yokan-projects/lablab-bean/.agent/adapters/* .agent/adapters/

# Copy any useful scripts
cp -r ../yokan-projects/lablab-bean/.agent/scripts/* .agent/scripts/
```

**Organize (review and clean):**

- [ ] Review `.agent/rules/` - remove lablab-specific rules
- [ ] Review `.agent/prompts/` - generalize for any project
- [ ] Review `.agent/adapters/` - keep IDE-specific configs

**Commit:**

```bash
git add .agent/
git commit -m "feat: add agent rules from lablab-bean"
git push
```

---

### 3️⃣ Extract NUKE Common Build (30 min)

**Check lablab-bean NUKE:**

```bash
cd D:\lunar-snake\personal-work\yokan-projects\lablab-bean\.nuke
ls -la
# Identify common targets
```

**Extract common:**

```bash
cd C:\lunar-snake\personal-work\lunar-snake-hub\nuke

# Create Build.Common.cs with shared targets
# (restore, clean, compile, test, pack)
```

**Commit:**

```bash
git add nuke/
git commit -m "feat: add common NUKE build components"
git push
```

---

### 4️⃣ Create Hub Manifest in lablab-bean (15 min)

**Create file:**

```bash
cd D:\lunar-snake\personal-work\yokan-projects\lablab-bean
```

**`.hub-manifest.toml`:**

```toml
[hub]
repo = "GiantCroissant-Lunar/lunar-snake-hub"
branch = "main"

[packs]
nuke = "0.1.0"
precommit = "0.1.0"

[sync]
include = [
    ".agent/rules/**",
    ".agent/prompts/**",
    ".agent/adapters/**",
    "nuke/**",
]
```

**Update `.gitignore`:**

```gitignore
# Add these lines
.hub-cache/
.agent
```

**Commit:**

```bash
git add .hub-manifest.toml .gitignore
git commit -m "feat: add hub manifest for lunar-snake-hub consumption"
git push
```

---

### 5️⃣ Add `hub:sync` Task (30 min)

**Install dependencies (if needed):**

```bash
# You need yq for TOML parsing
# Windows: scoop install yq
# Or use dasel, jq, etc.
```

**Edit `Taskfile.yml`:**

```yaml
# Add to your existing lablab-bean/Taskfile.yml

tasks:
  hub:sync:
    desc: Sync assets from lunar-snake-hub
    cmds:
      - |
        echo "🔄 Syncing from lunar-snake-hub..."

        # For Phase 1, just clone the hub repo locally
        if [ ! -d .hub-cache/hub-repo ]; then
          git clone https://github.com/GiantCroissant-Lunar/lunar-snake-hub .hub-cache/hub-repo
        else
          git -C .hub-cache/hub-repo pull
        fi

        # Sync to .hub-cache/
        mkdir -p .hub-cache/.agent .hub-cache/nuke

        cp -r .hub-cache/hub-repo/.agent/* .hub-cache/.agent/
        cp -r .hub-cache/hub-repo/nuke/* .hub-cache/nuke/

        # Create symlink for backward compat
        rm -rf .agent
        ln -s .hub-cache/.agent .agent

        echo "✅ Hub sync complete"
        echo "   Agents: $(ls .hub-cache/.agent/rules | wc -l) rules"
        echo "   NUKE: $(ls .hub-cache/nuke | wc -l) files"

  hub:check:
    desc: Verify hub cache is fresh
    cmds:
      - |
        if [ ! -d .hub-cache/.agent ]; then
          echo "❌ Run 'task hub:sync' first"
          exit 1
        fi
        echo "✅ Hub cache present"

  hub:clean:
    desc: Remove hub cache (force fresh sync)
    cmds:
      - rm -rf .hub-cache .agent
      - echo "✅ Hub cache cleaned"
```

**Test:**

```bash
task hub:sync
task hub:check
```

**Verify:**

```bash
ls -la .hub-cache/.agent/rules/
ls -la .agent
```

**Commit:**

```bash
git add Taskfile.yml
git commit -m "feat: add hub sync tasks"
git push
```

---

### 6️⃣ Set Up Letta on Mac Mini (30 min)

**SSH to Mac Mini:**

```bash
ssh <your-mac-mini>
# Or use Tailscale name: ssh <name>.tailscale.net
```

**Create SOPS secret (on Windows first):**

```bash
cd C:\lunar-snake\personal-work\lunar-snake-hub\infra\secrets

# Create age key if you don't have one
# age-keygen -o age-key.txt

# Create secrets file
cat > mac-mini.yaml <<EOF
OPENAI_API_KEY=your_glm_api_key_here
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
EOF

# Encrypt with SOPS
sops encrypt mac-mini.yaml > mac-mini.enc.yaml

# Remove plaintext
rm mac-mini.yaml

# Commit encrypted
git add mac-mini.enc.yaml
git commit -m "feat: add Mac Mini secrets (SOPS encrypted)"
git push
```

**On Mac Mini:**

```bash
mkdir -p ~/ctx-hub
cd ~/ctx-hub

# Clone hub to get secrets
git clone https://github.com/GiantCroissant-Lunar/lunar-snake-hub.git

# Decrypt secrets
sops decrypt lunar-snake-hub/infra/secrets/mac-mini.enc.yaml > .env

# Create docker-compose.yml
cat > docker-compose.yml <<'EOF'
services:
  letta:
    image: ghcr.io/letta-ai/letta:latest
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL}
      - LETTA_DB_URL=sqlite:///data/letta.db
    volumes:
      - ./data:/data
    ports:
      - "5055:5055"
    restart: unless-stopped
EOF

# Start
docker compose up -d

# Wait 10 seconds
sleep 10

# Test
curl http://localhost:5055/v1/health
# Should return: {"status":"ok"}
```

**Get Tailscale hostname:**

```bash
tailscale status | grep $(hostname)
# Note the hostname, e.g., mac-mini.tailscale.net
```

**Test from Windows:**

```powershell
# On Windows
curl http://<mac-mini-tailscale-name>:5055/v1/health
```

---

### 7️⃣ Configure Letta in Your IDE (15 min)

**Find your MCP config location:**

- Cline: VS Code settings → MCP Servers
- Or `.mcp-config.json` in workspace

**Add Letta tool:**

```json
{
  "mcpServers": {
    "letta-memory": {
      "type": "http",
      "baseUrl": "http://<mac-mini-tailscale-name>:5055",
      "tools": [
        {
          "name": "save_memory",
          "description": "Save a decision or context to persistent memory",
          "method": "POST",
          "path": "/v1/agents/default/memory",
          "input_schema": {
            "type": "object",
            "properties": {
              "key": {"type": "string"},
              "value": {"type": "string"}
            }
          }
        },
        {
          "name": "get_memory",
          "description": "Retrieve a saved decision or context",
          "method": "GET",
          "path": "/v1/agents/default/memory/{key}"
        }
      ]
    }
  }
}
```

*(Adjust based on actual Letta API - this is conceptual)*

**Restart VS Code**

---

### 8️⃣ Test Everything (45 min)

#### Test 1: Hub Sync

```bash
cd D:\lunar-snake\personal-work\yokan-projects\lablab-bean
task hub:clean
task hub:sync
```

**Expected:**

```
✅ Hub sync complete
   Agents: 15 rules
   NUKE: 3 files
```

#### Test 2: Agent Reads Hub Rules

1. Open `lablab-bean` in VS Code
2. Start Cline/Roo/Kilo
3. Ask: **"What are our naming conventions? Check the agent rules."**
4. Agent should read from `.hub-cache/.agent/rules/...` (or `.agent/...`)

**Success:** Agent finds and quotes rules from hub

#### Test 3: Letta Memory (Basic)

1. Ask agent: **"Remember this decision: We chose Repository pattern for data access because it decouples domain from infrastructure."**
2. Agent should call Letta to save
3. Restart VS Code
4. Ask: **"What pattern did we choose for data access and why?"**

**Success:** Agent recalls from Letta memory

#### Test 4: Update Hub, Re-sync

1. Edit a rule in `lunar-snake-hub/.agent/rules/`
2. Commit and push
3. In `lablab-bean`: `task hub:sync`
4. Ask agent to read the updated rule

**Success:** Agent sees the new version

---

## ✅ Phase 1 Complete When

- [ ] `lunar-snake-hub` repo exists with initial structure
- [ ] Agent rules extracted from lablab-bean → hub
- [ ] `lablab-bean` has `.hub-manifest.toml`
- [ ] `task hub:sync` works (fetches to `.hub-cache/`)
- [ ] `.agent/` is symlink (gitignored)
- [ ] Letta running on Mac Mini (accessible via Tailscale)
- [ ] Agent reads rules from synced cache
- [ ] Agent stores/retrieves memory via Letta

---

## 🎯 Success Test Script

Run this to verify everything works:

```bash
cd lablab-bean

# 1. Clean sync
task hub:clean
task hub:sync

# 2. Check cache
ls .hub-cache/.agent/rules
ls .agent  # Should be symlink

# 3. Test Letta from Windows
curl http://<mac-mini>.tailscale.net:5055/v1/health

# 4. Open in IDE, ask agent:
# - "List our agent rules"
# - "Remember: Test decision for Phase 1"
# - Restart IDE
# - "What decision did I just ask you to remember?"
```

**All green?** Phase 1 complete! 🎉

---

## 🐛 Troubleshooting

### `task: command not found`

```bash
# Install go-task
# Windows: scoop install task
# Mac: brew install go-task/tap/go-task
```

### `yq: command not found`

```bash
# Install yq
# Windows: scoop install yq
# Mac: brew install yq
```

### Symlink fails on Windows

```bash
# Run PowerShell as Admin
# Or use junction instead:
cmd /c mklink /J .agent .hub-cache\agents
```

### Letta not accessible from Windows

```bash
# Check Tailscale status
tailscale status

# Check firewall on Mac Mini
# System Settings → Network → Firewall → Allow port 5055
```

### Hub sync shows no files

```bash
# Check git clone worked
ls .hub-cache/hub-repo
git -C .hub-cache/hub-repo log

# Re-clone
task hub:clean
task hub:sync
```

---

## 📊 Time Tracker

| Task | Estimated | Actual | Notes |
|------|-----------|--------|-------|
| 1. Create hub repo | 30 min | ___ | |
| 2. Extract agent rules | 45 min | ___ | |
| 3. Extract NUKE | 30 min | ___ | |
| 4. Hub manifest | 15 min | ___ | |
| 5. Taskfile hub:sync | 30 min | ___ | |
| 6. Letta on Mac Mini | 30 min | ___ | |
| 7. IDE config | 15 min | ___ | |
| 8. Testing | 45 min | ___ | |
| **Total** | **4 hours** | ___ | |

---

## 🎓 What You Learned

After Phase 1, you will have:

- ✅ One source of truth for agent rules (hub)
- ✅ Runtime sync pattern (no duplication in git)
- ✅ Persistent memory across sessions (Letta)
- ✅ Clean satellite repos (code + manifest only)
- ✅ Task automation (`task hub:sync`)
- ✅ SOPS encrypted secrets workflow
- ✅ Mac Mini as infrastructure brain

---

## 🚀 After Phase 1

**Use it for a week:**

- Work on lablab-bean normally
- Note when context burns / agents forget
- Note if hub sync is smooth or annoying
- Collect pain points

**Then decide:**

- Continue to Phase 2 (RAG) if context is still a problem
- Scale to more satellites if Phase 1 is working well
- Adjust hub structure based on learnings

---

**Ready? Let's build this!** 🎯

When you want to start, just say:

- "Let's create the hub repo" (I'll guide step-by-step)
- Or work through the checklist at your own pace

**Questions before starting?** Ask away!
