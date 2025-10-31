# 🛠️ Secrets Management Scripts

This directory contains scripts for managing age encryption keys and SOPS-encrypted secrets.

## 📋 Active Scripts (Bash/Shell - macOS/Linux)

These are the **recommended** scripts for use on macOS and Linux systems:

### Key Rotation Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `rotate-key-now.sh` | Quick age key rotation | Emergency key rotation, simple workflow |
| `rotate-secret-values.sh` | Rotate secret values | After key compromise, rotate actual passwords/tokens |
| `finish-key-rotation.sh` | Complete rotation workflow | Interactive guided workflow for full rotation |
| `rotate-age-key.sh` | Ansible-based rotation | Enterprise/automated rotation approach |

### Usage Examples

```bash
# Quick key rotation
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub/infra/secrets/scripts
./rotate-key-now.sh

# Rotate secret values interactively
./rotate-secret-values.sh

# Complete rotation workflow (recommended)
./finish-key-rotation.sh

# Ansible-based rotation (advanced)
./rotate-age-key.sh
```

## 🪟 Legacy Scripts (PowerShell - Windows)

These scripts are **deprecated** in favor of Taskfile commands and bash scripts:

| Script | Purpose | Replacement |
|--------|---------|-------------|
| `generate-age-key.ps1` | Generate age key | Use `task sops:rotate-key` or `./rotate-key-now.sh` |
| `encrypt-secrets.ps1` | Encrypt secrets.json | Use `task sops:edit` or `sops` directly |
| `decrypt-secrets.ps1` | Decrypt secrets.enc.json | Use `task sops:decrypt` or `sops -d` |

**Why deprecated?**

- PowerShell scripts were Windows-specific
- Project is now primarily macOS-based (Mac Mini runner)
- Taskfile provides cross-platform task automation
- Bash scripts are more native to macOS/Linux/CI environments

**Should you delete them?**

- ❌ Don't delete - keep for reference
- ✅ Use Taskfile commands instead: `task sops:info`, `task sops:edit`, `task sops:decrypt`
- ✅ Use bash rotation scripts for key management

## 🎯 Recommended Workflow

### For macOS/Linux Users (You!)

1. **View secrets**: `task sops:decrypt`
2. **Edit secrets**: `task sops:edit`
3. **Rotate key**: `./rotate-key-now.sh`
4. **Check security**: `task sops:check-git`

### For Windows Users (If Needed)

1. Install [WSL2](https://docs.microsoft.com/en-us/windows/wsl/install) (Windows Subsystem for Linux)
2. Use bash scripts within WSL2
3. Or use PowerShell scripts as-is (no updates planned)

## 📖 Documentation

For detailed guides, see:

- **Quick Start**: `../../../docs/security/README.md`
- **Key Rotation**: `../../../docs/security/AGE_KEY_ROTATION.md`
- **Secret Values**: `../../../docs/security/SECRET_VALUES_ROTATION.md`

## 🔧 Task Commands (Cross-Platform)

Instead of scripts, you can use Taskfile commands from anywhere:

```bash
# From project root
task sops:info        # View SOPS configuration
task sops:decrypt     # View decrypted secrets
task sops:edit        # Edit secrets (auto-encrypts on save)
task sops:check-git   # Check if private keys in git
task sops:rotate-key  # Rotate age key (Ansible)
task sops:reencrypt   # Re-encrypt all SOPS files
```

## 🚀 Quick Decision Tree

```
Need to...
├─ Generate NEW age key?
│  └─ Use: ./rotate-key-now.sh (generates + updates config)
│
├─ View decrypted secrets?
│  └─ Use: task sops:decrypt
│
├─ Edit secrets?
│  └─ Use: task sops:edit (opens in $EDITOR)
│
├─ Rotate after compromise?
│  ├─ 1. Run: ./rotate-key-now.sh (new key)
│  ├─ 2. Run: ./rotate-secret-values.sh (new values)
│  └─ 3. Run: ./finish-key-rotation.sh (cleanup)
│
└─ On Windows?
   ├─ Preferred: Install WSL2, use bash scripts
   └─ Alternative: Use PowerShell scripts (deprecated)
```

## ⚠️ Security Notes

1. **Never commit** `.sops/age.key` (private key)
2. **Always commit** `secrets.enc.json` (encrypted secrets)
3. **After key compromise**: Rotate BOTH key AND secret values
4. **Test before pushing**: `task sops:check-git`

---

**Last Updated**: October 31, 2025  
**Platform**: macOS (Mac Mini)  
**Primary Approach**: Bash scripts + Taskfile
