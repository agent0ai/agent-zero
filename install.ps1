$ErrorActionPreference = 'Stop'

# Agent Zero Install Script v1 (PowerShell)
# Windows equivalent of install.sh
# https://github.com/agent0ai/agent-zero

$script:HomeDir = [Environment]::GetFolderPath('UserProfile')
$script:SelectedTag = 'latest'

function Show-Banner {
    Write-Host @"
 █████╗   ██████╗ ███████╗███╗   ██╗████████╗   ███████╗███████╗██████╗  ██████╗ 
██╔══██╗ ██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝   ╚══███╔╝██╔════╝██╔══██╗██╔═══██╗
███████║ ██║  ███╗█████╗  ██╔██╗ ██║   ██║        ███╔╝ █████╗  ██████╔╝██║   ██║
██╔══██║ ██║   ██║██╔══╝  ██║╚██╗██║   ██║       ███╔╝  ██╔══╝  ██╔══██╗██║   ██║
██║  ██║ ╚██████╔╝███████╗██║ ╚████║   ██║      ███████╗███████╗██║  ██║╚██████╔╝
╚═╝  ╚═╝  ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝      ╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ 
"@ -ForegroundColor Blue
}

function print_ok {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function print_info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function print_warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function print_error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Wait-ForKeypress {
    Write-Host ''
    Write-Host 'Press any key to continue...' -NoNewline
    $null = [Console]::ReadKey($true)
    Write-Host ''
}

# Check whether a TCP port is in use on localhost.
# Checks Docker container port mappings and system listeners.
# Returns $true if in use, $false if free.
function Is-PortInUse {
    param([int]$Port)

    # Check Docker-published ports
    try {
        $dockerPorts = & docker ps -a --format '{{.Ports}}' 2>$null
        if ($LASTEXITCODE -eq 0 -and $dockerPorts) {
            $portsText = ($dockerPorts | Out-String)
            if ($portsText -match "(^|[\s,])0\.0\.0\.0:${Port}->" -or $portsText -match "(^|[\s,]):::${Port}->") {
                return $true
            }
        }
    }
    catch { }

    # System-level check via Test-NetConnection or .NET TcpClient
    try {
        $listener = New-Object System.Net.Sockets.TcpClient
        $listener.Connect('127.0.0.1', $Port)
        $listener.Close()
        return $true
    }
    catch {
        return $false
    }
}

# Find the first free port starting from a given base.
function Find-FreePort {
    param([int]$BasePort = 5080)

    $candidate = $BasePort
    $maxAttempts = 100
    $attempt = 0

    while ($attempt -lt $maxAttempts) {
        if (-not (Is-PortInUse -Port $candidate)) {
            return $candidate
        }
        $candidate++
        $attempt++
    }

    # If exhausted, return base port and let Docker report the conflict
    return $BasePort
}

# Escape-aware text input. Reads character by character with support for:
#   - Normal character input and Backspace for editing
#   - Escape key to abort (returns $null)
#   - Enter to submit (returns the entered text)
function Read-InputWithEscape {
    $buffer = ''

    while ($true) {
        $keyInfo = [Console]::ReadKey($true)

        # Handle Enter key
        if ($keyInfo.Key -eq 'Enter') {
            Write-Host ''
            return $buffer
        }

        # Handle Escape key
        if ($keyInfo.Key -eq 'Escape') {
            Write-Host ''
            return $null
        }

        # Handle Backspace
        if ($keyInfo.Key -eq 'Backspace') {
            if ($buffer.Length -gt 0) {
                $buffer = $buffer.Substring(0, $buffer.Length - 1)
                # Move cursor back, overwrite with space, move back again
                Write-Host "`b `b" -NoNewline
            }
            continue
        }

        # Regular printable character
        $ch = $keyInfo.KeyChar
        if ($ch -and [char]::IsControl($ch) -eq $false) {
            $buffer += $ch
            Write-Host $ch -NoNewline
        }
    }
}

# Legacy wrapper kept for compatibility - no longer used by main flow
function Read-HostWithDefault {
    param(
        [string]$Prompt,
        [string]$Default = ''
    )

    if ([string]::IsNullOrEmpty($Default)) {
        return (Read-Host $Prompt)
    }

    $value = Read-Host "$Prompt [$Default]"
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $Default
    }

    return $value
}

