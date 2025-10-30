---
doc_id: DOC-2025-00018
title: Infrastructure & Secrets Directory
doc_type: reference
status: active
canonical: true
created: 2025-10-30
tags: [infrastructure, secrets, sops, docker, reference]
summary: Directory reference for infrastructure templates and SOPS-encrypted secrets for hub services
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# 🏗️ lunar-snake-hub Infrastructure

Automated setup for Mac Mini infrastructure using Ansible, Docker, and SOPS.

## 📋 Overview

This infrastructure supports the lunar-snake-hub architecture with:

- **Letta**: Agent memory persistence (Phase 1)
- **Qdrant**: Vector database for RAG (Phase 2)
- **n8n**: Workflow automation (Phase 3)
- **Context Gateway**: HTTP API for agents (Phase 2)

## 🚀 Quick Start

### Windows (Setup & Deploy)

```powershell
# 1. Install prerequisites
winget install Mozilla.Sops FiloSottile.age

# 2. Generate age encryption key
cd infra\secrets
.\generate-age-key.ps1

# 3. Create and encrypt environment file
cp ..\docker\.env.template ..\docker\.env
# Edit ..\docker\.env with your GLM-4.6 API key
.\encrypt-env.ps1

# 4. Commit and push encrypted config
git add ..\docker\.env.enc ..\.sops.yaml
git commit -m "Add encrypted infrastructure configuration"
git push origin main
```

### Mac Mini (First Time Setup)

```bash
# 1. Clone the repository
cd ~/repos
git clone https://github.com/GiantCroissant-Lunar/lunar-snake-hub.git
cd lunar-snake-hub

# 2. Copy your age key from Windows to Mac
mkdir -p ~/.config/sops/age
# Paste the key contents into ~/.config/sops/age/keys.txt
chmod 600 ~/.config/sops/age/keys.txt

# 3. Run Ansible playbook (installs everything)
cd infra/ansible
ansible-playbook -i inventory/hosts.yml playbook.yml

# This installs: Docker, SOPS, age, gh, yq, task, etc.
# Configures: SOPS keys, Docker services, GitHub auth
# Starts: Letta, Qdrant, n8n containers
```

See detailed setup guides:

- [Secrets Management](secrets/README.md) - SOPS and age configuration
- [Ansible Automation](ansible/README.md) - Playbook details

## 📁 Directory Structure

```
infra/
├── ansible/                    # Ansible automation
│   ├── playbook.yml           # Main playbook
│   ├── inventory/hosts.yml    # Mac Mini configuration
│   ├── vars/config.yml        # Variables
│   └── roles/
│       ├── homebrew_packages/ # Install packages via brew
│       ├── sops_setup/        # Configure SOPS/age keys
│       ├── docker_services/   # Docker Compose management
│       └── github_integration/# GitHub CLI setup
│
├── docker/                    # Docker Compose setup
│   ├── docker-compose.yml     # All services (Letta, Qdrant, n8n)
│   ├── .env.template          # Template for secrets
│   ├── .env.enc               # Encrypted secrets (in git) ✅
│   ├── .env                   # Decrypted (gitignored) ❌
│   └── data/                  # Docker volumes (gitignored)
│
└── secrets/                   # SOPS key management
    ├── README.md              # Comprehensive secrets guide
    ├── generate-age-key.ps1   # Generate encryption keys (Windows)
    ├── encrypt-env.ps1        # Encrypt .env (Windows)
    └── decrypt-env.ps1        # Decrypt .env (Windows)
```

## 🔧 Services

| Service | Port | URL (Tailscale) | Purpose | Phase |
|---------|------|-----------------|---------|-------|
| **Letta** | 5055 | <http://juis-mac-mini:5055> | Agent memory | 1 |
| **Qdrant** | 6333 | <http://juis-mac-mini:6333> | Vector DB | 2 |
| **Gateway** | 5057 | <http://juis-mac-mini:5057> | HTTP API | 2 |
| **n8n** | 5678 | <http://juis-mac-mini:5678> | Automation | 3 |

**Health Checks:**

```bash
# On Mac Mini
curl http://localhost:5055/v1/health  # Letta
curl http://localhost:6333/healthz    # Qdrant

# From Windows (via Tailscale)
curl http://juis-mac-mini:5055/v1/health
```

## 🔐 Secrets Management

All secrets encrypted using SOPS + age. See [secrets/README.md](secrets/README.md) for details.

**Quick Reference:**

```powershell
# Windows: Generate key (first time)
cd infra\secrets
.\generate-age-key.ps1

# Windows: Encrypt secrets
.\encrypt-env.ps1

# Mac: Decrypt secrets
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
sops decrypt infra/docker/.env.enc > infra/docker/.env
```

**Key Locations:**

- Windows: `%USERPROFILE%\.config\sops\age\keys.txt`
- Mac: `~/.config/sops/age/keys.txt`
- GitHub Secret: `SOPS_AGE_KEY` (for CI/CD)

## 🧪 Testing

```bash
# Verify Ansible setup
cd infra/ansible
ansible-playbook -i inventory/hosts.yml playbook.yml --check

# Check Docker services
cd ../docker
docker compose ps
docker compose logs -f letta

# Test from Windows
curl http://juis-mac-mini:5055/v1/health
```

## 📊 Phase Rollout

### ✅ Phase 1: Memory (Current)

- **Services:** Letta
- **Goal:** Persistent agent memory
- **Status:** Ready to deploy

### 🔄 Phase 2: Context (Next)

- **Services:** Letta + Qdrant + Gateway
- **Goal:** RAG-based context retrieval
- **Status:** Infrastructure ready, Gateway code needed

### 🔄 Phase 3: Automation (Later)

- **Services:** All Phase 2 + n8n
- **Goal:** Auto-reindex on push, scheduled sync
- **Status:** n8n container ready, workflows needed

## 🆘 Troubleshooting

See comprehensive troubleshooting in [main README](README.md#troubleshooting).

**Common Issues:**

```bash
# Can't decrypt: Set environment variable
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt

# Services won't start: Check ports
lsof -i :5055  # Should be free

# Can't access from Windows: Check Tailscale
tailscale status
ping juis-mac-mini
```

## 📚 Next Steps

1. **Windows:** Generate age key and encrypt .env → `infra/secrets/`
2. **Mac Mini:** Run Ansible playbook → `infra/ansible/`
3. **Test:** Access Letta from Windows via Tailscale
4. **Configure:** Add Letta as MCP tool in VS Code

See: [SESSION_HANDOVER_2025-10-30.md](../SESSION_HANDOVER_2025-10-30.md) Task #6-8
