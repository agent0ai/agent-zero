# PowerShell script to schedule Foam integration tasks on Windows
# This creates Windows Task Scheduler jobs that act like cron jobs

param(
    [Parameter(Mandatory=$false)]
    [string]$Action = "install",

    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "D:\GithubRepos\agent-zero"
)

$TaskBaseName = "AgentZero_Foam"
$PythonPath = "python"  # Adjust if using specific Python path

function Write-ColorOutput($ForegroundColor, $Text) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Text
    $host.UI.RawUI.ForegroundColor = $fc
}

function Install-FoamTasks {
    Write-ColorOutput Green "`n====================================="
    Write-ColorOutput Green "Installing Foam Integration Tasks"
    Write-ColorOutput Green "====================================="

    # Task 1: Symbol Tagging (Every hour)
    $taskName1 = "${TaskBaseName}_SymbolTagging"
    $trigger1 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([System.TimeSpan]::MaxValue)
    $action1 = New-ScheduledTaskAction -Execute $PythonPath -Argument "$ProjectPath\foam_integration.py --task symbol_tagging" -WorkingDirectory $ProjectPath
    $settings1 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

    try {
        $existingTask = Get-ScheduledTask -TaskName $taskName1 -ErrorAction SilentlyContinue
        if ($existingTask) {
            Unregister-ScheduledTask -TaskName $taskName1 -Confirm:$false
            Write-Output "  Removed existing task: $taskName1"
        }

        Register-ScheduledTask -TaskName $taskName1 -Trigger $trigger1 -Action $action1 -Settings $settings1 -Description "Scan and tag important symbols in Agent Zero codebase" | Out-Null
        Write-ColorOutput Green "  ✓ Created task: $taskName1 (runs hourly)"
    }
    catch {
        Write-ColorOutput Red "  ✗ Failed to create task: $taskName1"
        Write-Output "    Error: $_"
    }

    # Task 2: Relationship Mapping (Every 30 minutes)
    $taskName2 = "${TaskBaseName}_RelationMapping"
    $trigger2 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration ([System.TimeSpan]::MaxValue)
    $action2 = New-ScheduledTaskAction -Execute $PythonPath -Argument "$ProjectPath\foam_integration.py --task relation_mapping" -WorkingDirectory $ProjectPath
    $settings2 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

    try {
        $existingTask = Get-ScheduledTask -TaskName $taskName2 -ErrorAction SilentlyContinue
        if ($existingTask) {
            Unregister-ScheduledTask -TaskName $taskName2 -Confirm:$false
            Write-Output "  Removed existing task: $taskName2"
        }

        Register-ScheduledTask -TaskName $taskName2 -Trigger $trigger2 -Action $action2 -Settings $settings2 -Description "Map relationships between files for Foam graph" | Out-Null
        Write-ColorOutput Green "  ✓ Created task: $taskName2 (runs every 30 minutes)"
    }
    catch {
        Write-ColorOutput Red "  ✗ Failed to create task: $taskName2"
        Write-Output "    Error: $_"
    }

    # Task 3: Memory Update (Every 4 hours)
    $taskName3 = "${TaskBaseName}_MemoryUpdate"
    $trigger3 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 4) -RepetitionDuration ([System.TimeSpan]::MaxValue)
    $action3 = New-ScheduledTaskAction -Execute $PythonPath -Argument "$ProjectPath\foam_integration.py --task memory_update" -WorkingDirectory $ProjectPath
    $settings3 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

    try {
        $existingTask = Get-ScheduledTask -TaskName $taskName3 -ErrorAction SilentlyContinue
        if ($existingTask) {
            Unregister-ScheduledTask -TaskName $taskName3 -Confirm:$false
            Write-Output "  Removed existing task: $taskName3"
        }

        Register-ScheduledTask -TaskName $taskName3 -Trigger $trigger3 -Action $action3 -Settings $settings3 -Description "Update Agent Zero memory with symbol discoveries" | Out-Null
        Write-ColorOutput Green "  ✓ Created task: $taskName3 (runs every 4 hours)"
    }
    catch {
        Write-ColorOutput Red "  ✗ Failed to create task: $taskName3"
        Write-Output "    Error: $_"
    }

    # Task 4: Graph Refresh (Every 2 hours)
    $taskName4 = "${TaskBaseName}_GraphRefresh"
    $trigger4 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 2) -RepetitionDuration ([System.TimeSpan]::MaxValue)
    $action4 = New-ScheduledTaskAction -Execute $PythonPath -Argument "$ProjectPath\foam_integration.py --task graph_refresh" -WorkingDirectory $ProjectPath
    $settings4 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

    try {
        $existingTask = Get-ScheduledTask -TaskName $taskName4 -ErrorAction SilentlyContinue
        if ($existingTask) {
            Unregister-ScheduledTask -TaskName $taskName4 -Confirm:$false
            Write-Output "  Removed existing task: $taskName4"
        }

        Register-ScheduledTask -TaskName $taskName4 -Trigger $trigger4 -Action $action4 -Settings $settings4 -Description "Refresh Foam graph visualization data" | Out-Null
        Write-ColorOutput Green "  ✓ Created task: $taskName4 (runs every 2 hours)"
    }
    catch {
        Write-ColorOutput Red "  ✗ Failed to create task: $taskName4"
        Write-Output "    Error: $_"
    }

    Write-ColorOutput Green "`n====================================="
    Write-ColorOutput Green "Task Installation Complete!"
    Write-ColorOutput Green "====================================="
    Write-Output ""
    Write-Output "Scheduled Tasks Created:"
    Write-Output "  1. Symbol Tagging    - Every 1 hour"
    Write-Output "  2. Relation Mapping  - Every 30 minutes"
    Write-Output "  3. Memory Update     - Every 4 hours"
    Write-Output "  4. Graph Refresh     - Every 2 hours"
    Write-Output ""
    Write-Output "To view tasks: taskschd.msc"
    Write-Output "To test a task: schtasks /run /tn `"TaskName`""
}

function Uninstall-FoamTasks {
    Write-ColorOutput Yellow "`nUninstalling Foam Integration Tasks..."

    $taskNames = @(
        "${TaskBaseName}_SymbolTagging",
        "${TaskBaseName}_RelationMapping",
        "${TaskBaseName}_MemoryUpdate",
        "${TaskBaseName}_GraphRefresh"
    )

    foreach ($taskName in $taskNames) {
        try {
            $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($task) {
                Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
                Write-ColorOutput Green "  ✓ Removed: $taskName"
            }
            else {
                Write-Output "  - Task not found: $taskName"
            }
        }
        catch {
            Write-ColorOutput Red "  ✗ Error removing: $taskName"
        }
    }

    Write-ColorOutput Yellow "Uninstall complete."
}

