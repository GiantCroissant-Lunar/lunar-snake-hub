---
doc_id: DOC-2025-00023
title: Phase 1-3 Hardening Plan
doc_type: implementation-plan
status: active
canonical: true
created: 2025-10-31
tags: [hardening, phase1, phase2, phase3, production-ready]
summary: Focused plan to complete and harden Phase 1-3 for production use, ignoring Phase 4-6 over-engineering
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# Phase 1-3 Hardening Plan

**Mission:** Complete and harden the core lunar-snake-hub system (Phase 1-3) to production-ready state, delivering the original vision without over-engineering.

**Date:** 2025-10-31
**Status:** READY TO EXECUTE
**Timeline:** 2 weeks total

---

## 🎯 Core Principles

### What We're Building

**Phase 1:** Hub sync + Memory (Letta) - **STOP DUPLICATION**
**Phase 2:** RAG (Qdrant + Gateway) - **FIX CONTEXT BURN**
**Phase 3:** Automation (n8n + webhooks) - **AUTOMATE WORKFLOW**

### What We're NOT Building

- ❌ Multi-modal tools (images, audio, video)
- ❌ Workflow composition engines
- ❌ Plugin marketplaces
- ❌ Advanced ML pipelines
- ❌ Full web applications
- ❌ Kubernetes orchestration

**Why?** These are Phase 4-6 features for building a product. You're building a personal development tool.

---

## 📋 PHASE 1: COMPLETION & VALIDATION

**Current Status:** 87% Complete (7/8 tasks done)
**Remaining:** Testing and validation
**Timeline:** 2-3 days

### Task 1.1: Complete Phase 1 Testing ⏰ 2-3 hours

**What to do:**

1. **Test Hub Sync** (15 min)

   ```bash
   cd lablab-bean
   task hub:clean
   task hub:sync
   task hub:check
   ```

   ✅ Verify: 15 agent files + 1 NUKE file synced

2. **Test Agent Reads Hub Rules** (30 min)
   - Open lablab-bean in VS Code
   - Ask Cline: "What are our naming conventions?"
   - ✅ Verify: Agent quotes from `.hub-cache/agents/rules/`

3. **Test Rule Updates** (30 min)
   - Edit a rule in `lunar-snake-hub/agents/rules/20-rules.md`
   - Commit and push
   - In lablab-bean: `task hub:sync`
   - Ask agent to read updated rule
   - ✅ Verify: Agent sees new version

4. **Test Letta Memory** (1 hour)
   - Ask agent: "Remember: We use Repository pattern for data access"
   - Restart VS Code completely
   - Ask: "What pattern do we use for data access?"
   - ✅ Verify: Agent recalls from Letta

5. **Commit Changes** (15 min)

   ```bash
   cd lablab-bean
   git add .hub-manifest.toml Taskfile.yml .gitignore
   git commit -m "feat: integrate lunar-snake-hub runtime sync"
   git push
   ```

**Success Criteria:**

- ✅ Hub sync working reliably
- ✅ Agent reads from hub (not local copies)
- ✅ Memory persists across sessions
- ✅ No duplication in git

---

### Task 1.2: Use Phase 1 for Real Work ⏰ 1 week

**Purpose:** Validate Phase 1 in real-world usage before building Phase 2

**What to do:**

1. Work on lablab-bean normally for 5-7 days
2. Track these metrics:
   - How often do you run `hub:sync`? (should be automatic in pre-commit)
   - Does agent memory actually help?
   - Is context still burning? (loading full repos?)
3. Document pain points

**Decision Point:** After 1 week, decide if Phase 2 (RAG) is needed

**Possible Outcomes:**

- **Context burn is bad** → Proceed to Phase 2
- **Context is fine** → Skip to Phase 3 (automation)
- **Memory not working** → Fix Phase 1 first

---

### Task 1.3: Clean Up Phase 4-6 Code ⏰ 30 min

**Remove unnecessary code that was prematurely generated:**

