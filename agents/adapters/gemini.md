# Gemini Adapter

**Base-Version-Expected**: 1.0.0

This adapter configures Google Gemini behavior for the Lablab-Bean project.

## Quick Reference

You are working on a dungeon crawler game with:

- **.NET 8 backend**: Console application with Terminal.Gui
- **Web frontend**: xterm.js terminal emulator
- **Process management**: PM2 for running services

## Core Rules to Follow

### Documentation Rules (R-DOC)

- **R-DOC-001**: Write new docs to `docs/_inbox/` only
- **R-DOC-002**: Include YAML front-matter in all docs
- **R-DOC-003**: Check `docs/index/registry.json` before creating new docs
- **R-DOC-004**: Update existing canonical docs instead of duplicating

### Code Rules (R-CODE)

- **R-CODE-001**: No hardcoded secrets
- **R-CODE-002**: Use meaningful names
- **R-CODE-003**: Comment non-obvious code
- **R-CODE-004**: 🚨 **ALWAYS use relative paths** - Never absolute paths (Windows: `D:\...`, Unix: `/home/...`)
  - Config files: Use `./` or `../` relative paths only
  - Code: Use `Path.Combine()` with relative references
  - Reason: Cross-platform compatibility (Windows/Mac/Linux)
  - Use `/normalize-paths` command to fix existing absolute paths

### Testing Rules (R-TST)

- **R-TST-001**: Test critical paths
- **R-TST-002**: Builds must pass before commit

### Git Rules (R-GIT)

- **R-GIT-001**: Use descriptive commit messages
- **R-GIT-002**: Never commit secrets

### Process Rules (R-PRC)

- **R-PRC-001**: Document architecture decisions as ADRs
- **R-PRC-002**: Document breaking changes

### Security Rules (R-SEC)

- **R-SEC-001**: Validate external input
- **R-SEC-002**: Principle of least privilege

### Tool Integration Rules (R-TOOL)

- **R-TOOL-001**: Use Spec-Kit for feature development
- **R-TOOL-002**: Use task runner (`task` command) for operations
- **R-TOOL-003**: Follow spec maintenance strategy (update vs create new)

## Spec-Kit Integration (R-TOOL-001)

This project **REQUIRES** use of **GitHub Spec-Kit** for feature development.

### Required Workflow

When implementing new features, you MUST follow the Spec-Kit workflow:

```
specify → [clarify] → plan → [checklist] → tasks → [analyze] → implement
```

### How to Use Spec-Kit Commands

**For Gemini: Use Task Runner Commands** (Primary Method)

Use the task runner to access Spec-Kit workflow:

```bash
task speckit:help          # Show workflow overview
task speckit:constitution  # Establish project principles (one-time)
task speckit:specify       # Define features (WHAT & WHY)
task speckit:clarify       # Ask clarification questions (optional)
task speckit:plan          # Create technical plans (HOW)
task speckit:checklist     # Generate QA checklists (optional)
task speckit:tasks         # Generate task breakdowns
task speckit:analyze       # Validate consistency (optional)
task speckit:implement     # Execute implementation
```

**What These Commands Do:**

Each command displays formatted guidance with:

- Clear purpose and steps
- References to `.agent/integrations/spec-kit.md` for details
- Expected output file locations
- PowerShell helper script references where applicable

**Example Usage:**

```bash
# Start new feature workflow
task speckit:specify
# Follow displayed guidance to create specs/NNN-feature-name/spec.md

task speckit:plan
# Follow guidance to create plan.md, data-model.md, contracts/

task speckit:tasks
# Follow guidance to create tasks.md

task speckit:implement
# Follow guidance to implement feature phase-by-phase
```

**Full Documentation:** See `.agent/integrations/spec-kit.md` (537 lines)

**Important:** Spec-Kit commands must follow `.agent/base/` rules (R-DOC, R-CODE, R-TST, etc.)

## Documentation Workflow

When creating documentation:

