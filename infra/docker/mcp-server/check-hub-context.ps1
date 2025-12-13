param(
    [string]$ConfigPath = "$env:USERPROFILE\.codeium\windsurf-next\mcp_config.json",
    [int]$SampleSeconds = 8
)

$ErrorActionPreference = "SilentlyContinue"

Write-Output "== hub-context MCP process check =="

if (Test-Path $ConfigPath) {
    $hubContextCount = (Get-Content -LiteralPath $ConfigPath | Select-String -SimpleMatch '"hub-context"' | Measure-Object).Count
    Write-Output "mcp_config.json: $ConfigPath"
    Write-Output "Occurrences of \"hub-context\": $hubContextCount"
    if ($hubContextCount -gt 1) {
        Write-Output "WARNING: Multiple \"hub-context\" entries detected. This can spawn multiple MCP server processes."
    }
    Write-Output ""
}

$procs = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like '*mcp_server.py*' -and $_.CommandLine -like '*infra\\docker\\mcp-server*' }

if (-not $procs) {
    Write-Output "No mcp_server.py processes found."
    Write-Output ""
    Write-Output "Checking for smoke_test.py processes..."
    $smoke = Get-CimInstance Win32_Process |
        Where-Object { $_.CommandLine -like '*smoke_test.py*' -and $_.CommandLine -like '*infra\\docker\\mcp-server*' }
    if ($smoke) {
        $smoke | Select-Object ProcessId, Name, CommandLine | Format-List
        Write-Output "Interpretation: smoke_test.py running likely means indexing/search is in progress."
        exit 0
    }

    Write-Output "No smoke_test.py processes found."
    Write-Output ""
    Write-Output "Checking for any python.exe with connections to OpenAI/Qdrant/Letta ports..."
    $py = Get-CimInstance Win32_Process |
        Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine }

    $rows = @()
    foreach ($proc in $py) {
        $procId = [int]$proc.ProcessId
        $conns = Get-NetTCPConnection -OwningProcess $procId |
            Where-Object { $_.State -eq 'Established' -and $_.RemotePort -in 443, 5055, 6333 }
        if (-not $conns) {
            continue
        }

        $openAiCount = ($conns | Where-Object { $_.RemotePort -eq 443 } | Measure-Object).Count
        $lettaCount = ($conns | Where-Object { $_.RemotePort -eq 5055 } | Measure-Object).Count
        $qdrantCount = ($conns | Where-Object { $_.RemotePort -eq 6333 } | Measure-Object).Count

        $cmd = $proc.CommandLine
        if ($cmd.Length -gt 120) {
            $cmd = $cmd.Substring(0, 120) + '...'
        }

        $rows += [pscustomobject]@{
            Pid = $procId
            OpenAI_443 = $openAiCount
            Letta_5055 = $lettaCount
            Qdrant_6333 = $qdrantCount
            Cmd = $cmd
        }
    }

    if ($rows) {
        $rows | Sort-Object OpenAI_443 -Descending | Format-Table -AutoSize
        Write-Output "Interpretation: if OpenAI_443 > 0 for a python.exe, some embedding work is likely happening."
    } else {
        Write-Output "No python.exe processes with connections to OpenAI/Qdrant/Letta detected."
    }

    exit 0
}

$before = @{}
foreach ($proc in $procs) {
    $procId = [int]$proc.ProcessId
    $p = Get-Process -Id $procId
    if ($p) {
        $before[$procId] = $p.CPU
    }
}

Start-Sleep -Seconds $SampleSeconds

$rows = @()
foreach ($proc in $procs) {
    $procId = [int]$proc.ProcessId
    $p = Get-Process -Id $procId
    if (-not $p) {
        continue
    }

    $cpuBefore = 0
    if ($before.ContainsKey($procId)) {
        $cpuBefore = [double]$before[$procId]
    }

    $cpuDelta = [double]$p.CPU - $cpuBefore

    $conns = Get-NetTCPConnection -OwningProcess $procId |
        Where-Object { $_.State -eq 'Established' -and $_.RemotePort -in 443, 5055, 6333 }

    $openAiCount = ($conns | Where-Object { $_.RemotePort -eq 443 } | Measure-Object).Count
    $lettaCount = ($conns | Where-Object { $_.RemotePort -eq 5055 } | Measure-Object).Count
    $qdrantCount = ($conns | Where-Object { $_.RemotePort -eq 6333 } | Measure-Object).Count

    $cmd = $proc.CommandLine
    if ($cmd.Length -gt 120) {
        $cmd = $cmd.Substring(0, 120) + '...'
    }

    $rows += [pscustomobject]@{
        Pid = $procId
        CpuDelta = [math]::Round($cpuDelta, 2)
        CpuTotal = [math]::Round([double]$p.CPU, 2)
        WS_MB = [math]::Round([double]$p.WorkingSet64 / 1MB, 1)
        OpenAI_443 = $openAiCount
        Letta_5055 = $lettaCount
        Qdrant_6333 = $qdrantCount
        Cmd = $cmd
    }
}

$rows | Sort-Object CpuDelta -Descending | Format-Table -AutoSize
Write-Output ""
Write-Output "Interpretation:"
Write-Output "- If CpuDelta is increasing and OpenAI_443 > 0, indexing/embedding is likely running."
Write-Output "- Multiple processes usually means duplicate config entries or restarts; keep only one hub-context entry."
