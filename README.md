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

**Central hub for lunar-snake projects** - Single source of truth for specs, agent rules, build components, and shared infrastructure.

## 🎯 Purpose

This repository provides:
- **Specifications & RFCs** - API contracts, architecture decisions, design docs
- **Agent Rules** - AI agent prompts, coding standards, best practices
- **Build Components** - Reusable NUKE build targets for .NET/Unity projects
- **Pre-commit Hooks** - Shared linting, formatting, security checks
- **Infrastructure Templates** - Docker, Terraform, GitHub Actions

## 🏗️ Architecture

Satellite repos (like `lablab-bean`) consume this hub via:
1. **`.hub-manifest.toml`** - Pins versions of packs to use
2. **`task hub:sync`** - Fetches assets to `.hub-cache/` (gitignored)
3. **Runtime access** - Agents read rules, builds use NUKE components

**Key principle:** Satellites commit only code + manifest. All shared assets are synced at runtime.

## 📁 Structure

```
lunar-snake-hub/
├── agents/              # Agent rules, prompts, adapters
│   ├── rules/          # Coding standards (R-CODE-*, R-DOC-*, etc.)
│   ├── prompts/        # Agent prompt templates
│   └── adapters/       # IDE-specific configs (Cline, Roo, etc.)
├── nuke/               # NUKE build components
│   ├── Build.Common.cs
│   ├── Build.DotNet.cs
│   └── Build.Unity.cs
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
└── docs/               # Documentation
    ├── architecture/   # Design docs
    └── guides/         # How-to guides
```

## 🚀 Quick Start (For Satellites)

### 1. Add manifest to your project

**`.hub-manifest.toml`:**
```toml
[hub]
repo = "GiantCroissant-Lunar/lunar-snake-hub"

[packs]
agents = "0.1.0"
nuke = "0.1.0"
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
        cp -r .hub-cache/hub-repo/agents .hub-cache/
        cp -r .hub-cache/hub-repo/nuke .hub-cache/
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
# Agents now read from .hub-cache/agents/rules/
# NUKE imports from .hub-cache/nuke/
```

## 📚 Documentation

- **[Architecture Discussion](docs/architecture/ARCHITECTURE_DISCUSSION.md)** - Complete system design
- **[Quick Reference](docs/architecture/ARCHITECTURE_QUICK_REF.md)** - Command cheat sheets
- **[Decisions Summary](docs/architecture/YOUR_DECISIONS_SUMMARY.md)** - Design decisions & rationale
- **[Phase 1 Checklist](docs/guides/PHASE1_CHECKLIST.md)** - Implementation guide

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

## 📦 Versioning

Releases are tagged by pack type:
- `packs-agents-v0.1.0` - Agent rules/prompts
- `packs-nuke-v0.1.0` - NUKE build components
- `packs-precommit-v0.1.0` - Pre-commit hooks
- `spec-{domain}-v1.0.0` - Specification releases

## 🤝 Contributing

1. Create feature branch: `git checkout -b feat/new-agent-rule`
2. Make changes to `agents/`, `nuke/`, etc.
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
