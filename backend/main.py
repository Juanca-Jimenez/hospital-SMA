from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime
import json
import uuid

from backend.event_bus import EventBus
from backend.state_manager import HospitalStateManager
from backend.agents import (
    TriageAgent,
    ResourceAgent,
    StaffAgent,
    ForecastAgent,
    WorkflowAgent,
    QualityAgent,
    OrchestratorAgent,
)

app = FastAPI()

# CORS Configuration - MUST be before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"


class WebSocketManager:
    def __init__(self):
        self.active = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: dict):
        to_remove = []
        for ws in list(self.active):
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                to_remove.append(ws)
        for ws in to_remove:
            if ws in self.active:
                self.active.remove(ws)


event_bus = EventBus()
state_manager = HospitalStateManager(DATA_DIR)

triage = TriageAgent(event_bus, state_manager)
resource = ResourceAgent(event_bus, state_manager)
staff = StaffAgent(event_bus, state_manager)
forecast = ForecastAgent(event_bus, state_manager)
workflow = WorkflowAgent(event_bus, state_manager)
quality = QualityAgent(event_bus, state_manager)
orchestrator = OrchestratorAgent(event_bus, state_manager)

ws_manager = WebSocketManager()


def make_broadcaster(event_type: str):
    async def _broadcast(payload: dict):
        await ws_manager.broadcast(
            {
                "event_type": event_type,
                "payload": payload,
                "global_state": state_manager.get_global_state(),
            }
        )
    return _broadcast


for event_type in [
    "PATIENT_ARRIVED",
    "PATIENT_TRIAGED",
    "RESOURCE_ALLOCATED",
    "STAFF_ASSIGNED",
    "SATURATION_WARNING",
    "WORKFLOW_ALERT",
    "CRITICAL_ALERT",
]:
    event_bus.subscribe(event_type, make_broadcaster(event_type))


@app.get("/api/patients")
def get_patients(limit: int = 100):
    patients = state_manager.get_all_patients(limit)
    return {"patients": patients, "count": len(patients)}


@app.get("/api/departments")
def get_departments():
    """Obtiene la disponibilidad de recursos por departamento"""
    try:
        import pandas as pd
        path = DATA_DIR / "recursos.csv"
        if not path.exists():
            return {"departments": [], "error": "CSV no encontrado"}
        
        df = pd.read_csv(path)
        departments = []
        for _, row in df.iterrows():
            departments.append({
                "departamento": row.get("departamento"),
                "total": int(row.get("total")),
                "ocupados": int(row.get("ocupados")),
                "disponibles": int(row.get("total")) - int(row.get("ocupados")),
                "ocupacion_pct": round((int(row.get("ocupados")) / int(row.get("total")) * 100) if int(row.get("total")) > 0 else 0, 1)
            })
        
        return {"departments": departments, "count": len(departments)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando departamentos: {str(e)}")


@app.get("/api/resources")
def get_resources():
    """Obtiene la disponibilidad de recursos por departamento"""
    try:
        import pandas as pd
        path = DATA_DIR / "recursos.csv"
        if not path.exists():
            return {"resources": [], "error": "CSV no encontrado"}
        
        df = pd.read_csv(path)
        resources = []
        for _, row in df.iterrows():
            resources.append({
                "departamento": row.get("departamento"),
                "total": int(row.get("total")),
                "ocupados": int(row.get("ocupados")),
                "disponibles": int(row.get("total")) - int(row.get("ocupados"))
            })
        
        return {"resources": resources, "count": len(resources)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando recursos: {str(e)}")


@app.get("/api/staff")
def get_staff():
    """Obtiene el personal disponible por departamento"""
    try:
        import pandas as pd
        path = DATA_DIR / "personal.csv"
        if not path.exists():
            return {"staff": [], "error": "CSV no encontrado"}
        
        df = pd.read_csv(path)
        staff = df.where(pd.notna(df), None).to_dict(orient="records")
        
        return {"staff": staff, "count": len(staff)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando personal: {str(e)}")


@app.get("/api/metrics")
def get_metrics():
    """Obtiene las métricas resumidas del hospital"""
    try:
        import pandas as pd
        path = DATA_DIR / "metricas.csv"
        if not path.exists():
            return {"metrics": {}, "error": "CSV no encontrado"}
        
        df = pd.read_csv(path)
        if len(df) > 0:
            metrics = df.iloc[0].to_dict()
            return {"metrics": metrics, "count": 1}
        else:
            return {"metrics": {}, "count": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando métricas: {str(e)}")


@app.get("/api/state")
def api_state():
    return state_manager.get_global_state()


@app.get("/api/health")
def health():
    try:
        return {
            "status": "ok",
            "active_patients": state_manager.get_global_state().get("active_patients", 0),
            "resources": state_manager.get_global_state().get("resources", {}),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

    snapshot = {
        "event_type": "INITIAL_SNAPSHOT",
        "patients": state_manager.get_all_patients(200),
        "global_state": state_manager.get_global_state(),
        "events": state_manager.event_timeline[:50],
        "decisions": state_manager.decision_trace[-50:],
    }
    await websocket.send_text(json.dumps(snapshot))

    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                payload = json.loads(data_text)
            except ValueError:
                continue

            if payload.get("action") == "NEW_PATIENT":
                patient = payload.get("patient") or {}
                patient.setdefault("id_paciente", f"P{str(uuid.uuid4())[:7].upper()}")
                patient["timestamp"] = patient.get("timestamp") or datetime.now().isoformat()
                patient.setdefault("estado", "En_espera")
                state_manager.add_patient(patient)
                await event_bus.publish("PATIENT_ARRIVED", patient)

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