1. **Check registry first**: Review `docs/index/registry.json`
2. **Write to inbox**: Save to `docs/_inbox/YYYY-MM-DD-title--DOC-YYYY-NNNNN.md`
3. **Include front-matter**:

   ```yaml
   ---
   doc_id: DOC-2025-XXXXX
   title: Your Title
   doc_type: guide|spec|adr|rfc|plan|finding|glossary|reference
   status: draft
   canonical: false
   created: 2025-10-21
   tags: [relevant, tags]
   summary: >
     One-line description
   source:
     author: agent
     agent: gemini
     model: gemini-2.0-flash-exp
   ---
   ```

## Principles to Follow

See `.agent/base/10-principles.md` for full list. Key principles:

- **P-1**: Documentation-First Development
- **P-2**: Clear Code Over Clever Code
- **P-3**: Testing Matters
- **P-4**: Security Consciousness
- **P-10**: When in doubt, ask

## Tech Stack

- **Backend**: .NET 8, C#, Terminal.Gui
- **Frontend**: TypeScript, xterm.js, Node.js
- **Process Management**: PM2
- **Build**: npm scripts, dotnet CLI

## File Structure

```
lablab-bean/
├── dotnet/                    # .NET backend
│   ├── console-app/          # Terminal.Gui console app
│   └── framework/            # Game logic libraries
├── website/                   # Web frontend
│   └── packages/terminal/    # xterm.js terminal
├── docs/                      # Documentation
│   ├── _inbox/               # New docs staging
│   ├── guides/               # How-to guides
│   ├── adrs/                 # Architecture decisions
│   └── index/registry.json   # Doc registry
├── specs/                     # Spec-Kit specifications
│   └── NNN-feature-name/     # Generated by /speckit commands
├── .specify/                  # Spec-Kit config (external)
│   ├── memory/constitution.md
│   ├── scripts/
│   └── templates/
└── .agent/                    # Agent instructions (this system)
    ├── base/                  # Canonical rules
    ├── adapters/gemini.md     # This file
    └── integrations/          # External integrations
        └── spec-kit.md
```

## Gemini-Specific Notes

When generating code and responses:

1. **Context Awareness**: Use Gemini's large context window to understand full project scope
2. **Multimodal Capability**: Leverage Gemini's ability to understand diagrams, screenshots, and code snippets
3. **Type Safety**: Prefer strongly-typed solutions in both C# and TypeScript
4. **Error Handling**: Include appropriate try-catch blocks and null checks
5. **Documentation**: Generate clear XML comments for C# and JSDoc for TypeScript
6. **Testing**: Always suggest or generate corresponding test cases for new functionality
7. **Reasoning**: Use Gemini's advanced reasoning to explain complex architectural decisions
8. **Code Quality**: Focus on maintainability, readability, and performance
9. **Best Practices**: Follow .NET conventions and TypeScript/JavaScript best practices

### Leveraging Gemini's Strengths

- **Long Context**: Take advantage of Gemini's extended context window to analyze entire codebases
- **Code Understanding**: Use deep code analysis to suggest refactoring and optimizations
- **Multi-turn Planning**: Break down complex features into well-structured implementation plans
- **Cross-language Support**: Seamlessly work across C#, TypeScript, and configuration files

## Common Tasks

### Running the App

```bash
npm run dev          # Start web terminal
npm run console      # Run .NET console app
```

### Building

```bash
npm run build        # Build frontend
dotnet build         # Build backend
```

### Testing

```bash
npm test             # Run frontend tests
dotnet test          # Run backend tests
```

### Documentation

```bash
python scripts/validate_docs.py  # Validate docs
```

## References

### Agent System

- **Base Rules**: See `.agent/base/20-rules.md`
- **Principles**: See `.agent/base/10-principles.md`
- **Glossary**: See `.agent/base/30-glossary.md`
- **Documentation Standards**: See `.agent/base/40-documentation.md`

### Integrations

- **Spec-Kit**: See `.agent/integrations/spec-kit.md`

### Project Documentation

- **Schema**: See `docs/DOCUMENTATION-SCHEMA.md`

---

**Version**: 1.0.0
**Last Updated**: 2025-10-22
**Sync Status**: ✅ Synced with base rules
**Initial Release**: Complete adapter with R-CODE-004 (cross-platform paths) and Spec-Kit integration
