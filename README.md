# hospital-SMA

Sistema Multiagente de Gestión Hospitalaria Integral

Instalación y ejecución (método rápido):

Backend (Python 3.11+)

1. Crear y activar un virtualenv:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
pip install -r backend/requirements.txt
```

3. Ejecutar el servidor:

```powershell
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (Node + Vite)

1. Entrar a la carpeta frontend e instalar dependencias:

```bash
cd frontend
npm install
```

2. Añadir Tailwind vía CDN (ya incluido en index.html) y ejecutar:

```bash
npm run dev
```

Workflow en tiempo real

- El frontend se conecta a `ws://localhost:8000/ws`.
- Al enviar un nuevo paciente desde el formulario (`action: NEW_PATIENT`), el backend publica `PATIENT_ARRIVED` en el Event Bus.
- Los agentes (Triage, Resource, Staff, Forecast, Workflow, Quality, Orchestrator) reaccionan asíncronamente a eventos y publican resultados que son retransmitidos vía WebSocket al dashboard.