# Returns selected index (0-based) on Enter, or -1 on Escape/Backspace (go back).
# Throws "GO_BACK" is NOT used; callers check for -1 return value.
function select_from_menu {
    param(
        [string]$Header = '',
        [string[]]$Options
    )

    if (-not $Options -or $Options.Count -eq 0) {
        print_error "select_from_menu requires at least one menu option"
        exit 1
    }

    $selectedIndex = 0

    while ($true) {
        Clear-Host
        Show-Banner

        if (-not [string]::IsNullOrWhiteSpace($Header)) {
            Write-Host $Header
            Write-Host ''
        }

        for ($i = 0; $i -lt $Options.Count; $i++) {
            if ($i -eq $selectedIndex) {
                Write-Host "  > $($Options[$i])" -ForegroundColor Green
            }
            else {
                Write-Host "    $($Options[$i])"
            }
        }

        Write-Host ''
        Write-Host 'Use arrow keys to navigate, Enter to select, Esc to go back'

        $keyInfo = [Console]::ReadKey($true)
        switch ($keyInfo.Key) {
            'Enter' {
                return $selectedIndex
            }
            'Escape' {
                return -1
            }
            'Backspace' {
                return -1
            }
            'UpArrow' {
                $selectedIndex--
                if ($selectedIndex -lt 0) {
                    $selectedIndex = $Options.Count - 1
                }
            }
            'DownArrow' {
                $selectedIndex++
                if ($selectedIndex -ge $Options.Count) {
                    $selectedIndex = 0
                }
            }
        }
    }
}

function check_docker_daemon_running {
    & docker info *> $null
    return ($LASTEXITCODE -eq 0)
}

function start_docker_daemon {
    print_info "Starting Docker Desktop..."

    $candidatePaths = @(
        (Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe')
    )

    if (${env:ProgramFiles(x86)}) {
        $candidatePaths += (Join-Path ${env:ProgramFiles(x86)} 'Docker\Docker\Docker Desktop.exe')
    }

    foreach ($path in $candidatePaths) {
        if (Test-Path -LiteralPath $path) {
            Start-Process -FilePath $path
            return $true
        }
    }

    try {
        Start-Process 'docker-desktop:'
        return $true
    }
    catch {
        print_error "Cannot start Docker Desktop automatically."
        return $false
    }
}

function wait_for_docker_daemon {
    $maxWait = 30
    $waited = 0

    print_info "Waiting for Docker daemon to be ready..."
    while ($waited -lt $maxWait) {
        if (check_docker_daemon_running) {
            Write-Host ''
            print_ok "Docker daemon is ready"
            return $true
        }

        Start-Sleep -Seconds 1
        $waited++
        Write-Host '.' -NoNewline
    }

    Write-Host ''
    print_error "Docker daemon did not become ready within $maxWait seconds."
    return $false
}

function check_docker {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        print_ok "Docker already installed"
    }
    else {
        print_warn "Docker not found. Please install Docker Desktop from https://www.docker.com/products/docker-desktop/"
        try {
            Start-Process 'https://www.docker.com/products/docker-desktop/'
        }
        catch {
            # ignore and continue with manual instructions
        }
        print_error "Docker is required. Install Docker Desktop, start it, then re-run this script."
        exit 1
    }

    & docker compose version *> $null
    if ($LASTEXITCODE -eq 0) {
        print_ok "Docker Compose available"
    }
    else {
        print_error "Docker Compose plugin not found. Please install Docker Compose."
        exit 1
    }

    if (-not (check_docker_daemon_running)) {
        print_warn "Docker daemon is not running"
        if (start_docker_daemon) {
            if (-not (wait_for_docker_daemon)) {
                print_error "Failed to start Docker daemon. Please start Docker manually and try again."
                exit 1
            }
        }
        else {
            print_error "Please start Docker manually and try again."
            exit 1
        }
    }
    else {
        print_ok "Docker daemon is running"
    }
}

