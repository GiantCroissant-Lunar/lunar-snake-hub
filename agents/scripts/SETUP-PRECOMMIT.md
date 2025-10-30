# Pre-commit Setup Guide

This project uses [pre-commit](https://pre-commit.com/) to ensure code quality and consistency.

## What Pre-commit Does

Pre-commit automatically runs checks before each commit to:

1. **Format code**: Auto-format Python with Black, YAML, and Markdown
2. **Lint code**: Check Python with flake8, organize imports with isort
3. **Validate files**: Check for trailing whitespace, large files, merge conflicts
4. **Validate agent files**: Ensure pointer files are in sync with `.agent/` system
5. **Enforce commit messages**: Validate conventional commit format

## Installation

### Option 1: Using uv (Recommended)

```bash
# Install uv if not already installed
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install pre-commit with uv
uv tool install pre-commit

# Install the git hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

### Option 2: Using pip

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

### Option 3: Using pipx

```bash
# Install pipx if needed
python -m pip install --user pipx
python -m pipx ensurepath

# Install pre-commit
pipx install pre-commit

# Install the git hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

## Verify Installation

```bash
# Check pre-commit is installed
pre-commit --version

# Run against all files (optional)
pre-commit run --all-files
```

## Daily Usage

Once installed, pre-commit runs **automatically** on every commit. You don't need to do anything!

### Manual Runs

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Run specific hook
pre-commit run ruff
pre-commit run ruff-format
pre-commit run validate-pointer-files
```

### Skipping Hooks (Not Recommended)

If you absolutely must skip hooks:

```bash
git commit --no-verify -m "message"
```

**Warning**: Only use `--no-verify` in emergencies. Skipping hooks may introduce issues.

## Hooks Configured

### File Checks

- `trailing-whitespace`: Remove trailing whitespace
- `end-of-file-fixer`: Ensure files end with newline
- `check-yaml`: Validate YAML syntax
- `check-json`: Validate JSON syntax
- `check-toml`: Validate TOML syntax
- `check-added-large-files`: Prevent large files from being committed
- `check-merge-conflict`: Detect merge conflict markers
- `detect-private-key`: Prevent committing private keys

### Formatting

- `ruff-format`: Auto-format Python code (replaces black)
- `pretty-format-yaml`: Format YAML files
- `markdownlint`: Lint and fix Markdown

### Linting

- `ruff`: Python linter (replaces flake8, isort, pyupgrade, and 50+ tools)
- `mypy`: Python type checking (optional)

### Project-Specific

- `validate-pointer-files`: Ensure agent pointer files are up to date
- `conventional-pre-commit`: Enforce conventional commit messages

## Updating Hooks

Pre-commit hooks are versioned in `.pre-commit-config.yaml`. To update:

```bash
# Update all hooks to latest versions
pre-commit autoupdate

# Install updated hooks
pre-commit install
```

## Troubleshooting

### Hook fails with "command not found"

Ensure pre-commit is installed and git hooks are set up:

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

### Python hooks fail

Ensure Python 3 is installed and available:

```bash
python3 --version
# or
python --version
```

### Ruff not found

Install Ruff (modern Python linter/formatter):

```bash
pip install ruff
# or: uv tool install ruff
# or: pipx install ruff
```

Ruff is 10-100x faster than black+flake8+isort combined!

### Pointer file validation fails

Run the generator to fix:

```bash
python .agent/scripts/generate_pointers.py
git add CLAUDE.md AGENTS.md .github/copilot-instructions.md .windsurf/rules.md
```

### Clear pre-commit cache

If hooks misbehave:

```bash
pre-commit clean
pre-commit install --install-hooks
```

## CI/CD Integration

The same hooks can run in CI/CD:

```yaml
# Example: GitHub Actions
- name: Run pre-commit
  uses: pre-commit/action@v3.0.0
```

## Related Documentation

- **Pre-commit Official Docs**: <https://pre-commit.com/>
- **Agent Pointer Scripts**: [.agent/scripts/README.md](README.md)
- **Base Rules**: [.agent/base/20-rules.md](../base/20-rules.md)

---

**Last Updated**: 2025-10-21
