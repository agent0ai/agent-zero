$ErrorActionPreference = 'Stop'

# Agent Zero Install Script v1 (PowerShell)
# Windows equivalent of install.sh
# https://github.com/agent0ai/agent-zero

$script:HomeDir = [Environment]::GetFolderPath('UserProfile')
$script:SelectedTag = 'latest'

function Show-Banner {
    Write-Host @"
                   0000000000000000
              0000000000000000000000000
           000000000000000  00000000000000
         0000000000000000    0000000000000000
        000000000000000        000000000000000
       000000000000000          000000000000000
      00000000000000              00000000000000
     00000000000000       00       00000000000000
     0000000000000      000000      0000000000000
     00000000000       00000000       00000000000
     0000000000       0000000000       0000000000
     000000000      00000000000000      000000000
      000000       000          000       0000000
       0000       000            000       00000
        00      0000              0000      00
         000000000000000000000000000000000000
           00000000000000000000000000000000
              00000000000000000000000000
                  000000000000000000
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
        Write-Host "Use ↑/↓ arrows to navigate, Enter to select"

        $keyInfo = [Console]::ReadKey($true)
        switch ($keyInfo.Key) {
            'Enter' {
                return $selectedIndex
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

function count_existing_agent_zero_containers {
    $rows = & docker ps -a --filter 'ancestor=agent0ai/agent-zero' --format '{{.Names}}' 2>$null
    if ($LASTEXITCODE -ne 0) {
        return 0
    }

    return (Get-NonEmptyLines $rows).Count
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
    $tagsUrl = 'https://registry.hub.docker.com/v2/repositories/agent0ai/agent-zero/tags/?page_size=5&ordering=last_updated'

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

    $availableTags = @(fetch_available_tags)
    $availableTags = @($availableTags | Where-Object { $_.ToLowerInvariant() -ne 'latest' })

    if ($availableTags.Count -eq 0) {
        Write-Host 'Select image tag:'
        print_warn 'No additional tags found. Using latest.'
        print_info "Image tag: $script:SelectedTag"
        Write-Host ''
        return
    }

    $options = @('latest') + $availableTags
    $selectedIndex = select_from_menu -Header 'Select image tag:' -Options $options
    $script:SelectedTag = $options[$selectedIndex]

    print_info "Image tag: $script:SelectedTag"
    Write-Host ''
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

function create_instance {
    $installRoot = Join-Path $script:HomeDir '.agentzero'
    $defaultPort = '5080'
    $defaultName = suggest_next_instance_name -BaseName 'agent-zero'

    select_image_tag
    Write-Host ''

    Write-Host 'Container name:'
    $containerName = Read-HostWithDefault -Prompt 'Name' -Default $defaultName

    if (instance_name_taken -NameToCheck $containerName) {
        $suggestedName = suggest_next_instance_name -BaseName $containerName
        print_warn "Instance name '$containerName' is already taken. Using '$suggestedName'."
        $containerName = $suggestedName
    }
    print_info "Instance name: $containerName"

    $instanceDir = Join-Path $installRoot $containerName
    $defaultDataDir = Join-Path $instanceDir 'usr'

    Write-Host 'Data directory:'
    $dataDir = Read-HostWithDefault -Prompt 'Where to store Agent Zero user data?' -Default $defaultDataDir
    $dataDir = Expand-UserPath -PathValue $dataDir
    New-Item -ItemType Directory -Force -Path $dataDir *> $null
    print_info "Data directory: $dataDir"

    Write-Host 'Web UI port:'
    $port = Read-HostWithDefault -Prompt 'Web UI port?' -Default $defaultPort
    if ($port -notmatch '^[0-9]+$') {
        print_error "Invalid port. Falling back to $defaultPort."
        $port = $defaultPort
    }
    print_info "Web UI port: $port"

    Write-Host 'Authentication:'
    $authLogin = Read-Host 'Web UI login username (leave empty for no auth)'
    $authPassword = ''
    if (-not [string]::IsNullOrWhiteSpace($authLogin)) {
        $authPassword = Read-HostWithDefault -Prompt 'Web UI password' -Default '12345678'
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
    & docker compose -f $composeFile pull
    if ($LASTEXITCODE -ne 0) {
        throw 'Failed to pull Docker image.'
    }

    print_info 'Starting Agent Zero...'
    & docker compose -f $composeFile up -d
    if ($LASTEXITCODE -ne 0) {
        throw 'Failed to start Agent Zero.'
    }

    Write-Host ''
    Write-Host '=========================================='
    Write-Host '  Installation Complete!' -ForegroundColor Green
    Write-Host '=========================================='
    Write-Host ''
    Write-Host "  Image tag      : $script:SelectedTag"
    Write-Host "  Instance name  : $containerName"
    Write-Host "  Compose file   : $composeFile"
    Write-Host "  Data directory : $dataDir"
    Write-Host "  Web UI         : http://localhost:$port"
    if (-not [string]::IsNullOrWhiteSpace($authLogin)) {
        Write-Host '  Authentication : enabled'
        Write-Host "  Login          : $authLogin"
        Write-Host "  Password       : $authPassword"
    }
    else {
        Write-Host '  Authentication : none'
    }
    Write-Host ''
    Write-Host '  Useful commands:'
    Write-Host "    docker compose -f `"$composeFile`" logs -f   # View logs"
    Write-Host "    docker compose -f `"$composeFile`" down      # Stop"
    Write-Host "    docker compose -f `"$composeFile`" up -d     # Start"
    Write-Host "    docker compose -f `"$composeFile`" pull      # Update image"
    Write-Host ''
    print_info 'Happy automating with Agent Zero!'
}

function Get-AgentZeroContainerRows {
    $rows = & docker ps -a --filter 'ancestor=agent0ai/agent-zero' --format '{{.Names}}|{{.Image}}|{{.Status}}' 2>$null
    if ($LASTEXITCODE -ne 0) {
        return @()
    }

    return (Get-NonEmptyLines $rows)
}

function manage_instances {
    while ($true) {
        $containerRows = @(Get-AgentZeroContainerRows)

        if ($containerRows.Count -eq 0) {
            print_warn 'No Agent Zero containers found to manage.'
            return
        }

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

        $selectedRow = $containerRows[$selectedIndex]
        $selectedParts = $selectedRow -split '\|', 3
        $selectedName = if ($selectedParts.Count -ge 1) { $selectedParts[0] } else { '' }
        $selectedImage = if ($selectedParts.Count -ge 2) { $selectedParts[1] } else { '' }

        while ($true) {
            $statusOutput = & docker ps -a --filter "name=^/$selectedName$" --format '{{.Status}}' 2>$null
            $selectedStatus = ((Get-NonEmptyLines $statusOutput) | Select-Object -First 1)
            if ([string]::IsNullOrWhiteSpace($selectedStatus)) {
                $selectedStatus = 'Unknown'
            }

            $isRunning = $selectedStatus -like 'Up*'
            $instanceHeader = "Selected: $selectedName ($selectedImage, $selectedStatus)"

            if ($isRunning) {
                $actionOptions = @('Open in browser', 'Stop', 'Back/Exit manage menu')
                $actionIndex = select_from_menu -Header $instanceHeader -Options $actionOptions
                switch ($actionIndex) {
                    0 { $actionKey = 'open' }
                    1 { $actionKey = 'stop' }
                    default { $actionKey = 'back' }
                }
            }
            else {
                $actionOptions = @('Start', 'Back/Exit manage menu')
                $actionIndex = select_from_menu -Header $instanceHeader -Options $actionOptions
                switch ($actionIndex) {
                    0 { $actionKey = 'start' }
                    default { $actionKey = 'back' }
                }
            }

            switch ($actionKey) {
                'open' {
                    $portOutput = & docker port $selectedName '80/tcp' 2>$null
                    $hostPort = ''

                    foreach ($line in (Get-NonEmptyLines $portOutput)) {
                        if ($line -match ':(\d+)\s*$') {
                            $hostPort = $Matches[1]
                            break
                        }
                    }

                    if ([string]::IsNullOrWhiteSpace($hostPort)) {
                        print_warn "Could not resolve a host port for '$selectedName' on 80/tcp. Ensure it is running with a published port."
                    }
                    else {
                        $targetUrl = "http://localhost:$hostPort"
                        print_info "Opening $targetUrl"
                        open_browser -Url $targetUrl
                    }
                    Write-Host ''
                }
                'start' {
                    print_info "Starting '$selectedName'..."
                    & docker start $selectedName *> $null
                    if ($LASTEXITCODE -eq 0) {
                        print_ok "Started '$selectedName'."
                    }
                    else {
                        print_error "Failed to start '$selectedName'."
                    }
                    Write-Host ''
                }
                'stop' {
                    print_info "Stopping '$selectedName'..."
                    & docker stop $selectedName *> $null
                    if ($LASTEXITCODE -eq 0) {
                        print_ok "Stopped '$selectedName'."
                    }
                    else {
                        print_error "Failed to stop '$selectedName'."
                    }
                    Write-Host ''
                }
                'back' {
                    return
                }
                default {
                    print_warn 'Invalid action. Please try again.'
                    Write-Host ''
                }
            }
        }
    }
}

function main_menu_for_existing {
    param([int]$ExistingCount)

    $header = "Detected $ExistingCount Agent Zero container(s). What would you like to do?"
    $selectedIndex = select_from_menu -Header $header -Options @('Install new instance', 'Manage existing instances')

    switch ($selectedIndex) {
        0 { create_instance }
        1 { manage_instances }
        default { create_instance }
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
        main_menu_for_existing -ExistingCount $existingCount
    }
    else {
        create_instance
    }
}

Show-Banner
main
