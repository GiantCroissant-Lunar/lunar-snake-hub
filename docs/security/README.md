# 🔐 Security Documentation Index

Documentation for age key rotation and secrets management.

## 📚 Quick Navigation

### 🚨 If You Have a Compromised Key

**START HERE:** [`ROTATION_COMPLETE.md`](./ROTATION_COMPLETE.md)

- Complete guide for age key rotation
- Step-by-step checklist
- What was rotated and next steps

### 📖 Detailed Guides

1. **[AGE_KEY_ROTATION.md](./AGE_KEY_ROTATION.md)**
   - Comprehensive age encryption key rotation guide
   - Security incident response procedures
   - Prevention measures

2. **[SECRET_VALUES_ROTATION.md](./SECRET_VALUES_ROTATION.md)**
   - How to rotate the actual secret values (API keys, passwords)
   - Why re-encrypting isn't enough
   - Step-by-step rotation process

3. **[WHAT_TO_ROTATE.md](./WHAT_TO_ROTATE.md)**
   - Specific list of all secrets in your system
   - Exact locations and how to rotate each one
   - Commands and links to provider dashboards

4. **[SERVICE_USAGE_ANALYSIS.md](./SERVICE_USAGE_ANALYSIS.md)**
   - Which services are actually using which secrets
   - What's required vs optional
   - Recommendations for simplification

5. **[KEY_ROTATION_COMPLETED.md](./KEY_ROTATION_COMPLETED.md)**
   - Final summary of October 31, 2025 key rotation
   - Old vs new key details
   - Backup locations

---

## 🛠️ Scripts Available

All scripts located in: `../../infra/secrets/scripts/`

### Quick Actions

```bash
# Rotate age key quickly
./infra/secrets/scripts/rotate-key-now.sh

# Rotate secret values interactively
./infra/secrets/scripts/rotate-secret-values.sh

# Complete rotation workflow
./infra/secrets/scripts/finish-key-rotation.sh

# Full Ansible-based rotation
./infra/secrets/scripts/rotate-age-key.sh
```

### Task Commands

```bash
# View SOPS configuration
task sops:info

# Check git security
task sops:check-git

# Rotate age key (Ansible)
task sops:rotate-key

# Re-encrypt all files
task sops:reencrypt

# Clean git history
task sops:clean-history

# Edit encrypted secrets
task sops:edit

# View decrypted secrets
task sops:decrypt
```

---

## 📋 Common Tasks

### View Current Secrets (Decrypted)

```bash
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub
sops --decrypt infra/secrets/secrets.enc.json
```

### Edit Secrets

```bash
cd /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub
sops infra/secrets/secrets.enc.json
```

### Verify Age Key

```bash
# Check public key
cat /Users/apprenticegc/Work/lunar-snake/lunar-snake-hub/.sops/age.pub

# Check if private key is in git (should return nothing)
git ls-files | grep "\.sops/age.key"
```

### Generate New Tokens/Passwords

```bash
# Generate a secure password
openssl rand -base64 24

# Generate an authentication token
openssl rand -base64 32

# Generate a webhook secret
openssl rand -hex 32
```

---

## 🔒 Security Best Practices

### DO ✅

- ✅ Keep private key (`.sops/age.key`) out of git
- ✅ Commit public key (`.sops/age.pub`)
- ✅ Commit encrypted files (`*.enc.json`, `*.enc.yaml`)
- ✅ Rotate keys immediately if compromised
- ✅ Rotate actual secret values, not just encryption key
- ✅ Use `chmod 600` on private key file
- ✅ Store private key in CI/CD secrets

### DON'T ❌

- ❌ Commit private key (`.sops/age.key`)
- ❌ Commit decrypted secrets files
- ❌ Share private key via insecure channels
- ❌ Reuse compromised passwords/tokens
- ❌ Skip rotating actual secret values after key compromise
- ❌ Leave decrypted files in `/tmp/`

---

## 🆘 Troubleshooting

### Can't decrypt files

```bash
# Check key file format
cat .sops/age.key | head -1
# Should start with: # created:

# Check permissions
ls -la .sops/age.key
# Should show: -rw------- (600)

# Verify SOPS configuration
cat .sops.yaml
```

### Key was committed to git

1. Stop immediately
2. Rotate the key: `./infra/secrets/rotate-key-now.sh`
3. Rotate all secret values: `./infra/secrets/rotate-secret-values.sh`
4. Clean git history: `task sops:clean-history`
5. Force push: `git push --force --all`

### Services won't start after rotation

```bash
# Regenerate .env file
task infra:setup

# Restart services
task infra:restart

# Check status
task infra:status
```

---

## 📅 Rotation History

### October 31, 2025

- **Event:** Private age key accidentally committed to git
- **Action:** Complete key and secret values rotation
- **Status:** ✅ Completed
- **Details:** See [KEY_ROTATION_COMPLETED.md](./KEY_ROTATION_COMPLETED.md)

---

## 📖 Related Documentation

- Main secrets README: [`../../infra/secrets/README.md`](../../infra/secrets/README.md)
- SOPS setup role: [`../../infra/ansible/roles/sops_setup/`](../../infra/ansible/roles/sops_setup/)
- Taskfile SOPS tasks: [`../../Taskfile.yml`](../../Taskfile.yml) (search for `sops:`)

---

## 🎯 Quick Reference

| What | Where | Command |
|------|-------|---------|
| **Private Key** | `.sops/age.key` | `cat .sops/age.key` |
| **Public Key** | `.sops/age.pub` | `cat .sops/age.pub` |
| **Encrypted Secrets** | `infra/secrets/secrets.enc.json` | `sops -d infra/secrets/secrets.enc.json` |
| **SOPS Config** | `.sops.yaml` | `cat .sops.yaml` |
| **Edit Secrets** | N/A | `sops infra/secrets/secrets.enc.json` |
| **Rotate Key** | N/A | `./infra/secrets/scripts/rotate-key-now.sh` |
| **Check Security** | N/A | `task sops:check-git` |

---

## 💡 Remember

**After key compromise:**

1. Rotate the encryption key ✅
2. Rotate all secret VALUES ✅ ← **This is critical!**
3. Update CI/CD with new key ✅
4. Clean git history ✅
5. Force push ✅
6. Notify team to re-clone ✅

**The old passwords/tokens are still valid until you rotate them!**
