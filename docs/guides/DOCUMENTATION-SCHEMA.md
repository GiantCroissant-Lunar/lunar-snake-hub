---
doc_id: DOC-2025-00011
title: Documentation Front-Matter Schema
doc_type: guide
status: active
canonical: true
created: 2025-10-20
tags: [docs, schema, meta]
summary: Mandatory front-matter schema for all documentation files
---

# Documentation Front-Matter Schema

All markdown files in `docs/` MUST include YAML front-matter with the following structure.

## Required Fields

```yaml
---
doc_id: DOC-YYYY-NNNNN          # Permanent unique ID (e.g., DOC-2025-00001)
title: Short descriptive title  # Max 80 chars
doc_type: spec|rfc|adr|plan|finding|guide|glossary|reference
status: draft|active|superseded|rejected|archived
canonical: true|false           # Only 1 canonical per concept
created: YYYY-MM-DD            # ISO date
tags: [tag1, tag2]             # Lowercase, hyphenated
summary: >
  One-line description to help deduplication and search.
---
```

## Optional Fields

```yaml
supersedes: [DOC-2024-00991, DOC-2024-01005]  # Previous doc IDs this replaces
related: [DOC-2025-00077, ADR-0010]           # Related documentation
source:
  author: agent|human|system
  agent: claude|copilot|windsurf|gemini       # If author=agent
  model: sonnet-4.5|gpt-4|...                 # Optional model name
  session: abc123                              # Optional session ID
updated: YYYY-MM-DD                            # Last modification date
owner: team-name                               # Responsible team/person
```

## Document Types

| Type       | Purpose                                      | Location        |
|------------|----------------------------------------------|-----------------|
| `spec`     | Product/technical specifications             | `docs/specs/`   |
| `rfc`      | Proposals under discussion                   | `docs/rfcs/`    |
| `adr`      | Architecture decision records                | `docs/adrs/`    |
| `plan`     | Implementation plans, milestones, phases     | `docs/plans/`   |
| `finding`  | Research, benchmarks, analysis               | `docs/findings/`|
| `guide`    | How-tos, tutorials, playbooks, runbooks      | `docs/guides/`  |
| `glossary` | Term definitions                             | `docs/glossary/`|
| `reference`| API docs, technical reference                | `docs/`         |

## Status Lifecycle

```
draft → active → superseded|rejected|archived
```

- **draft**: Work in progress, not ready for consumption
- **active**: Current, canonical, actively maintained
- **superseded**: Replaced by newer document (use `supersedes` field)
- **rejected**: Proposal/RFC not accepted
- **archived**: No longer relevant but kept for historical reference

## Canonical Documents

Only **one** document per concept may have `canonical: true`. When creating a new version:

1. Set old doc `status: superseded`
2. Add `supersedes: [OLD-DOC-ID]` to new doc
3. Set new doc `canonical: true`
4. Move old doc to `docs/archive/`

## File Naming Convention

```
YYYY-MM-DD-kebab-case-title--DOC-YYYY-NNNNN.md
```

Examples:

- `2025-10-20-api-design--DOC-2025-00042.md`
- `2025-10-20-deployment-strategy--ADR-2025-00008.md`

## Agent Instructions

If you are an AI agent creating documentation:

1. **Always write to `docs/_inbox/` first** (never directly to canonical locations)
2. **Include complete front-matter** with all required fields
3. **Check `docs/index/registry.json`** to find existing canonical docs
4. **Update existing canonical docs** instead of creating duplicates
5. **Use next available doc_id** from registry (increment highest number)
6. **Tag with source metadata** (agent name, model, session if available)

## For Humans

When promoting from inbox to canonical:

1. Review content quality and completeness
2. Check for duplicates via `docs/index/registry.json`
3. Merge into existing canonical if appropriate
4. Move to correct category directory
5. Update supersedes chain if replacing
6. Move old version to `docs/archive/`

## See Also

- `docs/index/registry.json` - Machine-readable doc registry
- `docs/README.md` - Documentation navigation
