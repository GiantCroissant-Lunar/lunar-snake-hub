---
doc_id: DOC-2025-00027
title: Phase 1-3 Complete Deployment Guide
doc_type: guide
status: active
canonical: true
created: 2025-10-31
tags: [deployment, phase1, phase2, phase3, production]
summary: Step-by-step guide to deploy and verify Phase 1-3 infrastructure end-to-end
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# Phase 1-3 Complete Deployment Guide

**Objective:** Get Phase 1-3 fully working end-to-end on Mac Mini

**Timeline:** 2-3 hours
**Prerequisites:** Docker, docker-compose, Mac Mini accessible

---

## 🎯 What We're Deploying

```
Phase 1: Hub Sync + Memory
  ├─ ✅ Hub sync (already working)
  └─ ✅ Letta (already running)

Phase 2: RAG (Context Server)
  ├─ Qdrant (vector database)
  ├─ Context Gateway (FastAPI service)
  └─ MCP Server (tool integration)

Phase 3: Automation
  ├─ n8n (workflow automation)
  └─ Webhook handlers
```

---

## 📋 Pre-Deployment Checklist

### Environment Check

```bash
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub/infra/docker

# 1. Verify .env file exists and has all variables
cat .env

# Should contain:
# - OPENAI_API_KEY=...
# - OPENAI_BASE_URL=...
# - GATEWAY_TOKEN=...
# - N8N_USER=...
# - N8N_PASSWORD=...
```

### Current Services Check

```bash
# Check what's currently running
docker ps

# Should see:
# - letta-memory (Phase 1) ✅
# - lunar-frontend-test (Phase 5, can leave running)
```

---

## 🚀 PHASE 2 DEPLOYMENT

### Step 1: Deploy Qdrant Vector Database (5 min)

```bash
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub/infra/docker

# Start Qdrant
docker-compose up -d qdrant

# Wait for startup (30 seconds)
sleep 30

# Verify Qdrant is healthy
docker ps | grep qdrant
# Should show: Up X seconds (healthy)

# Test Qdrant API
curl http://localhost:6333/collections
# Expected: {"result":{"collections":[]}}
```

**Success Criteria:**

- ✅ Container status: "healthy"
- ✅ API responds on port 6333
- ✅ Returns empty collections list

---

### Step 2: Deploy Context Gateway (10 min)

```bash
# Build and start Gateway
docker-compose up -d gateway

# Watch logs (Ctrl+C to exit)
docker-compose logs -f gateway

# Wait for: "Application startup complete"
# Then Ctrl+C

# Verify Gateway is healthy
docker ps | grep gateway
# Should show: Up X seconds (healthy)

# Test Gateway health endpoint
curl http://localhost:5057/health
# Expected: {"status":"healthy"} or similar
```

**Troubleshooting:**

If gateway fails to start:

```bash
# Check logs for errors
docker-compose logs gateway | tail -50

# Common issues:
# 1. Missing dependencies - rebuild: docker-compose build gateway
# 2. Port conflict - check if 5057 is in use: lsof -i :5057
# 3. Environment variables - verify .env file
```

**Success Criteria:**

- ✅ Container running and healthy
- ✅ API responds on port 5057
- ✅ No errors in logs

---

### Step 3: Deploy MCP Server (5 min)

```bash
# Build and start MCP Server
docker-compose up -d mcp-server

# Check logs
docker-compose logs mcp-server | tail -20

# Verify it's running
docker ps | grep mcp-server
# Should show: Up X seconds
```

**Note:** MCP server runs in stdio mode (no HTTP endpoint), so there's no health check to curl

**Success Criteria:**

- ✅ Container running
- ✅ No errors in logs
- ✅ Shows "Starting MCP server" or similar

---

### Step 4: Index hyacinth-bean-base Repository (15 min)

Now we need to index your repository so RAG can search it.

#### Option A: Using Gateway API Directly (Recommended)

