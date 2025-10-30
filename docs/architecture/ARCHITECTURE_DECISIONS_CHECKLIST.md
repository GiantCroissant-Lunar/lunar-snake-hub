---
doc_id: DOC-2025-00009
title: Architecture Decisions Checklist
doc_type: guide
status: active
canonical: true
created: 2025-10-30
tags: [architecture, decisions, checklist, planning]
summary: Checklist for making architecture decisions before starting Phase 1 implementation
related: [DOC-2025-00007, DOC-2025-00010]
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# Architecture Decisions Checklist

## Make These Choices Before Phase 1

**Status:** Decision phase
**Deadline:** Before creating central hub repo

---

## Critical Decisions (Must Decide First)

### 1. Central Hub Repository Name

**Current:** "platform-orchestrator" (you said it's misleading)

**Options:**

| Name | Pros | Cons | Score |
|------|------|------|-------|
| `lunar-hub` | ✅ Your namespace<br>✅ Clear "hub" purpose<br>✅ Short | ⚠️ Might conflict with future project | 8/10 |
| `lunar-core` | ✅ Professional<br>✅ Clear "central" meaning | ⚠️ Could mean "main project" | 7/10 |
| `dev-nexus` | ✅ Clear purpose<br>✅ Professional | ❌ Generic (not your brand) | 6/10 |
| `lunar-foundation` | ✅ Descriptive | ❌ Long | 6/10 |
| `hub` | ✅ Simple | ❌ Too generic, likely taken | 4/10 |
| `shared` | ✅ Obvious | ❌ Too generic | 3/10 |

**Recommendation:** `lunar-hub`

**Your choice:** ________________________

I think I will use "lunar-snake-hub". As Lunar Snake is not over yet. And I intend to use lunar-horse next lunar year, so on and on.

**Rationale:**

- Keep "lunar" namespace for all your projects
- "hub" clearly indicates central role
- Short and memorable
- Unlikely to conflict

---

### 2. Pilot Satellite Project

**Goal:** Pick ONE project to test Phase 1 with

**Your projects:**

```
C:\lunar-snake\personal-work\
├── infra-projects\
├── plate-projects\
└── yokan-projects\
```

**Selection criteria:**

- ✅ Small-to-medium size (not huge)
- ✅ Has NUKE build (to extract)
- ✅ Has agent rules (to centralize)
- ✅ Actively developed (so you'll test it immediately)
- ❌ Not experimental (needs stability)

**Your choice:** ________________________

**Why this one?** ________________________

Originally, I have made 3 layers, where infra layer deals the foundation, build, report. And plate layer mostly be general game dev package(unity packages primarily) and yokan layer is the actual unity project. But then I decide to generalize the dev to dotnet and specialized to unity, console app, etc. as shown in "D:\lunar-snake\personal-work\yokan-projects\lablab-bean"

---

### 3. GitHub Organization vs Personal

**Question:** Create a GitHub organization or use personal account?

| Option | Pros | Cons |
|--------|------|------|
| **Personal account** | ✅ Simple<br>✅ Zero setup<br>✅ Good for solo | ❌ Can't easily add team later<br>❌ Looks less professional |
| **Organization** (`lunar-snake`) | ✅ Professional<br>✅ Easy to add collaborators<br>✅ Better permissions | ⚠️ Need to create org first<br>⚠️ Slight overhead |

**Recommendation:** Personal account for now (migrate to org if team grows)

**Your choice:** ☐ Personal  ☐ Organization

Organization
"<https://github.com/GiantCroissant-Lunar/lablab-bean>"

---

### 4. Embeddings Provider

**Question:** What embeddings to use for Qdrant RAG?

| Provider | Model | Pros | Cons |
|----------|-------|------|------|
| **OpenAI** | `text-embedding-3-small` | ✅ Best quality<br>✅ Well-tested<br>✅ 1536 dims | ⚠️ Costs money<br>⚠️ Separate API key |
| **OpenAI** | `text-embedding-3-large` | ✅ Highest quality | ❌ Expensive<br>❌ 3072 dims (slower) |
| **GLM (Zhipu)** | GLM embeddings | ✅ Same provider as chat<br>✅ One API key | ⚠️ Possibly lower quality<br>⚠️ Less tested |
| **Sentence-Transformers** | Local model | ✅ Free<br>✅ Private | ❌ Lower quality<br>❌ Needs GPU or slow |

**Recommendation:**

- **Phase 1-2:** OpenAI `text-embedding-3-small` (proven)
- **Phase 3+:** Test GLM embeddings, switch if comparable

**Your choice:** ________________________

**Budget consideration:**

- Small: ~$0.02 per 1M tokens
- For your repos (~10 repos, 100K lines each): ~$5-10 one-time + $1-2/month for updates

I have subscribed to "<https://docs.z.ai/devpack/overview>" GLM 4.6 coding plan. So will mainly use it.

```
Current Rate Limits
API usage is limited by concurrency (i.e., the number of in-flight requests). Below are the current rate limits for each model.

Model type Model name Concurrency limit
Language Model GLM-4.6 5
Language Model GLM-4.5 10
Language Model GLM-4-Plus 20
Language Model GLM-4.5-X 1
Language Model GLM-4.5V 10
Language Model GLM-4.5-Air 5
Language Model GLM-4.5-AirX 5
Language Model GLM-4.5-Flash 2
Language Model GLM-4-32B-0414-128K 15
Image Generation Model CogView-4-250304 5
Video Generation Model ViduQ1-text 5
Video Generation Model viduq1-image 5
Video Generation Model viduq1-start-end 5
Video Generation Model vidu2-image 5
Video Generation Model vidu2-start-end 5
Video Generation Model vidu2-reference 5
Video Generation Model CogVideoX-3 1


Explanation of Rate Limits
To ensure stable access to GLM-4-Flash during the free trial, requests with context lengths over 8K will be throttled to 1% of the standard concurrency limit.
```

---

## Important Decisions (Can Decide Later)

### 5. Networking: Tailscale vs LAN

**Question:** How should Windows access Mac Mini services?

| Option | Pros | Cons |
|--------|------|------|
| **Tailscale VPN** | ✅ Secure<br>✅ Works anywhere<br>✅ Easy DNS | ⚠️ Depends on 3rd party<br>⚠️ Slight latency overhead |
| **Local network static IP** | ✅ Fastest<br>✅ No dependencies | ⚠️ Only works at home<br>⚠️ Firewall setup |

**Recommendation:** Tailscale (you already installed it)

**Your choice:** ☐ Tailscale  ☐ Static IP  ☐ Both

Both windows, mac are installed with Tailscale hours ago.

---

### 6. Self-Hosted GitHub Runner

**Question:** Run GitHub Actions on Mac Mini?

**Use case:** Push → runner pulls + reindexes immediately

| Choice | When | Why |
|--------|------|-----|
| **Yes** | Phase 3+ | ✅ Automatic sync<br>✅ Faster (local)<br>✅ No webhook delays |
| **No (use n8n only)** | Phase 1-2 | ✅ Simpler<br>✅ Less moving parts |

**Recommendation:**

- Phase 1-2: Use n8n webhooks only
- Phase 3+: Add self-hosted runner

**Your choice:** ________________________

I prefer to utilize github public free runner minute as much as possible, so I intend to make lunar-snake-hub public, but some satellite repos might be either public or private

---

### 7. Contract Tests

**Question:** Add contract tests to enforce spec compliance?

**Example:**

```csharp
// specs/auth-api/v1.2.0/contract-tests/AuthApiContractTests.cs
[Fact]
public void MustHaveHealthCheckEndpoint()
{
    var response = client.Get("/healthz");
    Assert.Equal(200, response.StatusCode);
}
```

**Decision points:**

| Choice | When | Why |
|--------|------|-----|
| **Phase 1** | Now | ✅ Enforce specs from day 1<br>⚠️ More upfront work |
| **Phase 4** | Later | ✅ Start simple<br>⚠️ Risk of drift |

**Recommendation:** Phase 2 (after hub + 1 satellite working)

**Your choice:** ________________________

I have no idea, you can decide for me.

---

### 8. Mac Mini .env Location

**Question:** Where to store secrets on Mac Mini?

| Location | Pros | Cons |
|----------|------|------|
| `~/ctx-hub/.env` | ✅ Co-located with compose | ⚠️ Must remember to exclude from git |
| `~/.config/lunar-hub/.env` | ✅ Centralized secrets | ⚠️ Compose needs `env_file` path |
| Tailscale env vars | ✅ Can inject remotely | ⚠️ Less portable |

**Recommendation:** `~/ctx-hub/.env` (simplest)

**Your choice:** ________________________

I prefer to store secret in lunar-snake-hub repo encrypted using sops and decrypted whenever necessary. You can check "C:\lunar-snake\personal-work\infra-projects\giantcroissant-lunar-ai\infra" to know how I tried before.

---

## Minor Decisions (Use Defaults)

### 9. Agent Rules Naming

**Current suggestion:** `R-{CATEGORY}-{NUMBER}-{desc}.md`

**Examples:**

- `R-CODE-010-naming.md`
- `R-DOC-030-comments.md`
- `R-NUKE-001-targets.md`

**Alternatives:**

- `{category}/{number}-{desc}.md` (folder-based)
- `{category}-{desc}.md` (no numbers)

**Your choice:** ☐ Keep suggestion  ☐ Change to: ________________

The agent rule folder "D:\lunar-snake\personal-work\yokan-projects\lablab-bean\.agent". This could be changed, does not need to follow.

---

### 10. Bootstrap Tool (Phase 2+)

**Question:** Replace bash script with a tool?

| Option | When | Why |
|--------|------|-----|
| **Bash/PowerShell** | Phase 1-3 | ✅ Simple<br>✅ No install |
| **Custom CLI** (`lunar-cli`) | Phase 4+ | ✅ Better UX<br>✅ Validation<br>⚠️ Maintenance |
| **Make/Just** | Phase 2 | ✅ Standard<br>✅ Multi-command |

**Recommendation:** Bash for Phase 1, add `Makefile` in Phase 2

**Your choice:** ________________________

I don't want to use old "make". I am using "task"
"D:\lunar-snake\personal-work\yokan-projects\lablab-bean\Taskfile.yml"

---

## Timeline & Effort Estimates

### Phase 1: Foundation (Week 1)

**Prerequisites:**

- ✅ Decide hub name
- ✅ Pick pilot satellite
- ✅ Mac Mini accessible (Tailscale)

**Tasks:** (4 hours total)

1. Create `lunar-hub` repo (30 min)
2. Extract NUKE build → hub (45 min)
3. Move agent rules → hub (30 min)
4. Write bootstrap script (45 min)
5. Set up Letta on Mac Mini (30 min)
6. Configure IDE MCP tool (30 min)
7. Test with pilot satellite (45 min)

**Deliverable:** One satellite consuming hub, agent can remember decisions

---

### Phase 2: Context Server (Week 2)

**Prerequisites:**

- ✅ Phase 1 complete
- ✅ Embeddings provider decided

**Tasks:** (6 hours total)

1. Add Qdrant to compose (15 min)
2. Build Context Gateway (3 hours)
3. Index pilot satellite (1 hour)
4. Add `/ask` MCP tool (30 min)
5. Test RAG queries (1 hour)

**Deliverable:** Agent uses `/ask` instead of loading full repo

---

### Phase 3: Orchestration (Week 3)

**Prerequisites:**

- ✅ Phase 2 complete

**Tasks:** (4 hours total)

1. Set up n8n (30 min)
2. Create webhook workflow (1 hour)
3. Create cron fallback (30 min)
4. Configure GitHub webhooks (30 min)
5. Add `/reindex` endpoint (1 hour)
6. Test end-to-end (30 min)

**Deliverable:** Push → auto-reindex within 30 seconds

---

### Phase 4: Scale (Week 4+)

**Prerequisites:**

- ✅ Phase 3 complete
- ✅ Hub tested with 1 satellite for 1 week

**Tasks:** (2 hours per satellite + 4 hours infrastructure)

1. Publish packs as releases (2 hours)
2. Create `registry/satellites.json` (30 min)
3. Write PR-opener script (1.5 hours)
4. Add reusable workflows (1 hour)
5. Migrate satellites (2 hours each)

**Deliverable:** All satellites consuming hub

---

## Commitment Checkpoint

**Before you start, commit to:**

- [ ] **Time:** I can dedicate 4 hours this week to Phase 1
- [ ] **Mac Mini:** It will stay on and accessible
- [ ] **Testing:** I'll actually use the pilot satellite (not just set up)
- [ ] **Iteration:** I'll complete Phase 1 before starting Phase 2

**If you can't commit to all four:** Wait until you can, or adjust scope.

---

## Decision Summary Template

Once decided, fill this out:

```yaml
# decisions.yml (save this)
project_name: lunar-snake

central_hub:
  name: _______________
  url: https://github.com/_______________/_______________

pilot_satellite:
  name: _______________
  path: C:\lunar-snake\personal-work\_______________\_______________
  reason: _______________

github:
  type: personal | organization
  org_name: _______________  # if organization

embeddings:
  provider: openai | glm | local
  model: _______________

networking:
  method: tailscale | static_ip
  mac_mini_ip: _______________  # Tailscale or LAN

phase_1_start_date: 2025-__-__
phase_1_target_completion: 2025-__-__

additional_notes: |
  _______________
```

---

## Red Flags to Watch For

**Stop and reconsider if:**

- ❌ You're tempted to add features before Phase 1 works
- ❌ You start gold-plating (e.g., building a web UI before CLI works)
- ❌ You skip testing the pilot satellite for a week
- ❌ You try to migrate all satellites at once
- ❌ Mac Mini becomes unreliable (then switch to cloud)

**Green flags you're on track:**

- ✅ Bootstrap script works reliably
- ✅ Agent actually uses synced rules (not re-inventing)
- ✅ Letta memory persists across sessions
- ✅ You catch yourself saying "this is cleaner"

---

## Next Action

**Right now:**

1. ☐ Read full architecture doc (`ARCHITECTURE_DISCUSSION.md`)
2. ☐ Fill out decisions above
3. ☐ Create `decisions.yml` (save for reference)
4. ☐ Decide: Start Phase 1 now, or wait?

**If starting Phase 1:**

5. ☐ Create `lunar-hub` repo (or chosen name)
6. ☐ Come back here and run: `claude code "Start Phase 1: create lunar-hub structure"`

**If waiting:**

5. ☐ Set a date to revisit: _______________
6. ☐ Move these docs to permanent location
7. ☐ Add to backlog/roadmap

---

**Status:** Decisions pending
**Owner:** lunar-snake
**Created:** 2025-10-30
**Location:** `jack-bean/docs/ARCHITECTURE_DECISIONS_CHECKLIST.md`

I would like to utilize agentic development as much as possible.
I try to adopt speck-kit, but I see some limitation for just driven by spec. I may try "<https://github.com/bmad-code-org/BMAD-METHOD>"
