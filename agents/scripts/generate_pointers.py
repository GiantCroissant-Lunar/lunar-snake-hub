#!/usr/bin/env python3
"""
Generate pointer files that redirect agents to the .agent/ instruction system.

This script generates root-level pointer files (CLAUDE.md, AGENTS.md, etc.) that
reference the canonical agent instructions in .agent/adapters/.

Usage:
    python .agent/scripts/generate_pointers.py
    python .agent/scripts/generate_pointers.py --check  # Validate only
"""

import argparse
from datetime import date
from pathlib import Path
from typing import Dict, Optional

# Pointer file configurations
POINTER_CONFIGS = {
    "CLAUDE.md": {
        "adapter": "claude.md",
        "agent_name": "Claude Code",
        "description": "comprehensive agent instructions",
        "path": None,  # Root level
    },
    "AGENTS.md": {
        "adapter": None,  # Generic file pointing to system overview
        "agent_name": "All Agents",
        "description": "agent instruction system overview",
        "path": None,  # Root level
    },
    ".github/copilot-instructions.md": {
        "adapter": "copilot.md",
        "agent_name": "GitHub Copilot",
        "description": "Copilot code suggestions and completions",
        "path": ".github",  # Needs directory creation
    },
    ".windsurf/rules.md": {
        "adapter": "windsurf.md",
        "agent_name": "Windsurf",
        "description": "Windsurf AI assistance and Flow mode",
        "path": ".windsurf",  # Needs directory creation
    },
    ".kiro/steering/README.md": {
        "adapter": "kiro.md",
        "agent_name": "Kiro",
        "description": "Kiro steering system overview",
        "path": ".kiro/steering",  # Needs directory creation
    },
}


def get_base_version() -> str:
    """Extract version from .agent/base/00-index.md."""
    index_path = Path(".agent/base/00-index.md")

    if not index_path.exists():
        raise FileNotFoundError(f"Base index not found: {index_path}")

    content = index_path.read_text(encoding="utf-8")

    # Look for "Version: X.Y.Z"
    for line in content.split("\n"):
        if line.strip().startswith("Version:"):
            version = line.split(":", 1)[1].strip()
            return version

    raise ValueError("Version not found in .agent/base/00-index.md")


def generate_claude_md(config: Dict[str, Optional[str]], version: str) -> str:
    """Generate CLAUDE.md pointer file content."""
    return f"""# Claude Code Instructions

Welcome to the Lablab-Bean project!

This file redirects you to the comprehensive agent instructions.

## Quick Start

For complete Claude Code configuration and rules, see:

**→ [.agent/adapters/claude.md](.agent/adapters/claude.md)**

## Agent Instruction System

This project uses a structured multi-agent instruction system located in `.agent/`:

```
.agent/
├── README.md              # System overview
├── base/                  # Canonical rules (source of truth)
│   ├── 00-index.md       # Version, structure, conventions
│   ├── 10-principles.md  # Core development principles
│   ├── 20-rules.md       # Normative rules with IDs
│   ├── 30-glossary.md    # Domain terminology
│   └── 40-documentation.md # Documentation standards
├── adapters/             # Agent-specific configurations
│   └── claude.md         # ← Your configuration
└── meta/                 # Versioning and governance
    ├── changelog.md      # Version history
    ├── versioning.md     # Sync protocol
    └── adapter-template.md # Template for new adapters
```

## Key Rules to Remember

### Documentation (R-DOC)
- Always write new docs to `docs/_inbox/` first
- Include YAML front-matter in all documentation
- Check `docs/index/registry.json` before creating new docs
- Update existing canonical docs instead of duplicating

### Code Quality (R-CODE)
- No hardcoded secrets or credentials
- Use meaningful variable and function names
- Comment non-obvious code

### Testing (R-TST)
- Test critical functionality
- Ensure builds pass before committing

### Git (R-GIT)
- Use descriptive commit messages (conventional commit format)
- Never commit secrets

## Documentation Schema

All documentation must include YAML front-matter. See:
- **Schema Definition**: [docs/DOCUMENTATION-SCHEMA.md](docs/DOCUMENTATION-SCHEMA.md)
- **Validation**: Run `python scripts/validate_docs.py`

## Quick Reference

**Project Type**: Dungeon crawler game with .NET backend and web terminal UI

**Tech Stack**:
- Backend: .NET 8, C#, Terminal.Gui
- Frontend: TypeScript, xterm.js
- Process Management: PM2

**Common Commands**:
```bash
npm run dev          # Start development server
npm run console      # Run console app
python scripts/validate_docs.py  # Validate documentation
```

## Learn More

- **Full Instructions**: [.agent/adapters/claude.md](.agent/adapters/claude.md)
- **Base Rules**: [.agent/base/20-rules.md](.agent/base/20-rules.md)
- **Principles**: [.agent/base/10-principles.md](.agent/base/10-principles.md)
- **Documentation Guide**: [.agent/base/40-documentation.md](.agent/base/40-documentation.md)

---

**Version**: {version} | **Last Updated**: {date.today()}
**Generated by**: `.agent/scripts/generate_pointers.py`
"""


