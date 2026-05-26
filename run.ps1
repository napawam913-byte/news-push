$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath ".\.env")) {
    Copy-Item -Path ".\.env.example" -Destination ".\.env"
}

if (-not (Test-Path -LiteralPath ".\.venv")) {
    python -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.main --once

