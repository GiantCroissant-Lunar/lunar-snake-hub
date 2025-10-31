#!/usr/bin/env bash
# Quick age key rotation script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔐 Age Key Rotation Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if age is installed
if ! command -v age-keygen &> /dev/null; then
    echo "❌ age-keygen not found!"
    echo ""
    echo "Installing age via Homebrew..."
    brew install age

    # Verify installation
    if ! command -v age-keygen &> /dev/null; then
        echo "❌ Failed to install age"
        echo ""
        echo "Please install manually:"
        echo "  brew install age"
        exit 1
    fi

    echo "✅ age installed successfully"
    echo ""
fi

echo "📁 Current directory: $PWD"
echo "📁 .sops directory: .sops/"
echo ""

# Backup existing keys
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -f .sops/age.key ]; then
    echo "📦 Backing up old keys..."
    cp .sops/age.key ".sops/age.key.backup.$TIMESTAMP"
    cp .sops/age.pub ".sops/age.pub.backup.$TIMESTAMP"
    echo "✅ Backed up to .sops/age.key.backup.$TIMESTAMP"
    echo ""
fi

# Generate new key
echo "🔑 Generating new age key pair..."
age-keygen > .sops/age.key 2>&1

# Extract public key
NEW_PUBLIC_KEY=$(grep "^# public key:" .sops/age.key | awk '{print $4}')

if [ -z "$NEW_PUBLIC_KEY" ]; then
    echo "❌ Failed to extract public key"
    exit 1
fi

# Write public key file
echo "# public key: $NEW_PUBLIC_KEY" > .sops/age.pub

echo "✅ New key pair generated!"
echo ""
echo "📋 New Public Key: $NEW_PUBLIC_KEY"
echo ""

# Update .sops.yaml
echo "📝 Updating .sops.yaml..."
if [ -f .sops.yaml ]; then
    # Create backup
    cp .sops.yaml ".sops.yaml.backup.$TIMESTAMP"

    # Replace the old public key with the new one
    OLD_PUBLIC_KEY=$(grep "age:" .sops.yaml | head -1 | awk '{print $2}')

    if [ -n "$OLD_PUBLIC_KEY" ]; then
        sed -i.bak "s/$OLD_PUBLIC_KEY/$NEW_PUBLIC_KEY/g" .sops.yaml
        rm .sops.yaml.bak
        echo "✅ Updated .sops.yaml"
    else
        echo "⚠️  Could not find old public key in .sops.yaml"
    fi
else
    echo "⚠️  .sops.yaml not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Key rotation complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Re-encrypt secrets: sops updatekeys infra/secrets/secrets.enc.json"
echo "  2. Re-encrypt: sops updatekeys infra/secrets/mac-mini.enc.yaml"
echo "  3. Commit changes: git add .sops.yaml .sops/age.pub infra/secrets/"
echo "  4. Update CI/CD with new private key from .sops/age.key"
echo ""
