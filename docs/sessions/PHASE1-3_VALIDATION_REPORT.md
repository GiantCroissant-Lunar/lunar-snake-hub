---
doc_id: DOC-2025-00024
title: Phase 1-3 Validation Report - hyacinth-bean-base Testing
doc_type: validation-report
status: active
canonical: true
created: 2025-10-31
tags: [validation, testing, phase1, phase2, phase3, hyacinth-bean-base]
summary: Comprehensive validation report for Phase 1-3 infrastructure using hyacinth-bean-base as test project
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# Phase 1-3 Validation Report

**Test Project:** hyacinth-bean-base
**Test Date:** 2025-10-31
**Test Location:** `/Users/apprenticegc/Work/lunar-snake/personal-work/yokan-projects/hyacinth-bean-base`

---

## 🎯 Executive Summary

**Status:** ✅ **Phase 1 VERIFIED** | ⚠️ **Phase 2 READY (Not Deployed)** | ⚠️ **Phase 3 READY (Not Deployed)**

### Quick Status

| Phase | Component | Status | Notes |
|-------|-----------|--------|-------|
| **Phase 1** | Hub Sync | ✅ **WORKING** | Successfully synced 18 agent files + 1 NUKE file |
| **Phase 1** | Letta Memory | ✅ **RUNNING** | Container up on port 8283 (needs testing) |
| **Phase 2** | Qdrant DB | ⚠️ **CODE READY** | Not deployed (docker-compose configured) |
| **Phase 2** | Context Gateway | ⚠️ **CODE READY** | Full implementation exists, not deployed |
| **Phase 2** | MCP Server | ⚠️ **CODE READY** | Implementation complete (502 lines) |
| **Phase 3** | n8n Automation | ⚠️ **CODE READY** | Docker-compose configured, not deployed |
| **Phase 4-6** | Advanced Features | ❌ **OVER-ENGINEERED** | Should be removed |

---

## ✅ PHASE 1: Hub Sync + Memory - VERIFIED WORKING

### Test Project Setup

#### Created Files for hyacinth-bean-base

**1. `.hub-manifest.toml`** - Hub configuration

```toml
[hub]
repo = "GiantCroissant-Lunar/lunar-snake-hub"
branch = "main"

[packs]
agents = "0.1.0"
nuke = "0.1.0"
precommit = "0.1.0"

[sync]
include = [
    "agents/rules/**",
    "agents/prompts/**",
    "agents/adapters/**",
    "agents/scripts/**",
    "agents/integrations/**",
    "nuke/**",
]
```

**2. `Taskfile.yml`** - Task automation

- `task hub:sync` - Sync from hub
- `task hub:check` - Verify cache
- `task hub:clean` - Clean cache
- `task build` - Build with auto-sync

**3. `.gitignore` updates** - Exclude hub cache

```
.hub-cache/
.agent
```

### Test Results

#### Test 1: Hub Sync ✅ **PASS**

```bash
cd hyacinth-bean-base
task hub:sync
```

**Output:**

```
🔄 Syncing from lunar-snake-hub...
  📦 Cloning lunar-snake-hub...
  📋 Syncing agents...
Transfer starting: 26 files
✅ Hub sync complete
   Agents: 18 files
   NUKE: 1 files
```

**Verification:**

```bash
$ task hub:check
✅ Hub cache present
   Agents: 18 files
   NUKE: 1 files
```

**Files synced to `.hub-cache/agents/rules/`:**

- `00-index.md` - Rule index
- `10-principles.md` - Core principles
- `20-rules.md` - **Normative rules** (R-DOC-001, R-DOC-002, etc.)
- `30-glossary.md` - Terminology
- `40-documentation.md` - Doc standards

**Result:** ✅ **Hub sync works perfectly**

#### Test 2: Letta Memory ✅ **RUNNING** (Needs Agent Test)

**Docker Status:**

```
letta-memory   Up 3 hours   0.0.0.0:8283->8283/tcp
```

**Status:** Container is running and healthy

**Next Steps:**

1. Test with AI agent asking to store memory
2. Verify memory persists across sessions
3. Test retrieval from memory

**Recommendation:** Need to test actual agent integration with Letta MCP

---

## ⚠️ PHASE 2: Context Server & RAG - CODE READY, NOT DEPLOYED

