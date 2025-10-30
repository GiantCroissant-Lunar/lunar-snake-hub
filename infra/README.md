# Infrastructure & Secrets

Infrastructure templates and encrypted secrets for hub services.

## Secrets (SOPS)

Secrets are encrypted with [SOPS](https://github.com/mozilla/sops) and stored here.

### Setup

**1. Generate Age key (one-time):**
```bash
age-keygen -o ~/.config/sops/age/keys.txt
# Save the public key for .sops.yaml
```

**2. Create `.sops.yaml`:**
```yaml
creation_rules:
  - path_regex: secrets/.*\.enc\.yaml$
    age: age1your_public_key_here
```

**3. Create & encrypt secrets:**
```bash
# Create plaintext
cat > secrets/mac-mini.yaml <<EOF
OPENAI_API_KEY=your_glm_api_key
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
GATEWAY_TOKEN=your_random_token
EOF

# Encrypt
sops encrypt secrets/mac-mini.yaml > secrets/mac-mini.enc.yaml

# Delete plaintext
rm secrets/mac-mini.yaml

# Commit encrypted
git add secrets/mac-mini.enc.yaml
```

**4. Decrypt on Mac Mini:**
```bash
# Direct to .env
sops decrypt infra/secrets/mac-mini.enc.yaml > ~/ctx-hub/.env

# Or exec directly
sops exec-env infra/secrets/mac-mini.enc.yaml 'docker compose up -d'
```

## Mac Mini Services

See `docs/architecture/YOUR_DECISIONS_SUMMARY.md` for full setup.

**Services:**
- **Letta** (port 5055) - Agent memory
- **Qdrant** (port 6333) - Vector database
- **Context Gateway** (port 5057) - HTTP API
- **n8n** (port 5678) - Workflow orchestration

**docker-compose.yml** (example - add in Phase 1, Task #6):
```yaml
services:
  letta:
    image: ghcr.io/letta-ai/letta:latest
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL}
    ports: ["5055:5055"]
    volumes: ["./data:/data"]
```

## Next Steps

- Phase 1: Create `.sops.yaml` and encrypt Mac Mini secrets
- Phase 1: Set up Letta on Mac Mini (Task #6)
- Phase 2: Add Qdrant, Gateway services

See: `docs/guides/PHASE1_CHECKLIST.md` (Task #6)
