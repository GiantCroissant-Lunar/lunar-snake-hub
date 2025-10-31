# Age Key Rotation - Completion Summary

## ✅ Completed on: October 31, 2025

### 🔑 What Was Done

1. **Generated New Age Key Pair**
   - Old public key: `age1ydjyyu9m550m8dj22qag8qlk8ugh6n454tjezenmtra48tjaypeq5m3zj0`
   - New public key: `age1jgv3pfxe8a5nw4hnf2hwt4w6h0npwtgtj66xnl6fw7j49n5jr54qgfvagl`

2. **Backed Up Old Keys**
   - `.sops/age.key.backup.20251031_101650`
   - `.sops/age.pub.backup.20251031_101650`

3. **Updated Configuration**
   - ✅ `.sops.yaml` updated with new public key
   - ✅ `.sops/age.pub` updated

4. **Re-encrypted Secrets**
   - ✅ `infra/secrets/secrets.enc.json`
   - ✅ `infra/secrets/mac-mini.enc.yaml`

### 📋 Files Changed

```
Modified:
  .sops.yaml                         (new public key)
  .sops/age.pub                      (new public key)
  .sops/age.key                      (NEW PRIVATE KEY - DO NOT COMMIT!)
  infra/secrets/secrets.enc.json     (re-encrypted with new key)
  infra/secrets/mac-mini.enc.yaml    (re-encrypted with new key)

Created (backups):
  .sops/age.key.backup.20251031_101650
  .sops/age.pub.backup.20251031_101650
  .sops.yaml.backup.20251031_101650
```

### 🚨 CRITICAL: Next Steps Required

#### 1. Remove Private Key from Git (if tracked)

Check if age.key is in git:

```bash
git ls-files | grep "\.sops/age.key"
```

If found, remove it:

```bash
git rm --cached .sops/age.key
```

#### 2. Commit the Changes

**IMPORTANT:** Only commit the public key and re-encrypted files!

```bash
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub

# Stage ONLY these files:
git add .sops.yaml
git add .sops/age.pub  
git add infra/secrets/secrets.enc.json
git add infra/secrets/mac-mini.enc.yaml

# Verify what you're about to commit (should NOT include age.key)
git status

# Commit
git commit -m "security: rotate age key and re-encrypt secrets

- Generated new age key pair
- Old key: age1ydjyyu9m550m8dj22qag8qlk8ugh6n454tjezenmtra48tjaypeq5m3zj0 (COMPROMISED)
- New key: age1jgv3pfxe8a5nw4hnf2hwt4w6h0npwtgtj66xnl6fw7j49n5jr54qgfvagl
- Re-encrypted all SOPS-encrypted secrets
- Old keys backed up with timestamp"
```

#### 3. Update CI/CD Secrets

The **NEW private key** needs to be added to your CI/CD system:

1. Read the new private key:

   ```bash
   cat /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub/.sops/age.key
   ```

2. Update your CI/CD secrets (GitHub Actions, etc.) with this new key

3. The CI/CD secret name is likely one of:
   - `SOPS_AGE_KEY`
   - `AGE_SECRET_KEY`
   - `SOPS_AGE_KEY_FILE`

#### 4. Clean Git History (REQUIRED!)

The old private key was committed to git. Even though it's removed now, it still exists in git history. Anyone with access to the repository history can still retrieve it.

**Option A: Using git-filter-repo (recommended)**

```bash
# Install if needed
brew install git-filter-repo

# Remove the file from ALL history
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub
git filter-repo --path .sops/age.key --invert-paths --force

# Force push to remote (THIS REWRITES HISTORY!)
git push origin --force --all
git push origin --force --tags
```

**Option B: Using BFG Repo-Cleaner**

```bash
brew install bfg
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub
bfg --delete-files age.key
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin --force --all
```

⚠️ **IMPORTANT:** After rewriting history, all collaborators must:

1. Delete their local clones
2. Clone fresh from the remote repository

#### 5. Verify Security

After completing all steps, verify:

```bash
# Verify private key is NOT tracked
git ls-files | grep "\.sops/age.key"
# Should return nothing

# Verify private key is NOT in history
git log --all --full-history -- .sops/age.key
# Should return nothing

# Verify decryption works with new key
sops decrypt infra/secrets/secrets.enc.json
# Should successfully decrypt
```

### 🗑️ Cleanup Old Backups (After Verification)

Once everything is working, you can remove the backup files:

```bash
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub/.sops
rm -f age.key.backup.* age.pub.backup.* age.key.new
rm -f ../.sops.yaml.backup.*
```

### ✅ Security Checklist

- [ ] Old private key backed up
- [ ] New key pair generated
- [ ] .sops.yaml updated with new public key
- [ ] All encrypted secrets re-encrypted
- [ ] Changes committed (without private key)
- [ ] CI/CD secrets updated with new private key
- [ ] Git history cleaned (old private key removed)
- [ ] All collaborators notified to re-clone
- [ ] Decryption verified with new key
- [ ] Old backup files removed

### 📞 If You Need Help

See the complete guide: `infra/secrets/AGE_KEY_ROTATION.md`

Or use the task commands:

```bash
task sops:info        # Show current status
task sops:check-git   # Verify git security
task sops:decrypt     # Test decryption
```

## 🔒 Old Compromised Key (For Reference)

**DO NOT USE THIS KEY ANYMORE!**

Public key: `age1ydjyyu9m550m8dj22qag8qlk8ugh6n454tjezenmtra48tjaypeq5m3zj0`

This key must be considered compromised and should not be used to encrypt any new secrets.