```bash
# First, make repository accessible to gateway container
# The docker-compose.yml maps ~/repos to /repos in container

# Copy hyacinth-bean-base to ~/repos (if not already there)
mkdir -p ~/repos
cp -r /Users/apprenticegc/Work/lunar-snake/personal-work/yokan-projects/hyacinth-bean-base \
     ~/repos/hyacinth-bean-base

# Index the repository
curl -X POST http://localhost:5057/search/index \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer aQPY0XwHOB7n3IJWqHVqLUkDP5Yf9Zucdqy3NG1HHRA=" \
  -d '{
    "repo_path": "/repos/hyacinth-bean-base",
    "collection_name": "hyacinth-bean-base"
  }'

# This will take 5-10 minutes depending on repo size
# Expected output:
# {
#   "status": "success",
#   "files_processed": 150,
#   "chunks_indexed": 1250,
#   "indexing_time_ms": 45000
# }
```

#### Option B: If Gateway Doesn't Have Index Endpoint Yet

Create a simple indexing script:

```bash
# Create indexing script
cat > index_repo.py << 'EOF'
#!/usr/bin/env python3
import sys
import glob
import hashlib
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import httpx

# Initialize clients
qdrant = QdrantClient(url="http://localhost:6333")
glm_api_key = "9e567274013f4adda2e680acb223178c.NP6DC8NilcIQRlZ2"
glm_base_url = "https://api.z.ai/api/coding/paas/v4"

def get_embedding(text: str):
    """Get embedding from GLM API"""
    response = httpx.post(
        f"{glm_base_url}/embeddings",
        headers={"Authorization": f"Bearer {glm_api_key}"},
        json={"input": text, "model": "embedding-2"},
        timeout=30.0
    )
    return response.json()["data"][0]["embedding"]

def index_file(file_path: Path, collection_name: str):
    """Index a single file"""
    content = file_path.read_text(errors='ignore')

    # Simple chunking: split by lines, ~500 chars per chunk
    chunks = []
    current_chunk = []
    current_size = 0

    for line in content.split('\n'):
        current_chunk.append(line)
        current_size += len(line)

        if current_size > 500:
            chunk_text = '\n'.join(current_chunk)
            chunks.append(chunk_text)
            current_chunk = []
            current_size = 0

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    # Index each chunk
    points = []
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        point_id = hashlib.md5(f"{file_path}:{i}".encode()).hexdigest()

        points.append(PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "file_path": str(file_path),
                "chunk_index": i,
                "content": chunk[:1000]  # Store first 1000 chars
            }
        ))

    if points:
        qdrant.upsert(collection_name=collection_name, points=points)

    return len(points)

def main():
    repo_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("~/repos/hyacinth-bean-base").expanduser()
    collection_name = "hyacinth-bean-base"

    # Create collection
    try:
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)  # GLM embedding size
        )
    except:
        print(f"Collection {collection_name} already exists, reusing...")

    # Index code files
    total_chunks = 0
    file_count = 0

    for ext in ['*.cs', '*.py', '*.md', '*.yml', '*.json']:
        for file_path in repo_path.rglob(ext):
            if 'node_modules' in str(file_path) or 'bin' in str(file_path) or 'obj' in str(file_path):
                continue

            print(f"Indexing: {file_path.name}")
            chunks = index_file(file_path, collection_name)
            total_chunks += chunks
            file_count += 1

    print(f"\n✅ Indexing complete!")
    print(f"   Files: {file_count}")
    print(f"   Chunks: {total_chunks}")

if __name__ == "__main__":
    main()
EOF

# Install dependencies
pip install qdrant-client httpx

# Run indexing
python index_repo.py ~/repos/hyacinth-bean-base
```

**Success Criteria:**

- ✅ Collection created in Qdrant
- ✅ Files indexed successfully
- ✅ Can query collection

**Verify Indexing:**

```bash
# Check collection exists
curl http://localhost:6333/collections/hyacinth-bean-base

# Expected: Collection info with point count > 0
```

---

