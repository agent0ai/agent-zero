$ErrorActionPreference = 'Stop'
$failures = @()

function Require-Command($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) { $script:failures += $name }
}

Require-Command 'git'
Require-Command 'gh'
Require-Command 'node'
Require-Command 'npm'
Require-Command 'py'

if ($failures.Count -gt 0) {
  throw ('Missing required commands: ' + ($failures -join ', ') + '. Run the host bootstrap script as Administrator.')
}

foreach ($version in @('3.10','3.11','3.12','3.13')) {
  & py "-$version" --version *> $null
  if ($LASTEXITCODE -ne 0) { $failures += "Python $version" }
}

if ($env:RUNNER_NAME -and $env:RUNNER_NAME -notlike 'local-windows-*') {
  throw "Unexpected runner: $env:RUNNER_NAME"
}

if ($failures.Count -gt 0) {
  throw ('CI preflight failed: ' + ($failures -join ', '))
}

Write-Host 'CI preflight passed.' -ForegroundColor Green

