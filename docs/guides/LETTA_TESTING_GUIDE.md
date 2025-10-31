---
doc_id: DOC-2025-00025
title: Letta Memory Testing Guide
doc_type: guide
status: active
canonical: true
created: 2025-10-31
tags: [letta, memory, testing, phase1, validation]
summary: Comprehensive guide for testing Letta memory integration with automated scripts and manual verification
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# Letta Memory Testing Guide

**Purpose:** Verify that Letta memory service is working correctly for Phase 1 validation

**Prerequisites:**

- Letta container running on port 8283
- Python 3.8+ installed
- `httpx` library (`pip install httpx`)

---

## 🎯 Testing Methods

We provide **three ways** to test Letta memory:

1. **Automated Script** - Comprehensive API testing
2. **Manual IDE Testing** - Real-world agent integration
3. **Direct API Testing** - curl-based verification

---

## Method 1: Automated Test Script ✅ RECOMMENDED

### Quick Start

```bash
cd infra/docker

# Install dependencies
pip install httpx

# Run tests (default: localhost:8283)
python test_letta_memory.py

# Or specify custom host/port
python test_letta_memory.py --host mac-mini.local --port 8283

# Or full URL
python test_letta_memory.py --url http://mac-mini:8283
```

### What It Tests

The script runs 7 comprehensive tests:

1. **Health Check** - Verifies Letta server is running
2. **List Agents** - Checks API connectivity
3. **Create Agent** - Creates test agent
4. **Store Memory** - Sends message to store information
5. **Retrieve Memory** - Gets agent's memory state
6. **Query Context** - Verifies agent recalls stored info
7. **Cleanup** - Deletes test agent

### Expected Output

```
======================================================================
  LETTA MEMORY INTEGRATION TEST
======================================================================
Target: http://localhost:8283
Started: 2025-10-31 20:45:00
======================================================================

✅ PASS | Health Check
       Letta server is running

✅ PASS | List Agents
       Found 0 agents

✅ PASS | Create Agent
       Created agent: agent_123abc

✅ PASS | Send Message
       Message sent: 'We are using the Repository pattern...'

✅ PASS | Retrieve Memory
       Memory retrieved successfully

✅ PASS | Query with Context
       Agent recalled context: The Repository pattern...

✅ PASS | Delete Agent
       Cleaned up agent: agent_123abc

======================================================================
  TEST SUMMARY
======================================================================
Total Tests:  7
Passed:       7 ✅
Failed:       0 ❌
Success Rate: 100.0%

======================================================================

📄 Detailed results saved to: letta_test_results.json
```

### Interpreting Results

**All tests pass (100%):** ✅ Letta is working perfectly!
**Some tests fail:** ⚠️ Check the error messages and troubleshoot

**Common Issues:**

| Error | Cause | Solution |
|-------|-------|----------|
| "Cannot connect to Letta server" | Container not running | `docker ps` and verify letta-memory running |
| "Status: 404" | Wrong endpoint | Check Letta version and API docs |
| "Timeout" | Letta starting up | Wait 30 seconds and retry |
| "Status: 500" | Server error | Check `docker logs letta-memory` |

---

## Method 2: Manual IDE Testing (Real-World)

### Prerequisites

- Letta MCP server configured in Cline/Windsurf settings
- hyacinth-bean-base project open in IDE

### Step-by-Step Test

#### Test 2A: Store Memory

1. Open hyacinth-bean-base in VS Code/Cursor
2. Start your AI agent (Cline, Windsurf, etc.)
3. Send this message:

```
Please remember this decision for our project:

We are using the Repository pattern for data access in hyacinth-bean-base
because it decouples domain logic from infrastructure concerns and makes
testing easier.

Store this in your persistent memory.
```

4. **Verify:** Agent should respond acknowledging the storage
5. **Check:** Agent should use Letta MCP tool (check tool calls in UI)

#### Test 2B: Verify Persistence

1. **Close VS Code completely** (Cmd+Q / Alt+F4)
2. Wait 10 seconds
3. **Reopen VS Code** and open hyacinth-bean-base
4. **Start a NEW agent conversation**
5. Ask: `"What pattern are we using for data access in this project, and why?"`

**Expected Result:**

- ✅ Agent recalls: "Repository pattern"
- ✅ Agent explains: "Decouples domain from infrastructure"
- ✅ Agent retrieves from Letta, not from current conversation

**If it fails:**

- ❌ Agent says "I don't have information about that"
- ❌ Check Letta MCP configuration
- ❌ Run automated test script to verify Letta is working

#### Test 2C: Cross-Session Memory

1. Store 3 different decisions in separate conversations:
   - `"Remember: We use xUnit for testing"`
   - `"Remember: We follow Domain-Driven Design principles"`
   - `"Remember: API versioning uses semantic versioning"`

2. Close IDE, reopen, new conversation

3. Ask: `"What are all the architectural decisions you remember for this project?"`

**Expected Result:**

- ✅ Agent lists all 3 decisions
- ✅ Agent combines memory from Letta with current context

---

## Method 3: Direct API Testing with curl

### Quick Verification