### Step 5: Configure MCP in IDE (10 min)

Now configure your IDE (Cline/Windsurf) to use the Context Gateway via MCP.

#### For Cline (VS Code)

Create or update `.vscode/settings.json` in hyacinth-bean-base:

```json
{
  "cline.mcpServers": {
    "lunar-context-gateway": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "lunar-mcp-server",
        "python",
        "/app/mcp_server.py"
      ],
      "env": {
        "GATEWAY_URL": "http://gateway:5057",
        "GATEWAY_TOKEN": "aQPY0XwHOB7n3IJWqHVqLUkDP5Yf9Zucdqy3NG1HHRA="
      }
    }
  }
}
```

#### For Windsurf

Update Windsurf MCP settings similarly (location varies by OS).

**Test MCP Integration:**

1. Open hyacinth-bean-base in IDE
2. Start Cline/Windsurf
3. Ask: "Search for the AuthController implementation"
4. ✅ Agent should use `search_vectors` or `ask_rag` tool
5. ✅ Response should include file paths and code snippets

---

### Step 6: Test RAG Queries (15 min)

Test that the full RAG pipeline works:

#### Test 1: Direct API Query

```bash
# Query via Gateway API
curl -X POST http://localhost:5057/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer aQPY0XwHOB7n3IJWqHVqLUkDP5Yf9Zucdqy3NG1HHRA=" \
  -d '{
    "query": "How is dependency injection configured?",
    "repo": "hyacinth-bean-base",
    "top_k": 5
  }'

# Expected: JSON response with answer and source citations
```

#### Test 2: Vector Search Only

```bash
# Search without LLM generation
curl -X POST http://localhost:5057/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer aQPY0XwHOB7n3IJWqHVqLUkDP5Yf9Zucdqy3NG1HHRA=" \
  -d '{
    "query": "dependency injection",
    "repo": "hyacinth-bean-base",
    "top_k": 5
  }'

# Expected: JSON array of matching chunks with scores
```

#### Test 3: IDE Integration

1. In IDE, ask: "Where is dependency injection configured in this project?"
2. ✅ Agent should:
   - Use RAG tool
   - Return relevant code locations
   - Include file:line citations
3. Token usage should be much lower than loading full repo

**Success Criteria:**

- ✅ API queries return relevant results
- ✅ Citations include correct file paths
- ✅ IDE integration works
- ✅ Token usage reduced vs full repo

---

## 🚀 PHASE 3 DEPLOYMENT

### Step 7: Deploy n8n (5 min)

```bash
# Start n8n
docker-compose up -d n8n

# Wait for startup
sleep 30

# Verify n8n is running
docker ps | grep n8n
# Should show: Up X seconds

# Access n8n UI
open http://localhost:5678
# Or visit in browser

# Login:
# Username: admin
# Password: Ra9+1hA4dRc60seDsNPvWxInYP3VpYvy
```

**Success Criteria:**

- ✅ Container running
- ✅ UI accessible on port 5678
- ✅ Can login successfully

---

### Step 8: Create GitHub Webhook Workflow (20 min)

Now create an n8n workflow to automatically reindex when you push to GitHub.

#### Create Webhook Workflow

