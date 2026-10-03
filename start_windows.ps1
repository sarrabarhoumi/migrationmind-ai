$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python n'est pas installé ou n'est pas disponible dans le PATH."
}

$PhpExecutable = $null
$PhpCommand = Get-Command php -ErrorAction SilentlyContinue
if ($PhpCommand) {
    $PhpExecutable = $PhpCommand.Source
} elseif (Test-Path "C:\xampp\php\php.exe") {
    $PhpExecutable = "C:\xampp\php\php.exe"
} else {
    throw "PHP n'est pas disponible. Installez PHP ou XAMPP."
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}

& ".venv\Scripts\python.exe" -m pip install --upgrade pip
& ".venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"

$BackendCommand = "Set-Location '$Root\backend'; & '$Root\.venv\Scripts\python.exe' -m uvicorn app.main:app --reload --port 8000"
$FrontendCommand = "Set-Location '$Root\frontend\public'; & '$PhpExecutable' -S localhost:8080"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCommand
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", $FrontendCommand
Start-Sleep -Seconds 2
Start-Process "http://localhost:8080"

Write-Host "MigrationMind AI est lance." -ForegroundColor Green
Write-Host "Interface : http://localhost:8080"
Write-Host "API       : http://localhost:8000/docs"
