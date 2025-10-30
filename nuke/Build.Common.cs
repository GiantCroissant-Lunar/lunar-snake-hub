using System;
using System.Linq;
using Nuke.Common;
using Nuke.Common.IO;
using Nuke.Common.ProjectModel;
using Nuke.Common.Tools.DotNet;
using Nuke.Common.Utilities.Collections;
using Serilog;
using static Nuke.Common.IO.FileSystemTasks;
using static Nuke.Common.Tools.DotNet.DotNetTasks;

/// <summary>
/// Common NUKE build targets for .NET projects.
/// Import this into your satellite project's Build.cs with: #load ".hub-cache/nuke/Build.Common.cs"
/// </summary>
public abstract class CommonBuildTargets : NukeBuild
{
    /// <summary>
    /// Configuration to build - Debug for local, Release for server
    /// </summary>
    [Parameter("Configuration to build - Default is 'Debug' (local) or 'Release' (server)")]
    public string Configuration { get; set; } = IsLocalBuild ? "Debug" : "Release";

    /// <summary>
    /// Solution file to build
    /// </summary>
    [Solution]
    public Solution Solution { get; set; }

    /// <summary>
    /// Source directory containing projects
    /// </summary>
    public virtual AbsolutePath SourceDirectory => RootDirectory / "src";

    /// <summary>
    /// Build artifacts output directory
    /// </summary>
    public virtual AbsolutePath ArtifactsDirectory => RootDirectory / "artifacts";

    /// <summary>
    /// Clean build outputs (bin, obj, artifacts)
    /// </summary>
    public virtual Target Clean => _ => _
        .Executes(() =>
        {
            Serilog.Log.Information("Cleaning build outputs...");

            SourceDirectory.GlobDirectories("**/bin", "**/obj").ForEach(d =>
            {
                if (System.IO.Directory.Exists(d))
                {
                    Serilog.Log.Debug("Deleting {Directory}", d);
                    DeleteDirectory(d);
                }
            });

            if (System.IO.Directory.Exists(ArtifactsDirectory))
            {
                Serilog.Log.Debug("Cleaning artifacts at {Directory}", ArtifactsDirectory);
                ArtifactsDirectory.CreateOrCleanDirectory();
            }

            Serilog.Log.Information("✅ Clean complete");
        });

    /// <summary>
    /// Restore NuGet packages
    /// </summary>
    public virtual Target Restore => _ => _
        .Executes(() =>
        {
            Serilog.Log.Information("Restoring NuGet packages...");

            DotNetRestore(s => s
                .SetProjectFile(Solution));

            Serilog.Log.Information("✅ Restore complete");
        });

    /// <summary>
    /// Compile the solution
    /// </summary>
    public virtual Target Compile => _ => _
        .DependsOn(Restore)
        .Executes(() =>
        {
            Serilog.Log.Information("Compiling solution...");

            DotNetBuild(s => s
                .SetProjectFile(Solution)
                .SetConfiguration(Configuration)
                .EnableNoRestore());

            Serilog.Log.Information("✅ Compile complete");
        });

    /// <summary>
    /// Run unit tests
    /// </summary>
    public virtual Target Test => _ => _
        .DependsOn(Compile)
        .Executes(() =>
        {
            Serilog.Log.Information("Running tests...");

            DotNetTest(s => s
                .SetProjectFile(Solution)
                .SetConfiguration(Configuration)
                .EnableNoBuild()
                .EnableNoRestore());

            Serilog.Log.Information("✅ Tests complete");
        });

    /// <summary>
    /// Format code using dotnet-format
    /// </summary>
    public virtual Target Format => _ => _
        .DependsOn(Restore)
        .Executes(() =>
        {
            Serilog.Log.Information("Formatting code...");

            DotNet($"format \"{Solution}\" --verbosity minimal", workingDirectory: RootDirectory);

            Serilog.Log.Information("✅ Format complete");
        });

    /// <summary>
    /// Verify code formatting (CI-friendly)
    /// </summary>
    public virtual Target FormatCheck => _ => _
        .DependsOn(Restore)
        .Executes(() =>
        {
            Serilog.Log.Information("Verifying code formatting...");

            DotNet($"format \"{Solution}\" --verify-no-changes --verbosity minimal", workingDirectory: RootDirectory);

            Serilog.Log.Information("✅ Format check complete");
        });

    /// <summary>
    /// Create NuGet packages
    /// </summary>
    public virtual Target Pack => _ => _
        .DependsOn(Compile)
        .Executes(() =>
        {
            Serilog.Log.Information("Creating NuGet packages...");

            var nugetDirectory = ArtifactsDirectory / "nuget";
            nugetDirectory.CreateOrCleanDirectory();

            DotNetPack(s => s
                .SetProject(Solution)
                .SetConfiguration(Configuration)
                .EnableNoRestore()
                .EnableNoBuild()
                .SetOutputDirectory(nugetDirectory));

            Serilog.Log.Information("✅ Pack complete. Packages at: {Directory}", nugetDirectory);
        });

    /// <summary>
    /// Publish application
    /// </summary>
    public virtual Target Publish => _ => _
        .DependsOn(Test)
        .Executes(() =>
        {
            Serilog.Log.Information("Publishing application...");

            var publishDirectory = ArtifactsDirectory / "publish";
            publishDirectory.CreateOrCleanDirectory();

            // This is a base implementation - override in your project's Build.cs
            // to specify which projects to publish and how

            Serilog.Log.Information("⚠️  Override Publish target in your Build.cs to specify projects");
            Serilog.Log.Information("✅ Publish target complete");
        });
}