1. **In n8n UI**, click "New Workflow"
2. **Add Webhook Trigger Node:**
   - Node type: "Webhook"
   - Method: POST
   - Path: `github/push`
   - Authentication: None (we'll verify signature in next step)

3. **Add HTTP Request Node (Verify Signature):**
   - Connect to Webhook
   - Method: POST
   - URL: `http://gateway:5057/webhooks/github/verify`
   - Body: `{{ $json }}`
   - Headers: Pass through all headers

4. **Add HTTP Request Node (Reindex):**
   - Connect to previous node (if verification passes)
   - Method: POST
   - URL: `http://gateway:5057/search/index`
   - Body:

     ```json
     {
       "repo_path": "/repos/{{ $json.repository.name }}",
       "collection_name": "{{ $json.repository.name }}"
     }
     ```

   - Headers:
     - `Authorization`: `Bearer aQPY0XwHOB7n3IJWqHVqLUkDP5Yf9Zucdqy3NG1HHRA=`

5. **Add Slack Notification Node (Optional):**
   - Connect to reindex node
   - Send message: "✅ Reindexed {{ $json.repository.name }} after push"

6. **Save** workflow as "GitHub Auto-Reindex"

#### Configure GitHub Webhook

1. Go to your GitHub repo settings
2. Webhooks → Add webhook
3. Payload URL: `http://<your-mac-mini-ip>:5678/webhook/github/push`
4. Content type: `application/json`
5. Secret: (generate a secure secret, store in GitHub and n8n)
6. Events: Just `push`
7. Active: ✓

**Test Webhook:**

```bash
# Push a small change to trigger webhook
cd ~/repos/hyacinth-bean-base
echo "# Test" >> README.md
git add README.md
git commit -m "test: trigger webhook"
git push

# Check n8n execution log
# Check gateway logs: docker-compose logs gateway | tail -20
# Verify collection was updated: curl http://localhost:6333/collections/hyacinth-bean-base
```

**Success Criteria:**

- ✅ Webhook triggers on git push
- ✅ Gateway receives reindex request
- ✅ Qdrant collection updates
- ✅ Notification sent (if configured)

---

### Step 9: Create Fallback Cron Workflow (10 min)

Create a backup workflow that runs every 10 minutes to catch any missed webhooks.

1. **New Workflow** in n8n
2. **Add Cron Node:**
   - Trigger: Schedule
   - Mode: Every X minutes
   - Value: 10

3. **Add Execute Command Node (Git Pull):**
   - Command: `git -C /repos/hyacinth-bean-base fetch --all && git -C /repos/hyacinth-bean-base pull --ff-only`

4. **Add If Node:**
   - Condition: Check if git pull had changes
   - Expression: `{{ $json.stdout.includes('Already up to date') }}` = false

5. **Add HTTP Request (Reindex)** - same as before
6. **Save** as "Auto-Pull and Reindex"

---

## 🧪 END-TO-END INTEGRATION TEST

### Full System Test (30 min)

Test the complete Phase 1-3 flow:

#### Test Scenario: New Feature Development

1. **Hub Sync (Phase 1)**

   ```bash
   cd ~/repos/hyacinth-bean-base
   task hub:sync
   # ✅ Verify: Latest agent rules synced
   ```

2. **Code with Agent Using Memory (Phase 1)**
   - Open hyacinth-bean-base in IDE
   - Ask agent: "Remember: We're implementing authentication using JWT tokens"
   - ✅ Verify: Agent stores to Letta

3. **Code with Agent Using RAG (Phase 2)**
   - Ask: "Show me similar authentication patterns in the codebase"
   - ✅ Verify: Agent uses RAG, returns relevant code with citations
   - ✅ Verify: Token usage much lower than full repo

4. **Push Changes and Auto-Reindex (Phase 3)**

   ```bash
   # Make a change
   echo "// New auth implementation" >> some-file.cs
   git add .
   git commit -m "feat: add JWT authentication"
   git push

   # Wait 30 seconds
   # ✅ Verify: GitHub webhook triggered
   # ✅ Verify: n8n executed reindex
   # ✅ Verify: Qdrant collection updated
   ```

5. **Query Updated Index**
   - Ask agent: "What's the new authentication implementation?"
   - ✅ Verify: Agent finds the new code you just pushed

6. **Memory Persistence**
   - Close IDE completely
   - Reopen, new conversation
   - Ask: "What authentication approach are we using?"
   - ✅ Verify: Agent recalls "JWT tokens" from Letta

### Success Criteria Checklist

**Phase 1:**

- [ ] Hub sync works
- [ ] Letta stores memories
- [ ] Letta recalls across sessions

**Phase 2:**

- [ ] Qdrant running and healthy
- [ ] Gateway running and healthy
- [ ] Repository indexed
- [ ] RAG queries return relevant results
- [ ] MCP integration works in IDE
- [ ] Token usage reduced significantly

**Phase 3:**

- [ ] n8n running and accessible
- [ ] GitHub webhook triggers workflows
- [ ] Auto-reindex on push works
- [ ] Fallback cron runs correctly
- [ ] Notifications work (if configured)

**Integration:**

- [ ] All services communicate correctly
- [ ] No errors in any logs
- [ ] End-to-end workflow smooth
- [ ] System responds within acceptable time

---

## 📊 Monitoring & Maintenance

### Check Service Health

```bash
# All services status
docker-compose ps

# Check logs for all services
docker-compose logs --tail=50

# Individual service logs
docker-compose logs -f gateway
docker-compose logs -f qdrant
docker-compose logs -f n8n
```

### Monitor Resource Usage

```bash
# Container resource usage
docker stats

# Disk usage (Qdrant data can grow)
du -sh ~/Work/lunar-snake/lunar-snake-hub/infra/docker/data/*
```

### Backup Important Data

```bash
# Backup Qdrant collections
cp -r infra/docker/data/qdrant backups/qdrant-$(date +%Y%m%d)

# Backup Letta database
cp -r infra/docker/data/letta backups/letta-$(date +%Y%m%d)

# Backup n8n workflows
cp -r infra/docker/data/n8n backups/n8n-$(date +%Y%m%d)
```

---

## 🔧 Troubleshooting

### Gateway Fails to Start

```bash
# Check for port conflicts
lsof -i :5057

# Rebuild gateway
docker-compose build gateway
docker-compose up -d gateway

# Check dependencies
docker-compose exec gateway pip list
```

### Qdrant Out of Memory

```bash
# Check Qdrant memory usage
docker stats lunar-qdrant

# Compact collection
curl -X POST http://localhost:6333/collections/hyacinth-bean-base/optimize

# Or recreate with optimized settings
```

### Indexing Fails

```bash
# Check repository path
docker-compose exec gateway ls -la /repos/hyacinth-bean-base

# Check GLM API quota
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  $OPENAI_BASE_URL/usage

# Manual reindex
curl -X POST http://localhost:5057/search/index \
  -H "Authorization: Bearer $GATEWAY_TOKEN" \
  -d '{"repo_path":"/repos/hyacinth-bean-base","collection_name":"test","force_reindex":true}'
```

### n8n Webhook Not Triggering

```bash
# Check n8n logs
docker-compose logs n8n | grep webhook

# Test webhook directly
curl -X POST http://localhost:5678/webhook/github/push \
  -H "Content-Type: application/json" \
  -d '{"repository":{"name":"test"}}'

# Check GitHub webhook delivery logs
```

---

## 🎯 Post-Deployment Checklist

- [ ] All Phase 2 services running (Qdrant, Gateway, MCP)
- [ ] All Phase 3 services running (n8n)
- [ ] hyacinth-bean-base indexed successfully
- [ ] RAG queries working in IDE
- [ ] GitHub webhooks configured
- [ ] n8n workflows created and tested
- [ ] End-to-end test passed
- [ ] Monitoring set up
- [ ] Backups configured
- [ ] Documentation updated with actual config

---

## 📝 What to Document

After successful deployment, update:

1. **Actual service URLs and ports**
2. **Collection names used**
3. **Webhook URLs configured**
4. **Any deviations from this guide**
5. **Performance metrics (token usage, response time)**
6. **Lessons learned**

---

## 🎉 Success

If all tests pass, you now have:

- ✅ **Phase 1** - Hub sync + Letta memory working
- ✅ **Phase 2** - RAG with Qdrant + Gateway fully operational
- ✅ **Phase 3** - Automated reindexing on git push
- ✅ **Integration** - All systems working together

**Next:** Use it for real work and refine based on actual usage!

---

**Document Status:** Deployment Guide
**Last Updated:** 2025-10-31
**Next Review:** After successful deployment
