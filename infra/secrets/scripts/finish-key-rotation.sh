#!/usr/bin/env bash
# Final steps after age key rotation
set -euo pipefail

cd "$(dirname "$0")"

echo "🔐 Age Key Rotation - Final Steps"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Check if age.key is tracked
echo "📋 Step 1: Checking if private key is tracked in git..."
if git ls-files | grep -q "\.sops/age.key"; then
    echo "❌ CRITICAL: .sops/age.key is tracked in git!"
    echo ""
    echo "Removing from git index..."
    git rm --cached .sops/age.key
    echo "✅ Removed from git (but still exists locally)"
else
    echo "✅ Private key is NOT tracked (good!)"
fi
echo ""

# Step 2: Show what will be committed
echo "📋 Step 2: Files to commit:"
echo ""
git status --short .sops.yaml .sops/age.pub infra/secrets/ 2>/dev/null || echo "No changes detected"
echo ""

# Step 3: Stage files
read -p "Stage these files for commit? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add .sops.yaml .sops/age.pub infra/secrets/secrets.enc.json infra/secrets/mac-mini.enc.yaml
    echo "✅ Files staged"
    echo ""

    # Show what's staged
    echo "📋 Staged changes:"
    git diff --cached --name-status
    echo ""

    # Commit
    read -p "Commit these changes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git commit -m "security: rotate age key and re-encrypt secrets

- Generated new age key pair
- Old key: age1ydjyyu9m550m8dj22qag8qlk8ugh6n454tjezenmtra48tjaypeq5m3zj0 (COMPROMISED)
- New key: age1jgv3pfxe8a5nw4hnf2hwt4w6h0npwtgtj66xnl6fw7j49n5jr54qgfvagl
- Re-encrypted all SOPS-encrypted secrets
- Old keys backed up with timestamp"
        echo ""
        echo "✅ Changes committed!"
        echo ""
    else
        echo "⏸️  Commit skipped. Files remain staged."
        echo ""
    fi
else
    echo "⏸️  Staging skipped."
    echo ""
fi

# Step 4: Display new private key for CI/CD
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Step 3: Update CI/CD Secrets"
echo ""
echo "Copy this NEW private key to your CI/CD system:"
echo "(GitHub Actions secret, etc.)"
echo ""
echo "Secret name: SOPS_AGE_KEY (or similar)"
echo ""
cat .sops/age.key
echo ""

# Step 5: Git history cleanup warning
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  Step 4: Clean Git History (REQUIRED!)"
echo ""
echo "The old private key still exists in git history."
echo "You MUST remove it using one of these methods:"
echo ""
echo "Option 1 - git-filter-repo (recommended):"
echo "  brew install git-filter-repo"
echo "  git filter-repo --path .sops/age.key --invert-paths --force"
echo "  git push origin --force --all"
echo ""
echo "Option 2 - Use the task command:"
echo "  task sops:clean-history"
echo ""
echo "⚠️  After cleaning history, ALL collaborators must re-clone!"
echo ""

# Step 6: Verification
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Step 5: Verify Everything"
echo ""
echo "Test decryption with new key:"
echo "  sops decrypt infra/secrets/secrets.enc.json | jq -r 'keys'"
echo ""
echo "Check git security:"
echo "  task sops:check-git"
echo ""
echo "View full guide:"
echo "  cat KEY_ROTATION_COMPLETED.md"
echo ""
