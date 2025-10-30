---
doc_id: DOC-2025-00017
title: Specifications & RFCs Directory
doc_type: reference
status: active
canonical: true
created: 2025-10-30
tags: [specs, rfcs, api, contracts, directory, reference]
summary: Directory reference for domain specifications, API contracts, and architecture decision records
source:
  author: agent
  agent: claude
  model: sonnet-4.5
---

# Specifications & RFCs

Domain specifications, API contracts, and architecture decision records.

## Structure

```
specs/
└── {domain}/           # e.g., auth-api, inventory-system
    └── v{version}/     # e.g., v1.0, v1.1
        ├── rfc.md      # Request for Comments (what & why)
        ├── adr.md      # Architecture Decision Record
        ├── schema/     # OpenAPI, JSON Schema, Protobuf
        │   └── openapi.yaml
        └── contract-tests/  # Optional: enforcement tests
            └── dotnet/
```

## Versioning

- **Semantic versioning:** `v{major}.{minor}`
- **Breaking changes:** Bump major version
- **Backward-compatible additions:** Bump minor version

## Satellite Consumption

**`.hub-manifest.toml`:**
```toml
[specs]
auth-api = "1.2.0"          # Pins to specific version
inventory-system = "0.7.1"
```

**Sync:**
```bash
task hub:sync  # Fetches only pinned specs to .hub-cache/specs/
```

## Contract Tests (Phase 2)

Contract tests enforce that implementations comply with specs:
```csharp
// specs/auth-api/v1.2/contract-tests/dotnet/AuthApiContractTests.cs
[Fact]
public void MustHaveHealthCheckEndpoint()
{
    var response = client.Get("/healthz");
    Assert.Equal(200, response.StatusCode);
}
```

## Next Steps

- Phase 1: Create folder structure ✅
- Phase 2: Add first spec (from lablab-bean if applicable)
- Phase 2: Add contract tests

See: `docs/architecture/YOUR_DECISIONS_SUMMARY.md`
