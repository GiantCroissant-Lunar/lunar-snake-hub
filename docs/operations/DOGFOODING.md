---
doc_id: DOC-2025-00003
title: Dogfooding in lunar-snake-hub
doc_type: guide
status: active
canonical: true
created: 2025-10-30
tags: [dogfooding, infrastructure, best-practices, self-reference]
summary: Guide to dogfooding in lunar-snake-hub - how the hub uses its own infrastructure to ensure quality and prove it works
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# Dogfooding Checklist

Use this checklist to validate `lunar-snake-hub` when consumed as a package.

## Pre-commit Hooks

- Install with: `pwsh -File precommit/utils/install.ps1`
- Verify empty commit triggers hooks: `git commit --allow-empty -m "hook test"`
- Confirm `git config --local core.hooksPath` is `.git/hooks`

## Taskfile Import

- Include `Taskfile.hub.yml` in consumer project and list tasks.
- Run `task hub:install-hooks` and confirm success.

## .agent Rules/Adapters

- Ensure IDE integrations and agents reference `.agent/` as single source of truth.
- Validate any adapter-specific setup in `.agent/adapters/README.md`.

## Versioning

- Consumer pins to a tag (e.g., `hub-v0.1.0`) or a published package version.
- Record changes in release notes.

## Notes

- Capture pass/fail and any issues discovered.

---

# Dogfooding in lunar-snake-hub

**Status:** ✅ Implemented
**Date:** 2025-10-30
**Principle:** The hub practices what it preaches

---

## What is Dogfooding?

This hub provides infrastructure (agent rules, pre-commit hooks, build tools) for satellite repositories. To ensure quality and prove that our infrastructure works, **the hub uses its own infrastructure**.

This is called "dogfooding" (eating your own dog food).

---

## What We Dogfood

### 1. Agent Rules via `.agent/`

**What:** The hub stores agent rules in `.agent/rules/`. Satellites sync these rules into `.hub-cache/.agent/` and may create a `.agent/` junction pointing to that cache location for IDEs.

**Why:** AI assistants (like Claude, Copilot, Windsurf) read from `.agent/` to understand coding standards. By using `.agent/` consistently in both hub and satellites, agents see the same rule set everywhere.

**Location:** `.agent/` (gitignored directory, often a symlink to `.hub-cache/.agent/` in satellites)

**Test:**

```bash
ls .agent/rules/
# Should show: 00-index.md, 10-principles.md, 20-rules.md, etc.
```

---

### 2. Pre-commit Hooks

**What:** The hub defines pre-commit hooks in `.pre-commit-config.yaml` and installs them in `.git/hooks/`

**Why:** Ensures all commits to the hub pass validation (markdown lint, YAML checks, security scans) before they're committed.

**Location:** `.pre-commit-config.yaml` + `.git/hooks/pre-commit`

**Test:**

```bash
pre-commit run --all-files
# Should run: trailing-whitespace, yaml checks, markdown lint, etc.
```

---

### 3. Hub Self-Reference via `.hub-manifest.toml`

**What:** The hub has its own `.hub-manifest.toml` that references itself

**Why:**

- Proves the manifest format works
- Allows testing `task hub:sync` on the hub itself
- Validates version pinning mechanism

**Location:** `.hub-manifest.toml`

**Test:**

```bash
task hub:sync
task hub:check
# Should sync agents and precommit from hub to .hub-cache/
```

---

### 4. Task Runner (Taskfile.yml)

**What:** The hub uses Task for automation (validation, testing, linting)

**Why:** Satellites use Task for `hub:sync` and other operations. The hub uses it too for consistency.

**Location:** `Taskfile.yml`

**Available tasks:**

```bash
task --list

# Key tasks:
task validate:all       # Validate hub structure and agents
task hub:sync           # Dogfood test: sync from self
task pre-commit:run     # Run pre-commit checks
task test:all           # Run all tests
task ci                 # Run CI checks locally
```

---

### 5. GitHub Actions CI

**What:** CI workflow runs pre-commit, validation, and tests on every push/PR

**Why:** Ensures hub changes don't break infrastructure that satellites depend on

**Location:** `.github/workflows/ci.yml`

**Jobs:**

- `pre-commit`: Run all pre-commit hooks
- `validate`: Validate hub structure and agent rules
- `test-sync`: Test hub sync mechanism (dogfooding)
- `lint-markdown`: Lint all markdown files
- `check-docs`: Verify required documentation exists
- `security`: Check for hardcoded secrets