```bash
cd lunar-snake-hub

# Delete Phase 4-6 generated code
rm -rf infra/docker/mcp-server/tools/

# Keep only what exists in Phase 1-3:
# - infra/docker/mcp-server/mcp_server.py (Phase 2 - simple proxy)
# - infra/docker/gateway/ (Phase 2 - to be built)
# - infra/docker/docker-compose.yml (Phase 1-3)

# Commit cleanup
git add -A
git commit -m "chore: remove Phase 4-6 over-engineering

- Remove multi-modal tools (image/audio processing)
- Remove workflow composition engine
- Remove tool SDK framework
- Keep focus on Phase 1-3: Hub sync, RAG, and automation"
git push
```

**Files to DELETE:**

- `infra/docker/mcp-server/tools/` (entire directory)
- Phase 4-6 completion summaries (keep implementation plans for reference)

**Files to KEEP:**

- Phase 1-3 implementation plans
- Phase 1 progress docs
- All original architecture docs

---

## 📋 PHASE 2: CONTEXT SERVER & RAG

**Prerequisite:** Phase 1 validated AND context burn confirmed as problem
**Timeline:** 5 days
**Skip if:** Phase 1 solves context issues

### Task 2.1: Qdrant Setup ⏰ 2 hours

**Add to docker-compose.yml:**

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"   # REST API
      - "6334:6334"   # gRPC
    volumes:
      - ./data/qdrant:/qdrant/storage
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Validation:**

```bash
# On Mac Mini
curl http://localhost:6333/collections
# Should return: {"result":{"collections":[]}}
```

---

### Task 2.2: Context Gateway Service ⏰ 2 days

**Build minimal FastAPI service:**

**Directory structure:**

```
infra/docker/gateway/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── main.py          # FastAPI app
│   ├── config.py        # Environment config
│   ├── routers/
│   │   ├── ask.py       # POST /ask - RAG
│   │   ├── search.py    # POST /search - vector search
│   │   ├── memory.py    # POST /memory - Letta proxy
│   │   └── notes.py     # POST /notes - simple notes
│   └── services/
│       ├── qdrant.py    # Qdrant client
│       ├── letta.py     # Letta client
│       └── embeddings.py # GLM-4.6 embeddings
```

**Core endpoints (keep it simple):**

1. **POST /ask** - RAG query

   ```python
   # 1. Embed query with GLM-4.6
   # 2. Search Qdrant (top 5 chunks)
   # 3. Build context from chunks
   # 4. Ask GLM-4.6 with context
   # 5. Return answer + citations
   ```

2. **POST /search** - Vector search only (no LLM)

   ```python
   # 1. Embed query
   # 2. Search Qdrant
   # 3. Return chunks with scores
   ```

3. **POST /memory** - Proxy to Letta

   ```python
   # Just forward to Letta service
   ```

4. **POST /notes** - Simple file-based notes

   ```python
   # Store in ./data/notes/{repo}/notes.json
   ```

**Keep it under 500 lines total**

---

### Task 2.3: Repository Indexing ⏰ 1 day

**Simple indexing script:**

```python
# infra/docker/gateway/app/indexer.py

async def index_repository(repo_path: str, collection_name: str):
    """Index repository into Qdrant"""

    # 1. Discover files (*.py, *.cs, *.md, *.yml)
    files = discover_files(repo_path)

    # 2. Chunk files
    #    - Code: by function/class (simple regex)
    #    - Markdown: by section (## headers)
    #    - Config: whole file
    chunks = []
    for file in files:
        chunks.extend(chunk_file(file))

    # 3. Generate embeddings (batch)
    embeddings = await generate_embeddings([c.content for c in chunks])

    # 4. Upload to Qdrant
    await qdrant.upsert(
        collection_name=collection_name,
        points=[{
            "id": chunk.id,
            "vector": embedding,
            "payload": {
                "content": chunk.content,
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "language": chunk.language,
            }
        } for chunk, embedding in zip(chunks, embeddings)]
    )
```

**No fancy ML needed - keep it simple!**

---

### Task 2.4: MCP Integration ⏰ 4 hours

**The MCP server is already built!** (`mcp_server.py` - 502 lines)

Just needs:

1. **Environment variables** in `.cline/mcp_settings.json`:

   ```json
   {
     "mcpServers": {
       "context-gateway": {
         "command": "docker",
         "args": ["exec", "context-gateway", "python", "mcp_server.py"],
         "env": {
           "GATEWAY_URL": "http://gateway:5057",
           "GATEWAY_TOKEN": "your-secure-token"
         }
       }
     }
   }
   ```