def generate_agents_md(config: Dict[str, Optional[str]], version: str) -> str:
    """Generate AGENTS.md pointer file content."""
    return f"""# Agent Instructions

**→ See [.agent/README.md](.agent/README.md) for the complete agent instruction system.**

This project uses a multi-agent instruction system with:

## Quick Links

- **System Overview**: [.agent/README.md](.agent/README.md)
- **Base Rules**: [.agent/base/20-rules.md](.agent/base/20-rules.md)
- **Principles**: [.agent/base/10-principles.md](.agent/base/10-principles.md)
- **Documentation Standards**: [.agent/base/40-documentation.md](.agent/base/40-documentation.md)

## Agent-Specific Adapters

Different AI assistants should read their specific adapter file:

- **Claude Code**: [.agent/adapters/claude.md](.agent/adapters/claude.md) (also see [CLAUDE.md](CLAUDE.md))
- **GitHub Copilot**: [.agent/adapters/copilot.md](.agent/adapters/copilot.md) (also see [.github/copilot-instructions.md](.github/copilot-instructions.md))
- **Windsurf**: [.agent/adapters/windsurf.md](.agent/adapters/windsurf.md) (also see [.windsurf/rules.md](.windsurf/rules.md))
- **Kiro**: [.agent/adapters/kiro.md](.agent/adapters/kiro.md) (also see [.kiro/steering/README.md](.kiro/steering/README.md))
- **Google Gemini**: [.agent/adapters/gemini.md](.agent/adapters/gemini.md)
- **OpenAI Codex**: [.agent/adapters/codex.md](.agent/adapters/codex.md)

## Structure

```
.agent/
├── README.md              # Start here
├── base/                  # Canonical rules (source of truth)
│   ├── 00-index.md       # Version {version}
│   ├── 10-principles.md  # Development principles
│   ├── 20-rules.md       # Enforceable rules with IDs
│   ├── 30-glossary.md    # Domain terminology
│   └── 40-documentation.md # Documentation standards
├── adapters/             # Agent-specific configurations
│   ├── claude.md         # Claude Code
│   ├── copilot.md        # GitHub Copilot
│   ├── windsurf.md       # Windsurf/Codeium
│   ├── kiro.md           # Kiro
│   ├── gemini.md         # Google Gemini
│   └── codex.md          # OpenAI Codex
├── integrations/         # External tool integrations
│   └── spec-kit.md       # GitHub Spec-Kit
├── meta/                 # Versioning and governance
│   ├── changelog.md      # Version history
│   ├── versioning.md     # Sync protocol
│   └── adapter-template.md # New adapter template
└── scripts/              # Maintenance scripts
    └── generate_pointers.py # This generator
```

## Rule Categories

- **R-CODE**: Code quality & architecture
- **R-SEC**: Security guidelines
- **R-TST**: Testing standards
- **R-DOC**: Documentation conventions
- **R-GIT**: Git workflow
- **R-PRC**: Process guidelines
- **R-TOOL**: Tool integration

## For New Agents

To add support for a new AI assistant:

1. Copy [.agent/meta/adapter-template.md](.agent/meta/adapter-template.md)
2. Customize for your agent
3. Save to `.agent/adapters/{{agent-name}}.md`
4. Create a pointer file in project root (optional)
5. Update this file to reference the new adapter

---

**Version**: {version} | **Last Updated**: {date.today()}
**Generated by**: `.agent/scripts/generate_pointers.py`
"""


