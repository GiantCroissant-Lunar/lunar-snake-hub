# Phase 1 Test Suite

This comprehensive test suite validates the complete Phase 1 implementation of the lunar-snake-hub project.

## Test Overview

The Phase 1 test suite consists of 5 main tests:
1. **Hub Sync Test** - Runtime synchronization from hub
2. **Agent Rules Test** - Agent reads hub rules correctly
3. **Hub Update Test** - Changes propagate to satellites
4. **Letta Memory Test** - Persistent memory across sessions
5. **Integration Test** - End-to-end workflow

## Prerequisites

- Mac Mini with Letta running (Task #6)
- MCP tool configured (Task #7)
- lablab-bean workspace with hub sync configured

## Test 1: Hub Sync Functionality

### 1.1 Clean Sync Test
```bash
cd D:\lunar-snake\personal-work\yokan-projects\lablab-bean

# Clean existing cache
task hub:clean

# Perform fresh sync
task hub:sync

# Expected output:
# ✅ Hub sync complete
# ✅ Agents: 15 files
# ✅ NUKE: 1 file
# ✅ Total: 16 files synced

# Verify cache contents
task hub:check

# Expected output:
# ✅ Hub cache present
# ✅ Agents: 15 files
# ✅ NUKE: 1 file
# ✅ Total: 16 files
```

### 1.2 File Structure Verification
```bash
# Check agent files exist
ls .hub-cache/agents/rules/
# Should show: 00-index.md, 10-principles.md, 20-rules.md, 30-glossary.md, 40-documentation.md

ls .hub-cache/agents/adapters/
# Should show: claude.md, codex.md, copilot.md, gemini.md, kiro.md, windsurf.md

ls .hub-cache/nuke/
# Should show: Build.Common.cs

# Check symlink exists (on Unix-like systems)
ls -la .agent
# Should point to .hub-cache/agents/
```

### 1.3 Sync Validation
```bash
# Verify file contents
cat .hub-cache/agents/rules/20-rules.md | head -20
# Should contain actual rule content, not placeholders

# Verify NUKE build targets
grep -E "(Clean|Restore|Compile|Test)" .hub-cache/nuke/Build.Common.cs
# Should show common build targets
```

**Success Criteria:**
- ✅ Sync completes without errors
- ✅ All 16 files present in cache
- ✅ File contents are valid
- ✅ Symlink created correctly

---

## Test 2: Agent Reads Hub Rules

### 2.1 Basic Rule Query
1. Open `lablab-bean` in VS Code
2. Start Cline/Roo/Kilo conversation
3. Ask: **"What are our naming conventions? Check the agent rules."**

**Expected Response:**
- Agent should reference `.hub-cache/agents/rules/20-rules.md`
- Should quote specific naming conventions
- Should mention "hub" as source of rules

### 2.2 Multiple Rule Sources Test
Ask: **"What are our development principles and coding rules?"**

**Expected Response:**
- Should reference both `10-principles.md` and `20-rules.md`
- Should distinguish between principles and rules
- Should provide specific examples

### 2.3 Adapter-Specific Rules Test
Ask: **"What are the specific guidelines for using Claude as an adapter?"**

**Expected Response:**
- Should reference `.hub-cache/agents/adapters/claude.md`
- Should provide Claude-specific guidelines
- Should mention adapter pattern

### 2.4 Error Handling Test
Ask: **"What are our guidelines for React development?"** (Not in rules)

**Expected Response:**
- Should indicate React guidelines not found
- Should suggest available rule categories
- Should not hallucinate React-specific rules

**Success Criteria:**
- ✅ Agent reads from correct hub cache files
- ✅ Responses match actual rule content
- ✅ Agent attributes information to hub
- ✅ Graceful handling of missing information

---

## Test 3: Hub Update Propagation

### 3.1 Rule Update Test
```bash
# In lunar-snake-hub repo
cd D:\lunar-snake\lunar-snake-hub

# Edit a rule file
nano agents/rules/20-rules.md

# Add a test rule at the end:
# "TEST RULE: All test functions must start with 'test_' prefix"

# Commit and push
git add agents/rules/20-rules.md
git commit -m "test: add test rule for Phase 1 validation"
git push
```

### 3.2 Sync Update Test
```bash
# In lablab-bean
cd D:\lunar-snake\personal-work\yokan-projects\lablab-bean

# Sync updates
task hub:sync

# Expected: Should show updated files
# ✅ Hub sync complete
# ✅ Updated: agents/rules/20-rules.md
```

### 3.3 Agent Sees Updated Rule
1. In VS Code, ask agent: **"What are our rules for test function naming?"**

**Expected Response:**
- Should quote the new test rule
- Should mention it was recently updated
- Should provide the exact rule text

### 3.4 Rollback Test
```bash
# In lunar-snake-hub
git reset --hard HEAD~1
git push --force-with-lease

# In lablab-bean
task hub:sync

# Agent should no longer see the test rule
```

**Success Criteria:**
- ✅ Changes propagate within minutes
- ✅ Agent sees updated content immediately
- ✅ Rollback works correctly
- ✅ No caching issues or stale content

---

## Test 4: Letta Memory Persistence

### 4.1 Memory Save Test
1. In VS Code with lablab-bean, ask agent:
   **"Remember this decision: We chose Repository pattern for data access because it decouples domain logic from infrastructure details."**

2. Monitor for MCP tool call:
   - Should call `save_memory` or equivalent
   - Should save to Letta with appropriate key
   - Should return success confirmation

### 4.2 Memory Retrieval Test
1. Restart VS Code completely (close and reopen)
2. Start new conversation with agent
3. Ask: **"What pattern did we choose for data access and why?"**

**Expected Response:**
- Should call `get_memory` or equivalent
- Should retrieve the exact decision
- Should mention both pattern and reasoning

### 4.3 Multiple Memory Test
1. Save multiple decisions:
   - "Remember: We use TypeScript for type safety"
   - "Remember: We prefer functional components over class components"
   - "Remember: We enforce 80% test coverage minimum"

2. Test retrieval of each
3. Ask for summary of all decisions

### 4.4 Memory Persistence Across Projects
1. Open a different project/workspace
2. Ask about previous decisions
3. Should still be accessible (global memory)

### 4.5 Memory Error Handling
1. Try to retrieve non-existent memory
2. Should handle gracefully
3. Should indicate memory not found

**Success Criteria:**
- ✅ Agent can save and retrieve memories
- ✅ Memory persists across VS Code restarts
- ✅ Multiple memories don't interfere
- ✅ Error handling works correctly

---

## Test 5: End-to-End Integration

### 5.1 Complete Workflow Test
1. **Setup**: Ensure all components are running
   - Hub sync working
   - Letta accessible
   - MCP tools configured

2. **Scenario**: Implement a new feature
   ```
   User: "I need to add a new user authentication service. 
   Remember to follow our coding principles and naming conventions."
   ```

3. **Expected Agent Behavior:**
   - Checks hub rules for principles and conventions
   - Saves decision about authentication approach to memory
   - Follows established patterns
   - References hub rules throughout

### 5.2 Multi-Session Continuity Test
1. **Session 1**: Start implementing feature, save decisions
2. **Session 2**: Next day, continue implementation
3. **Expected**: Agent remembers previous decisions and context

### 5.3 Multi-Satellite Test (if available)
1. Set up a second satellite project
2. Verify it can sync from same hub
3. Verify shared memory access

**Success Criteria:**
- ✅ Complete workflow functions smoothly
- ✅ All components work together
- ✅ Context maintained across sessions
- ✅ Hub serves as single source of truth

---

## Test Results Tracking

### Test Results Template
```markdown
## Phase 1 Test Results - [Date]

### Test 1: Hub Sync
- [ ] Clean sync test
- [ ] File structure verification
- [ ] Sync validation
- **Status**: ❌ Failed / ⚠️ Partial / ✅ Passed
- **Issues**: [List any issues]

### Test 2: Agent Rules
- [ ] Basic rule query
- [ ] Multiple rule sources
- [ ] Adapter-specific rules
- [ ] Error handling
- **Status**: ❌ Failed / ⚠️ Partial / ✅ Passed
- **Issues**: [List any issues]

### Test 3: Hub Updates
- [ ] Rule update test
- [ ] Sync update test
- [ ] Agent sees updates
- [ ] Rollback test
- **Status**: ❌ Failed / ⚠️ Partial / ✅ Passed
- **Issues**: [List any issues]

### Test 4: Letta Memory
- [ ] Memory save test
- [ ] Memory retrieval test
- [ ] Multiple memory test
- [ ] Cross-project persistence
- [ ] Error handling
- **Status**: ❌ Failed / ⚠️ Partial / ✅ Passed
- **Issues**: [List any issues]

### Test 5: Integration
- [ ] Complete workflow
- [ ] Multi-session continuity
- [ ] Multi-satellite test
- **Status**: ❌ Failed / ⚠️ Partial / ✅ Passed
- **Issues**: [List any issues]

## Overall Status: ❌ Failed / ⚠️ Partial / ✅ Passed

## Blockers
- [List any blocking issues]

## Next Steps
- [List next actions]
```

---

## Troubleshooting Common Issues

### Hub Sync Issues
```bash
# Clear cache and resync
task hub:clean
rm -rf .hub-cache
task hub:sync

# Check git connectivity
git ls-remote https://github.com/GiantCroissant-Lunar/lunar-snake-hub

# Verify manifest
cat .hub-manifest.toml
```

### Agent Not Reading Rules
```bash
# Check cache exists
ls -la .hub-cache/agents/rules/

# Verify symlink
ls -la .agent

# Check file permissions
cat .hub-cache/agents/rules/20-rules.md
```

### Letta Memory Issues
```bash
# Test Letta directly
curl http://<mac-mini-hostname>:5055/v1/health

# Check MCP configuration
# Verify in VS Code settings

# Check network connectivity
ping <mac-mini-hostname>
```

### MCP Tool Not Available
1. Restart VS Code
2. Check MCP configuration syntax
3. Verify Letta is running
4. Check VS Code developer console

---

## Success Criteria Summary

✅ **Phase 1 Complete When:**
- All 5 test suites pass
- Hub sync works reliably
- Agent reads rules from hub
- Updates propagate correctly
- Memory persists across sessions
- End-to-end workflow functions

✅ **Ready for Production When:**
- Tests pass consistently
- No blocking issues
- Documentation complete
- Team trained on workflow

---

**Reference**: This test suite implements Task #8 from `PHASE1_PROGRESS.md`
