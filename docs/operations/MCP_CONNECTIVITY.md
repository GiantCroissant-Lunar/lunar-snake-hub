---
doc_id: DOC-2025-00009
title: MCP Connectivity Verification
doc_type: guide
status: active
canonical: true
created: 2025-10-31
tags: [mcp, connectivity, verification, troubleshooting]
summary: Guide to verify and troubleshoot MCP server connectivity for Cline and Windsurf
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# MCP Connectivity Verification

**Complete guide to verify MCP servers are working in Cline and Windsurf.**

---

## 🔍 Quick Verification Test

### 1. Test Server Accessibility

```bash
# Test each MCP server is accessible via npx
npx -y @playwright/mcp --version
npx -y @modelcontextprotocol/server-filesystem D:\lunar-snake\lunar-snake-hub --help
npx -y @upstash/context7-mcp --help
npx -y @modelcontextprotocol/server-sequential-thinking --help
```

**Expected Results:**

- ✅ Playwright: Shows version and help options
- ✅ Filesystem: Shows error (expected - needs directory path)
- ✅ Context7: Shows usage help
- ✅ Sequential Thinking: Starts server (expected)

---

## 🛠️ Cline Configuration

### Local Project Config

**File:** `d:\lunar-snake\lunar-snake-hub\cline_mcp_settings.json`

### Global Cline Config

**File:** `c:\Users\User\AppData\Roaming\Cline\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

### Verification Steps

1. **Open Cline settings** → MCP Servers
2. **Check servers are listed** with green status
3. **Restart Cline** after config changes
4. **Test tools** in chat: "Show me filesystem tools"

---

## 🌊 Windsurf Configuration

### Global Windsurf Config

**File:** `c:\Users\User\AppData\Roaming\Windsurf\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

### Verification Steps

1. **Open Windsurf** → Command Palette → "MCP: Show Servers"
2. **Check server status** (should show connected)
3. **Restart Windsurf** after config changes
4. **Test tools** in chat: "List available MCP tools"

---

## 🧪 Functional Testing

### Test Filesystem Operations

```bash
# In Cline/Windsurf chat, ask:
"Read the README.md file using filesystem tools"
"Create a test file in docs/operations/"
"List the contents of the .agent/ directory"
```

### Test Playwright

```bash
# In chat, ask:
"Take a screenshot of https://example.com"
"Navigate to a webpage and extract text"
```

### Test Context7

```bash
# In chat, ask:
"Show me React documentation for useState"
"How do I implement authentication in Next.js?"
```

### Test Sequential Thinking

```bash
# In chat, ask:
"Use sequential thinking to solve this coding problem"
"Break down this complex task into steps"
```

---

## 🔧 Troubleshooting Guide

### Common Issues & Solutions

#### ❌ "Server not found" Error

**Cause:** Incorrect package name or network issues
**Solution:**

```bash
# Verify package exists
npm view @package/name

# Clear npm cache
npm cache clean --force

# Check internet connection
ping registry.npmjs.org
```

#### ❌ "Permission denied" Error

**Cause:** Filesystem server lacks proper permissions
**Solution:**

```json
{
  "autoApprove": [
    "list_allowed_directories",
    "read_text_file",
    "write_text_file",
    "create_directory",
    "list_directory",
    "move_file",
    "delete_file"
  ]
}
```

#### ❌ "Server failed to start" Error

**Cause:** Port conflicts or missing dependencies
**Solution:**

```bash
# Check if port is in use
netstat -ano | findstr :3000

# Kill conflicting processes
taskkill /PID <process_id> /F

# Restart IDE/client
```

#### ❌ "Tools not available" Error

**Cause:** Server started but tools not loaded
**Solution:**

1. Check server logs in IDE console
2. Verify configuration syntax
3. Restart the IDE completely
4. Check for conflicting MCP configurations

### Debug Mode

Enable debug logging by adding to config:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@package/name", "--debug"],
      "env": {
        "DEBUG": "mcp:*"
      }
    }
  }
}
```

---

## 📊 Status Verification

### Check Server Health

```bash
# Create a test script to verify all servers
node -e "
const servers = [
  '@playwright/mcp',
  '@modelcontextprotocol/server-filesystem',
  '@upstash/context7-mcp',
  '@modelcontextprotocol/server-sequential-thinking'
];

servers.forEach(async (server) => {
  try {
    const { exec } = require('child_process');
    exec(\`npx -y \${server} --version\`, (error, stdout) => {
      console.log(\`✅ \${server}: \${stdout.trim()}\`);
    });
  } catch (error) {
    console.log(\`❌ \${server}: \${error.message}\`);
  }
});
"
```

### Monitor Server Activity

**In Cline/Windsurf console:**

- Look for "MCP server connected" messages
- Check for tool registration logs
- Monitor error messages during startup

---

## 🔄 Configuration Sync

### Copy Between Environments

```bash
# Copy local config to global
copy "d:\lunar-snake\lunar-snake-hub\cline_mcp_settings.json" "c:\Users\User\AppData\Roaming\Cline\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json"

# Copy to Windsurf
copy "d:\lunar-snake\lunar-snake-hub\cline_mcp_settings.json" "c:\Users\User\AppData\Roaming\Windsurf\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json"
```

### Environment-Specific Configs

For different projects, create project-specific configs:

```json
// Project-specific: ./cline_mcp_settings.json
{
  "mcpServers": {
    "@modelcontextprotocol/server-filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    }
  }
}
```

---

## 📞 Getting Help

### Check Logs

**Cline:** Help → Toggle Developer Tools → Console
**Windsurf:** View → Toggle Developer Tools → Console

### Community Support

- **[MCP Discord](https://discord.gg/modelcontextprotocol)**
- **[Cline Issues](https://github.com/roovetermaninc/roo-cline/issues)**
- **[Windsurf Support](https://windsurf.dev/support)**

### Server-Specific Issues

- **Playwright:** [@playwright/mcp GitHub](https://github.com/microsoft/playwright-mcp)
- **Filesystem:** [MCP Servers GitHub](https://github.com/modelcontextprotocol/servers)
- **Context7:** [Upstash Context7](https://github.com/upstash/context7-mcp)
- **Sequential Thinking:** [MCP Sequential Thinking](https://github.com/modelcontextprotocol/servers)

---

## ✅ Success Checklist

- [ ] All npm packages accessible via `npx`
- [ ] Configuration files valid JSON
- [ ] Servers show "connected" status in IDE
- [ ] Tools appear in chat completions
- [ ] File operations work within project scope
- [ ] Playwright can navigate and take screenshots
- [ ] Context7 returns documentation
- [ ] Sequential thinking processes complex tasks

---

**Last Updated:** 2025-10-31
**Tested on:** Windows 11, Node.js 18+, Cline 1.0+, Windsurf 1.0+