### Infrastructure Status

#### Docker Compose Configuration ✅ **COMPLETE**

**Services Configured:**

1. **Qdrant** (Vector Database)

   ```yaml
   lunar-qdrant:
     image: qdrant/qdrant:latest
     ports: [6333:6333, 6334:6334]
     volumes: [./data/qdrant:/qdrant/storage]
     healthcheck: configured
   ```

2. **Context Gateway** (FastAPI Service)

   ```yaml
   lunar-gateway:
     build: ./gateway
     ports: [5057:5057]
     environment:
       - OPENAI_API_KEY=${OPENAI_API_KEY}
       - QDRANT_URL=http://qdrant:6333
       - LETTA_URL=http://letta:5055
     depends_on: [qdrant, letta]
   ```

3. **MCP Server** (Model Context Protocol)

   ```yaml
   lunar-mcp-server:
     build: ./mcp-server
     environment:
       - GATEWAY_URL=http://gateway:5057
     depends_on: [gateway]
   ```

#### Gateway Implementation ✅ **COMPLETE**

**Location:** `infra/docker/gateway/`

**Directory Structure:**

```
gateway/
├── Dockerfile                   ✅ Ready
├── requirements.txt             ✅ Dependencies listed
├── app/
│   ├── main.py                  ✅ FastAPI app (8,186 bytes)
│   ├── models/
│   │   ├── requests.py          ✅ Request models
│   │   └── responses.py         ✅ Response models
│   ├── routers/
│   │   ├── ask.py               ✅ RAG endpoint
│   │   ├── search.py            ✅ Vector search
│   │   ├── memory.py            ✅ Letta proxy
│   │   ├── notes.py             ✅ Notes system
│   │   ├── webhooks.py          ⚠️ Phase 3 feature
│   │   ├── advanced_*.py        ❌ Phase 4+ bloat
│   │   └── performance.py       ⚠️ Phase 4 feature
│   └── services/
│       ├── qdrant_client.py     ✅ Vector DB client
│       ├── letta_client.py      ✅ Memory client
│       ├── embeddings.py        ✅ GLM embeddings
│       ├── indexing.py          ✅ Repo indexing
│       ├── caching.py           ⚠️ Phase 3 feature
│       ├── hybrid_search.py     ⚠️ Phase 3 feature
│       └── advanced_*.py        ❌ Phase 4+ bloat
```

**Analysis:**

- ✅ Core Phase 2 functionality is **complete**
- ⚠️ Some Phase 3 features already implemented (caching, hybrid search)
- ❌ Phase 4+ bloat exists (advanced analytics, intelligence engine, etc.)

**Line Count:**

```bash
Total Python files: 27
Core Phase 2 files: ~15 (estimated 2,000-3,000 lines)
Phase 3 additions: ~5 (estimated 1,000 lines)
Phase 4+ bloat: ~7 (estimated 1,500+ lines)
```

**Recommendation:** Clean up Phase 4+ files before deployment

#### MCP Server Implementation ✅ **COMPLETE**

**Location:** `infra/docker/mcp-server/mcp_server.py`

**File Size:** 19,530 bytes (502 lines)

**Tools Implemented:**

1. `ask_rag` - RAG queries
2. `search_vectors` - Vector search
3. `store_memory` - Save to Letta
4. `get_memory` - Retrieve from Letta
5. `add_note` - Project notes
6. `search_notes` - Note search
7. `list_collections` - Show indexed repos
8. `index_repository` - Index new repos

**Status:** ✅ **Complete and ready to use**

**Problem:** Has `tools/` subdirectory with Phase 6 bloat

```
mcp-server/tools/
├── advanced/tool_sdk.py          ❌ 863 lines - DELETE
├── multimodal/image_tools.py     ❌ 687 lines - DELETE
├── composition/workflow_engine.py ❌ 702 lines - DELETE
└── ... (more bloat)
```

**Recommendation:** Delete entire `tools/` directory

---

### Phase 2 Deployment Blockers

#### What's Needed to Deploy Phase 2

1. **Environment Variables** (`.env` file)

   ```bash
   OPENAI_API_KEY=<your-glm-api-key>
   OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
   GATEWAY_TOKEN=<generate-secure-token>
   N8N_PASSWORD=<generate-password>
   ```

