---
doc_id: DOC-2025-00022
title: Phase 2 Implementation Plan - Context Server & RAG
doc_type: implementation-plan
status: active
canonical: true
created: 2025-10-31
tags: [phase2, context-server, rag, qdrant, implementation]
summary: Comprehensive implementation plan for Phase 2 - adding Qdrant vector database and Context Gateway for RAG capabilities
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# Phase 2 Implementation Plan - Context Server & RAG

**Implementation Date:** 2025-10-31
**Status:** Ready to Begin
**Phase:** 2 - Context Server (Week 2)
**Dependencies:** ✅ Phase 1 Complete

---

## 🎯 **Phase 2 Mission**

**Primary Goal:** Add RAG (Retrieval-Augmented Generation) to prevent context burn by implementing Qdrant vector database and Context Gateway

**Success Criteria:**

- Agent retrieves top-5 relevant chunks instead of full repo
- Token usage drops by >50%
- Answers include citations (file paths + line numbers)
- Context Gateway available as HTTP MCP tool

---

## 📋 **Phase 2 Deliverables**

### **Core Infrastructure Components**

1. ✅ **Qdrant Vector Database**
   - Add to Mac Mini Docker Compose
   - Configure collections and embeddings
   - Set up persistence and backups

2. ✅ **Context Gateway Service**
   - Build minimal HTTP API (`/ask`, `/memory`, `/notes`)
   - Integrate with Qdrant and Letta
   - Add GLM-4.6 embeddings support

3. ✅ **Repository Indexing**
   - Index one pilot repo into Qdrant
   - Implement chunking and metadata extraction
   - Test embedding generation and search

4. ✅ **MCP Integration**
   - Add Context Gateway as HTTP MCP tool in IDE
   - Configure authentication and endpoints
   - Test agent interactions via gateway

5. ✅ **Performance Validation**
   - Measure token usage reduction
   - Verify response quality with citations
   - Benchmark search performance

---

## 🏗️ **Technical Architecture**

### **Phase 2 System Overview**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Development Machine (Windows)                 │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  IDE (VS Code) + AI Agents (Cline/Roo/Kilo)             │   │
│  │  - Chat/Plans/Edits                                      │   │
│  │  - MCP Clients                                           │   │
│  │  - Filesystem MCP (local files)                          │   │
│  │  - HTTP MCP (new: Context Gateway)                       │   │
│  └────────────┬─────────────────────────────────┬───────────┘   │
│               │                                 │               │
│               │ (2) HTTP MCP Tool               │ (1) FS MCP    │
│               │     (to Mac Mini)               │     (local)   │
│               │                                 │               │
│  ┌────────────▼─────────────────────────────────▼───────────┐   │
│  │  Satellite Repo (Code Only)                              │   │
│  │  - src/                                                  │   │
│  │  - .hub-manifest.toml  (pins versions)                   │   │
│  │  - .hub-cache/ (agents, nuke from Phase 1)               │   │
│  └──────────────────────────────────────────────────────────┘   │
│               │                                                  │
│               │ git push                                         │
└───────────────┼──────────────────────────────────────────────────┘
                │
                │ GitHub
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│              Infrastructure (Mac Mini - Always On)               │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Context Gateway (HTTP Service) - NEW IN PHASE 2        │   │
│  │  - POST /ask     → RAG (context retrieval)               │   │
│  │  - POST /memory  → Persistent agent memory               │   │
│  │  - POST /notes   → Project notes/decisions               │   │
│  │  - POST /reindex → Full rebuild (GitHub Actions)         │   │
│  │  - POST /search   → Vector search only                   │   │
│  └───────┬──────────────────────────────────┬────────────────┘   │
│          │                                  │                    │
│  ┌───────▼──────────┐              ┌────────▼──────────┐         │
│  │  Qdrant DB       │              │  Letta Agent Hub  │         │
│  │  - Embeddings    │              │  - Memory/State   │         │
│  │  - Vector Search │              │  - SQL/SQLite     │         │
│  │  - Collections   │              │  - .af checkpoints│         │
│  │  - Metadata      │              │  (from Phase 1)   │         │
│  └──────────────────┘              └───────────────────┘         │
│          │                                  │                    │
│  ┌───────▼──────────────────────────────────▼──────────┐         │
│  │  Local Git Clones (Read-Only Mirrors)               │         │
│  │  ~/repos/infra-projects/project-a/                  │         │
│  │  ~/repos/plate-projects/project-b/                  │         │
│  │  ~/repos/lunar-snake-hub/                           │         │
│  └──────────────────────────────────────────────────────┘         │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Orchestration (n8n) - PHASE 3 (future)                 │   │
│  │  - git pull on webhook/schedule                          │   │
│  │  - Trigger /reindex                                      │   │
│  │  - Open PRs for version bumps                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│          All services share one GLM-4.6 BYOK endpoint            │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ **Implementation Tasks**

