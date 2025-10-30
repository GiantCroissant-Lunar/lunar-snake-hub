# Letta MCP Tool Configuration Guide

This guide explains how to configure Letta as an MCP (Model Context Protocol) tool in VS Code for Phase 1.

## Prerequisites

- Letta is running on Mac Mini (see Task #6)
- Tailscale connectivity between Windows and Mac Mini
- Mac Mini's Tailscale hostname known

## Step 1: Find Your MCP Configuration

### Option A: VS Code Settings (Recommended)
1. Open VS Code
2. Go to **Settings** (Ctrl+, or Cmd+,)
3. Search for "MCP" or "Cline"
4. Look for "MCP Servers" configuration

### Option B: Workspace Configuration File
1. Check for `.mcp-config.json` in your workspace root
2. Or look in `.vscode/settings.json`

### Option C: Cline Extension Settings
1. VS Code → Extensions → Cline
2. Look for MCP Server configuration

## Step 2: Add Letta MCP Configuration

Add the following configuration to your MCP settings:

```json
{
  "mcpServers": {
    "letta-memory": {
      "type": "http",
      "baseUrl": "http://<mac-mini-tailscale-name>:5055",
      "description": "Persistent agent memory via Letta",
      "tools": [
        {
          "name": "save_memory",
          "description": "Save a decision or context to persistent memory",
          "method": "POST",
          "path": "/v1/agents/default/memory",
          "headers": {
            "Content-Type": "application/json"
          }
        },
        {
          "name": "get_memory",
          "description": "Retrieve saved decision or context",
          "method": "GET",
          "path": "/v1/agents/default/memory/{key}",
          "headers": {
            "Content-Type": "application/json"
          }
        },
        {
          "name": "list_memories",
          "description": "List all saved memories",
          "method": "GET",
          "path": "/v1/agents/default/memories",
          "headers": {
            "Content-Type": "application/json"
          }
        },
        {
          "name": "delete_memory",
          "description": "Delete a specific memory",
          "method": "DELETE",
          "path": "/v1/agents/default/memory/{key}",
          "headers": {
            "Content-Type": "application/json"
          }
        }
      ]
    }
  }
}
```

**IMPORTANT**: Replace `<mac-mini-tailscale-name>` with your actual Mac Mini Tailscale hostname (e.g., `mac-mini.tailscale.net`).

## Step 3: Verify Letta API Endpoints

Before configuring MCP, verify the actual Letta API endpoints:

```bash
# On Mac Mini
curl http://localhost:5055/docs

# Or from Windows
curl http://<mac-mini-tailscale-name>:5055/docs
```

The actual endpoints might differ from the examples above. Update the MCP configuration accordingly.

## Step 4: Test MCP Configuration

### Basic Memory Test
1. Restart VS Code to load the new MCP configuration
2. Open a conversation with Cline/Roo/Kilo
3. Ask: **"Remember this: We chose Repository pattern for data access"**
4. The agent should call the `save_memory` tool

### Memory Retrieval Test
1. Restart VS Code completely
2. Ask: **"What pattern did we choose for data access?"**
3. The agent should call `get_memory` and recall the previous decision

## Step 5: Common MCP Configuration Patterns

### Pattern 1: VS Code Settings UI
```json
// In VS Code Settings
{
  "cline.mcpServers": {
    "letta-memory": {
      "type": "http",
      "baseUrl": "http://mac-mini.tailscale.net:5055",
      // ... rest of configuration
    }
  }
}
```

### Pattern 2: Workspace .mcp-config.json
```json
{
  "mcpServers": {
    "letta-memory": {
      // ... configuration
    }
  }
}
```

### Pattern 3: .vscode/settings.json
```json
{
  "mcp.mcpServers": {
    "letta-memory": {
      // ... configuration
    }
  }
}
```

## Troubleshooting

### MCP Server Not Found
```bash
# Check if Letta is running
curl http://<mac-mini-tailscale-name>:5055/v1/health

# Check network connectivity
ping <mac-mini-tailscale-name>
```

### Tool Not Available
1. Restart VS Code
2. Check MCP configuration syntax
3. Verify Letta API endpoints exist
4. Check VS Code developer console for errors

### Authentication Issues
If Letta requires authentication:
```json
{
  "headers": {
    "Authorization": "Bearer <your-token>",
    "Content-Type": "application/json"
  }
}
```

### SSL/TLS Issues
If using HTTPS:
```json
{
  "baseUrl": "https://<mac-mini-tailscale-name>:5055",
  "allowInsecure": true,
  // ... rest of configuration
}
```

## Step 6: Advanced Configuration

### Custom Tool Mappings
If Letta has different API structure:

```json
{
  "tools": [
    {
      "name": "store_context",
      "method": "POST",
      "path": "/api/agents/{agent_id}/messages",
      "body": {
        "role": "system",
        "content": "{{content}}"
      }
    }
  ]
}
```

### Multiple Agents
```json
{
  "tools": [
    {
      "name": "save_to_agent",
      "path": "/v1/agents/{{agent_id}}/memory"
    }
  ]
}
```

## Next Steps

After MCP configuration is working:

1. **Run Phase 1 Tests**: Execute the complete test suite (Task #8)
2. **Verify Memory Persistence**: Test across VS Code restarts
3. **Commit lablab-bean Changes**: Finalize the satellite configuration

## Success Criteria

✅ **MCP Configuration Working:**
- Letta tools appear in agent tool list
- Agent can save and retrieve memories
- Configuration persists across VS Code restarts

✅ **Integration Verified:**
- Memory works across different conversations
- Agent recalls decisions correctly
- No errors in VS Code developer console

---

**Reference**: This setup is part of Phase 1 Task #7 in `PHASE1_PROGRESS.md`
