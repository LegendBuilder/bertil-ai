param(
  [string]$Host="127.0.0.1",
  [int]$Port=8000
)

Write-Host "Starting backend on http://$Host:$Port" -ForegroundColor Green
uvicorn services.api.app.main:app --host $Host --port $Port --reload