### **Task 1: Qdrant Vector Database Setup**

**Subtasks:**

- [ ] Add Qdrant service to Docker Compose
- [ ] Configure persistent storage volume
- [ ] Set up network and ports
- [ ] Create initial collections
- [ ] Test basic CRUD operations

**Docker Compose Addition:**

```yaml
# Add to existing docker-compose.yml
qdrant:
  image: qdrant/qdrant:latest
  container_name: qdrant
  ports:
    - "6333:6333"   # REST API
    - "6334:6334"   # gRPC
  volumes:
    - ./data/qdrant:/qdrant/storage
  restart: unless-stopped
  networks:
    - hub-network
```

**Validation:**

```bash
# Test Qdrant is running
curl http://localhost:6333/collections
# Should return empty collections list
```

---

### **Task 2: Context Gateway Development**

**Subtasks:**

- [ ] Create FastAPI project structure
- [ ] Implement `/ask` endpoint (RAG)
- [ ] Implement `/memory` endpoint (Letta proxy)
- [ ] Implement `/notes` endpoint (project notes)
- [ ] Add authentication and error handling
- [ ] Integrate GLM-4.6 embeddings

**Project Structure:**

```
context-gateway/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── ask.py           # RAG endpoint
│   │   ├── memory.py        # Letta proxy
│   │   └── notes.py         # Project notes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── qdrant_client.py # Vector DB client
│   │   ├── letta_client.py  # Memory client
│   │   └── embeddings.py    # GLM embeddings
│   └── models/
│       ├── __init__.py
│       ├── requests.py      # Request models
│       └── responses.py     # Response models
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

**Core API Endpoints:**

**POST /ask** - RAG Query:

```python
@app.post("/ask")
async def ask(request: AskRequest):
    # 1. Embed query using GLM-4.6
    query_vector = embeddings.embed_query(request.query)

    # 2. Search Qdrant for relevant chunks
    results = qdrant_client.search(
        collection_name=request.repo or "default",
        query_vector=query_vector,
        limit=request.top_k or 5,
        query_filter=build_filter(request.hints)
    )

    # 3. Build context from chunks
    context = "\n\n".join([r.payload["content"] for r in results])

    # 4. Call GLM-4.6 with context
    response = await call_glm_4_6(
        f"Context:\n{context}\n\nQuestion: {request.query}"
    )

    return {
        "answer": response,
        "chunks": [format_chunk(r) for r in results],
        "model": "glm-4.6",
        "tokens_used": estimate_tokens(context + response)
    }
```

---

### **Task 3: Repository Indexing System**

**Subtasks:**

- [ ] Implement file discovery and filtering
- [ ] Create chunking strategy (by file/function)
- [ ] Extract metadata (language, symbols, dependencies)
- [ ] Generate embeddings for chunks
- [ ] Batch upload to Qdrant with metadata

**Indexing Pipeline:**

```python
async def index_repository(repo_path: str, collection_name: str):
    """Index entire repository into Qdrant"""
    chunks = []

    # 1. Discover files
    for file_path in discover_files(repo_path):
        if is_indexable(file_path):
            # 2. Read and chunk file
            file_chunks = chunk_file(file_path)

            for chunk in file_chunks:
                # 3. Extract metadata
                metadata = extract_metadata(file_path, chunk)

                # 4. Generate embedding
                embedding = embeddings.embed_query(chunk.content)

                chunks.append({
                    "id": chunk.id,
                    "vector": embedding,
                    "payload": {
                        "content": chunk.content,
                        "file_path": str(file_path),
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        **metadata
                    }
                })

    # 5. Batch upload to Qdrant
    await qdrant_client.upsert(
        collection_name=collection_name,
        points=chunks
    )

    return len(chunks)
