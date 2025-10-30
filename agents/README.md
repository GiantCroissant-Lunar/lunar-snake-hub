---
doc_id: DOC-2025-00016
title: Agent Rules & Prompts Directory
doc_type: reference
status: active
canonical: true
created: 2025-10-30
tags: [agents, rules, prompts, directory, reference]
summary: Directory reference for agent rules, prompts, adapters, and scripts consumed by satellite repos
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# Agent Rules & Prompts

This directory contains all agent-related assets consumed by satellite repos.

## Structure

```
agents/
├── rules/          # Coding standards, conventions, best practices
├── prompts/        # Agent prompt templates for common tasks
├── adapters/       # IDE-specific configurations (Cline, Roo, Kilo, etc.)
└── scripts/        # Helper scripts for agent workflows
```

## Rules Naming Convention

**Format:** `R-{CATEGORY}-{NUMBER}-{description}.md`

**Categories:**
- `R-CODE-*` - Code style, naming, structure
- `R-DOC-*` - Documentation standards
- `R-NUKE-*` - Build rules
- `R-PRC-*` - Process/workflow rules
- `R-TEST-*` - Testing standards

**Examples:**
- `R-CODE-010-naming-conventions.md`
- `R-DOC-030-inline-comments.md`
- `R-NUKE-001-common-targets.md`

## Next Steps (Phase 1)

Extract agent rules from `lablab-bean/.agent/`:
1. Copy `lablab-bean/.agent/base/` → `agents/rules/`
2. Copy `lablab-bean/.agent/agents/` → `agents/prompts/`
3. Copy `lablab-bean/.agent/adapters/` → `agents/adapters/`
4. Generalize (remove lablab-specific content)
5. Organize according to naming convention

See: `docs/guides/PHASE1_CHECKLIST.md` (Task #2)
