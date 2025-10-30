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