2. **Gateway running** with endpoints implemented

3. **Test** by asking agent: "Search for authentication code"

---

### Task 2.5: Validation ⏰ 4 hours

**Test scenarios:**

1. **Token Usage Test**
   - Baseline: Ask agent about full repo context
   - With RAG: Ask same question
   - ✅ Verify: >50% token reduction

2. **Citation Test**
   - Ask: "Where is the AuthController defined?"
   - ✅ Verify: Response includes `src/Auth/Controllers/AuthController.cs:42-89`

3. **Relevance Test**
   - Ask 10 different questions
   - ✅ Verify: Top 5 chunks are actually relevant

4. **Performance Test**
   - Measure query response time
   - ✅ Verify: <2 seconds

**Success Criteria:**

- ✅ Token usage reduced significantly
- ✅ Answers include accurate citations
- ✅ Response time acceptable
- ✅ Agent workflow improved

---

## 📋 PHASE 3: AUTOMATION & ORCHESTRATION

**Prerequisite:** Phase 2 working reliably
**Timeline:** 3-4 days
**Purpose:** Automate the manual workflows

### Task 3.1: n8n Setup ⏰ 2 hours

**Add to docker-compose.yml:**

```yaml
services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    environment:
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
    ports:
      - "5678:5678"
    volumes:
      - ./data/n8n:/home/node/.n8n
    restart: unless-stopped
```

**Access:** <http://mac-mini:5678>

---

### Task 3.2: Webhook Workflows ⏰ 1 day

**Workflow 1: Repo Updated (GitHub Webhook)**

```
GitHub Push Event
  ↓
[Webhook Trigger] /webhook/github/push
  ↓
[Verify Signature] HMAC validation
  ↓
[Execute Shell] cd ~/repos/{repo} && git pull --ff-only
  ↓
[HTTP Request] POST http://gateway:5057/reindex
  ↓
[Slack Notify] "✅ Indexed {repo}@{sha}" (if error: alert)
```

**Configure GitHub webhook:**

- URL: `http://<tailscale-mac-mini>:5678/webhook/github/push`
- Secret: Store in SOPS
- Events: `push`

---

**Workflow 2: Scheduled Sync (Fallback)**

```
[Cron Trigger] */10 * * * * (every 10 minutes)
  ↓
[Loop: Each repo]
  ↓
[Execute Shell] git fetch && git status -sb
  ↓
[If: Behind remote]
  ↓
[Execute Shell] git pull --ff-only
  ↓
[HTTP Request] POST /reindex
```

**Purpose:** Catch missed webhooks

---

### Task 3.3: Auto Hub Sync ⏰ 2 hours

**Update lablab-bean's Taskfile.yml:**

```yaml
tasks:
  # Add automatic sync before build
  build:
    deps: [hub:sync]  # Sync before building
    cmds:
      - nuke

  # Add sync to pre-commit
  pre-commit:
    cmds:
      - task hub:sync --silent
      - pre-commit run --all-files
```

**Result:** Hub always fresh before builds

---

### Task 3.4: Validation ⏰ 2 hours

**Test scenarios:**

1. **Webhook Test**
   - Push to lunar-snake-hub
   - ✅ Verify: n8n triggers within 30 seconds
   - ✅ Verify: Mac Mini pulls repo
   - ✅ Verify: Reindex completes

2. **Fallback Test**
   - Disable webhook temporarily
   - Wait 10 minutes
   - ✅ Verify: Cron catches the update

3. **Auto Sync Test**
   - Edit hub rule
   - Push to hub
   - Run `task build` in lablab-bean
   - ✅ Verify: Gets latest rules automatically

**Success Criteria:**

- ✅ Webhook triggers reliably
- ✅ Fallback cron works
- ✅ Auto-sync seamless
- ✅ No manual sync needed

---

## 🎯 Phase 1-3 Complete - Success Metrics

After completing all three phases, you should have:

### Functional Outcomes

✅ **No Duplication**

- Agent rules in one place (hub)
- NUKE components shared
- Zero drift between projects

✅ **Memory Persists**

- Decisions remembered across sessions
- No "agent amnesia"
- Context accumulates

✅ **Context Efficient** (if Phase 2 implemented)

- 50%+ token reduction
- Faster agent responses
- Answers include citations