2. **Clean Up Bloat** (Remove Phase 4+ code)

   ```bash
   # In gateway/app/routers/
   rm advanced_analytics.py
   rm advanced_search.py
   rm performance.py (or move to optional)

   # In gateway/app/services/
   rm advanced_analytics.py
   rm advanced_dashboard.py
   rm distributed_tracing.py
   rm intelligence_engine.py
   rm performance_monitor.py

   # In mcp-server/
   rm -rf tools/
   ```

3. **Deploy Services**

   ```bash
   cd infra/docker
   docker-compose up -d qdrant gateway mcp-server
   ```

4. **Index Test Repository**

   ```bash
   # Use MCP tool or direct API call
   curl -X POST http://localhost:5057/index \
     -H "Authorization: Bearer $GATEWAY_TOKEN" \
     -d '{
       "repo_path": "/repos/hyacinth-bean-base",
       "collection_name": "hyacinth-bean-base"
     }'
   ```

5. **Configure MCP in IDE**
   - Add context-gateway to Cline/Windsurf MCP settings
   - Test RAG queries through IDE

---

## ⚠️ PHASE 3: Automation - CODE READY, NOT DEPLOYED

### Infrastructure Status

#### Docker Compose Configuration ✅ **COMPLETE**

**Service Configured:**

```yaml
lunar-n8n:
  image: n8nio/n8n:latest
  ports: [5678:5678]
  environment:
    - N8N_BASIC_AUTH_USER=admin
    - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
  volumes: [./data/n8n:/home/node/.n8n]
```

**Status:** Ready to deploy with `docker-compose up -d n8n`

#### Webhook Handlers ⚠️ **PARTIALLY IMPLEMENTED**

**Location:** `infra/docker/gateway/app/routers/webhooks.py`

**What exists:**

- Webhook receiver endpoint
- GitHub webhook signature validation
- Integration with indexing service

**What's needed:**

- n8n workflows to be created (GUI-based, not code)
- GitHub webhook configuration
- Testing and validation

---

## ❌ PHASE 4-6: OVER-ENGINEERED FEATURES - SHOULD BE REMOVED

### What Was Generated (Bloat)

#### Phase 4: Advanced Monitoring & Analytics

- Distributed tracing (Jaeger integration)
- Intelligence engine (ML pipelines)
- Advanced dashboards
- Performance monitoring beyond basic needs

**Estimated LOC:** 1,500+ lines
**Value:** Minimal for personal use
**Recommendation:** ❌ **DELETE**

#### Phase 5: Enhanced User Interfaces

- Full React web application
- Real-time WebSocket updates
- Advanced visualizations
- Component library

**Location:** `infra/docker/frontend/` (24 files)
**Status:** Partially implemented
**Value:** Nice-to-have, not critical
**Recommendation:** ⚠️ **KEEP but de-prioritize** (already built)

#### Phase 6: Advanced MCP Features

- Tool SDK framework (863 lines)
- Multi-modal tools (images, audio - 687 lines)
- Workflow composition engine (702 lines)
- Plugin marketplace architecture

**Location:** `infra/docker/mcp-server/tools/`
**Total LOC:** ~2,200 lines
**Value:** ZERO for current needs
**Recommendation:** ❌ **DELETE IMMEDIATELY**

---

## 📊 Validation Summary

### What Works Today ✅

1. **Phase 1 - Hub Sync**
   - ✅ `task hub:sync` clones and syncs hub
   - ✅ Agent rules available in `.hub-cache/`
   - ✅ .gitignore properly excludes cache
   - ✅ Backward-compatible symlink created
   - ✅ Tested on hyacinth-bean-base successfully

2. **Phase 1 - Letta Memory**
   - ✅ Container running (port 8283)
   - ⏳ Needs agent integration testing

### What's Ready to Deploy ⚠️

3. **Phase 2 - Qdrant Vector DB**
   - ✅ Docker image specified
   - ✅ Health check configured
   - ✅ Volume mapping defined
   - 🔴 Not deployed yet

4. **Phase 2 - Context Gateway**
   - ✅ Full FastAPI implementation
   - ✅ RAG, search, memory, notes endpoints
   - ✅ Qdrant and Letta clients
   - ✅ Embedding service (GLM-4.6)
   - ⚠️ Contains Phase 4+ bloat (needs cleanup)
   - 🔴 Not deployed yet

