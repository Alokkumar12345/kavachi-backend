# Build and Setup script for Kavachi Backend (Windows)

Write-Host "Installing Node Dependencies..." -ForegroundColor Cyan
npm install

Write-Host "Setting up Python Virtual Environment..." -ForegroundColor Cyan
if (!(Test-Path -Path "venv")) {
    python -m venv venv
}

Write-Host "Activating Virtual Environment and Installing Python Requirements..." -ForegroundColor Cyan
if ($PSVersionTable.PSVersion.Major -ge 5) {
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
} else {
    Write-Host "This script is intended for Windows PowerShell/Core." -ForegroundColor Yellow
}

Write-Host "Build Successful!" -ForegroundColor Green
