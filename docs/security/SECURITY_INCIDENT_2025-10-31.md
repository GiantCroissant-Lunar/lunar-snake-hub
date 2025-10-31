# Security Incident Report - Private Key in Git History

**Date:** 2025-10-31  
**Severity:** HIGH  
**Status:** RESOLVED

## Summary

A private age encryption key was accidentally committed to the git repository and pushed to the remote (GitHub). The key has been removed from all git history and the remote repository has been cleaned.

## Timeline

- **2025-06-18:** Private key `AGE-SECRET-KEY-165LYMYX742PP7QCHK05C26UYKJM7V6PYEJHTVRQPPWMN7W8E77EQ0C09W5` was committed in commit `cd57ae1`
- **2025-10-31 15:21:** Issue discovered during repository cleanup
- **2025-10-31 15:22:** Confirmed key was in remote repository history
- **2025-10-31 15:23:** Git history rewritten using `git-filter-repo`
- **2025-10-31 15:24:** Remote repository force-pushed with cleaned history

## Compromised Key Details

```
# Public key: age1ydjyyu9m550m8dj22qag8qlk8ugh6n454tjezenmtra48tjaypeq5m3zj0
# Private key: AGE-SECRET-KEY-165LYMYX742PP7QCHK05C26UYKJM7V6PYEJHTVRQPPWMN7W8E77EQ0C09W5
# Created: 2025-06-18T16:03:39+08:00
```

**This key is now considered COMPROMISED and must not be used.**

## Actions Taken

### 1. History Cleanup ✅

- Installed `git-filter-repo` tool
- Created backup: `../lunar-snake-hub-backup.git`
- Removed `.sops/age.key` from all git history
- Force-pushed cleaned history to remote

### 2. Prevention Measures ✅

- Added `.sops/age.key` to `.gitignore`
- Implemented pre-commit hook (`check-sops-security.sh`) to prevent future commits
- Updated security documentation

### 3. New Key Generated ✅

- New age key pair generated on 2025-10-31T10:16:50+08:00
- Public key: `age1jgv3pfxe8a5nw4hnf2hwt4w6h0npwtgtj66xnl6fw7j49n5jr54qgfvagl`
- Private key stored locally in `.sops/age.key` (gitignored)

## Required Actions

### CRITICAL: Re-encrypt All Secrets ⚠️

All secrets encrypted with the old key must be re-encrypted with the new key:

```bash
# 1. Decrypt with old key (if you still have it)
export SOPS_AGE_KEY="AGE-SECRET-KEY-165LYMYX742PP7QCHK05C26UYKJM7V6PYEJHTVRQPPWMN7W8E77EQ0C09W5"
sops -d infra/secrets/secrets.enc.json > secrets.decrypted.json

# 2. Re-encrypt with new key
export SOPS_AGE_KEY_FILE=.sops/age.key
sops -e secrets.decrypted.json > infra/secrets/secrets.enc.json

# 3. Securely delete decrypted file
shred -u secrets.decrypted.json  # Linux
rm -P secrets.decrypted.json     # macOS
```

### For Team Members

If other team members have cloned this repository:

1. **Backup any local changes**
2. **Delete local repository**
3. **Fresh clone from remote:**

   ```bash
   git clone git@github.com:GiantCroissant-Lunar/lunar-snake-hub.git
   ```

4. **Generate new local age key** (do not use the old one)

## Verification

```bash
# Verify key is not in history
git log --all --full-history -- .sops/age.key
# Should return nothing

# Verify key is ignored
git check-ignore -v .sops/age.key
# Should show: .gitignore:6:.sops/age.key

# Try to commit key (should be blocked)
git add -f .sops/age.key
git commit -m "test"
# Should fail with pre-commit hook error
```

## Lessons Learned

1. **Never commit private keys** - Even temporarily
2. **Use .gitignore from the start** - Add sensitive files before first commit
3. **Pre-commit hooks are essential** - Automated checks prevent human error
4. **Regular security audits** - Review what's in git history periodically
5. **Assume compromise** - Any key in git history should be considered compromised

## References

- [Age Key Rotation Guide](./AGE_KEY_ROTATION.md)
- [Pre-commit Security Checklist](./PRE_COMMIT_CHECKLIST.md)
- [SOPS Documentation](https://github.com/mozilla/sops)

## Backup Location

A full backup of the repository (before cleanup) is stored at:

```
/Users/apprenticegc/Work/lunar-snake/lunar-snake-hub-backup.git
```

**Keep this backup secure and delete it after verifying all secrets are re-encrypted.**
