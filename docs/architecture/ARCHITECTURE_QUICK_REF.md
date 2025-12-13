---
doc_id: DOC-2025-00008
title: Architecture Quick Reference
doc_type: reference
status: active
canonical: true
created: 2025-10-30
tags: [architecture, quick-reference, commands, cheatsheet]
summary: Quick reference guide for architecture implementation - command cheatsheets and TL;DR
related: [DOC-2025-00007]
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# Architecture Quick Reference

## TL;DR for Implementation

**Full Documentation:** See `ARCHITECTURE_DISCUSSION.md`

---

## The Big Idea

**Problem:** Agent rules, NUKE builds, pre-commit hooks duplicated across repos. Context burns fast. No memory.

**Solution:** Central hub repo + satellite repos + Mac Mini "brain"

```
Central Hub (lunar-hub)          Mac Mini Brain              Satellite Repos
├─ specs/                   ┌──────────────────┐          ├─ src/ (code only)
├─ .agent/                  │  Context Gateway │          ├─ .hub-manifest.toml
├─ nuke/builds/             │  Letta (memory)  │          └─ tools/bootstrap-hub.sh
├─ precommit/hooks/         │  Qdrant (RAG)    │
└─ .github/workflows/       │  n8n (orchestr.) │          Runtime only (gitignored):
                            └──────────────────┘          └─ .hub-cache/ (synced)
```

---

## Key Decisions

### ✅ DO

- **Satellites:** Commit only code + `.hub-manifest.toml`
- **Central Hub:** Single source of truth for all shared assets
- **Runtime Sync:** Fetch packs at dev/CI time, never commit them
- **Mac Mini:** Run context services locally (Letta, Qdrant, Gateway)
- **Version Pin:** Satellites pin exact pack versions

### ❌ DON'T

- **Don't commit** `.hub-cache/`, `.agents/`, synced NUKE builds
- **Don't duplicate** agent rules, hooks, or builds
- **Don't use** git submodules (runtime sync instead)
- **Don't commit** hub assets to satellites (defeats the purpose)

---

## File Tree Cheat Sheet

### Central Hub (`lunar-hub`)

```
lunar-hub/
├── specs/{domain}/{version}/
│   ├── rfc.md
│   ├── adr.md
│   └── schema/
├── .agent/
│   ├── rules/
│   └── prompts/
├── nuke/
│   ├── Build.Common.cs
│   └── Build.Unity.cs
├── precommit/
│   └── hooks/
├── .github/workflows/
│   ├── dotnet-ci.yml (reusable)
│   └── hub-sync.yml
└── registry/
    ├── specs.toml
    └── satellites.json
```

### Satellite Repo

```
satellite-repo/
├── src/                         # YOUR CODE ONLY
├── .hub-manifest.toml           # Pins versions (15 lines)
├── tools/bootstrap-hub.sh       # Fetches packs (50 lines)
├── .gitignore                   # Ignores .hub-cache/
└── .pre-commit-config.yaml      # References hub

# Runtime only (NEVER COMMITTED):
.hub-cache/                      # ← Synced from hub
├── .agent/
├── nuke/
└── specs/
```

---

## Manifest Example

**`.hub-manifest.toml`** (the ONLY config file satellites commit):

```toml
[hub]
repo = "lunar-snake/lunar-hub"

[specs]
auth-api = "1.2.0"              # Which specs you implement

[packs]
nuke = "2.1.0"                   # NUKE build version
precommit = "2.3.0"              # Pre-commit hooks version
```

---

## Bootstrap Script

**`tools/bootstrap-hub.sh`** (fetches packs at runtime):

```bash
#!/usr/bin/env bash
set -euo pipefail
MANIFEST=".hub-manifest.toml"
CACHE=".hub-cache"

echo "✅ Hub assets synced to $CACHE"
```

**Run:**

- On setup: `make setup` or `./tools/bootstrap-hub.sh`
- In CI: First step before build
- IDE: VS Code `preLaunchTask`

---

## Mac Mini Setup

**`~/ctx-hub/docker-compose.yml`:**

```yaml
services:
  letta:
    image: ghcr.io/letta-ai/letta:latest
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL}
    volumes: ["./data:/data"]
    ports: ["5055:5055"]

  qdrant:
    image: qdrant/qdrant:latest
    volumes: ["./data/qdrant:/qdrant/storage"]
    ports: ["6333:6333"]

  gateway:
    build: ./gateway
    environment:
      - QDRANT_URL=http://qdrant:6333
      - LETTA_URL=http://letta:5055
      - GATEWAY_TOKEN=${GATEWAY_TOKEN}
    ports: ["5057:5057"]

  n8n:
    image: n8nio/n8n:latest
    ports: ["5678:5678"]
    volumes: ["./data/n8n:/home/node/.n8n"]
```

**Start:** `docker compose up -d`

---