```bash
# 1. Check Letta is running
curl http://localhost:8283/v1/health

# Expected: {"status":"ok"} or similar

# 2. List existing agents
curl http://localhost:8283/v1/agents

# Expected: JSON array of agents

# 3. Create a test agent
curl -X POST http://localhost:8283/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_agent",
    "system": "You are a helpful assistant",
    "human": "User",
    "persona": "Assistant"
  }'

# Expected: JSON with agent_id

# 4. Send a message (replace AGENT_ID)
curl -X POST http://localhost:8283/v1/agents/AGENT_ID/messages \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Remember: We use Repository pattern for data access",
    "stream": false
  }'

# Expected: JSON with response

# 5. Query to verify memory
curl -X POST http://localhost:8283/v1/agents/AGENT_ID/messages \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What pattern do we use for data access?",
    "stream": false
  }'

# Expected: Response mentioning "Repository pattern"

# 6. Clean up
curl -X DELETE http://localhost:8283/v1/agents/AGENT_ID
```

---

## 🔧 Troubleshooting

### Issue: Letta container not running

```bash
# Check if container exists
docker ps -a | grep letta

# If not running, start it
docker start letta-memory

# If doesn't exist, check docker-compose
cd infra/docker
docker-compose up -d letta
```

### Issue: Connection refused

```bash
# Check which port Letta is on
docker ps | grep letta

# Should show: 0.0.0.0:8283->8283/tcp

# If different port, use that port in tests
python test_letta_memory.py --port 5055  # or whatever port
```

### Issue: "Port 8283 in use"

```bash
# Find what's using the port
lsof -i :8283

# If it's another service, stop it or change Letta's port in docker-compose.yml
```

### Issue: API errors (404, 500)

```bash
# Check Letta logs
docker logs letta-memory

# Look for errors
docker logs letta-memory | grep -i error

# Restart with fresh logs
docker restart letta-memory && docker logs -f letta-memory
```

### Issue: Memory not persisting

**Possible causes:**

1. **Letta data volume not mounted**
   - Check `docker-compose.yml` has: `volumes: - ./data/letta:/data`
   - Verify `./data/letta` directory exists

2. **Wrong agent ID**
   - Each agent has separate memory
   - Use same agent_id across sessions

3. **MCP configuration issue**
   - Check `.cline/mcp_settings.json` or Windsurf config
   - Verify Letta MCP server is enabled

---

## 📊 Success Criteria

### Phase 1 Validation - Memory Tests

- [ ] ✅ Automated script passes all 7 tests
- [ ] ✅ Manual IDE test stores and retrieves memory
- [ ] ✅ Memory persists across IDE restarts
- [ ] ✅ Cross-session memory recall works
- [ ] ✅ No errors in Letta logs

### When All Pass

**Congratulations!** 🎉 Phase 1 memory integration is **validated and working**

**Next steps:**

1. Use hyacinth-bean-base for real work (1 week)
2. Track if context burn is still an issue
3. Decide if Phase 2 (RAG) is needed

### If Tests Fail

1. Run automated script to identify specific failure
2. Check Letta logs for errors
3. Verify docker-compose.yml configuration
4. Try direct API testing with curl
5. Check MCP settings in IDE

---

## 🔍 Advanced: Understanding the Test Script

### Test Script Architecture

```python
LettaMemoryTester
├── test_1_health_check()      # HTTP GET /v1/health
├── test_2_list_agents()        # HTTP GET /v1/agents
├── test_3_create_agent()       # HTTP POST /v1/agents
├── test_4_send_message()       # HTTP POST /v1/agents/{id}/messages
├── test_5_retrieve_memory()    # HTTP GET /v1/agents/{id}/memory
├── test_6_query_with_context() # HTTP POST /v1/agents/{id}/messages
└── test_7_delete_agent()       # HTTP DELETE /v1/agents/{id}
```

### Extending the Tests

Add custom tests by subclassing:

```python
class MyLettaTester(LettaMemoryTester):
    def test_8_custom_memory_query(self, agent_id: str):
        """Custom test for specific use case"""
        # Your test logic here
        pass

    def run_full_test_suite(self):
        super().run_full_test_suite()
        # Add your custom tests
        agent_id = self.test_3_create_agent()
        self.test_8_custom_memory_query(agent_id)
```

---

## 📝 Test Results Format

### JSON Output (`letta_test_results.json`)

```json
{
  "test_run": "2025-10-31T20:45:00",
  "base_url": "http://localhost:8283",
  "summary": {
    "total": 7,
    "passed": 7,
    "failed": 0,
    "success_rate": 100.0
  },
  "results": [
    {
      "test": "Health Check",
      "success": true,
      "message": "Letta server is running",
      "timestamp": "2025-10-31T20:45:01"
    },
    ...
  ]
}
```

Use this for:

- Automated CI/CD testing
- Monitoring Letta health
- Regression testing
- Performance tracking over time

---

## 🚀 Next Steps After Successful Testing

Once all tests pass:

1. **Mark Phase 1 as complete** ✅
2. **Use in real work** - Work on hyacinth-bean-base for 1 week
3. **Track metrics:**
   - How often do you reference stored memories?
   - Does agent recall help your workflow?
   - Is context still burning (loading full repos)?
4. **Decision point:** After 1 week, decide on Phase 2
   - If context burn is bad → Deploy Phase 2 (RAG)
   - If Phase 1 sufficient → Phase 1 is done!

---

## 📚 References

- **Letta API Docs:** <https://docs.letta.ai/>
- **Letta GitHub:** <https://github.com/letta-ai/letta>
- **MCP Protocol:** <https://modelcontextprotocol.io/>
- **Phase 1 Validation Report:** `docs/sessions/PHASE1-3_VALIDATION_REPORT.md`
- **Phase 1 Hardening Plan:** `docs/sessions/PHASE1-3_HARDENING_PLAN.md`

---

**Document Status:** Active Testing Guide
**Last Updated:** 2025-10-31
**Next Review:** After Phase 1 completion