function Show-TaskStatus {
    Write-ColorOutput Cyan "`n====================================="
    Write-ColorOutput Cyan "Foam Integration Task Status"
    Write-ColorOutput Cyan "====================================="

    $taskNames = @(
        "${TaskBaseName}_SymbolTagging",
        "${TaskBaseName}_RelationMapping",
        "${TaskBaseName}_MemoryUpdate",
        "${TaskBaseName}_GraphRefresh"
    )

    foreach ($taskName in $taskNames) {
        try {
            $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($task) {
                $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName
                Write-Output ""
                Write-Output "Task: $taskName"
                Write-Output "  State: $($task.State)"
                Write-Output "  Last Run: $($taskInfo.LastRunTime)"
                Write-Output "  Last Result: $($taskInfo.LastTaskResult)"
                Write-Output "  Next Run: $($taskInfo.NextRunTime)"
            }
            else {
                Write-Output ""
                Write-ColorOutput Yellow "Task not found: $taskName"
            }
        }
        catch {
            Write-ColorOutput Red "Error getting info for: $taskName"
        }
    }
}

function Test-FoamIntegration {
    Write-ColorOutput Cyan "`nTesting Foam Integration..."

    # Check if Python script exists
    $scriptPath = Join-Path $ProjectPath "foam_integration.py"
    if (-not (Test-Path $scriptPath)) {
        Write-ColorOutput Red "  ✗ foam_integration.py not found at $scriptPath"
        return
    }
    Write-ColorOutput Green "  ✓ foam_integration.py found"

    # Check Python
    try {
        $pythonVersion = & $PythonPath --version 2>&1
        Write-ColorOutput Green "  ✓ Python found: $pythonVersion"
    }
    catch {
        Write-ColorOutput Red "  ✗ Python not found or not accessible"
        return
    }

    # Try to run the integration script
    Write-Output "`nRunning integration test..."
    try {
        Set-Location $ProjectPath
        & $PythonPath foam_integration.py --test 2>&1 | Out-String
        Write-ColorOutput Green "  ✓ Integration script executed successfully"
    }
    catch {
        Write-ColorOutput Red "  ✗ Integration script failed: $_"
    }
}

# Main execution
switch ($Action.ToLower()) {
    "install" {
        Install-FoamTasks
    }
    "uninstall" {
        Uninstall-FoamTasks
    }
    "status" {
        Show-TaskStatus
    }
    "test" {
        Test-FoamIntegration
    }
    "run" {
        Write-Output "Running Foam integration manually..."
        Set-Location $ProjectPath
        & $PythonPath foam_integration.py
    }
    default {
        Write-Output "Usage: .\schedule_foam_tasks.ps1 -Action [install|uninstall|status|test|run]"
        Write-Output ""
        Write-Output "Actions:"
        Write-Output "  install   - Create scheduled tasks"
        Write-Output "  uninstall - Remove scheduled tasks"
        Write-Output "  status    - Show task status"
        Write-Output "  test      - Test integration"
        Write-Output "  run       - Run integration manually"
    }
}