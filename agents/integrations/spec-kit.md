# Spec-Kit Integration

**Type**: Development Methodology
**Version**: 1.2.0
**Status**: Active
**Last Updated**: 2025-10-21
**Rule Reference**: R-TOOL-001, R-TOOL-003

## Overview

This project **REQUIRES** use of GitHub's **Spec-Kit** for Specification-Driven Development (SDD).

**All AI agents** (Claude, GitHub Copilot, Windsurf, Codex, Cursor, etc.) must use the Spec-Kit workflow when implementing new features.

Spec-Kit provides slash commands that enable AI-driven development from specifications.

## Architecture

```
.specify/               # Spec-Kit configuration (external)
├── memory/
│   └── constitution.md
├── scripts/
└── templates/

.claude/commands/       # Slash command implementations (external)
└── speckit.*.md

specs/                  # Generated specifications (project-managed)
└── NNN-feature-name/
    ├── spec.md
    ├── plan.md
    └── tasks.md
```

## Multi-Agent Support

### For Agents with Slash Command Support

**Examples:** Claude Code, GitHub Copilot Chat

Use slash commands directly:

```
/speckit.specify
/speckit.plan
/speckit.tasks
/speckit.implement
```

### For Agents without Slash Commands

**Examples:** Windsurf, Cursor, Codex, other AI coding assistants

Use task runner commands instead:

```bash
task speckit:specify
task speckit:plan
task speckit:tasks
task speckit:implement
```

These tasks are defined in `Taskfile.yml` and provide guidance for agents.

### For Non-AI Developers

Reference the Spec-Kit workflow manually:

1. Read `.agent/base/20-rules.md` (R-TOOL-001)
2. Review existing specs in `specs/`
3. Follow the SDD methodology

## Available Commands

### Core Workflow

Commands follow the SDD workflow:

```
/speckit.constitution → /speckit.specify → /speckit.plan → /speckit.tasks → /speckit.implement
```

**Task Runner Alternative:**

```bash
task speckit:constitution  # One-time setup
task speckit:specify       # Create spec
task speckit:plan          # Create plan
task speckit:tasks         # Generate tasks
task speckit:implement     # Execute
```

#### `/speckit.constitution`

**Purpose:** Establish project governance principles

**When to use:** First time setup, or when updating core principles

**Example:**

```
/speckit.constitution

Create constitution focusing on:
- Data-driven entity design (YAML/JSON)
- Component-based architecture
- Test-driven development
- Terminal.Gui best practices
```

**Output:** `.specify/memory/constitution.md`

---

#### `/speckit.specify`

**Purpose:** Define feature requirements (WHAT and WHY)

**When to use:** Starting a new feature

**Important:**

- Focus on WHAT and WHY, NOT HOW
- Describe user needs, not implementation
- Be explicit about requirements

**Example:**

```
/speckit.specify

Create an inventory system where players can:
- Pick up items from the dungeon floor
- View items in a grid-based inventory UI
- Equip weapons and armor to character slots
- Drop items back onto the floor
```

**Output:**

- New branch: `NNN-inventory-system`
- `specs/NNN-inventory-system/spec.md`

---

#### `/speckit.plan`

**Purpose:** Create technical implementation plan (HOW)

**When to use:** After specification is complete and clarified

**Important:**

- Now specify tech stack and architecture
- Reference constitution principles
- Consider existing codebase

**Example:**

```
/speckit.plan

Use data-driven approach:
- Item definitions in YAML files
- Component-based inventory system
- Terminal.Gui dialog for inventory UI
- Grid layout with 20 slots
```

**Output:**

- `specs/NNN-inventory-system/plan.md`
- `specs/NNN-inventory-system/data-model.md`
- `specs/NNN-inventory-system/contracts/`

---

#### `/speckit.tasks`

**Purpose:** Generate actionable task breakdown

**When to use:** After plan is validated

**Output:** `specs/NNN-inventory-system/tasks.md`

---

#### `/speckit.implement`

**Purpose:** Execute implementation from tasks

**When to use:** After tasks are reviewed

**Important:**

- AI will run local commands (dotnet, npm, etc.)
- Review generated code
- Test incrementally

---

### Enhancement Commands (Optional)

#### `/speckit.clarify`

**Purpose:** Ask structured clarifying questions

