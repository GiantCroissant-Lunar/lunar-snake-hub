# Age Key Rotation - Security Incident Response

## 🚨 Situation

The private age key (`.sops/age.key`) was accidentally committed to git. This is a **critical security issue** because:

- Anyone with access to the git repository can decrypt all secrets
- The key must be considered compromised
- All encrypted secrets need to be re-encrypted with a new key

## ✅ Solution Implemented

### 1. Automated Key Rotation via Taskfile

Added comprehensive SOPS management tasks to `Taskfile.yml`:

```bash
# View SOPS configuration and key status
task sops:info

# Check if age.key is in git (security check)
task sops:check-git

# Rotate the age key (generates new key pair)
task sops:rotate-key

# Re-encrypt all SOPS files with new key
task sops:reencrypt

# Clean age.key from git history
task sops:clean-history

# Edit encrypted secrets
task sops:edit

# View decrypted secrets
task sops:decrypt
```

### 2. Ansible Playbook for Key Rotation

Created `infra/ansible/rotate_age_key_playbook.yml` with tasks that:

- Backup old keys with timestamp
- Generate new age key pair using `age-keygen`
- Extract public key and update `.sops.yaml`
- Provide clear next steps

### 3. Re-encryption Script

Created `infra/ansible/roles/sops_setup/files/reencrypt_all.sh` to automatically find and re-encrypt all SOPS files.

## 📋 Step-by-Step Recovery Process

### Step 1: Rotate the Age Key

```bash
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub
task sops:rotate-key
```

This will:

- ✅ Backup existing keys
- ✅ Generate new age key pair
- ✅ Update `.sops.yaml` with new public key
- ✅ Display the new public key

### Step 2: Re-encrypt All Secrets

```bash
task sops:reencrypt
```

This will re-encrypt:

- `infra/secrets/secrets.enc.json`
- `infra/secrets/mac-mini.enc.yaml`
- Any other SOPS-encrypted files

### Step 3: Update CI/CD Secrets

Update any CI/CD systems (GitHub Actions, etc.) with the **new private key** from `.sops/age.key`.

**IMPORTANT:** The private key content should be stored as a secret in your CI/CD system, NOT committed to git.

### Step 4: Commit the Changes

```bash
# Stage the updated files (NOT age.key!)
git add .sops.yaml .sops/age.pub infra/secrets/*.enc.*

# Commit
git commit -m "security: rotate age key and re-encrypt secrets"

# Push
git push
```

### Step 5: Clean Git History

Remove the compromised key from git history:

```bash
# First, install git-filter-repo if not already installed
brew install git-filter-repo

# Then clean the history
task sops:clean-history

# Force push to remote
git push origin --force --all
git push origin --force --tags
```

**⚠️ WARNING:** This rewrites git history. All collaborators must re-clone the repository.

### Step 6: Notify Team

1. Inform all team members that the repository history was rewritten
2. Ask them to:
   - Delete their local clones
   - Clone fresh from remote
   - Verify they have the new `.sops/age.key` (share via secure channel)

## 🔒 Prevention

### Verify .gitignore

The `.gitignore` file should already contain:

```
.sops/age.key       # Private age key (project-scoped)
!.sops/age.pub      # Public age key (can be committed)
```

### Regular Security Checks

Run periodically:

```bash
task sops:check-git
```

This will verify that:

- Private key is NOT tracked by git
- Private key doesn't exist in git history

### Pre-commit Hooks

Consider adding a pre-commit hook to prevent committing the private key:

```bash
# In .git/hooks/pre-commit
if git diff --cached --name-only | grep -q "\.sops/age\.key$"; then
    echo "ERROR: Attempting to commit .sops/age.key!"
    echo "Private keys should NEVER be committed."
    exit 1
fi
```

## 📚 Additional Resources

- [SOPS Documentation](https://github.com/getsops/sops)
- [Age Encryption](https://age-encryption.org/)
- [Git Filter Repo](https://github.com/newren/git-filter-repo)

## 🆘 Emergency Contacts

If you discover additional compromised secrets:

1. Immediately rotate ALL affected credentials
2. Review access logs for unauthorized access
3. Update all affected systems
4. Document the incident

## ✅ Checklist

- [ ] Run `task sops:rotate-key`
- [ ] Run `task sops:reencrypt`
- [ ] Update CI/CD secrets
- [ ] Commit updated encrypted files
- [ ] Run `task sops:clean-history`
- [ ] Force push to remote
- [ ] Notify all team members
- [ ] Verify `task sops:check-git` passes
- [ ] Rotate any secrets that were accessible with old key
- [ ] Review access logs for suspicious activity
