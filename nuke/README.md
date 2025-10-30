# NUKE Build Components

Reusable NUKE build targets for .NET projects.

## Components

- `Build.Common.cs` - Common targets (Restore, Clean, Compile, Test, Pack)
- `Build.DotNet.cs` - .NET-specific targets
- `Build.Unity.cs` - Unity-specific targets
- `Build.Docker.cs` - Docker containerization

## Usage in Satellites

**Option A: Direct import (once published as NuGet)**

```csharp
// In your satellite's build project
<PackageReference Include="LunarSnake.Nuke.Common" Version="0.1.0" />
```

**Option B: File sync (Phase 1)**

```bash
# Satellite's Taskfile.yml
task hub:sync  # Copies to .hub-cache/nuke/

# Import in Build.cs
#load ".hub-cache/nuke/Build.Common.cs"
```

## Next Steps (Phase 1)

Extract common NUKE targets from `lablab-bean/.nuke/`:

1. Identify shared build logic
2. Create `Build.Common.cs` with:
   - Restore
   - Clean
   - Compile
   - Test
   - Pack
3. Test import from lablab-bean

See: `docs/guides/PHASE1_CHECKLIST.md` (Task #3)