✅ **Automated Workflow**

- Repos sync automatically
- Reindexing on push
- No manual maintenance

### Non-Functional Outcomes

✅ **Maintainable**

- Simple codebase (<2000 lines total)
- Clear separation of concerns
- Easy to debug

✅ **Reliable**

- Fallback mechanisms
- Health checks
- Clear error messages

✅ **Extensible**

- Easy to add new satellites
- Easy to add new tools
- Easy to modify rules

---

## 🔧 Technology Stack Summary

### Phase 1

- **Hub:** Git repo (lunar-snake-hub)
- **Sync:** Task runner + bash/powershell
- **Memory:** Letta (Docker container)
- **MCP:** Letta MCP client

### Phase 2 (if needed)

- **Vector DB:** Qdrant
- **Gateway:** FastAPI (Python)
- **Embeddings:** GLM-4.6 API
- **MCP:** Custom server (already built)

### Phase 3

- **Orchestration:** n8n
- **Webhooks:** GitHub → n8n
- **Automation:** Shell scripts + HTTP calls

**Total Services:** 4-5 Docker containers
**Total Code:** ~1500-2000 lines
**Complexity:** LOW (no ML frameworks, no complex abstractions)

---

## 📋 Cleanup Checklist

### Delete These Files

- [ ] `infra/docker/mcp-server/tools/` (entire directory)
- [ ] `docs/sessions/PHASE4_COMPLETION_SUMMARY.md`
- [ ] `docs/sessions/PHASE5_COMPLETION_SUMMARY.md`
- [ ] Any other Phase 4-6 generated artifacts

### Keep These Files

- [ ] All Phase 1-3 implementation plans
- [ ] `PHASE1_PROGRESS.md`
- [ ] `ARCHITECTURE_DISCUSSION.md`
- [ ] Current working `mcp_server.py`
- [ ] Docker compose configurations

### Document Status

- [ ] Update README to reflect Phase 1-3 focus
- [ ] Mark Phase 4-6 plans as "Future/Optional"
- [ ] Create this hardening plan as canonical Phase 1-3 guide

---

## 🚀 Execution Plan

### Week 1: Phase 1 Completion

- **Day 1-2:** Complete Phase 1 testing (Task 1.1)
- **Day 3:** Clean up Phase 4-6 code (Task 1.3)
- **Day 4-7:** Use Phase 1 in real work (Task 1.2)

### Week 2: Phase 2/3 (if needed)

- **Day 1-2:** Decide if Phase 2 needed based on Week 1 usage
- **Day 3-7:** Either:
  - Implement Phase 2 (if context burn confirmed)
  - OR skip to Phase 3 (if Phase 1 sufficient)

### Decision Points

**After Week 1:**

- Is context burning?
  - YES → Implement Phase 2
  - NO → Skip to Phase 3

**After Week 2:**

- Is manual sync annoying?
  - YES → Implement Phase 3
  - NO → Done! Just use Phase 1-2

---

## 🎯 Final Validation

You're done when:

1. ✅ **Satellites are clean** - Only code in git, no agent rules
2. ✅ **Memory works** - Agent remembers across sessions
3. ✅ **Context efficient** - Not loading full repos (if Phase 2)
4. ✅ **Workflow smooth** - Minimal manual intervention
5. ✅ **You're productive** - System helps, doesn't hinder

**Then:** Use it for 3-6 months before considering Phase 4+

---

## 📝 Why This Plan Works

### Based on Original Vision

- Solves the 3 core pain points (duplication, context, memory)
- Follows original phased approach
- Stops before over-engineering

### Pragmatic Scope

- Simple tools, not frameworks
- Direct implementations, not abstractions
- Focus on usage, not features

### Maintainable

- Small codebase
- Clear boundaries
- Easy to understand

### Validates Incrementally

- Phase 1 proves hub model
- Phase 2 only if needed
- Phase 3 only if helpful

---

**Status:** READY TO EXECUTE
**Timeline:** 2 weeks
**Next Action:** Complete Phase 1 testing (Task 1.1)
**Questions?** Review original `ARCHITECTURE_DISCUSSION.md`

---

*This hardening plan supersedes Phase 4-6 implementation plans.*
*Focus: Deliver the original vision without scope creep.*
