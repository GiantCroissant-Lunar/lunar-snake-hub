---
doc_id: DOC-2025-00008
title: MCP Server Setup with Smithery
doc_type: guide
status: active
canonical: true
created: 2025-10-31
tags: [mcp, smithery, setup, configuration]
summary: Guide to setting up MCP servers using Smithery registry for lunar-snake-hub
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# MCP Server Setup with Smithery

**Configuration for Model Context Protocol (MCP) servers using Smithery registry.**

---

## 🎯 Overview

This project uses **Smithery** - the largest marketplace of MCP servers - to manage AI agent tools and extensions. Smithery provides:

- 2,300+ pre-built MCP servers
- Centralized registry and updates
- Cross-platform compatibility
- Quality assurance and maintenance

---

## 📁 Configuration Files

### Primary Configuration

**`cline_mcp_settings.json`** - Main MCP server configuration for Cline/Windsurf

### Server Registry

All servers are sourced from [Smithery.ai](https://smithery.ai) - browse for additional servers as needed.

---

## 🔧 Active Servers

### 1. **@microsoft/playwright-mcp**

- **Purpose:** Browser automation and web interactions
- **Source:** Microsoft's official Playwright MCP server
- **Tools:** Page navigation, element interaction, screenshots
- **Usage:** `npx -y @microsoft/playwright-mcp`

### 2. **@smithery-ai/filesystem**

- **Purpose:** File system operations
- **Source:** Smithery's official filesystem server
- **Tools:** Read/write files, directory management
- **Scope:** Limited to `D:\lunar-snake\lunar-snake-hub`
- **Auto-approved:** All file operations within project scope

### 3. **@upstash/context7-mcp**

- **Purpose:** Up-to-date code documentation
- **Source:** Context7 by Upstash
- **Tools:** SDK documentation, framework references
- **Usage:** `npx -y @upstash/context7-mcp`

### 4. **@smithery-ai/server-sequential-thinking**

- **Purpose:** Structured problem-solving
- **Source:** Smithery's sequential thinking server
- **Tools:** Multi-step reasoning, hypothesis validation
- **Usage:** `npx -y @smithery-ai/server-sequential-thinking`

---

## 🚀 Setup Instructions

### 1. Prerequisites

```bash
# Ensure Node.js is installed
node --version
npm --version

# Verify npx works
npx --version
```

### 2. Configuration

The `cline_mcp_settings.json` file is already configured with Smithery servers. No additional setup needed.

### 3. Adding New Servers

1. Browse [Smithery.ai](https://smithery.ai/search)
2. Find desired server package name
3. Add to `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "your-server-name": {
      "command": "npx",
      "args": ["-y", "@package/name"],
      "description": "Server description",
      "source": "smithery"
    }
  }
}
```

---

## 🔍 Server Management

### Adding Servers

```bash
# Test server installation before adding to config
npx -y @package/name --help
```

### Updating Servers

```bash
# Clear npx cache to force update
npx clear-npx-cache
# Restart your IDE/client to reload servers
```

### Troubleshooting

```bash
# Check if server is accessible
npx -y @package/name --version

# Clear npx cache if issues occur
npx clear-npx-cache
```

---

## 📊 Benefits of Smithery

### ✅ Advantages

- **Centralized:** Single registry for all MCP servers
- **Quality:** Vetted, production-ready servers
- **Updates:** Automatic maintenance and security patches
- **Discovery:** Easy to find servers by category
- **Cross-platform:** Works on Windows, macOS, Linux

### 🔄 Migration Benefits

- **Simplified setup:** No more empty local directories
- **Reduced maintenance:** Servers managed by Smithery
- **Better documentation:** Each server has dedicated docs
- **Community support:** Active development and issues tracking

---

## 🛠️ Advanced Configuration

### Custom Server Paths

```json
{
  "mcpServers": {
    "@smithery-ai/filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@smithery-ai/filesystem",
        "D:\\custom\\path"
      ],
      "autoApprove": ["list_allowed_directories", "read_text_file"]
    }
  }
}
```

### Environment Variables

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@package/name"],
      "env": {
        "API_KEY": "your-key",
        "CUSTOM_VAR": "value"
      }
    }
  }
}
```

---

## 📚 Additional Resources

- **[MCP Connectivity Guide](MCP_CONNECTIVITY.md)** - Verify and troubleshoot MCP servers
- **[Smithery Documentation](https://smithery.ai/docs)** - Complete setup guide
- **[MCP Specification](https://modelcontextprotocol.io)** - Protocol details
- **[Server Marketplace](https://smithery.ai/search)** - Browse 2,300+ servers

---

## 🆘 Support

### Common Issues

1. **Server not found:** Verify package name on Smithery
2. **Permission denied:** Check autoApprove settings
3. **Path issues:** Ensure absolute paths are correct

### Getting Help

- Check server documentation on Smithery
- Review [Smithery Discord](https://discord.gg/sKd9uycgH9)
- Open issue on server's GitHub repository

---

**Last Updated:** 2025-10-31
**Maintained by:** [GiantCroissant-Lunar](https://github.com/GiantCroissant-Lunar)
