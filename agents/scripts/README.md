# Agent Scripts

Maintenance scripts for the `.agent/` instruction system.

## Scripts

### `generate_pointers.py`

Generates and updates pointer files that redirect agents to the canonical instruction system.

**Purpose**: Ensures pointer files (like `CLAUDE.md`, `AGENTS.md`) stay in sync with `.agent/` system.

**Usage**:

```bash
# Generate/update all pointer files
python .agent/scripts/generate_pointers.py

# Check if pointer files need updating (CI/CD friendly)
python .agent/scripts/generate_pointers.py --check
```

**Pointer Files Generated**:

- `CLAUDE.md` → Points to `.agent/adapters/claude.md`
- `AGENTS.md` → Points to `.agent/README.md`
- `.github/copilot-instructions.md` → Points to `.agent/adapters/copilot.md`
- `.windsurf/rules.md` → Points to `.agent/adapters/windsurf.md`

**When to Run**:

- After updating `.agent/base/00-index.md` version
- After modifying `.agent/README.md` structure
- Before committing changes to agent instructions
- In CI/CD to validate pointer files are up to date

**Exit Codes**:

- `0`: Success (files generated or up to date)
- `1`: Error or files need updating (in `--check` mode)

## Adding New Pointer Files

To add a new pointer file:

1. Edit `generate_pointers.py`
2. Add entry to `POINTER_CONFIGS` dictionary:

   ```python
   "path/to/NEW_FILE.md": {
       "adapter": "adapter-name.md",  # or None for generic
       "agent_name": "Agent Name",
       "description": "short description",
       "path": "path/to",  # or None for root level
   }
   ```

3. Add generator function `generate_new_file_md(config, version)`
4. Update `generate_pointer_file()` to handle new file
5. Run script to test
6. Update this README

**Note**: The script automatically creates subdirectories if `"path"` is specified.

## CI/CD Integration

Add to your CI pipeline to ensure pointer files stay synchronized:

```yaml
# Example GitHub Actions
- name: Validate agent pointer files
  run: python .agent/scripts/generate_pointers.py --check
```

## Design Philosophy

**Single Source of Truth**: All agent instructions live in `.agent/`. Pointer files are generated artifacts that should never be manually edited.

**Version Tracking**: Pointer files include version and generation timestamp to aid debugging.

**Fail Fast**: In `--check` mode, the script exits with code 1 if files are out of sync, preventing accidental commits of stale pointers.

## Related Documentation

- **Agent System Overview**: [.agent/README.md](../README.md)
- **Base Rules**: [.agent/base/20-rules.md](../base/20-rules.md)
- **Versioning Protocol**: [.agent/meta/versioning.md](../meta/versioning.md)

---

**Last Updated**: 2025-10-21