**When to use:** Before `/speckit.plan` if requirements are unclear

**Example:**

```
/speckit.clarify
```

AI asks systematic questions to de-risk ambiguities.

---

#### `/speckit.analyze`

**Purpose:** Cross-artifact consistency analysis

**When to use:** After `/speckit.tasks`, before `/speckit.implement`

Validates alignment between spec, plan, and tasks.

---

#### `/speckit.checklist`

**Purpose:** Generate quality validation checklists

**When to use:** After `/speckit.plan`

Creates "unit tests for English" - validates requirements completeness.

---

## Integration with .agent/ System

### Constitution Alignment

Spec-Kit constitution (`.specify/memory/constitution.md`) should align with:

- `.agent/base/10-principles.md` - Core development principles
- `.agent/base/20-rules.md` - Normative rules

**Recommendation:** Cross-reference both systems in constitution.

### Rule Compliance

Spec-Kit implementations must follow `.agent/` rules:

- **R-DOC-001**: Generated specs go to `specs/NNN-feature/` (not `docs/`)
- **R-DOC-002**: Include YAML front-matter in spec files
- **R-CODE-001**: No hardcoded secrets in generated code
- **R-TST-001**: Spec-Kit should include test generation

### Workflow Integration

```
User Request
    ↓
Check .agent/base/ principles
    ↓
/speckit.specify (generates spec aligned with principles)
    ↓
/speckit.plan (follows R-CODE, R-TST rules)
    ↓
/speckit.implement (validates against .agent/ standards)
```

## Best Practices

### 1. Constitution as Single Source of Truth

Create constitution that references `.agent/` rules:

```markdown
# .specify/memory/constitution.md

## Integration with Project Standards

This constitution extends the base rules in `.agent/base/`:

### From .agent/base/10-principles.md
- Principle 1: Simplicity First
- Principle 2: Explicit over Implicit

### From .agent/base/20-rules.md
- R-CODE-001: No hardcoded secrets
- R-DOC-001: Docs go to inbox first
- R-TST-001: Test critical paths
```

### 2. Feature Branches Align with Specs

Each spec gets a branch:

```
Branch: 042-inventory-system
Spec: specs/042-inventory-system/spec.md
```

Follows git workflow from `.agent/base/20-rules.md` (R-GIT rules).

### 3. Documentation Standards

Spec files should include YAML front-matter per R-DOC-002:

```yaml
---
doc_id: SPEC-042
title: Inventory System
doc_type: spec
status: draft
canonical: true
created: 2025-10-21
tags: [inventory, gameplay, ui]
summary: Player inventory management system
---
```

## Migration from Old System

Previously, the project had a fake "spec-kit" (template generator).

**Old System (REMOVED):**

- Handlebars templates
- Generated C# boilerplate
- YAML variable files

**New System (CURRENT):**

- AI-driven from specifications
- Living documentation
- Complete feature generation

See: `docs/_inbox/spec-kit-migration-complete.md`

## File Locations

### External (Managed by Spec-Kit)

```
.specify/               # DO NOT EDIT - managed by `specify` CLI
.claude/commands/       # DO NOT EDIT - managed by `specify` CLI
```

### Project-Managed

```
specs/                  # Managed by you via /speckit commands
├── 001-dungeon-system/
├── 002-inventory-system/
└── ...

.specify/memory/        # You edit constitution
└── constitution.md
```

## Troubleshooting

### Command Not Found

**Issue:** `/speckit.specify` doesn't autocomplete

**Fix:** Check `.claude/commands/` exists:

```bash
ls .claude/commands/speckit.*.md
```

### Scripts Not Executable

**Issue:** PowerShell scripts fail

**Fix:**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Branch Already Exists

**Issue:** Spec-Kit complains about existing branch

**Fix:** Delete old branch or use different feature name

## References

### External Documentation

- **Spec-Kit Repo:** <https://github.com/github/spec-kit>
- **SDD Methodology:** `ref-projects/spec-kit/spec-driven.md`

### Internal Documentation

- **Migration Guide:** `docs/_inbox/spec-kit-migration-complete.md`
- **Data-Driven Approach:** `docs/_inbox/data-driven-monster-approach.md`
- **Agent Principles:** `.agent/base/10-principles.md`
- **Agent Rules:** `.agent/base/20-rules.md`

