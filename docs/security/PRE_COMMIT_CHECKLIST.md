# Pre-Commit Checklist

## ✅ Files Ready to Commit

### Core Security Files

- [ ] `.gitignore` - Added backup file patterns
- [ ] `.sops.yaml` - Updated with new public key
- [ ] `.sops/age.pub` - New public key
- [ ] `Taskfile.yml` - Added SOPS management tasks
- [ ] `infra/ansible/roles/sops_setup/templates/sops.yaml.j2` - Updated template
- [ ] `infra/secrets/README.md` - Updated documentation
- [ ] `infra/secrets/secrets.enc.json` - Re-encrypted with new key

### Documentation (docs/security/)

- [ ] `docs/security/README.md` - Master index
- [ ] `docs/security/AGE_KEY_ROTATION.md` - Comprehensive guide
- [ ] `docs/security/COMMIT_SUMMARY.md` - This commit's changes
- [ ] `docs/security/KEY_ROTATION_COMPLETED.md` - Rotation summary
- [ ] `docs/security/ROTATION_COMPLETE.md` - Quick checklist
- [ ] `docs/security/SECRET_VALUES_ROTATION.md` - Values rotation guide
- [ ] `docs/security/SERVICE_USAGE_ANALYSIS.md` - Service analysis
- [ ] `docs/security/WHAT_TO_ROTATE.md` - Secret details

### Scripts (infra/secrets/)

- [ ] `infra/secrets/finish-key-rotation.sh` - Completion script
- [ ] `infra/secrets/rotate-age-key.sh` - Ansible rotation
- [ ] `infra/secrets/rotate-key-now.sh` - Quick rotation
- [ ] `infra/secrets/rotate-secret-values.sh` - Values rotation

### Ansible Playbooks

- [ ] `infra/ansible/rotate_age_key_playbook.yml` - Rotation playbook
- [ ] `infra/ansible/roles/sops_setup/tasks/rotate_age_key.yml` - Rotation tasks
- [ ] `infra/ansible/roles/sops_setup/files/reencrypt_all.sh` - Re-encryption script

---

## ❌ Files That Should NOT Be Committed

### Private Keys and Backups

- ❌ `.sops/age.key` - **PRIVATE KEY - NEVER COMMIT**
- ❌ `.sops/age.key.backup.*` - Backup private keys
- ❌ `.sops/age.pub.backup.*` - Backup public keys
- ❌ `.sops.yaml.backup.*` - Backup config files

These are now in `.gitignore` and will be automatically excluded.

---

## 🚀 Commit Command

```bash
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub

# Stage all the safe files
git add .gitignore
git add .sops.yaml
git add .sops/age.pub
git add Taskfile.yml
git add infra/ansible/
git add infra/secrets/README.md
git add infra/secrets/secrets.enc.json
git add infra/secrets/*.sh
git add docs/security/

# Verify what's staged (should NOT include age.key or backups)
git status

# Double-check private key is not being committed
git diff --cached | grep -i "age.key" || echo "✅ No private key in staged changes"

# Commit
git commit -m "security: complete age key rotation and secret values rotation

## What Changed

### Security
- Rotated age encryption key (old key compromised)
- Rotated ALL secret values (API keys, tokens, passwords)
- Old key: age1ydjyyu9m550m8dj22qag8qlk8ugh6n454tjezenmtra48tjaypeq5m3zj0 (COMPROMISED)
- New key: age1jgv3pfxe8a5nw4hnf2hwt4w6h0npwtgtj66xnl6fw7j49n5jr54qgfvagl

### New Features
- Added SOPS management tasks to Taskfile (sops:*)
- Created automated key rotation scripts
- Added comprehensive security documentation
- Updated Ansible playbooks for key rotation

### Files
- Updated: .sops.yaml, .sops/age.pub, secrets.enc.json
- Added: docs/security/, scripts, Ansible playbooks
- Protected: .gitignore now excludes backup files

## Critical Next Steps
1. Update CI/CD with new private key from .sops/age.key
2. Clean git history: task sops:clean-history
3. Force push: git push --force --all
4. Notify team to re-clone repository

See docs/security/COMMIT_SUMMARY.md for complete details."

# Push (but remember you still need to clean history!)
git push
```

---

## ⚠️ After Push - CRITICAL

The old private key is still in git history. You MUST:

```bash
# 1. Clean git history
task sops:clean-history

# 2. Force push (rewrites history)
git push origin --force --all
git push origin --force --tags

# 3. Notify all collaborators
# - Everyone must delete their local clones
# - Everyone must re-clone from remote

# 4. Update CI/CD
# - Add new private key from .sops/age.key
# - Secret name: SOPS_AGE_KEY or similar
```

---

## 🔒 Final Verification

After everything:

```bash
# Verify private key is not in current tree
git ls-files | grep "\.sops/age.key"
# Should return: nothing

# Verify private key is not in history
git log --all --full-history -- .sops/age.key
# Should return: nothing

# Verify new key works
sops --decrypt infra/secrets/secrets.enc.json | jq '.'
# Should successfully decrypt

# Verify services work
task infra:setup
task infra:restart
task infra:status
# Should all succeed
```

---

## 📋 Complete Workflow

1. ✅ Review this checklist
2. ✅ Stage and commit files
3. ✅ Push to remote
4. ⚠️ Update CI/CD secrets
5. ⚠️ Clean git history
6. ⚠️ Force push
7. ⚠️ Notify team
8. ⚠️ Test services
9. ⚠️ Verify everything works
10. ✅ Delete backup files locally

---

## 📚 Quick Reference

- Full guide: `docs/security/COMMIT_SUMMARY.md`
- Security index: `docs/security/README.md`
- Rotation complete: `docs/security/ROTATION_COMPLETE.md`
