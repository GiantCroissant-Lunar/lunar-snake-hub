---
doc_id: DOC-2025-00010
title: Your Architecture Decisions - Final Summary
doc_type: adr
status: active
canonical: true
created: 2025-10-30
tags: [architecture, decisions, adr, phase1]
summary: Finalized architecture decisions for Phase 1 - LLM choice, memory strategy, infrastructure setup
related: [DOC-2025-00007, DOC-2025-00009]
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# Your Architecture Decisions - Final Summary

**Date:** 2025-10-30
**Status:** ✅ Decisions Complete - Ready for Implementation

---

## 🎯 Your Specific Choices

### 1. Central Hub

**Name:** `lunar-snake-hub`

**Rationale:** Perfect! Yearly naming convention (lunar-snake → lunar-horse → ...) prevents future conflicts.

**Location:** `https://github.com/GiantCroissant-Lunar/lunar-snake-hub` (to be created)

**Visibility:** **Public** (to maximize GitHub free runner minutes)

---

### 2. Pilot Satellite

**Name:** `lablab-bean`

**Current location:** `D:\lunar-snake\personal-work\yokan-projects\lablab-bean`

**GitHub:** `https://github.com/GiantCroissant-Lunar/lablab-bean`

**Why this one:**

- ✅ Already has `.agent/` folder structure
- ✅ Already has `Taskfile.yml` (your preferred build tool)
- ✅ Has `specs/` folder (specs-driven development)
- ✅ Has NUKE build (`.nuke/` folder)
- ✅ Well-structured (agents, adapters, base, integrations)
- ✅ Active development

**Architecture context:**

- **Original 3-layer design:**
  - **infra-layer:** Foundation, build, report
  - **plate-layer:** General game dev packages (Unity packages)
  - **yokan-layer:** Actual Unity projects
- **New direction:** Generalizing from Unity-specific to .NET general with specializations (Unity, console, etc.)

---

### 3. GitHub Organization

**Type:** Organization

**Name:** `GiantCroissant-Lunar`

**URL:** `https://github.com/GiantCroissant-Lunar`

**Satellite visibility:** Mix of public and private repos

---

### 4. LLM & Embeddings

**Provider:** GLM 4.6 (Zhipu/Z.ai)

**Plan:** Coding plan subscription (`https://docs.z.ai/devpack/overview`)

**Rate limits:**

- GLM-4.6: 5 concurrent requests
- Context length >8K: throttled to 1% of standard concurrency

**Embeddings:** GLM embeddings (same provider, one API key)

**BYOK endpoint:**

```bash
OPENAI_API_KEY=<your_zhipu_jwt>
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
```

---

### 5. Networking

**Method:** Tailscale VPN

**Status:** ✅ Already installed on both Windows and Mac Mini

**Advantage:**

- Works anywhere (not just home network)
- Secure by default
- Easy DNS (use machine names)

**Mac Mini access:** `http://<mac-mini-tailscale-name>:5057`

---

### 6. CI/CD Strategy

**Self-hosted runner:** NO

**Rationale:**

- Maximize use of GitHub's free public runner minutes
- `lunar-snake-hub` will be public
- Satellites can be public or private
- Simpler infrastructure (no runner maintenance)

**Sync strategy:** n8n webhooks + scheduled fallback (no self-hosted runner needed)

---

### 7. Contract Tests

**Decision:** **Phase 2** (My recommendation since you asked me to decide)

**Rationale:**

- ✅ Phase 1: Prove the hub/satellite model works first
- ✅ Phase 2: Add contract tests after you have 1 working satellite
- ✅ This avoids over-engineering before validating the core concept
- ✅ You already have specs in `lablab-bean/specs/` to build tests from

**Action:** After Phase 1 works for a week, we'll add contract tests to enforce spec compliance.

---

### 8. Secrets Management

**Method:** SOPS (encrypted in repo)

**Reference implementation:** `C:\lunar-snake\personal-work\infra-projects\giantcroissant-lunar-ai\infra`

