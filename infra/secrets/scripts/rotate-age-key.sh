#!/usr/bin/env bash
# Rotate AGE key for SOPS encryption
# This script will:
# 1. Backup the old key
# 2. Generate a new age key pair
# 3. Update .sops.yaml with the new public key
# 4. Provide instructions for re-encrypting secrets

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANSIBLE_DIR="$SCRIPT_DIR/infra/ansible"

echo "🔐 AGE Key Rotation Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  WARNING: This will generate a NEW age key pair!"
echo ""
echo "Current key location: .sops/age.key"
echo "Old keys will be backed up with timestamp."
echo ""

# Check if the private key was committed
if git ls-files --error-unmatch .sops/age.key >/dev/null 2>&1; then
  echo "❌ SECURITY ISSUE: .sops/age.key is currently tracked by git!"
  echo ""
  echo "This is a security vulnerability. The private key should NEVER be committed."
  echo ""
  read -p "Do you want to continue with key rotation? (y/N): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted."
    exit 1
  fi
else
  echo "✅ Private key is not tracked by git (good!)"
  echo ""
  read -p "Continue with key rotation? (y/N): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted."
    exit 1
  fi
fi

echo ""
echo "🚀 Running Ansible playbook..."
echo ""

cd "$ANSIBLE_DIR"
ansible-playbook rotate_age_key_playbook.yml

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Key rotation complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Re-encrypt secrets: ./infra/ansible/roles/sops_setup/files/reencrypt_all.sh"
echo "  2. Update CI/CD with new private key from .sops/age.key"
echo "  3. Commit changes: git add .sops.yaml .sops/age.pub"
echo "  4. Remove old key from git history (see instructions below)"
echo ""
echo "🗑️  To remove the compromised key from git history:"
echo "  git filter-repo --path .sops/age.key --invert-paths"
echo "  # Or use: bfg --delete-files age.key"
echo ""