def generate_copilot_instructions_md(
    config: Dict[str, Optional[str]], version: str
) -> str:
    """Generate .github/copilot-instructions.md pointer file content."""
    return f"""# GitHub Copilot Instructions

**→ See [../.agent/adapters/copilot.md](../.agent/adapters/copilot.md) for complete instructions.**

This project uses a structured agent instruction system in `.agent/`.

## Quick Reference

- **Full Copilot Instructions**: [../.agent/adapters/copilot.md](../.agent/adapters/copilot.md)
- **Base Rules**: [../.agent/base/20-rules.md](../.agent/base/20-rules.md)
- **Principles**: [../.agent/base/10-principles.md](../.agent/base/10-principles.md)
- **System Overview**: [../.agent/README.md](../.agent/README.md)

## Key Rules

### Documentation (R-DOC)
- Write new docs to `docs/_inbox/` only
- Include YAML front-matter in all docs
- Check `docs/index/registry.json` before creating new docs

### Code Quality (R-CODE)
- No hardcoded secrets
- Use meaningful variable/function names
- Comment non-obvious code

### Testing (R-TST)
- Test critical functionality
- Ensure builds pass

### Git (R-GIT)
- Use descriptive commit messages
- Never commit secrets

## Tech Stack

- **Backend**: .NET 8, C#, Terminal.Gui
- **Frontend**: TypeScript, xterm.js, Node.js
- **Process**: PM2

---

**Version**: {version} | **Last Updated**: {date.today()}
**Generated by**: `../.agent/scripts/generate_pointers.py`
"""


def generate_windsurf_rules_md(config: Dict[str, Optional[str]], version: str) -> str:
    """Generate .windsurf/rules.md pointer file content."""
    return f"""# Windsurf Rules

**→ See [../.agent/adapters/windsurf.md](../.agent/adapters/windsurf.md) for complete instructions.**

This project uses a structured agent instruction system in `.agent/`.

## Quick Reference

- **Full Windsurf Instructions**: [../.agent/adapters/windsurf.md](../.agent/adapters/windsurf.md)
- **Base Rules**: [../.agent/base/20-rules.md](../.agent/base/20-rules.md)
- **Principles**: [../.agent/base/10-principles.md](../.agent/base/10-principles.md)
- **System Overview**: [../.agent/README.md](../.agent/README.md)

## Key Rules

### Documentation (R-DOC)
- Write new docs to `docs/_inbox/` only
- Include YAML front-matter in all docs
- Check `docs/index/registry.json` before creating new docs

### Code Quality (R-CODE)
- No hardcoded secrets
- Use meaningful variable/function names
- Comment non-obvious code

### Testing (R-TST)
- Test critical functionality
- Ensure builds pass

### Git (R-GIT)
- Use descriptive commit messages
- Never commit secrets

## Tech Stack

- **Backend**: .NET 8, C#, Terminal.Gui
- **Frontend**: TypeScript, xterm.js, Node.js
- **Process**: PM2

---

**Version**: {version} | **Last Updated**: {date.today()}
**Generated by**: `../.agent/scripts/generate_pointers.py`
"""


def generate_kiro_readme_md(config: Dict[str, Optional[str]], version: str) -> str:
    """Generate .kiro/steering/README.md pointer file content."""
    return f"""# Kiro Steering System

**→ See [../../.agent/adapters/kiro.md](../../.agent/adapters/kiro.md) for complete Kiro instructions.**

This directory contains **steering files** that give Kiro persistent knowledge about the Lablab-Bean project.

## Steering Files in This Directory

- **[product.md](product.md)** - Product purpose, users, and objectives
- **[tech.md](tech.md)** - Technical stack and constraints
- **[structure.md](structure.md)** - File organization and naming conventions
- **[agent-system.md](agent-system.md)** - Integration with `.agent/` canonical rules

## How Kiro Steering Works

Kiro automatically reads these markdown files to understand project context. Files with `mode: always` in their YAML front matter are loaded for every interaction.

## Integration with `.agent/` System

This project uses a unified agent instruction system in `.agent/` that all AI assistants follow. The steering files in this directory provide Kiro-specific context while referencing the canonical rules.

**Architecture**:
```
Kiro steering files (.kiro/steering/) → Kiro adapter (.agent/adapters/kiro.md) → Base rules (.agent/base/)
```

## Quick Reference

### For Kiro
- **Full Instructions**: [../../.agent/adapters/kiro.md](../../.agent/adapters/kiro.md)
- **Base Rules**: [../../.agent/base/20-rules.md](../../.agent/base/20-rules.md)
- **Principles**: [../../.agent/base/10-principles.md](../../.agent/base/10-principles.md)

### Core Rules Summary

- **R-DOC-001**: Write new docs to `docs/_inbox/` only
- **R-CODE-004**: Always use relative paths (never absolute)
- **R-TST-002**: Builds must pass before commit
- **R-TOOL-001**: Use Spec-Kit for feature development (REQUIRED)

### Tech Stack

- **Backend**: .NET 8, C#, Terminal.Gui
- **Frontend**: TypeScript, xterm.js, Node.js
- **Process Management**: PM2
- **Build**: npm scripts, dotnet CLI

## Creating Additional Steering Files

You can create custom steering files for domain-specific knowledge:

```
.kiro/steering/
├── api-standards.md       # API design patterns
├── testing-standards.md   # Testing approaches
├── security-policies.md   # Security requirements
└── deployment-workflow.md # Deployment process
```

Add YAML front matter to control when files are loaded:

```yaml
---
title: Your Title
mode: always  # or 'on-demand'
---
```

## Learn More

- **Kiro Documentation**: [https://kiro.dev/docs/steering/](https://kiro.dev/docs/steering/)
- **Project Agent System**: [../../.agent/README.md](../../.agent/README.md)

---

**Version**: {version} | **Last Updated**: {date.today()}
**Generated by**: `../../.agent/scripts/generate_pointers.py`
"""