**SOPS config example:** Found at `lablab-bean/ref-projects/winged-bean/infra/terraform/.sops.yaml`

**Implementation:**

```yaml
# lunar-snake-hub/infra/.sops.yaml
creation_rules:
  - path_regex: secrets/.*\.enc\.yaml$
    age: >-
      age1your-public-key-here
```

**Workflow:**

```bash
# Encrypt
sops encrypt secrets/mac-mini.yaml > secrets/mac-mini.enc.yaml

# Decrypt on Mac Mini
sops decrypt secrets/mac-mini.enc.yaml | source

# Or direct to Docker Compose
sops exec-env secrets/mac-mini.enc.yaml 'docker compose up -d'
```

**Advantage:** Secrets in git (encrypted), no `.env` files to manage separately.

---

### 9. Agent Rules Structure

**Current:** `lablab-bean/.agent/` folder

**Subfolders:**

- `.agent/adapters/` - IDE adapter configs
- `.agent/agents/` - Agent definitions
- `.agent/base/` - Base rules/prompts
- `.agent/integrations/` - Integration configs
- `.agent/meta/` - Metadata
- `.agent/scripts/` - Helper scripts
- `.agent/specs/` - Agent-specific specs

**Hub structure:** We'll adapt this into `lunar-snake-hub/agents/`

**Naming:** Flexible - can keep your current structure or migrate to `R-{CAT}-{NUM}-{desc}.md` pattern.

---

### 10. Build Automation

**Tool:** `task` (go-task, not make)

**Current:** `lablab-bean/Taskfile.yml`

**Example tasks:**

```yaml
version: '3'
tasks:
  venv:create: ...
  install: ...
  lint: ...
  format: ...
  test: ...
  precommit:install: ...
```

**Hub bootstrap:** We'll create a `task hub:sync` command instead of a bash script.

---

## 🚀 Agentic Development Approach

**Goal:** "Utilize agentic development as much as possible"

**Current exploration:**

- ❌ Tried spec-kit - "some limitations for just driven by spec"
- 🔍 Exploring BMAD-METHOD (`https://github.com/bmad-code-org/BMAD-METHOD`)

**My recommendation:**

### Hybrid Approach: Specs + Agents + Memory

1. **Specs as Foundation** (keep what works from spec-kit)
   - RFCs define "what" and "why"
   - Specs define "how" (API contracts, schemas)
   - Living in `lunar-snake-hub/specs/`

2. **Agent Rules as Guardrails**
   - Agents read rules from hub
   - Rules enforce coding standards, patterns, conventions
   - Living in `lunar-snake-hub/agents/rules/`

3. **Memory as Context**
   - Letta stores decisions, rationale, context
   - Agents query: "Why did we choose X?"
   - Persistent across sessions/projects

4. **RAG as Smart Retrieval**
   - Qdrant indexes code + specs + RFCs
   - Agents ask: "Show me auth implementation examples"
   - No context burn

5. **BMAD-METHOD Integration** (if it fits)
   - Review BMAD principles
   - Adapt what aligns with your workflow
   - Add to `lunar-snake-hub/docs/methodologies/`

**Workflow example:**

```
1. Create RFC in hub: specs/inventory-system/v1.0/rfc.md
2. Agent reads RFC + rules from hub
3. Agent checks Letta memory: "Have we done inventory before?"
4. Agent queries RAG: "Show similar patterns"
5. Agent proposes implementation
6. Developer reviews + commits
7. Agent stores decision in Letta: "Chose pattern X because..."
8. Contract tests enforce RFC compliance (Phase 2)
```

---

## 📁 Your Actual File Structure (Based on lablab-bean)

### Current lablab-bean structure

```
lablab-bean/
├── .agent/                      # Will move to hub
│   ├── adapters/
│   ├── agents/
│   ├── base/
│   ├── integrations/
│   ├── meta/
│   ├── scripts/
│   └── specs/
├── .nuke/                       # Will extract common parts to hub
├── specs/                       # Will reference hub specs
├── Taskfile.yml                 # Will add hub:sync task
├── .pre-commit-config.yaml      # Will reference hub hooks
├── dotnet/                      # Your code (stays)
├── docs/                        # Project-specific docs (stays)
└── ...
```