```

**Chunking Strategy:**

- **Code files:** Split by functions/classes with context
- **Markdown files:** Split by sections with headers
- **Config files:** Keep whole file as single chunk
- **Chunk size:** ~500-1000 tokens with overlap

---

### **Task 4: MCP Integration**

**Subtasks:**

- [ ] Add Context Gateway to MCP configuration
- [ ] Test HTTP MCP tool functionality
- [ ] Configure authentication tokens
- [ ] Validate agent-tool communication

**MCP Configuration Addition:**

```json
// Add to .cline/mcp_settings.json
{
  "mcpServers": {
    "context-gateway": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http"],
      "env": {
        "CONTEXT_GATEWAY_URL": "http://juis-mac-mini:5057",
        "CONTEXT_GATEWAY_TOKEN": "your-token-here"
      }
    }
  }
}
```

**Tool Usage Examples:**

```python
# Agent asks: "How is authentication implemented?"
# Tool calls: POST /ask with query="authentication implementation"
# Returns: Relevant code chunks + GLM-4.6 answer with citations
```

---

### **Task 5: Performance Validation**

**Subtasks:**

- [ ] Measure baseline token usage (full repo)
- [ ] Measure RAG token usage (chunks only)
- [ ] Validate response quality
- [ ] Benchmark search latency
- [ ] Test citation accuracy

**Success Metrics:**

- **Token Reduction:** >50% decrease vs full repo
- **Response Quality:** Answers include relevant context
- **Citations:** All claims reference specific files/lines
- **Latency:** <2 seconds for typical queries
- **Accuracy:** >90% relevant chunks in top-5 results

---

## 📊 **Testing Strategy**

### **Unit Tests**

```bash
# Test individual components
pytest tests/test_embeddings.py      # GLM embedding generation
pytest tests/test_qdrant_client.py  # Vector DB operations
pytest tests/test_chunking.py       # File chunking logic
```

### **Integration Tests**

```bash
# Test end-to-end workflows
pytest tests/test_ask_endpoint.py   # RAG query flow
pytest tests/test_indexing.py       # Repository indexing
pytest tests/test_memory_proxy.py   # Letta integration
```

### **Performance Tests**

```bash
# Benchmark token usage and latency
python benchmarks/token_usage.py    # Compare full vs RAG
python benchmarks/search_latency.py # Measure response times
python benchmarks/citation_accuracy.py # Validate citations
```

### **Manual Validation**

1. **Query Test:** Ask agent about specific implementation details
2. **Citation Check:** Verify all answers include file references
3. **Token Count:** Compare token usage before/after RAG
4. **Speed Test:** Measure response times for various queries

---

## 🚀 **Implementation Timeline**

### **Day 1: Infrastructure Setup**

- [ ] Add Qdrant to Docker Compose
- [ ] Set up Context Gateway project structure
- [ ] Configure networking and authentication
- [ ] Test basic service connectivity

### **Day 2: Core API Development**

- [ ] Implement `/ask` endpoint with RAG
- [ ] Integrate GLM-4.6 embeddings
- [ ] Connect to Qdrant for vector search
- [ ] Add basic error handling

### **Day 3: Indexing System**

- [ ] Implement file discovery and chunking
- [ ] Create metadata extraction
- [ ] Build batch upload to Qdrant
- [ ] Index pilot repository

### **Day 4: MCP Integration & Testing**

- [ ] Add Context Gateway to MCP configuration
- [ ] Test agent-tool communication
- [ ] Validate end-to-end workflows
- [ ] Performance benchmarking

### **Day 5: Validation & Documentation**

- [ ] Complete success criteria validation
- [ ] Document API usage and configuration
- [ ] Create troubleshooting guide
- [ ] Prepare Phase 3 handover

---

## 🔧 **Configuration Details**

### **Environment Variables**

```bash
# Context Gateway
CONTEXT_GATEWAY_URL=http://juis-mac-mini:5057
CONTEXT_GATEWAY_TOKEN=your-secure-token-here
GLM_API_KEY=your-glm-api-key
GLM_BASE_URL=https://api.z.ai/api/coding/paas/v4

# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=  # Optional, for security

# Letta (from Phase 1)
LETTA_URL=http://letta:8283
```

### **Docker Compose Service**

```yaml
context-gateway:
  build: ./context-gateway
  container_name: context-gateway
  environment:
    - CONTEXT_GATEWAY_TOKEN=${CONTEXT_GATEWAY_TOKEN}
    - GLM_API_KEY=${GLM_API_KEY}
    - GLM_BASE_URL=${GLM_BASE_URL}
    - QDRANT_URL=http://qdrant:6333
    - LETTA_URL=http://letta:8283
    - PORT=5057
  ports:
    - "5057:5057"
  depends_on:
    - qdrant
    - letta
  restart: unless-stopped
  networks:
    - hub-network
```

---

## 📋 **Pre-Implementation Checklist**

### **Prerequisites**

- [ ] Phase 1 fully operational (Letta + GLM-4.6)
- [ ] Mac Mini accessible with Docker Compose
- [ ] GLM-4.6 API key available
- [ ] Pilot repository selected for indexing
- [ ] Network connectivity between services

### **Security Setup**

- [ ] Generate secure gateway token
- [ ] Configure firewall rules for ports
- [ ] Set up API key rotation plan
- [ ] Document authentication flows

### **Monitoring Setup**

- [ ] Configure logging for all services
- [ ] Set up health check endpoints
- [ ] Create alerting for service failures
- [ ] Document troubleshooting procedures

---

## 🎯 **Success Criteria Validation**

### **Functional Requirements**

- [ ] ✅ Context Gateway responds to `/ask` queries
- [ ] ✅ RAG returns relevant code chunks with citations
- [ ] ✅ Token usage reduced by >50% vs full repo
- [ ] ✅ MCP integration working in IDE
- [ ] ✅ GLM-4.6 embeddings generating correctly

### **Performance Requirements**

- [ ] ✅ Query response time < 2 seconds
- [ ] ✅ Indexing completes in reasonable time
- [ ] ✅ Memory usage within limits
- [ ] ✅ Concurrent query handling stable

### **Quality Requirements**

- [ ] ✅ Citations accurate and specific
- [ ] ✅ Answers contextually relevant
- [ ] ✅ Error handling graceful
- [ ] ✅ Documentation comprehensive

---

## 🔄 **Phase 3 Preview**

**Next Phase Focus:** Orchestration & Automation

- Set up n8n for workflow automation
- Implement GitHub webhook integration
- Add automatic reindexing on changes
- Create version upgrade automation

**Dependencies:** Phase 2 Context Gateway must be fully operational

---

## 📝 **Implementation Notes**

### **Key Decisions Made**

1. **Qdrant over Chroma:** Production-ready, better performance
2. **FastAPI over Express:** Python ecosystem better for ML/AI
3. **GLM-4.6 embeddings:** Consistent with main LLM
4. **HTTP MCP tool:** Simpler than custom MCP server

### **Risk Mitigation**

- **Service Failure:** Docker restart policies
- **Data Loss:** Qdrant persistence volumes
- **API Limits:** Token usage monitoring
- **Network Issues:** Health checks and retries

### **Performance Considerations**

- **Embedding Caching:** Cache frequently used embeddings
- **Batch Processing:** Batch uploads to Qdrant
- **Connection Pooling:** Reuse HTTP connections
- **Async Operations:** Non-blocking I/O where possible

---

## 🚀 **Ready to Begin**

**Phase 2 Status:** ✅ **PLANNED AND READY**
**Dependencies:** ✅ **ALL MET (Phase 1 Complete)**
**Timeline:** 5 days implementation
**Success Criteria:** Clearly defined and measurable
**Risk Level:** LOW (building on solid Phase 1 foundation)

**Next Action:** Begin Task 1 - Qdrant Vector Database Setup

---

**Document Status:** Ready for Implementation
**Last Updated:** 2025-10-31
**Owner:** lunar-snake
**Location:** `docs/sessions/PHASE2_IMPLEMENTATION_PLAN.md`