## Agent-Agnostic Design

This integration is designed to work with **any AI coding assistant**:

| Agent | Integration Method | Notes |
|-------|-------------------|-------|
| Claude Code | `/speckit.*` slash commands | Native slash command support |
| GitHub Copilot | `/speckit.*` in chat | Uses Copilot Chat slash commands |
| Windsurf | `task speckit:*` commands | Via task runner |
| Cursor | `task speckit:*` commands | Via task runner |
| Codex | `task speckit:*` commands | Via task runner |
| Other AI | Read `.agent/integrations/spec-kit.md` | Manual reference |

### Why This Matters

**Consistency across teams:** Whether your team uses Claude, Copilot, or Windsurf, everyone follows the same Spec-Kit workflow.

**Future-proof:** New AI tools can integrate via task runner without code changes.

**Human-readable:** All specs are markdown files that humans can read and edit.

## Quick Start for Agents

### First Time Setup (Any Agent)

1. **Check if constitution exists:**

   ```bash
   ls .specify/memory/constitution.md
   ```

2. **If missing, create constitution:**
   - **Claude/Copilot:** `/speckit.constitution`
   - **Other agents:** `task speckit:constitution` (then follow prompts)

3. **Prompt for constitution:**

   ```
   Create constitution extending .agent/base/ rules:
   - Reference .agent/base/10-principles.md
   - Reference .agent/base/20-rules.md (R-CODE, R-TST, R-DOC, R-GIT, R-SEC)
   - Add game-specific rules for data-driven dungeon crawler design
   ```

### Implementing a Feature (Any Agent)

1. **Create specification (WHAT & WHY):**
   - **Claude/Copilot:** `/speckit.specify`
   - **Other:** `task speckit:specify` → describe feature

2. **Create plan (HOW):**
   - **Claude/Copilot:** `/speckit.plan`
   - **Other:** `task speckit:plan`

3. **Generate tasks:**
   - **Claude/Copilot:** `/speckit.tasks`
   - **Other:** `task speckit:tasks`

4. **Execute implementation:**
   - **Claude/Copilot:** `/speckit.implement`
   - **Other:** `task speckit:implement`

### Maintaining Specs After Implementation (Any Agent)

Follow **R-TOOL-003** for spec maintenance strategy:

**When to UPDATE existing spec:**

```bash
# Scenario: Bug fix or small adjustment
# Action: Update the existing spec file
cd specs/001-inventory-system/
# Edit spec.md, increment version (v1.0.0 → v1.0.1 or v1.1.0)
# Add changelog entry at bottom of spec
```

**Examples of updates:**

- Bug fixes: "Pickup doesn't work on diagonal tiles" → v1.0.1
- Small adjustments: "Change healing potion 30 HP → 40 HP" → v1.0.1
- Minor enhancements: "Add drop item feature" → v1.1.0

**When to CREATE new spec:**

```bash
# Scenario: Major new feature or breaking change
# Action: Create new spec with new number
/speckit.specify   # or: task speckit:specify
# Describe: "Item crafting system" → Creates specs/002-item-crafting/
```

**Examples of new specs:**

- New major features: Item crafting, trading, shops
- Breaking changes: Complete UI redesign
- Different user journeys: Multi-player inventory sharing

**Version Changelog Format:**

Add to bottom of spec file after implementation:

```markdown
## Version History

**Current Version**: v1.0.0

### v1.0.0 (2025-10-21) - Initial Release
- All P1/P2/P3 user stories implemented
- Item pickup, display, consumption, and equipment

### v1.0.1 (2025-10-25) - Bug Fix
- Fixed pickup detection for diagonal tiles (FR-003 clarification)

### v1.1.0 (2025-10-28) - Drop Items Enhancement
- Added P4 user story: Drop items from inventory
- Added FR-017: Players can drop items with 'D' key
```

**Reference:** See `.agent/base/20-rules.md` (R-TOOL-003)

## Version History

- **1.2.0** (2025-10-21): Added spec maintenance strategy (R-TOOL-003)
- **1.1.0** (2025-10-21): Added multi-agent support and task runner integration
- **1.0.0** (2025-10-21): Initial integration with .agent/ system

---

**Status:** Active and integrated with .agent/ architecture
**Multi-Agent:** ✅ Supports all AI coding assistants
