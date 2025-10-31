#!/bin/bash
# Check SOPS security - prevent private keys from being committed
# This is a comprehensive check for age encryption key security

set -e

echo "🔐 Checking SOPS security..."

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Track if any issues found
ISSUES_FOUND=0

# 1. Check if .sops/age.key is being staged
echo "  Checking for private key in staged files..."
if git diff --cached --name-only | grep -qE "\.sops/age\.key$"; then
    echo -e "${RED}❌ ERROR: SOPS private key (.sops/age.key) is staged!${NC}"
    echo ""
    echo "  This key must NEVER be committed to git."
    echo "  It would compromise ALL encrypted secrets."
    echo ""
    echo "  To fix:"
    echo "    git restore --staged .sops/age.key"
    echo ""
    ISSUES_FOUND=1
fi

# 2. Check for AGE-SECRET-KEY string in staged content (exclude this script itself)
echo "  Checking for private key content in staged changes..."
if git diff --cached --  ':!precommit/checks/check-sops-security.sh' | grep -q "AGE-SECRET-KEY"; then
    echo -e "${RED}❌ ERROR: Found AGE-SECRET-KEY in staged changes!${NC}"
    echo ""
    echo "  This appears to be a private age encryption key."
    echo "  Private keys must never be committed."
    echo ""
    echo "  To fix:"
    echo "    1. Review: git diff --cached"
    echo "    2. Unstage the file containing the key"
    echo "    3. Remove the private key from the file"
    echo ""
    ISSUES_FOUND=1
fi

# 3. Check for age private key format (backup files, etc.)
echo "  Checking for age key file patterns..."
if git diff --cached --name-only | grep -qE "age\.key(\.backup)?"; then
    echo -e "${YELLOW}⚠️  WARNING: Found age key file pattern in staged files${NC}"
    echo ""
    echo "  Files matching 'age.key' pattern:"
    git diff --cached --name-only | grep -E "age\.key(\.backup)?" | sed 's/^/    /'
    echo ""
    echo "  Verify these are not private keys!"
    echo ""
    ISSUES_FOUND=1
fi

# 4. Verify encrypted files are actually encrypted
echo "  Verifying encrypted files contain SOPS metadata..."
ENCRYPTED_FILES=$(git diff --cached --name-only | grep -E "\.(enc\.json|enc\.yaml)$" || true)
if [ -n "$ENCRYPTED_FILES" ]; then
    for file in $ENCRYPTED_FILES; do
        if [ -f "$file" ]; then
            # Check for SOPS metadata:
            # - JSON: "sops": { ... }
            # - YAML: sops:
            # - Encoded values often contain ENC[
            if ! grep -Eq '"sops"\s*:\s*\{|^sops:\s*$|ENC\[' "$file"; then
                echo -e "${RED}❌ ERROR: $file appears to be unencrypted!${NC}"
                echo ""
                echo "  Encrypted files must contain SOPS metadata (\"sops\": or sops: or ENC[)."
                echo "  This file may have been decrypted and not re-encrypted."
                echo ""
                echo "  To fix:"
                echo "    sops --encrypt $file > $file.tmp && mv $file.tmp $file"
                echo ""
                ISSUES_FOUND=1
            else
                echo -e "${GREEN}  ✓ $file is properly encrypted${NC}"
            fi
        fi
    done
fi

# 5. Check .gitignore has proper SOPS exclusions
echo "  Checking .gitignore for SOPS patterns..."
if ! grep -q "\.sops/age\.key" .gitignore 2>/dev/null; then
    echo -e "${YELLOW}⚠️  WARNING: .gitignore doesn't exclude .sops/age.key${NC}"
    echo ""
    echo "  Add to .gitignore:"
    echo "    .sops/age.key"
    echo "    .sops/*.backup.*"
    echo ""
fi

# 6. Check if .sops/age.key exists locally and has correct permissions
if [ -f ".sops/age.key" ]; then
    PERMS=$(stat -f "%Lp" .sops/age.key 2>/dev/null || stat -c "%a" .sops/age.key 2>/dev/null)
    if [ "$PERMS" != "600" ]; then
        echo -e "${YELLOW}⚠️  WARNING: .sops/age.key has permissions $PERMS (should be 600)${NC}"
        echo ""
        echo "  To fix:"
        echo "    chmod 600 .sops/age.key"
        echo ""
    fi
fi

# Summary
echo ""
if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ SOPS security checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ SOPS security issues found!${NC}"
    echo ""
    echo "Review the errors above and fix them before committing."
    echo ""
    echo "For more information, see:"
    echo "  docs/security/README.md"
    echo ""
    exit 1
fi
