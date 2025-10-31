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

### Infrastructure Philosophy

**Ansible = Provisioning** (install tools, setup environment)
**Task = Operations** (manage services, deploy, monitor)

This separation ensures:

- Ansible runs once to provision the Mac Mini
- Task commands handle day-to-day operations
- Clean separation of concerns

### Windows (Setup & Deploy)

```powershell
# 1. Install prerequisites
winget install Mozilla.Sops FiloSottile.age

# 2. Configure secrets (see infra/secrets/README.md)
cd infra\secrets
# Copy config.template.json to config.json
# Copy secrets.template.json to secrets.json
# Fill in your actual values (GLM API key, etc.)
.\encrypt-secrets.ps1

# 3. Commit and push
git add config.json secrets.enc.json
git commit -m "Add infrastructure configuration"
git push origin main
```

### Mac Mini (First Time Setup)

#### Step 1: Provisioning with Ansible (One-Time)

```bash
# 1. Clone the repository
cd ~/repos
git clone https://github.com/GiantCroissant-Lunar/lunar-snake-hub.git
cd lunar-snake-hub

# 2. Copy your age key from Windows
mkdir -p ~/.config/sops/age
nano ~/.config/sops/age/keys.txt
# Paste the key contents, then save
chmod 600 ~/.config/sops/age/keys.txt

# 3. Run Ansible provisioning playbook
cd infra/ansible
ansible-playbook -i inventory/hosts.yml playbook.yml

# This ONLY installs tools:
#  - Homebrew packages (Docker, SOPS, age, gh, yq, task)
#  - SOPS environment variables
#  - Docker data directories
# It does NOT start services!
```

#### Step 2: Operations with Task (Daily Use)

```bash
# After Ansible provisioning, use task commands:

cd ~/repos/lunar-snake-hub

# Setup: Generate .env from encrypted secrets
task infra:setup

# Start: Launch all services
task infra:start

# Status: Check health
task infra:status

# Logs: View service logs
task infra:logs:letta
task infra:logs:qdrant

# Stop: Stop all services
task infra:stop

# Development: Full setup + start + status
task infra:dev
```

See detailed setup guides:

- [Secrets Management](secrets/README.md) - SOPS and age configuration
- [Ansible Automation](ansible/README.md) - Playbook details

## 📁 Directory Structure

```
infra/
├── ansible/                    # Ansible provisioning (one-time setup)
│   ├── playbook.yml           # Main provisioning playbook
│   ├── inventory/hosts.yml    # Mac Mini configuration
│   ├── vars/config.yml        # Variables
│   └── roles/
│       ├── homebrew_packages/ # Install packages via brew
│       ├── sops_setup/        # Configure SOPS/age environment
│       ├── docker_setup/      # Create Docker directories
│       └── github_integration/# GitHub CLI setup
│
├── docker/                    # Docker Compose configuration
│   ├── docker-compose.yml     # All services (Letta, Qdrant, n8n)
│   ├── .env.template          # Template for environment
│   ├── .env                   # Generated (gitignored) ❌
│   └── data/                  # Docker volumes (gitignored)
│
└── secrets/                   # SOPS secrets management
    ├── README.md              # Comprehensive secrets guide
    ├── config.json            # Plain configuration ✅
    ├── config.template.json   # Configuration template ✅
    ├── secrets.json           # Sensitive data (gitignored) ❌
    ├── secrets.template.json  # Secrets template ✅
    ├── secrets.enc.json       # Encrypted secrets ✅
    ├── schemas/               # JSON Schema validation
    ├── json-to-env.ps1        # Convert JSON → .env
    ├── encrypt-secrets.ps1    # Encrypt secrets.json
    ├── decrypt-secrets.ps1    # Decrypt secrets.enc.json
    └── generate-age-key.ps1   # Generate age keys (Windows)
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

## 🎯 Available Task Commands

Run `task --list` to see all available commands. Key infrastructure tasks:

```bash
# Infrastructure Management
task infra:setup         # Generate .env from encrypted secrets
task infra:start         # Start all Docker services
task infra:stop          # Stop all services
task infra:restart       # Restart services
task infra:status        # Check service status and health
task infra:logs          # View all service logs
task infra:logs-letta    # View Letta logs only
task infra:logs-qdrant   # View Qdrant logs only
task infra:logs-n8n      # View n8n logs only
task infra:pull          # Pull latest Docker images
task infra:clean         # Stop and remove all data (WARNING!)
task infra:dev           # Quick dev setup (setup + start + status)
task infra:reset         # Complete reset and restart
```

## 📚 Next Steps

1. **Windows:** Configure secrets → `infra/secrets/`

   ```powershell
   cd infra\secrets
   # Edit config.json and secrets.json
   .\encrypt-secrets.ps1
   ```

2. **Mac Mini:** Provision with Ansible → `infra/ansible/`

   ```bash
   ansible-playbook -i inventory/hosts.yml playbook.yml
   ```

3. **Mac Mini:** Deploy services with Task

   ```bash
   task infra:dev  # Setup + start + status
   ```

4. **Test:** Access from Windows

   ```powershell
   curl http://juis-mac-mini:5055/v1/health
   ```

5. **Configure:** Add Letta as MCP tool in VS Code
