---
doc_id: DOC-2025-00001
title: lunar-snake-hub
doc_type: reference
status: active
canonical: true
created: 2025-10-30
tags: [hub, overview, reference, infrastructure]
summary: Central hub for lunar-snake projects - single source of truth for specs, agent rules, build components, and shared infrastructure
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# lunar-snake-hub

**Central hub for lunar-snake projects** - Single source of truth for specs, agent rules, and shared infrastructure.

## 🎯 Purpose

This repository provides:

- **Specifications & RFCs** - API contracts, architecture decisions, design docs
- **Agent Rules** - AI agent prompts, coding standards, best practices
- **Pre-commit Hooks** - Shared linting, formatting, security checks
- **Infrastructure Templates** - Docker, Terraform, GitHub Actions

## 🏗️ Architecture

Satellite repos (like `lablab-bean`) consume this hub via:

1. **`.hub-manifest.toml`** - Pins versions of packs to use
2. **`task hub:sync`** - Fetches assets to `.hub-cache/` (gitignored)
3. **Runtime access** - Agents read rules; build orchestration is provided by the separate `unify-build` repository

**Key principle:** Satellites commit only code + manifest. All shared assets are synced at runtime.

## 📁 Structure

```
lunar-snake-hub/
├── .agent/              # Agent configs (rules, skills, workflows, adapters)
│   ├── rules/           # Coding standards & project rules
│   ├── skills/          # Reusable skills
│   ├── workflows/       # Orchestrated workflows
│   ├── adapters/        # IDE-specific configs (Cline, Roo, etc.)
│   └── scripts/         # Helper scripts for agent workflows
├── specs/              # Specifications & RFCs
│   └── {domain}/
│       └── v{version}/
│           ├── rfc.md
│           ├── adr.md
│           └── schema/
├── precommit/          # Pre-commit hooks
│   ├── .pre-commit-config.base.yaml
│   └── hooks/
├── infra/              # Infrastructure & secrets
│   ├── .sops.yaml
│   └── secrets/
│       └── *.enc.yaml
├── .github/
│   └── workflows/      # Reusable GitHub Actions
├── docs/               # Documentation
│   ├── README.md       # 📖 Documentation index
│   ├── architecture/   # Design docs & decisions
│   ├── guides/         # How-to guides
│   ├── operations/     # Runbooks & procedures
│   └── sessions/       # Session handovers & progress
```

## 🚀 Quick Start (For Satellites)

### 1. Add manifest to your project

**`.hub-manifest.toml`:**

```toml
[hub]
repo = "GiantCroissant-Lunar/lunar-snake-hub"

[packs]
agents = "0.1.0"
precommit = "0.1.0"
```

### 2. Add sync task

**`Taskfile.yml`:**

```yaml
tasks:
  hub:sync:
    desc: Sync assets from lunar-snake-hub
    cmds:
      - |
        if [ ! -d .hub-cache/hub-repo ]; then
          git clone https://github.com/GiantCroissant-Lunar/lunar-snake-hub .hub-cache/hub-repo
        else
          git -C .hub-cache/hub-repo pull
        fi
        cp -r .hub-cache/hub-repo/.agent .hub-cache/
        echo "✅ Hub sync complete"
```

### 3. Gitignore synced content

**`.gitignore`:**

```
.hub-cache/
.agent          # If using symlink
```

### 4. Sync and use

```bash
task hub:sync
# Agents now read from .hub-cache/.agent/rules/
```

## 📚 Documentation

**📖 [Documentation Index](docs/README.md)** - Complete guide to all documentation

### Quick Access

- **[Quick Start](docs/operations/START_HERE.md)** - What to read first
- **[Phase 1 Progress](docs/sessions/PHASE1_PROGRESS.md)** - Current implementation status
- **[MCP Setup](docs/operations/MCP_SETUP.md)** - Smithery server configuration
- **[Architecture Discussion](docs/architecture/ARCHITECTURE_DISCUSSION.md)** - Complete system design
- **[Phase 1 Checklist](docs/guides/PHASE1_CHECKLIST.md)** - Step-by-step implementation guide

## 🔐 Secrets Management

Secrets are encrypted with [SOPS](https://github.com/mozilla/sops) and stored in `infra/secrets/*.enc.yaml`.

**Decrypt:**

```bash
sops decrypt infra/secrets/mac-mini.enc.yaml
```

**Encrypt:**

```bash
sops encrypt infra/secrets/mac-mini.yaml > infra/secrets/mac-mini.enc.yaml
```

## 🛠️ Infrastructure Services

This hub supports a Mac Mini "brain" running:

- **Letta** - Persistent agent memory
- **Qdrant** - Vector database for RAG
- **Context Gateway** - HTTP API for context retrieval
- **n8n** - Workflow orchestration

See `infra/README.md` for setup.

## 🔧 Build System

Build orchestration and reusable NUKE components are now owned by the dedicated `unify-build` repository.

Satellite repos should use `unify-build` for all build pipelines and publish workflows; `lunar-snake-hub` no longer ships build scripts or NUKE components.

## 📦 Versioning

Releases are tagged by pack type:

- `packs-agents-v0.1.0` - Agent rules/prompts
- `packs-precommit-v0.1.0` - Pre-commit hooks
- `spec-{domain}-v1.0.0` - Specification releases

## 📦 npm Package Consumption

Install into a consumer repo (runs hook installer automatically via `postinstall`):

```powershell
npm install @giantcroissant-lunar/lunar-snake-hub
```

Uninstall (runs cleanup via `preuninstall`, restores backups, unsets `core.hooksPath`):

```powershell
npm uninstall @giantcroissant-lunar/lunar-snake-hub
```

Manual hook install/uninstall:

```powershell
pwsh -File precommit\utils\install.ps1
pwsh -File precommit\utils\uninstall.ps1 -Restore
```

Run end-to-end dogfood test:

```powershell
task -f Taskfile.hub.yml hub:dogfood:e2e
```

Include shared Taskfile fragment in consumer repos:

```powershell
task -f Taskfile.hub.yml hub:install-hooks
```

Notes:

- Hub-installed hooks are marked with `# managed-by: lunar-snake-hub` and backed up prior to overwrite.
- Uninstall removes only managed hooks and restores backups.

## 🤝 Contributing

1. Create feature branch: `git checkout -b feat/new-agent-rule`
2. Make changes to `.agent/`, `precommit/`, `docs/`, etc.
3. Update version in `registry/packs.toml` (if applicable)
4. Commit: `git commit -m "feat: add new coding rule"`
5. Push and open PR

## 📖 Learn More

- **Naming Convention:** Lunar year naming (lunar-snake → lunar-horse → ...)
- **Organization:** [GiantCroissant-Lunar](https://github.com/GiantCroissant-Lunar)
- **Satellite Repos:** [lablab-bean](https://github.com/GiantCroissant-Lunar/lablab-bean) (pilot)

## 📄 License

See LICENSE file.

---

**Status:** Phase 1 - Foundation
**Version:** 0.1.0
**Last Updated:** 2025-10-30