---

## File Structure (Dogfooding Edition)

```
lunar-snake-hub/
├── .agent/                     # ✅ Agent configs (rules, skills, workflows, adapters)
├── .hub-manifest.toml          # ✅ Self-reference manifest
├── Taskfile.yml                # ✅ Task automation
├── .pre-commit-config.yaml     # ✅ Pre-commit hooks
├── .gitignore                  # ✅ Updated with hub patterns
├── .github/
│   └── workflows/
│       └── ci.yml              # ✅ CI automation
├── precommit/                  # Source of truth for pre-commit hooks
├── nuke/                       # Source of truth for NUKE components
└── docs/                       # Documentation
```

---

## Benefits of Dogfooding

### 1. **Quality Assurance**

- If hub's infrastructure is broken, we catch it immediately
- Every commit to the hub is validated by its own rules

### 2. **Documentation by Example**

- Satellites can copy the hub's setup
- The hub IS the reference implementation

### 3. **Confidence**

- We know the infrastructure works because we use it daily
- No "do as I say, not as I do"

### 4. **Rapid Iteration**

- Test infrastructure changes on the hub before satellites adopt them
- Catch issues early

---

## How to Verify Dogfooding Works

### Quick Check

```bash
cd D:\lunar-snake\lunar-snake-hub

# 1. Check .agent directory exists and works
# 1. Check .agent directory (or symlink) exists and works
ls .agent/rules/

# 2. Check pre-commit hooks installed
test -f .git/hooks/pre-commit && echo "✅ Installed"

# 3. Run validation
task validate:all

# 4. Test hub sync
task hub:sync
task hub:check
```

### Full Test Suite

```bash
# Run all tests (structure, agents, sync)
task test:all

# Run CI checks locally (same as GitHub Actions)
task ci

# Run pre-commit on all files
pre-commit run --all-files
```

---

## What's NOT Dogfooded (Intentionally)

### NUKE Build Components

**Why:** The hub is a documentation/specification repository. It doesn't have .NET projects to build, so it doesn't use NUKE.

**Who uses it:** Satellites with .NET/Unity projects (like `lablab-bean`)

---

## Maintenance

### When You Update Infrastructure

1. **Update the hub first** (dogfooding)
2. **Test on the hub** (`task test:all`)
3. **Commit & push** (CI runs automatically)
4. **Then update satellites** (via `task hub:sync`)

This ensures satellites never get broken infrastructure.

---

## Troubleshooting

### .agent symlink not working

```bash
# Recreate it
rm .agent
cmd /c "mklink /J .agent agents"
```

### Pre-commit hooks not running

```bash
# Reinstall hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

### Validation failing

```bash
# Check what's wrong
task validate:all

# Common fixes:
# - Missing agent rules in .agent/rules/
# - Missing required files (README.md, .gitignore, etc.)
```

### Task commands not working

```bash
# Verify Task is installed
task --version

# If missing, install: https://taskfile.dev/installation/
```

---

## Next Steps

### For Satellite Developers

Want to set up your satellite to consume the hub? The hub is now a **working reference implementation**. Copy these files:

1. `.hub-manifest.toml` (adjust versions)
2. `Taskfile.yml` (copy `hub:*` tasks)
3. `.pre-commit-config.yaml` (adjust for your project)
4. `.gitignore` (add `.hub-cache/` and `.agent`)

Then run:

```bash
task hub:sync
pre-commit install
```

### For Hub Developers

When working on the hub:

1. ✅ Pre-commit hooks run automatically on commit
2. ✅ CI runs on push/PR
3. ✅ Validation catches structural issues
4. ✅ Agent rules guide your coding

**You're now using the same infrastructure you're building!**

---

## Philosophy

> "If we don't use our own infrastructure, why should satellites trust it?"

Dogfooding ensures:

- **Reliability** - We catch issues before satellites do
- **Usability** - If it's hard for us, it's hard for everyone
- **Credibility** - We practice what we preach

---

**Last Updated:** 2025-10-30
**Status:** ✅ Fully implemented and tested

**Questions?** See:

- `HANDOVER.md` - Overview of Phase 1 implementation
- `PHASE1_PROGRESS.md` - Detailed progress tracking
- `Taskfile.yml` - Available automation tasks