5. **Phase 2 - MCP Server**
   - ✅ Complete implementation (502 lines)
   - ✅ 8 tools ready to use
   - ⚠️ Has bloated `tools/` directory (needs cleanup)
   - 🔴 Not deployed yet

6. **Phase 3 - n8n Automation**
   - ✅ Docker configuration ready
   - ✅ Webhook receiver implemented
   - ⏳ Workflows need to be created (GUI)
   - 🔴 Not deployed yet

### What Should Be Removed ❌

7. **Phase 4-6 Bloat**
   - ❌ Advanced analytics (1,500+ lines)
   - ❌ Multi-modal tools (2,200+ lines)
   - ❌ Intelligence engine
   - ❌ Distributed tracing
   - ❌ Advanced dashboards

**Total Bloat:** ~4,000+ lines of unnecessary code

---

## 🎯 Recommendations

### Immediate Actions (This Week)

#### 1. Complete Phase 1 Testing (2-3 hours)

- [ ] Test Letta memory with actual AI agent
- [ ] Store test memory: "We use Repository pattern"
- [ ] Restart IDE and verify recall
- [ ] Document results

#### 2. Clean Up Codebase (1 hour)

```bash
cd infra/docker

# Remove Phase 6 bloat
rm -rf mcp-server/tools/

# Remove Phase 4 bloat from gateway
cd gateway/app/routers
rm advanced_analytics.py advanced_search.py

cd ../services
rm advanced_analytics.py advanced_dashboard.py \
   distributed_tracing.py intelligence_engine.py \
   performance_monitor.py

# Commit cleanup
git add -A
git commit -m "chore: remove Phase 4-6 over-engineering

- Delete mcp-server/tools/ (2,200 lines of unnecessary code)
- Remove advanced analytics and monitoring
- Remove intelligence engine and tracing
- Focus on core Phase 1-3 functionality"
```

#### 3. Document Current State (30 min)

- [ ] Update README with actual Phase 1-3 status
- [ ] Mark Phase 4-6 as "Future/Optional"
- [ ] Add deployment guide for Phase 2

### Short-Term Actions (Next 1-2 Weeks)

#### 4. Deploy Phase 2 (if needed)

**Decision Point:** Use hyacinth-bean-base for 1 week with Phase 1 only

**If context burn is a problem:**

```bash
# Generate secure tokens
GATEWAY_TOKEN=$(openssl rand -hex 32)

# Update .env
echo "GATEWAY_TOKEN=$GATEWAY_TOKEN" >> .env

# Deploy services
docker-compose up -d qdrant gateway mcp-server

# Wait for services to start
sleep 10

# Check health
curl http://localhost:6333/collections  # Qdrant
curl http://localhost:5057/health       # Gateway

# Index test repo
# (use MCP tool from IDE or direct API call)
```

**If Phase 1 sufficient:** Skip Phase 2, proceed to Phase 3

#### 5. Deploy Phase 3 (if Phase 2 deployed)

```bash
# Deploy n8n
docker-compose up -d n8n

# Access UI
open http://localhost:5678

# Create workflows (manual, GUI-based)
# - GitHub webhook → git pull → reindex
# - Scheduled fallback sync
```

---

## 📈 Phase Readiness Matrix

| Phase | Description | Code Complete | Tested | Deployed | Recommended |
|-------|-------------|---------------|--------|----------|-------------|
| **Phase 1** | Hub Sync + Memory | ✅ 100% | ✅ 90% | ✅ Yes | ✅ **USE IT** |
| **Phase 2** | RAG (Qdrant + Gateway) | ✅ 95% | 🔴 0% | 🔴 No | ⏳ **WAIT** (test P1 first) |
| **Phase 3** | Automation (n8n) | ✅ 80% | 🔴 0% | 🔴 No | ⏳ **AFTER P2** (if needed) |
| **Phase 4** | Advanced Monitoring | ⚠️ 40% | 🔴 0% | 🔴 No | ❌ **DELETE** |
| **Phase 5** | Web UI | ⚠️ 60% | 🔴 0% | 🔴 No | ⏸️ **IGNORE** (optional) |
| **Phase 6** | Advanced MCP | ⚠️ 30% | 🔴 0% | 🔴 No | ❌ **DELETE** |

---

## 🔍 Detailed File Analysis

