# One-command dev setup (Windows PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "Setting up VishwasEdge..." -ForegroundColor Cyan

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example — edit it to add ANTHROPIC_API_KEY if you want cloud-tier answers." -ForegroundColor Yellow
}

Push-Location frontend
npm install
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}
Pop-Location

New-Item -ItemType Directory -Force -Path "data/raw", "data/processed" | Out-Null

Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Run backend:  .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload"
Write-Host "Run frontend: cd frontend; npm run dev"
