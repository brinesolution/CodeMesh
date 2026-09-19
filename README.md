# CodeMesh Local

CodeMesh is a local-first multi-model AI assistant. A lightweight Ollama router selects one focused specialist while FastAPI streams the response to a React chat UI.

## Quick start

```powershell
Set-Location E:\CodeMesh
.\scripts\bootstrap.ps1
.\scripts\doctor.ps1
.\scripts\pull-models.ps1
.\scripts\dev.ps1
```

Open `http://127.0.0.1:5173`. Stop owned services with `.\scripts\stop.ps1`.

Fast checks: `.\scripts\test.ps1`. The app stays local after dependencies and models are installed; Ollama must be running for live inference.