function Get-NonEmptyLines {
    param([object]$InputObject)

    if ($null -eq $InputObject) {
        return @()
    }

    $lines = @($InputObject)
    return @($lines | ForEach-Object { "$($_)".Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

function Wait-ForReady {
    param([string]$Url)

    $maxWait = 60
    $waited = 0

    Write-Host "[INFO] Launching Agent Zero..." -ForegroundColor Green -NoNewline
    while ($waited -lt $maxWait) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
                Write-Host ''
                print_ok "Agent Zero is ready at $Url"
                return $true
            }
        }
        catch { }

        Start-Sleep -Seconds 1
        $waited++
        Write-Host '.' -NoNewline
    }

    Write-Host ''
    print_warn "Agent Zero did not respond within $maxWait seconds. It may still be starting up."
    return $false
}

# Uses image name string matching instead of ancestor filter.
# The ancestor filter matches by image ID, not name, so containers created
# from a previous version of a tag become invisible after pulling a newer version.
function count_existing_agent_zero_containers {
    try {
        $rows = & docker ps -a --format '{{.Names}}|{{.Image}}' 2>$null
        if ($LASTEXITCODE -ne 0) {
            return 0
        }

        $count = 0
        foreach ($row in (Get-NonEmptyLines $rows)) {
            $parts = $row -split '\|', 2
            if ($parts.Count -ge 2) {
                $image = $parts[1]
                if ($image -match '^agent0ai/agent-zero(:|$)') {
                    $count++
                }
            }
        }
        return $count
    }
    catch {
        return 0
    }
}

function instance_name_taken {
    param([string]$NameToCheck)

    $names = & docker ps -a --format '{{.Names}}' 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    foreach ($name in (Get-NonEmptyLines $names)) {
        if ($name -eq $NameToCheck) {
            return $true
        }
    }

    return $false
}

function suggest_next_instance_name {
    param([string]$BaseName = 'agent-zero')

    $candidateName = $BaseName
    $index = 2

    while (instance_name_taken -NameToCheck $candidateName) {
        $candidateName = "$BaseName-$index"
        $index++
    }

    return $candidateName
}

function open_browser {
    param([string]$Url)

    try {
        Start-Process $Url
        print_ok "Opened browser: $Url"
    }
    catch {
        print_warn "Could not open browser automatically. Open this URL manually: $Url"
    }
}

function fetch_available_tags {
    $tagsUrl = 'https://registry.hub.docker.com/v2/repositories/agent0ai/agent-zero/tags/?page_size=20&ordering=last_updated'

    try {
        $payload = Invoke-RestMethod -Uri $tagsUrl -Method Get
    }
    catch {
        return @()
    }

    $seen = @{}
    $parsedTags = New-Object System.Collections.Generic.List[string]

    foreach ($item in @($payload.results)) {
        $name = $item.name
        if ([string]::IsNullOrWhiteSpace($name)) {
            continue
        }

        if (-not $seen.ContainsKey($name)) {
            $seen[$name] = $true
            $parsedTags.Add($name)
        }
    }

    return $parsedTags.ToArray()
}

function select_image_tag {
    $script:SelectedTag = 'latest'

    $allTags = @(fetch_available_tags)

    if ($allTags.Count -eq 0) {
        Write-Host 'Select version:'
        print_warn 'No additional tags found. Using latest.'
        print_info "Selected version: $script:SelectedTag"
        Write-Host ''
        return $true
    }

    # Build ordered tag list:
    #   1. Pinned tags (latest, testing, development) - only if they exist
    #   2. Up to 5 additional tags from newest, excluding pinned ones
    $pinnedNames = @('latest', 'testing', 'development')
    $pinnedTags = New-Object System.Collections.Generic.List[string]
    foreach ($pin in $pinnedNames) {
        if ($allTags -contains $pin) {
            $pinnedTags.Add($pin)
        }
    }

    $otherTags = New-Object System.Collections.Generic.List[string]
    foreach ($tag in $allTags) {
        if ($pinnedNames -contains $tag) {
            continue
        }
        if ($otherTags.Count -ge 5) {
            break
        }
        $otherTags.Add($tag)
    }

    # Combine pinned + other into final menu list
    $menuTags = New-Object System.Collections.Generic.List[string]
    foreach ($t in $pinnedTags) { $menuTags.Add($t) }
    foreach ($t in $otherTags) { $menuTags.Add($t) }

    if ($menuTags.Count -eq 0) {
        Write-Host 'Select version:'
        print_warn 'No tags found. Using latest.'
        print_info "Selected version: $script:SelectedTag"
        Write-Host ''
        return $true
    }

    $selectedIndex = select_from_menu -Header 'Select version:' -Options $menuTags.ToArray()

    # Handle go-back
    if ($selectedIndex -eq -1) {
        return $false
    }

    $script:SelectedTag = $menuTags[$selectedIndex]
    if ([string]::IsNullOrWhiteSpace($script:SelectedTag)) {
        $script:SelectedTag = 'latest'
    }

    print_info "Selected version: $script:SelectedTag"
    Write-Host ''
    return $true
}