def generate_pointer_file(
    filename: str,
    config: Dict[str, Optional[str]],
    version: str,
) -> str:
    """Generate content for a pointer file."""
    if filename == "CLAUDE.md":
        return generate_claude_md(config, version)
    elif filename == "AGENTS.md":
        return generate_agents_md(config, version)
    elif filename == ".github/copilot-instructions.md":
        return generate_copilot_instructions_md(config, version)
    elif filename == ".windsurf/rules.md":
        return generate_windsurf_rules_md(config, version)
    elif filename == ".kiro/steering/README.md":
        return generate_kiro_readme_md(config, version)
    else:
        raise ValueError(f"Unknown pointer file: {filename}")


def write_pointer_files(check_only: bool = False) -> bool:
    """
    Generate/update all pointer files.

    Args:
        check_only: If True, only validate without writing

    Returns:
        True if successful (files up to date or successfully updated), False on error
    """
    try:
        version = get_base_version()
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] Error reading base version: {e}")
        return False

    project_root = Path.cwd()
    all_up_to_date = True
    had_errors = False

    for filename, config in POINTER_CONFIGS.items():
        filepath = project_root / filename

        try:
            # Ensure directory exists if pointer file is in subdirectory
            if config.get("path"):
                dir_path = project_root / config["path"]
                dir_path.mkdir(parents=True, exist_ok=True)

            new_content = generate_pointer_file(filename, config, version)

            if filepath.exists():
                current_content = filepath.read_text(encoding="utf-8")

                if current_content == new_content:
                    print(f"[OK] {filename} is up to date")
                else:
                    all_up_to_date = False
                    if check_only:
                        print(f"[WARN] {filename} needs updating")
                    else:
                        filepath.write_text(new_content, encoding="utf-8")
                        print(f"[OK] {filename} updated")
            else:
                all_up_to_date = False
                if check_only:
                    print(f"[WARN] {filename} does not exist")
                else:
                    filepath.write_text(new_content, encoding="utf-8")
                    print(f"[OK] {filename} created")

        except Exception as e:
            print(f"[ERROR] Error processing {filename}: {e}")
            had_errors = True

    # In check mode, return True only if all files are up to date
    # In write mode, return True if no errors occurred
    if check_only:
        return all_up_to_date and not had_errors
    else:
        return not had_errors


def main():
    parser = argparse.ArgumentParser(
        description="Generate pointer files for agent instruction system"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if pointer files need updating without modifying them",
    )

    args = parser.parse_args()

    print("Agent Pointer File Generator")
    print("=" * 50)

    success = write_pointer_files(check_only=args.check)

    print("=" * 50)

    if args.check:
        if success:
            print("[OK] All pointer files are up to date")
            exit(0)
        else:
            print("[WARN] Some pointer files need updating")
            print("Run without --check to update them")
            exit(1)
    else:
        if success:
            print("[OK] All pointer files generated successfully")
            exit(0)
        else:
            print("[ERROR] Some pointer files failed to generate")
            exit(1)


if __name__ == "__main__":
    main()