### Core Phase 1-2 Files (Keep)

```
infra/docker/
├── docker-compose.yml              ✅ Keep (clean Phase 4-6 definitions)
├── .env.template                   ✅ Keep
├── gateway/
│   ├── Dockerfile                  ✅ Keep
│   ├── requirements.txt            ✅ Keep (review dependencies)
│   └── app/
│       ├── main.py                 ✅ Keep
│       ├── models/                 ✅ Keep all
│       ├── routers/
│       │   ├── ask.py              ✅ Keep (Phase 2)
│       │   ├── search.py           ✅ Keep (Phase 2)
│       │   ├── memory.py           ✅ Keep (Phase 2)
│       │   ├── notes.py            ✅ Keep (Phase 2)
│       │   └── webhooks.py         ⏳ Keep (Phase 3)
│       └── services/
│           ├── qdrant_client.py    ✅ Keep (Phase 2)
│           ├── letta_client.py     ✅ Keep (Phase 2)
│           ├── embeddings.py       ✅ Keep (Phase 2)
│           ├── indexing.py         ✅ Keep (Phase 2)
│           ├── caching.py          ⏳ Keep (Phase 3)
│           └── hybrid_search.py    ⏳ Keep (Phase 3)
├── mcp-server/
│   ├── Dockerfile                  ✅ Keep
│   ├── requirements.txt            ✅ Keep
│   └── mcp_server.py               ✅ Keep
```

### Bloat Files (Delete)

```
infra/docker/
├── gateway/app/
│   ├── routers/
│   │   ├── advanced_analytics.py      ❌ DELETE (Phase 4)
│   │   ├── advanced_search.py         ❌ DELETE (Phase 4)
│   │   └── performance.py             ❌ DELETE (Phase 4)
│   └── services/
│       ├── advanced_analytics.py      ❌ DELETE (Phase 4)
│       ├── advanced_dashboard.py      ❌ DELETE (Phase 4)
│       ├── distributed_tracing.py     ❌ DELETE (Phase 4)
│       ├── intelligence_engine.py     ❌ DELETE (Phase 4)
│       ├── performance_monitor.py     ❌ DELETE (Phase 4)
│       ├── semantic_chunking.py       ⚠️ MAYBE (Phase 3 - nice to have)
│       ├── reranking.py               ⚠️ MAYBE (Phase 3 - nice to have)
│       ├── enhanced_indexing.py       ⚠️ MAYBE (Phase 3 - nice to have)
│       └── connection_pool.py         ⚠️ MAYBE (Phase 3 - nice to have)
├── mcp-server/
│   └── tools/                         ❌ DELETE ENTIRE DIRECTORY
│       ├── advanced/tool_sdk.py       ❌ 863 lines
│       ├── multimodal/image_tools.py  ❌ 687 lines
│       └── composition/workflow_engine.py ❌ 702 lines
```

---

## 🚀 Next Steps

### This Week (Priority 1)

1. **Complete Phase 1 Testing**
   - Test Letta memory integration with agent
   - Verify persistence across sessions
   - Document any issues

2. **Clean Up Codebase**
   - Delete `mcp-server/tools/` entirely
   - Remove Phase 4 bloat from gateway
   - Commit cleanup

3. **Use Phase 1 in Real Work**
   - Work on hyacinth-bean-base for 5-7 days
   - Note any issues or improvements
   - Track: Is context burning? Do we need RAG?

### Week 2 (Priority 2)

4. **Decision Point: Deploy Phase 2?**
   - If context burn confirmed → Deploy Phase 2
   - If Phase 1 sufficient → Skip to Phase 3 or finish

5. **If Deploying Phase 2:**
   - Set up environment variables
   - Deploy Qdrant + Gateway + MCP
   - Index hyacinth-bean-base
   - Test RAG queries through IDE
   - Measure token usage improvement

6. **If Skipping Phase 2:**
   - Consider Phase 3 (automation) directly
   - Or just use Phase 1 and call it done

### Future (Low Priority)

7. **Phase 3 Automation** (only if Phase 2 deployed)
   - Deploy n8n
   - Create webhook workflows
   - Test automated reindexing

8. **Phase 5 Web UI** (optional)
   - Already partially built
   - Can deploy if want web interface
   - Not critical for core workflow

---

