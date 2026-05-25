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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"


# ─── WebSocket Manager ──────────────────────────────────────────────────────

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
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                to_remove.append(ws)
        for ws in to_remove:
            if ws in self.active:
                self.active.remove(ws)


# ─── Bootstrap ──────────────────────────────────────────────────────────────

event_bus = EventBus()
state_manager = HospitalStateManager(DATA_DIR)

triage     = TriageAgent(event_bus, state_manager)
resource   = ResourceAgent(event_bus, state_manager)
staff_ag   = StaffAgent(event_bus, state_manager)
forecast   = ForecastAgent(event_bus, state_manager)
workflow   = WorkflowAgent(event_bus, state_manager)
quality    = QualityAgent(event_bus, state_manager)
orchestrator = OrchestratorAgent(event_bus, state_manager)

ws_manager = WebSocketManager()


# ─── Broadcaster para todos los eventos ─────────────────────────────────────

def make_broadcaster(event_type: str):
    async def _broadcast(payload: dict):
        await ws_manager.broadcast(
            {
                "event_type": event_type,
                "payload": payload,
                "timestamp": datetime.now().isoformat(),
                "global_state": state_manager.get_global_state(),
            }
        )
    return _broadcast


BROADCAST_EVENTS = [
    "PATIENT_ARRIVED",
    "PATIENT_TRIAGED",
    "RESOURCE_ALLOCATED",
    "STAFF_ASSIGNED",
    "SATURATION_WARNING",
    "WORKFLOW_ALERT",
    "CRITICAL_ALERT",
    "FORECAST_UPDATED",
    "PATIENT_ESCALATED",
    "PATIENT_TRANSFERRED",
    "PATIENT_DISCHARGED",
    "SIMULATION_TICK",
]

for evt in BROADCAST_EVENTS:
    event_bus.subscribe(evt, make_broadcaster(evt))


# ─── REST endpoints ──────────────────────────────────────────────────────────

@app.get("/api/patients")
def get_patients(limit: int = 100):
    patients = state_manager.get_all_patients(limit)
    return {"patients": patients, "count": len(patients)}


@app.get("/api/departments")
def get_departments():
    try:
        import pandas as pd
        path = DATA_DIR / "recursos.csv"
        if not path.exists():
            return {"departments": [], "error": "CSV no encontrado"}
        df = pd.read_csv(path)
        departments = []
        for _, row in df.iterrows():
            total = int(row.get("total", 0))
            ocupados = int(row.get("ocupados", 0))
            departments.append({
                "departamento": row.get("departamento"),
                "total": total,
                "ocupados": ocupados,
                "disponibles": total - ocupados,
                "ocupacion_pct": round((ocupados / total * 100) if total > 0 else 0, 1),
            })
        return {"departments": departments, "count": len(departments)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/resources")
def get_resources():
    try:
        import pandas as pd
        path = DATA_DIR / "recursos.csv"
        if not path.exists():
            return {"resources": [], "error": "CSV no encontrado"}
        df = pd.read_csv(path)
        resources = []
        for _, row in df.iterrows():
            total = int(row.get("total", 0))
            ocupados = int(row.get("ocupados", 0))
            resources.append({
                "departamento": row.get("departamento"),
                "total": total,
                "ocupados": ocupados,
                "disponibles": total - ocupados,
            })
        return {"resources": resources, "count": len(resources)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/staff")
def get_staff():
    try:
        import pandas as pd
        path = DATA_DIR / "personal.csv"
        if not path.exists():
            return {"staff": [], "error": "CSV no encontrado"}
        df = pd.read_csv(path)
        staff = df.where(pd.notna(df), None).to_dict(orient="records")
        return {"staff": staff, "count": len(staff)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics")
def get_metrics():
    try:
        import pandas as pd
        path = DATA_DIR / "metricas.csv"
        if not path.exists():
            return {"metrics": {}, "error": "CSV no encontrado"}
        df = pd.read_csv(path)
        if len(df) > 0:
            return {"metrics": df.iloc[0].to_dict(), "count": 1}
        return {"metrics": {}, "count": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/state")
def api_state():
    return state_manager.get_global_state()


@app.get("/api/health")
def health():
    try:
        gs = state_manager.get_global_state()
        return {
            "status": "ok",
            "active_patients": gs.get("active_patients", 0),
            "resources": gs.get("resources", {}),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ─── WebSocket endpoint ──────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

    snapshot = {
        "event_type": "INITIAL_SNAPSHOT",
        "patients": state_manager.get_all_patients(200),
        "global_state": state_manager.get_global_state(),
        "events": state_manager.event_timeline[:50],
        "decisions": state_manager.decision_trace[-50:],
        "timestamp": datetime.now().isoformat(),
    }
    await websocket.send_text(json.dumps(snapshot, default=str))

    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                payload = json.loads(data_text)
            except ValueError:
                continue

            action = payload.get("action")
            patient_data = payload.get("patient") or {}

            # ── Ingresar nuevo paciente ───────────────────────────────────
            if action == "NEW_PATIENT":
                patient_id = f"P{str(uuid.uuid4())[:5].upper()}"
                patient_data["id_paciente"] = patient_id
                patient_data["timestamp"] = datetime.now().isoformat()
                patient_data["estado"] = "En_evaluacion"

                state_manager.add_patient(patient_data)
                await event_bus.publish("PATIENT_ARRIVED", patient_data)

            # ── Simular 1 hora ────────────────────────────────────────────
            elif action == "SIMULATE_HOUR":
                patient_id = payload.get("patient_id")
                result = state_manager.simulate_hour(patient_id)
                await event_bus.publish("SIMULATION_TICK", {
                    "patient_id": patient_id,
                    "result": result,
                    "message": f"Simulación de 1 hora completada para {patient_id}",
                    "timestamp": datetime.now().isoformat(),
                })

            # ── Escalar prioridad ─────────────────────────────────────────
            elif action == "ESCALATE":
                patient_id = payload.get("patient_id")
                result = state_manager.escalate_patient(patient_id)
                await event_bus.publish("PATIENT_ESCALATED", {
                    "patient_id": patient_id,
                    "new_priority": result.get("new_priority"),
                    "message": f"Prioridad escalada a {result.get('new_priority')} para {patient_id}",
                    "timestamp": datetime.now().isoformat(),
                })

            # ── Transferir paciente ───────────────────────────────────────
            elif action == "TRANSFER":
                patient_id = payload.get("patient_id")
                destination = payload.get("destination", "UCI")
                result = state_manager.transfer_patient(patient_id, destination)
                await event_bus.publish("PATIENT_TRANSFERRED", {
                    "patient_id": patient_id,
                    "destination": destination,
                    "message": f"Paciente {patient_id} transferido a {destination}",
                    "timestamp": datetime.now().isoformat(),
                })

            # ── Dar alta ──────────────────────────────────────────────────
            elif action == "DISCHARGE":
                patient_id = payload.get("patient_id")
                result = state_manager.discharge_patient(patient_id)
                await event_bus.publish("PATIENT_DISCHARGED", {
                    "patient_id": patient_id,
                    "message": f"Paciente {patient_id} dado de alta",
                    "timestamp": datetime.now().isoformat(),
                })

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