### After Phase 1 (lablab-bean as satellite)

```
lablab-bean/
├── dotnet/                      # ✅ Code only
├── docs/                        # ✅ Project-specific docs
├── .hub-manifest.toml           # ✅ Pins hub versions (new)
├── Taskfile.yml                 # ✅ With hub:sync task
├── .pre-commit-config.yaml      # ✅ References hub
├── .gitignore                   # ✅ Ignores .hub-cache/
└── README.md

# Runtime only (gitignored):
.hub-cache/                      # ❌ Synced from hub (gitignored)
├── agents/                      # from lunar-snake-hub
├── nuke/                        # from lunar-snake-hub
└── specs/                       # from lunar-snake-hub

.agent/ -> .hub-cache/agents/    # ❌ Symlink (gitignored)
```

---

## 🔧 Technical Stack Summary

| Component | Your Choice | Notes |
|-----------|------------|-------|
| **Central Hub** | `lunar-snake-hub` (public) | GiantCroissant-Lunar org |
| **Pilot Satellite** | `lablab-bean` | Already well-structured |
| **LLM** | GLM-4.6 | 5 concurrent, 200K context |
| **Embeddings** | GLM embeddings | Same provider as chat |
| **Memory** | Letta | Mac Mini, Docker |
| **Vector DB** | Qdrant | Mac Mini, Docker |
| **Gateway** | FastAPI | Mac Mini, Docker |
| **Orchestration** | n8n | Mac Mini, Docker |
| **CI/CD** | GitHub Actions | Public runners |
| **Secrets** | SOPS | Encrypted in repo |
| **Build Tool** | `task` | Taskfile.yml |
| **Networking** | Tailscale | Already installed |
| **Contract Tests** | Phase 2 | xUnit (C#) |

---

## 🎬 Phase 1 Action Plan (Updated for Your Setup)

### Prerequisites ✅

- [x] Hub name decided: `lunar-snake-hub`
- [x] Pilot satellite: `lablab-bean`
- [x] GitHub org: `GiantCroissant-Lunar`
- [x] Tailscale: Installed on Windows + Mac
- [x] GLM 4.6: Subscribed

### Tasks (4 hours)

#### 1. Create `lunar-snake-hub` repo (30 min)

```bash
# On GitHub: GiantCroissant-Lunar/lunar-snake-hub (public)
# Clone locally
git clone https://github.com/GiantCroissant-Lunar/lunar-snake-hub.git
cd lunar-snake-hub
```

**Initial structure:**

```
lunar-snake-hub/
├── README.md
├── .gitignore
├── agents/
│   ├── rules/          # From lablab-bean/.agent/base/
│   ├── prompts/        # From lablab-bean/.agent/agents/
│   └── adapters/       # From lablab-bean/.agent/adapters/
├── nuke/
│   └── Build.Common.cs # Extract from lablab-bean/.nuke/
├── specs/
│   └── .gitkeep        # Specs will reference this
├── precommit/
│   ├── .pre-commit-config.base.yaml
│   └── hooks/
├── infra/
│   ├── .sops.yaml
│   └── secrets/
│       └── mac-mini.enc.yaml
└── docs/
    ├── ARCHITECTURE_DISCUSSION.md  # Move from jack-bean
    ├── ARCHITECTURE_QUICK_REF.md
    └── YOUR_DECISIONS_SUMMARY.md
```

#### 2. Extract & move agent rules from lablab-bean (45 min)

```bash
# Copy .agent/ structure to hub
cp -r lablab-bean/.agent/* lunar-snake-hub/agents/

# Organize:
# - lablab-bean/.agent/base/ → lunar-snake-hub/agents/rules/
# - lablab-bean/.agent/agents/ → lunar-snake-hub/agents/prompts/
# - lablab-bean/.agent/adapters/ → lunar-snake-hub/agents/adapters/
```

#### 3. Extract NUKE common build (30 min)

```bash
# Identify common NUKE targets from lablab-bean/.nuke/
# Extract to lunar-snake-hub/nuke/Build.Common.cs
```

#### 4. Create `.hub-manifest.toml` in lablab-bean (15 min)

```toml
[hub]
repo = "GiantCroissant-Lunar/lunar-snake-hub"

[specs]
# Add when you have specs to implement

[packs]
agents = "0.1.0"      # Initial version
nuke = "0.1.0"
precommit = "0.1.0"

[sync]
include = [
    "agents/**",
    "nuke/**",
    "precommit/**",
]
```

#### 5. Add `hub:sync` task to Taskfile.yml (30 min)

```yaml
# lablab-bean/Taskfile.yml

tasks:
  hub:sync:
    desc: Sync assets from lunar-snake-hub
    cmds:
      - |
        echo "🔄 Syncing from lunar-snake-hub..."
        # Read manifest (requires yq or dasel)
        HUB_REPO=$(yq e '.hub.repo' .hub-manifest.toml)
        AGENTS_VER=$(yq e '.packs.agents' .hub-manifest.toml)

        mkdir -p .hub-cache

        # Download agents pack (when releases exist)
        # For now, clone locally:
        if [ ! -d .hub-cache/hub-repo ]; then
          git clone https://github.com/$HUB_REPO .hub-cache/hub-repo
        else
          git -C .hub-cache/hub-repo pull
        fi

        # Sync to .hub-cache/
        rsync -av .hub-cache/hub-repo/agents/ .hub-cache/agents/
        rsync -av .hub-cache/hub-repo/nuke/ .hub-cache/nuke/

        # Symlink .agent for backward compat
        ln -sf .hub-cache/agents .agent

        echo "✅ Hub sync complete"

  hub:check:
    desc: Verify hub cache is fresh
    cmds:
      - test -d .hub-cache/agents || (echo "❌ Run 'task hub:sync' first" && exit 1)
      - echo "✅ Hub cache present"
```

#### 6. Update .gitignore in lablab-bean (5 min)

```gitignore
# Hub-synced content (runtime only)
.hub-cache/
.agent           # Now a symlink
.nuke/Build.Common.cs  # If pulled from hub
```

#### 7. Set up Letta on Mac Mini (30 min)

```bash
# On Mac Mini
mkdir -p ~/ctx-hub
cd ~/ctx-hub

# Create docker-compose.yml (Phase 1 - Letta only)
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

# Create .env from SOPS (use your existing pattern)
sops decrypt ~/lunar-snake-hub/infra/secrets/mac-mini.enc.yaml > .env

# Start Letta
docker compose up -d

# Verify
curl http://localhost:5055/v1/health
```

#### 8. Test hub sync in lablab-bean (45 min)

```bash
# On Windows, in lablab-bean
task hub:sync

# Verify
ls -la .hub-cache/agents/
ls -la .agent  # Should be symlink

# Ask agent to read a rule
# "Read the naming conventions from agent rules"
# Agent should find it in .hub-cache/agents/rules/...

# Test Letta (add as MCP tool first - see below)
```

---

## 🔌 Configure Letta as MCP Tool (VS Code / Cline)

**Add to your MCP config:**

```json
{
  "mcpServers": {
    "letta": {
      "command": "node",
      "args": ["path/to/letta-mcp-adapter.js"],
      "env": {
        "LETTA_URL": "http://<mac-mini-tailscale-name>:5055"
      }
    }
  }
}
```

**Or use HTTP MCP tool directly:**

Tool spec:

```json
{
  "name": "letta_memory",
  "description": "Store and retrieve persistent agent memory",
  "input_schema": {
    "type": "object",
    "properties": {
      "op": {
        "type": "string",
        "enum": ["get", "put", "search"]
      },
      "key": {"type": "string"},
      "value": {"type": "object"}
    },
    "required": ["op"]
  },
  "endpoint": "http://<tailscale-name>:5055/v1/memory"
}
```

---

## ✅ Phase 1 Success Criteria

After 4 hours, you should have:

- [x] `lunar-snake-hub` repo created with initial structure
- [x] Agent rules extracted from `lablab-bean/.agent/` → hub
- [x] `lablab-bean` has `.hub-manifest.toml`
- [x] `task hub:sync` works (fetches rules to `.hub-cache/`)
- [x] `.agent/` in lablab-bean is now a symlink (gitignored)
- [x] Letta running on Mac Mini
- [x] Agent can read rules from synced cache
- [x] Agent can store/retrieve a decision via Letta

**Test:**

1. Open lablab-bean in VS Code
2. Run `task hub:sync`
3. Ask agent: "What are our naming conventions?" (should read from hub)
4. Ask agent to remember: "We decided to use Repository pattern for data access"
5. Restart IDE
6. Ask agent: "What pattern did we choose for data access?" (should recall from Letta)

---

## 🎯 Next: Phase 2 (Week 2)

**Only after Phase 1 works for a week:**

- [ ] Add Qdrant to Mac Mini
- [ ] Build Context Gateway (`/ask`, `/memory`, `/notes`)
- [ ] Index `lablab-bean` into Qdrant
- [ ] Test RAG: "Show me authentication examples"

---

## 📝 Decision Log for Reference

```yaml
# decisions.yml (save this in lunar-snake-hub/docs/)
project_name: lunar-snake

central_hub:
  name: lunar-snake-hub
  url: https://github.com/GiantCroissant-Lunar/lunar-snake-hub
  visibility: public

pilot_satellite:
  name: lablab-bean
  path: D:\lunar-snake\personal-work\yokan-projects\lablab-bean
  url: https://github.com/GiantCroissant-Lunar/lablab-bean
  reason: >
    Well-structured with .agent/, Taskfile.yml, specs/, .nuke/.
    Active development. Generalizing from Unity to .NET multi-target.

github:
  type: organization
  org_name: GiantCroissant-Lunar

llm:
  provider: glm
  model: glm-4.6
  plan: z.ai coding plan
  concurrency: 5
  api_base: https://open.bigmodel.cn/api/paas/v4

embeddings:
  provider: glm
  model: glm-embeddings

networking:
  method: tailscale
  status: installed_both_machines

ci_cd:
  self_hosted_runner: false
  strategy: github_public_runners
  hub_visibility: public

secrets:
  method: sops
  reference: C:\lunar-snake\personal-work\infra-projects\giantcroissant-lunar-ai\infra

build_tool:
  name: task
  file: Taskfile.yml

contract_tests:
  phase: 2
  rationale: Validate hub/satellite model first

agentic_development:
  goal: maximize_agentic_workflow
  exploring: bmad-method
  approach: specs + agent_rules + memory + rag

phase_1_start_date: 2025-10-30
phase_1_target_completion: 2025-11-06

additional_notes: |
  Using yearly naming (lunar-snake, lunar-horse, etc.)
  Focus on clean satellite repos (code-only on GitHub)
  Runtime sync from hub (no duplication)
  SOPS for encrypted secrets in repo
```

---

## 🚦 Ready to Start?

**You now have:**

- ✅ All decisions made
- ✅ Clear understanding of your current setup (`lablab-bean`)
- ✅ Concrete Phase 1 action plan (4 hours)
- ✅ Success criteria to validate
- ✅ Tech stack aligned with your preferences

**When you're ready:**

Option 1: **Start Phase 1 now**

```bash
# 1. Create lunar-snake-hub repo on GitHub
# 2. Come back here and say: "Let's start Phase 1"
# I'll guide you step-by-step
```

Option 2: **Wait for a good time block**

```bash
# Move these docs to safe location
# Schedule Phase 1 for next weekend
```

Option 3: **Ask questions first**

```bash
# Clarify anything before starting
```

---

**What would you like to do?** 🚀
