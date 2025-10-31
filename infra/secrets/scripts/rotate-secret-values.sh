#!/usr/bin/env bash
# Helper script to rotate secret values after age key compromise
set -euo pipefail

cd "$(dirname "$0")"

echo "🔐 Secret Values Rotation Helper"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  IMPORTANT: Re-encrypting is NOT enough!"
echo "    You must generate NEW secret values (API keys, passwords, etc.)"
echo ""
echo "This script will help you:"
echo "  1. Decrypt old secrets (using backed-up key)"
echo "  2. Create templates for new secrets"
echo "  3. Encrypt with new key"
echo ""

# Find the most recent backup
BACKUP_KEY=$(ls -t .sops/age.key.backup.* 2>/dev/null | head -1)

if [ -z "$BACKUP_KEY" ]; then
    echo "❌ No backup key found in .sops/"
    echo ""
    echo "Expected: .sops/age.key.backup.*"
    exit 1
fi

echo "📁 Using backup key: $BACKUP_KEY"
echo ""

# Step 1: Show current secrets structure
echo "📋 Step 1: Current Secrets Structure"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Showing keys (values hidden for security):"
echo ""

SOPS_AGE_KEY_FILE="$BACKUP_KEY" \
  sops decrypt infra/secrets/secrets.enc.json | \
  jq 'walk(if type == "string" and (. | length > 10) then "***REDACTED***" else . end)'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 2: Ask user what they want to do
echo "📋 Step 2: Choose Action"
echo ""
echo "What would you like to do?"
echo ""
echo "  1) View full current secrets (to know what to rotate)"
echo "  2) Edit secrets.enc.json with NEW values (using new key)"
echo "  3) Edit mac-mini.enc.yaml with NEW values (using new key)"
echo "  4) Show detailed rotation guide"
echo "  5) Exit"
echo ""
read -p "Choose (1-5): " -n 1 -r
echo
echo ""

case $REPLY in
    1)
        echo "🔓 Decrypting with OLD key..."
        echo ""
        echo "=== secrets.enc.json ==="
        SOPS_AGE_KEY_FILE="$BACKUP_KEY" \
          sops decrypt infra/secrets/secrets.enc.json | jq '.'
        echo ""
        echo "=== mac-mini.enc.yaml ==="
        SOPS_AGE_KEY_FILE="$BACKUP_KEY" \
          sops decrypt --input-type dotenv --output-type dotenv \
          infra/secrets/mac-mini.enc.yaml
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "⚠️  Remember: These values are COMPROMISED!"
        echo "    You must generate NEW values for all of these!"
        ;;
    2)
        echo "✏️  Opening secrets.enc.json for editing..."
        echo ""
        echo "📝 Instructions:"
        echo "  1. SOPS will decrypt the file for you"
        echo "  2. Replace ALL secret values with NEW ones:"
        echo "     - Generate new API keys from providers"
        echo "     - Generate new passwords"
        echo "     - Generate new tokens"
        echo "  3. Save and close the editor"
        echo "  4. SOPS will encrypt with the NEW key"
        echo ""
        read -p "Press Enter to open editor..."

        # Use new key for encryption
        sops infra/secrets/secrets.enc.json

        echo ""
        echo "✅ File updated and encrypted with NEW key!"
        ;;
    3)
        echo "✏️  Opening mac-mini.enc.yaml for editing..."
        echo ""
        echo "⚠️  Note: This file is in dotenv format"
        echo ""
        read -p "Press Enter to continue..."

        # Decrypt with old key
        SOPS_AGE_KEY_FILE="$BACKUP_KEY" \
          sops decrypt --input-type dotenv --output-type dotenv \
          infra/secrets/mac-mini.enc.yaml > /tmp/mac-mini.env

        echo "✏️  Opening in editor (nano). Generate NEW values for all secrets!"
        echo ""
        nano /tmp/mac-mini.env

        # Encrypt with new key
        sops encrypt --input-type dotenv --output-type dotenv \
          /tmp/mac-mini.env > infra/secrets/mac-mini.enc.yaml

        # Clean up
        rm /tmp/mac-mini.env

        echo ""
        echo "✅ File updated and encrypted with NEW key!"
        ;;
    4)
        echo "📖 Opening rotation guide..."
        echo ""
        cat infra/secrets/SECRET_VALUES_ROTATION.md | less
        ;;
    5)
        echo "👋 Exiting"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Next Steps:"
echo ""
echo "1. Make sure you've rotated ALL secret values"
echo "2. Test decryption: sops decrypt infra/secrets/secrets.enc.json"
echo "3. Update services: task infra:setup && task infra:restart"
echo "4. Commit changes: git add infra/secrets/*.enc.*"
echo "5. Update CI/CD with new secrets"
echo ""
echo "For detailed guide: cat infra/secrets/SECRET_VALUES_ROTATION.md"
echo ""