## Context Gateway API

**Endpoints your IDE agents call:**

```typescript
POST /ask              // RAG: get relevant code chunks
{
  query: "How does auth work?",
  hints: ["src/auth", "docs/rfcs"],
  top_k: 5
}
→ { answer, chunks[], tokens_used }

POST /memory           // Persistent memory
{
  op: "put",
  key: "project/decision/auth-strategy",
  value: { decision: "JWT", rationale: "..." }
}

POST /notes            // Project notes
{
  op: "add",
  text: "Chose Strategy B for performance",
  tags: ["architecture", "2025-10-30"]
}

POST /reindex          // Rebuild index (GitHub Actions)
{
  repo: "auth-service",
  changed: ["src/Controller.cs"]
}
```

**URL:** `http://<mac-mini-tailscale-ip>:5057`
**Auth:** `Authorization: Bearer <GATEWAY_TOKEN>`

---

## Workflows

### Developer Flow

1. **Setup new project:**

   ```bash
   git clone <satellite-repo>
   ./tools/bootstrap-hub.sh
   ```

2. **Work:**
   - Agent reads rules from `.hub-cache/.agent/rules/`
   - Agent calls Gateway `/ask` for context (not full repo)
   - Agent calls Gateway `/memory` to save decisions

3. **Commit & push:**
   - Only code changes committed
   - `.hub-cache/` stays gitignored

4. **Mac Mini:**
   - n8n detects push → `git pull` → `/reindex`
   - Fresh context available immediately

### Hub Update Flow

1. **Update rule in `lunar-hub`:**

   ```bash
   cd lunar-hub
   vim .agent/rules/00-index.md
   git add . && git commit -m "Update naming rule"
   ```

2. **Push changes:**

   ```bash
   git push
   ```

3. **GitHub Actions:**
   - Builds shared assets
   - Satellites pull updates on next sync

4. **Satellites:**
   - Run `task hub:sync` to refresh `.hub-cache/.agent/`

---

## Phased Rollout

### Phase 1 (Week 1): Foundation

- ✅ Create `lunar-hub`
- ✅ Move NUKE + agent rules
- ✅ Set up Letta (memory)
- ✅ Test with 1 satellite

**Result:** Zero duplication, persistent memory

### Phase 2 (Week 2): Context

- ✅ Add Qdrant + Context Gateway
- ✅ Index repos for RAG
- ✅ IDE agents use `/ask`

**Result:** Context burn solved

### Phase 3 (Week 3): Orchestration

- ✅ Set up n8n
- ✅ GitHub webhooks → auto-reindex
- ✅ Scheduled fallbacks

**Result:** Fully automated

### Phase 4 (Week 4+): Scale

- ✅ Migrate all satellites
- ✅ Version bump automation
- ✅ Contract tests

**Result:** Multi-repo ecosystem

---

## Naming Conventions

### Tags

```
packs-{type}-v{semver}        # packs-nuke-v2.1.0
spec-{name}-v{semver}         # spec-auth-api-v1.2.0
v{major}                      # v1 (for workflows)
```

### Agent Rules

```
R-{CATEGORY}-{NUMBER}-{desc}.md

R-CODE-010-naming.md          # Code rules
R-DOC-030-comments.md         # Doc rules
R-NUKE-001-builds.md          # Build rules
R-PRC-020-pr-format.md        # Process rules
```

---

## Tech Stack Summary

| Component | Technology | Location |
|-----------|-----------|----------|
| LLM | GLM-4.6 (Zhipu) | Cloud (BYOK) |
| IDE Agents | Cline, Roo, Kilo | Windows |
| Memory | Letta | Mac Mini |
| Vector DB | Qdrant | Mac Mini |
| API Gateway | FastAPI | Mac Mini |
| Orchestration | n8n | Mac Mini |
| Builds | NUKE (C#) | Central Hub |
| Hooks | Pre-commit | Central Hub |
| CI | GitHub Actions | GitHub + Mac runner |
| Network | Tailscale | VPN |

---

## Open Questions (Before Phase 1)

1. **Hub name?** `lunar-hub`, `dev-nexus`, or other?
2. **Pilot satellite?** Which repo to start with?
3. **GitHub org?** Create org or use personal account?
4. **Embeddings?** GLM embeddings or OpenAI?
5. **Networking?** Tailscale or static IP?

---

## Next Action

**Choose one:**

- **Option A:** Start Phase 1 (create hub + migrate 1 satellite)
- **Option B:** Set up Mac Mini infrastructure first
- **Option C:** Think through and finalize naming/structure

**Recommended:** Review full doc, decide on hub name, pick pilot satellite → start Phase 1.

---

**Full Documentation:** `ARCHITECTURE_DISCUSSION.md` (16,000 words)
**Status:** Design complete, ready to implement
**Owner:** lunar-snake
**Date:** 2025-10-30
