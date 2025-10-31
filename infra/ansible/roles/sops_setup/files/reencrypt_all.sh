#!/usr/bin/env bash
# Script to re-encrypt all SOPS-encrypted files with a new age key
# This should be run after rotating the age key

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

echo "🔍 Searching for SOPS-encrypted files..."

# Find all files that might be SOPS-encrypted
# Look for files with 'sops:' in them (SOPS metadata)
encrypted_files=$(find "$REPO_ROOT" -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.env" \) \
  -not -path "*/node_modules/*" \
  -not -path "*/.git/*" \
  -not -path "*/build/*" \
  -not -path "*/dist/*" \
  -exec grep -l "sops:" {} \; 2>/dev/null || true)

if [ -z "$encrypted_files" ]; then
  echo "✅ No SOPS-encrypted files found!"
  exit 0
fi

echo ""
echo "📋 Found the following encrypted files:"
echo "$encrypted_files"
echo ""

read -p "🔐 Do you want to re-encrypt these files with the new key? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "❌ Aborted."
  exit 1
fi

echo ""
echo "🔄 Re-encrypting files..."
echo ""

failed_files=()
success_count=0

while IFS= read -r file; do
  echo "  Processing: $file"
  if sops updatekeys "$file" 2>&1; then
    echo "    ✅ Success"
    ((success_count++))
  else
    echo "    ❌ Failed"
    failed_files+=("$file")
  fi
done <<< "$encrypted_files"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary:"
echo "  ✅ Successfully re-encrypted: $success_count files"
echo "  ❌ Failed: ${#failed_files[@]} files"

if [ ${#failed_files[@]} -gt 0 ]; then
  echo ""
  echo "❌ Failed files:"
  printf '  - %s\n' "${failed_files[@]}"
  exit 1
fi

echo ""
echo "✨ All files successfully re-encrypted with the new key!"
echo ""
echo "📝 Next steps:"
echo "  1. Review the changes: git diff"
echo "  2. Commit the re-encrypted files: git add . && git commit -m 'chore: re-encrypt secrets with new age key'"
echo "  3. Remove the compromised key from git history"