function Expand-UserPath {
    param([string]$PathValue)

    if ($PathValue -eq '~') {
        return $script:HomeDir
    }

    if ($PathValue.StartsWith('~/') -or $PathValue.StartsWith('~\')) {
        return (Join-Path $script:HomeDir $PathValue.Substring(2))
    }

    return $PathValue
}

function Convert-ToComposePath {
    param([string]$PathValue)

    return $PathValue -replace '\\', '/'
}

function New-ComposeFileContent {
    param(
        [string]$Tag,
        [string]$ContainerName,
        [string]$Port,
        [string]$DataDir,
        [string]$AuthLogin,
        [string]$AuthPassword
    )

    $dataDirForCompose = Convert-ToComposePath -PathValue $DataDir
    $lines = New-Object System.Collections.Generic.List[string]

    $lines.Add('services:')
    $lines.Add('  agent-zero:')
    $lines.Add("    image: agent0ai/agent-zero:$Tag")
    $lines.Add("    container_name: $ContainerName")
    $lines.Add('    restart: unless-stopped')
    $lines.Add('    ports:')
    $lines.Add("      - `"${Port}:80`"")
    $lines.Add('    volumes:')
    $lines.Add("      - `"${dataDirForCompose}:/a0/usr`"")

    if (-not [string]::IsNullOrWhiteSpace($AuthLogin)) {
        $lines.Add('    environment:')
        $lines.Add("      - AUTH_LOGIN=$AuthLogin")
        $lines.Add("      - AUTH_PASSWORD=$AuthPassword")
    }

    return $lines.ToArray()
}

# Returns $true on success, $false if user pressed Escape to go back.
function create_instance {
    $installRoot = Join-Path $script:HomeDir '.agentzero'
    $defaultPort = Find-FreePort -BasePort 5080
    $defaultName = suggest_next_instance_name -BaseName 'agent-zero'

    # Tag selection (Escape aborts create_instance)
    if (-not (select_image_tag)) {
        return $false
    }

    # Container / instance name
    Write-Host ''
    Write-Host 'What should this instance be called?' -ForegroundColor White -NoNewline
    Write-Host ' (Esc to go back)'
    Write-Host "Leave empty to use default [$defaultName]: " -NoNewline
    $containerName = Read-InputWithEscape
    if ($null -eq $containerName) { return $false }
    if ([string]::IsNullOrWhiteSpace($containerName)) {
        $containerName = $defaultName
    }

    if (instance_name_taken -NameToCheck $containerName) {
        $suggestedName = suggest_next_instance_name -BaseName $containerName
        print_warn "Instance name '$containerName' is already taken. Using '$suggestedName'."
        $containerName = $suggestedName
    }
    print_info "Instance name: $containerName"

    $instanceDir = Join-Path $installRoot $containerName
    $defaultDataDir = Join-Path $instanceDir 'usr'

    # Data directory
    Write-Host ''
    Write-Host 'Where should Agent Zero store user data?' -ForegroundColor White -NoNewline
    Write-Host ' (Esc to go back)'
    Write-Host "Leave empty to use default [$defaultDataDir]: " -NoNewline
    $dataDir = Read-InputWithEscape
    if ($null -eq $dataDir) { return $false }
    if ([string]::IsNullOrWhiteSpace($dataDir)) {
        $dataDir = $defaultDataDir
    }
    $dataDir = Expand-UserPath -PathValue $dataDir
    New-Item -ItemType Directory -Force -Path $dataDir *> $null
    print_info "Data directory: $dataDir"

    # Port
    Write-Host ''
    Write-Host 'What port should Agent Zero Web UI run on?' -ForegroundColor White -NoNewline
    Write-Host ' (Esc to go back)'
    Write-Host "Leave empty to use default [$defaultPort]: " -NoNewline
    $port = Read-InputWithEscape
    if ($null -eq $port) { return $false }
    if ([string]::IsNullOrWhiteSpace($port)) {
        $port = "$defaultPort"
    }
    if ($port -notmatch '^[0-9]+$') {
        print_error "Invalid port. Falling back to $defaultPort."
        $port = "$defaultPort"
    }
    print_info "Web UI port: $port"

    # Authentication
    Write-Host ''
    Write-Host 'What login username should be used for the Web UI?' -ForegroundColor White -NoNewline
    Write-Host ' (Esc to go back)'
    Write-Host 'Leave empty for no authentication: ' -NoNewline
    $authLogin = Read-InputWithEscape
    if ($null -eq $authLogin) { return $false }
    $authPassword = ''
    if (-not [string]::IsNullOrWhiteSpace($authLogin)) {
        Write-Host ''
        Write-Host 'What password should be used?' -ForegroundColor White -NoNewline
        Write-Host ' (Esc to go back)'
        Write-Host 'Leave empty to use default [12345678]: ' -NoNewline
        $authPassword = Read-InputWithEscape
        if ($null -eq $authPassword) { return $false }
        if ([string]::IsNullOrWhiteSpace($authPassword)) {
            $authPassword = '12345678'
        }
        print_info "Auth configured for user: $authLogin"
    }
    else {
        print_warn 'No authentication will be configured.'
    }

    Write-Host ''
    print_info 'Configuration complete. Setting up Agent Zero...'
    Write-Host ''

    New-Item -ItemType Directory -Force -Path $instanceDir *> $null
    $composeFile = Join-Path $instanceDir 'docker-compose.yml'

    $composeLines = New-ComposeFileContent -Tag $script:SelectedTag -ContainerName $containerName -Port $port -DataDir $dataDir -AuthLogin $authLogin -AuthPassword $authPassword
    Set-Content -Path $composeFile -Value $composeLines -Encoding Ascii

    print_info "Created $composeFile"

    print_info 'Pulling Agent Zero image (this may take a moment)...'
    & docker compose -f $composeFile pull --quiet
    if ($LASTEXITCODE -ne 0) {
        throw 'Failed to pull Docker image.'
    }

    print_info 'Starting Agent Zero...'
    & docker compose -f $composeFile up -d
    if ($LASTEXITCODE -ne 0) {
        throw 'Failed to start Agent Zero.'
    }

    # Wait for the service to become ready
    Wait-ForReady -Url "http://localhost:$port"

    # Store the created container name for the caller
    $script:CreatedContainerName = $containerName

    return $true
}

# Uses image name string matching instead of ancestor filter.
function Get-AgentZeroContainerRows {
    try {
        $rows = & docker ps -a --format '{{.Names}}|{{.Image}}|{{.Status}}' 2>$null
        if ($LASTEXITCODE -ne 0) {
            return @()
        }

        $matched = New-Object System.Collections.Generic.List[string]
        foreach ($row in (Get-NonEmptyLines $rows)) {
            $parts = $row -split '\|', 3
            if ($parts.Count -ge 2) {
                $image = $parts[1]
                if ($image -match '^agent0ai/agent-zero(:|$)') {
                    $matched.Add($row)
                }
            }
        }
        return $matched.ToArray()
    }
    catch {
        return @()
    }
}

function manage_instances {
    while ($true) {
        $containerRows = @(Get-AgentZeroContainerRows)

        if ($containerRows.Count -eq 0) {
            print_warn 'No Agent Zero containers found to manage.'
            return
        }

        # Build instance selection menu
        $instanceOptions = New-Object System.Collections.Generic.List[string]
        foreach ($row in $containerRows) {
            $parts = $row -split '\|', 3
            $name = if ($parts.Count -ge 1) { $parts[0] } else { '' }
            $image = if ($parts.Count -ge 2) { $parts[1] } else { '' }
            $status = if ($parts.Count -ge 3) { $parts[2] } else { '' }

            $tag = 'latest'
            if ($image -match ':(?<tag>[^:]+)$') {
                $tag = $Matches['tag']
            }

            $instanceOptions.Add("$name [tag: $tag] [status: $status]")
        }

        $selectedIndex = select_from_menu -Header 'Select existing instance:' -Options $instanceOptions.ToArray()

        # Handle go-back (Escape/Backspace)
        if ($selectedIndex -eq -1) {
            return
        }

        $selectedRow = $containerRows[$selectedIndex]
        $selectedParts = $selectedRow -split '\|', 3
        $selectedName = if ($selectedParts.Count -ge 1) { $selectedParts[0] } else { '' }

        manage_single_instance -ContainerName $selectedName
    }
}

# Show the action menu for a single container (open, start, stop, restart, delete).
# Can be called from manage_instances or directly after create_instance.
function manage_single_instance {
    param([string]$ContainerName)

    # Look up the image for display
    $selectedImage = ((Get-NonEmptyLines (& docker ps -a --filter "name=^/$ContainerName$" --format '{{.Image}}' 2>$null)) | Select-Object -First 1)

    while ($true) {
        $statusOutput = & docker ps -a --filter "name=^/$ContainerName$" --format '{{.Status}}' 2>$null
        $selectedStatus = ((Get-NonEmptyLines $statusOutput) | Select-Object -First 1)

        # If container no longer exists (e.g. after delete), return
        if ([string]::IsNullOrWhiteSpace($selectedStatus)) {
            break
        }

        $isRunning = $selectedStatus -like 'Up*'
        $instanceHeader = "Selected: $ContainerName ($selectedImage, $selectedStatus)"

        if ($isRunning) {
            $actionOptions = @('Open in browser', 'Restart', 'Stop', 'Delete', 'Back')
            $actionIndex = select_from_menu -Header $instanceHeader -Options $actionOptions
            switch ($actionIndex) {
                -1 { $actionKey = 'back' }   # Escape/Backspace
                0  { $actionKey = 'open' }
                1  { $actionKey = 'restart' }
                2  { $actionKey = 'stop' }
                3  { $actionKey = 'delete' }
                4  { $actionKey = 'back' }
                default { $actionKey = 'invalid' }
            }
        }
        else {
            $actionOptions = @('Start', 'Delete', 'Back')
            $actionIndex = select_from_menu -Header $instanceHeader -Options $actionOptions
            switch ($actionIndex) {
                -1 { $actionKey = 'back' }   # Escape/Backspace
                0  { $actionKey = 'start' }
                1  { $actionKey = 'delete' }
                2  { $actionKey = 'back' }
                default { $actionKey = 'invalid' }
            }
        }

        switch ($actionKey) {
            'open' {
                $portOutput = & docker port $ContainerName '80/tcp' 2>$null
                $hostPort = ''

                foreach ($line in (Get-NonEmptyLines $portOutput)) {
                    if ($line -match ':(\d+)\s*$') {
                        $hostPort = $Matches[1]
                        break
                    }
                }

                if ([string]::IsNullOrWhiteSpace($hostPort)) {
                    print_warn "Could not resolve a host port for '$ContainerName' on 80/tcp. Ensure it is running with a published port."
                }
                else {
                    $targetUrl = "http://localhost:$hostPort"
                    print_info "Opening $targetUrl"
                    open_browser -Url $targetUrl
                }
                Wait-ForKeypress
            }
            'start' {
                print_info "Starting '$ContainerName'..."
                $startOutput = & docker start $ContainerName 2>&1
                # Verify actual container state
                $runCheck = & docker ps --filter "name=^/$ContainerName$" --filter 'status=running' --format '{{.Names}}' 2>$null
                if ((Get-NonEmptyLines $runCheck) -contains $ContainerName) {
                    print_ok "Started '$ContainerName'."
                }
                else {
                    print_error "Failed to start '$ContainerName'."
                    if ($startOutput) {
                        Write-Host "  $startOutput"
                    }
                }
                Wait-ForKeypress
            }
            'stop' {
                print_info "Stopping '$ContainerName'..."
                & docker stop $ContainerName *> $null
                if ($LASTEXITCODE -eq 0) {
                    print_ok "Stopped '$ContainerName'."
                }
                else {
                    print_error "Failed to stop '$ContainerName'."
                }
                Wait-ForKeypress
            }
            'restart' {
                print_info "Restarting '$ContainerName'..."
                $restartOutput = & docker restart $ContainerName 2>&1
                # Verify actual container state
                $runCheck = & docker ps --filter "name=^/$ContainerName$" --filter 'status=running' --format '{{.Names}}' 2>$null
                if ((Get-NonEmptyLines $runCheck) -contains $ContainerName) {
                    print_ok "Restarted '$ContainerName'."
                }
                else {
                    print_error "Failed to restart '$ContainerName'."
                    if ($restartOutput) {
                        Write-Host "  $restartOutput"
                    }
                }
                Wait-ForKeypress
            }
            'delete' {
                Write-Host "Are you sure you want to delete '$ContainerName'? [y/N]: " -NoNewline
                $confirmKey = [Console]::ReadKey($true)
                Write-Host ''
                if ($confirmKey.KeyChar -eq 'y' -or $confirmKey.KeyChar -eq 'Y') {
                    # Stop first if running
                    & docker stop $ContainerName *> $null
                    & docker rm $ContainerName *> $null
                    if ($LASTEXITCODE -eq 0) {
                        print_ok "Deleted '$ContainerName'."
                    }
                    else {
                        print_error "Failed to delete '$ContainerName'."
                    }
                    Wait-ForKeypress
                    break  # Container no longer exists
                }
                else {
                    print_info 'Delete cancelled.'
                    Wait-ForKeypress
                }
            }
            'back' {
                break
            }
            default {
                print_warn 'Invalid action. Please try again.'
                Wait-ForKeypress
            }
        }
    }
}

function main_menu_for_existing {
    while ($true) {
        # Re-count containers each iteration (may change after delete/create)
        $menuCount = count_existing_agent_zero_containers
        if ($menuCount -lt 0) { $menuCount = 0 }

        if ($menuCount -gt 0) {
            $header = "Detected $menuCount Agent Zero container(s). What would you like to do?"
            $selectedIndex = select_from_menu -Header $header -Options @('Install new instance', 'Manage existing instances', 'Exit')

            switch ($selectedIndex) {
                -1 { exit 0 }    # Escape/Backspace - exit
                0 {
                    $script:CreatedContainerName = ''
                    $result = create_instance
                    if ($result) {
                        manage_single_instance -ContainerName $script:CreatedContainerName
                    }
                    # Escape pressed during create or back from detail - loop back to menu
                }
                1 { manage_instances }  # loops back to this menu after returning
                2 { exit 0 }     # Exit option
                default { exit 0 }
            }
        }
        else {
            # All containers were deleted - go straight to install
            $script:CreatedContainerName = ''
            $result = create_instance
            if (-not $result) {
                exit 0
            }
            manage_single_instance -ContainerName $script:CreatedContainerName
        }
    }
}

function main {
    check_docker
    Write-Host ''

    $existingCount = count_existing_agent_zero_containers
    if ($existingCount -lt 0) {
        $existingCount = 0
    }

    if ($existingCount -gt 0) {
        main_menu_for_existing
    }
    else {
        # No existing containers - go straight to install.
        # If Escape pressed during create, exit gracefully.
        $script:CreatedContainerName = ''
        $result = create_instance
        if (-not $result) {
            exit 0
        }
        manage_single_instance -ContainerName $script:CreatedContainerName
    }
}

Show-Banner
main
