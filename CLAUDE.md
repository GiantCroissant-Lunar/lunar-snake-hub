# Claude Adapter

Claude’s configuration is defined via the `.agent` adapters:

- Adapter spec: `.agent/adapters/claude-adapter.yaml`
- Provider config: `.agent/providers/claude.yaml`
- Workflows: `.claude/workflows/` (generated from `.agent/workflows/`)

This file is the entry point for Claude-specific behavior and should be kept in sync with the adapter configuration.
See `.agent/adapters/README.md` for details on how adapters work.