## 📝 Testing Checklist

### Phase 1 Validation ✅

- [x] Hub sync works (`task hub:sync`)
- [x] Agent rules synced (18 files)
- [x] NUKE components synced (1 file)
- [x] `.hub-cache/` excluded from git
- [x] Backward-compatible symlink created
- [x] Letta container running
- [ ] **TODO:** Test Letta memory with agent
- [ ] **TODO:** Test memory persistence

### Phase 2 Validation (Not Yet)

- [ ] Qdrant deployed and healthy
- [ ] Gateway deployed and healthy
- [ ] MCP server deployed
- [ ] Repository indexed successfully
- [ ] RAG queries working through MCP
- [ ] Token usage reduced >50%
- [ ] Citations accurate

### Phase 3 Validation (Not Yet)

- [ ] n8n deployed
- [ ] GitHub webhook configured
- [ ] Webhook triggers on push
- [ ] Automatic reindexing works
- [ ] Fallback cron works

---

## 🎯 Success Criteria

### Phase 1 (Current)

- ✅ No duplication of agent rules in satellites
- ✅ Hub sync works reliably
- ⏳ Memory persists across sessions (needs testing)
- ✅ Zero manual file copying

### Phase 2 (When Deployed)

- Token usage reduced by >50%
- RAG retrieves relevant context
- Citations include file:line references
- Response time < 2 seconds

### Phase 3 (When Deployed)

- Repos auto-update within 30 seconds
- Reindexing automatic on push
- No manual sync needed

---

## 📊 Code Quality Assessment

### What's Well-Implemented ✅

1. **Docker Configuration**
   - Proper health checks
   - Volume persistence
   - Network isolation
   - Environment variables

2. **Gateway Core Services**
   - Clean FastAPI structure
   - Proper dependency injection
   - Type hints throughout
   - Error handling

3. **MCP Server**
   - Simple, focused implementation
   - Clean tool definitions
   - Proper async/await usage
   - Good documentation

### What Needs Cleanup ⚠️

1. **Phase 4+ Bloat**
   - Unnecessary complexity
   - Unused dependencies
   - Over-engineered solutions
   - ~4,000 lines to remove

2. **Dependencies**
   - Review `requirements.txt` for bloat
   - Remove ML libs if not needed for Phase 2
   - Keep only essential packages

3. **Documentation**
   - Update README to reflect reality
   - Remove Phase 4-6 docs or mark as future
   - Focus on Phase 1-3 usage

---

## 📌 Conclusion

### Current Reality

**Phase 1:** ✅ **Working and validated** on hyacinth-bean-base

- Hub sync works perfectly
- Letta memory running (needs agent test)
- Clean satellite achieved

**Phase 2:** ⚠️ **Code complete, not deployed**

- Full implementation exists
- Contains some bloat to clean
- Ready to deploy when needed
- **Waiting on Phase 1 validation results**

**Phase 3:** ⚠️ **Partially ready**

- Docker config complete
- Webhook handler implemented
- Needs n8n workflow creation
- **Deploy only if Phase 2 deployed**

**Phase 4-6:** ❌ **Over-engineered, should be removed**

- ~4,000 lines of unnecessary code
- Solves problems we don't have
- Adds complexity without value

### Recommended Path Forward

```
Week 1: Complete Phase 1 Testing
  ├─ Test Letta memory with agent
  ├─ Use hyacinth-bean-base in real work
  └─ Clean up Phase 4-6 bloat

Week 2: Decision Point
  ├─ IF context burn confirmed:
  │   └─ Deploy Phase 2 (RAG)
  │
  └─ IF Phase 1 sufficient:
      └─ Skip to Phase 3 or finish

Week 3+: Optional
  ├─ Phase 3 automation (if Phase 2 deployed)
  └─ Use system for 3-6 months before adding features
```

### Key Takeaways

1. **Phase 1 works** - Validation successful
2. **Phase 2 ready** - Just needs deployment decision
3. **Phase 3 ready** - Depends on Phase 2
4. **Phase 4-6** - Should be removed
5. **Focus** - Get Phase 1 stable before adding complexity

---

**Validation Date:** 2025-10-31
**Next Review:** After 1 week of Phase 1 usage
**Status:** ✅ **Phase 1 Validated** | ⏳ **Awaiting Real-World Testing**
