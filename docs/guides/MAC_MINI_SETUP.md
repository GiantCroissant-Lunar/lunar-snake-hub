# Mac Mini Setup Guide for Phase 1

This guide walks through setting up Letta on the Mac Mini for Phase 1 of the lunar-snake-hub project.

## Prerequisites

- Mac Mini is powered on and accessible
- Tailscale installed and running on both Windows and Mac Mini
- SOPS and age installed on Mac Mini

## Step 1: SSH to Mac Mini

```bash
# Via Tailscale (preferred)
ssh <mac-mini-tailscale-name>

# Or via local IP
ssh <mac-mini-local-ip>
```

## Step 2: Install Required Tools

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker
brew install --cask docker

# Install SOPS and age
brew install sops age

# Start Docker Desktop
open /Applications/Docker.app
```

## Step 3: Create Setup Directory

```bash
mkdir -p ~/ctx-hub
cd ~/ctx-hub
```

## Step 4: Clone Hub and Decrypt Secrets

```bash
# Clone the hub repository
git clone https://github.com/GiantCroissant-Lunar/lunar-snake-hub.git

# Decrypt secrets to .env file
sops decrypt lunar-snake-hub/infra/secrets/mac-mini.enc.yaml > .env

# Verify the .env file contains your API keys
cat .env
```

**IMPORTANT**: Replace the placeholder values in the `.env` file with your actual API keys:

```bash
# Edit the .env file
nano .env

# Update these lines with real values:
# OPENAI_API_KEY=your_actual_glm_api_key_here
# OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
```

## Step 5: Create Docker Compose Configuration

```bash
cat > docker-compose.yml <<'EOF'
services:
  letta:
    image: ghcr.io/letta-ai/letta:latest
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL}
      - LETTA_DB_URL=sqlite:///data/letta.db
    volumes:
      - ./data:/data
    ports:
      - "5055:5055"
    restart: unless-stopped
EOF

# Create data directory
mkdir -p data
```

## Step 6: Start Letta

```bash
# Load environment variables
source .env

# Start Letta container
docker compose up -d

# Wait for startup
sleep 10

# Test local health check
curl http://localhost:5055/v1/health
# Should return: {"status":"ok"}
```

## Step 7: Get Tailscale Hostname

```bash
# Get your Tailscale hostname
tailscale status | grep $(hostname)

# Note the hostname, e.g., mac-mini.tailscale.net
```

## Step 8: Test Remote Access from Windows

On Windows, test connectivity:

```powershell
# Replace with your actual Tailscale hostname
curl http://<mac-mini-tailscale-name>:5055/v1/health

# Should return: {"status":"ok"}
```

## Step 9: Verify Letta API Endpoints

```bash
# Check available endpoints
curl http://localhost:5055/docs

# Test agent creation (example)
curl -X POST http://localhost:5055/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-agent",
    "system": "You are a helpful assistant."
  }'
```

## Troubleshooting

### If Docker won't start
```bash
# Check Docker status
docker info

# Restart Docker
sudo systemctl restart docker  # Linux
# Or restart Docker Desktop on Mac
```

### If Letta container fails
```bash
# Check logs
docker compose logs letta

# Restart container
docker compose restart letta

# Rebuild and start
docker compose down
docker compose up -d --build
```

### If SOPS decryption fails
```bash
# Check if age key is available
age-keygen -y

# If no key, create one
age-keygen -o ~/.config/sops/age/keys.txt

# Add the public key to .sops.yaml in the hub repo
```

### If Tailscale connection fails
```bash
# Check Tailscale status
tailscale status

# Test connectivity
ping <windows-tailscale-name>

# Restart Tailscale
sudo tailscale up
```

## Next Steps

After completing this setup:

1. **Configure MCP Tool**: Add Letta as MCP server in VS Code (see Task #7)
2. **Run Tests**: Execute Phase 1 test suite (see Task #8)
3. **Commit Changes**: Commit lablab-bean changes to git

## Success Criteria

✅ **Mac Mini Setup Complete:**
- Docker running
- Letta container accessible on port 5055
- Health check returns `{"status":"ok"}`
- Accessible from Windows via Tailscale

✅ **Ready for Phase 1 Testing:**
- Secrets decrypted and loaded
- Letta API responding
- Network connectivity confirmed

---

**Reference**: This setup is part of Phase 1 Task #6 in `PHASE1_PROGRESS.md`
