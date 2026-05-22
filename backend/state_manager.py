import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


class HospitalStateManager:
    """
    Single Source of Truth del hospital.
    Mantiene el estado global operativo y deriva métricas.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir or Path(__file__).resolve().parent / 'data')

        self.patients: List[Dict[str, Any]] = []
        self.active_patients: List[Dict[str, Any]] = []
        self.waiting_patients: List[Dict[str, Any]] = []
        self.discharged_patients: List[Dict[str, Any]] = []

        self.resources: Dict[str, Dict[str, Any]] = {}
        self.staff: List[Dict[str, Any]] = []
        self.historic_metrics: List[Dict[str, Any]] = []
        self.alerts: List[str] = []
        self.event_timeline: List[Dict[str, Any]] = []
        self.decision_trace: List[Dict[str, Any]] = []

        self.load_initial_state()

    def load_initial_state(self):
        self.load_historic_metrics()
        self.load_resources()
        self.load_staff()
        self.load_patients()
        self.refresh_derived_state()

    def _parse_vitals(self, raw_value: Any) -> Dict[str, Any]:
        if isinstance(raw_value, str):
            try:
                return json.loads(raw_value.replace("'", '"'))
            except Exception:
                return {"raw": raw_value}
        return raw_value or {}

    def _normalize_patient(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        patient = {k: v for k, v in patient.items()}
        patient["id_paciente"] = str(patient.get("id_paciente", "")).strip()
        patient["nivel_urgencia"] = int(patient.get("nivel_urgencia") or 5)
        patient["genero"] = str(patient.get("genero") or "No definido")
        patient["sintomas"] = str(patient.get("sintomas") or "No informado")
        patient["signos_vitales"] = self._parse_vitals(patient.get("signos_vitales", {}))
        patient["tiempo_espera_min"] = int(patient.get("tiempo_espera_min") or 0)
        patient["departamento_asignado"] = str(patient.get("departamento_asignado") or "Pendiente")
        patient["estado"] = str(patient.get("estado") or "En_espera")
        patient["medico_asignado"] = patient.get("medico_asignado") or None
        patient["bed_type"] = patient.get("bed_type") or None
        return patient

    def load_patients(self):
        path = self.data_dir / "pacientes_admisiones.csv"
        if not path.exists():
            return

        df = pd.read_csv(path)
        for row in df.to_dict(orient="records"):
            patient = self._normalize_patient(row)
            self.patients.append(patient)

    def load_resources(self):
        path = self.data_dir / "recursos_disponibilidad.csv"
        self.resources = {}
        if not path.exists():
            return

        df = pd.read_csv(path)
        mapping = {
            "Cama_UCI": "ICU",
            "Cama_General": "GENERAL",
            "Cama_Pediatria": "PEDIATRICS",
            "Cama_Emergencia": "EMERGENCY",
            "Quirofano": "SURGERY",
        }

        aggregated: Dict[str, Dict[str, Any]] = {}
        for row in df.to_dict(orient="records"):
            resource_type = mapping.get(row["tipo_recurso"], row["tipo_recurso"])
            aggregated.setdefault(resource_type, {"total": 0, "available": 0, "occupied": 0, "detail": []})
            total = int(row.get("total_disponible") or 0)
            available = int(row.get("disponibles") or 0)
            occupied = int(row.get("ocupados") or (total - available))
            aggregated[resource_type]["total"] += total
            aggregated[resource_type]["available"] += available
            aggregated[resource_type]["occupied"] += occupied
            aggregated[resource_type]["detail"].append(
                {
                    "departamento": row.get("departamento"),
                    "total": total,
                    "available": available,
                    "occupied": occupied,
                }
            )

        self.resources = aggregated

    def load_staff(self):
        path = self.data_dir / "personal_turnos.csv"
        self.staff = []
        if not path.exists():
            return

        df = pd.read_csv(path)
        for row in df.to_dict(orient="records"):
            self.staff.append(
                {
                    "id_empleado": row.get("id_empleado"),
                    "nombre": row.get("nombre"),
                    "rol": row.get("rol"),
                    "especialidad": str(row.get("especialidad") or "General"),
                    "turno_inicio": row.get("turno_inicio"),
                    "turno_fin": row.get("turno_fin"),
                    "horas_trabajadas_consecutivas": int(row.get("horas_trabajadas_consecutivas") or 0),
                    "pacientes_atendidos_turno": int(row.get("pacientes_atendidos_turno") or 0),
                    "estado": str(row.get("estado") or "Disponible"),
                }
            )

    def load_historic_metrics(self):
        path = self.data_dir / "historico_metricas.csv"
        self.historic_metrics = []
        if not path.exists():
            return

        df = pd.read_csv(path)
        self.historic_metrics = df.to_dict(orient="records")

    def refresh_derived_state(self):
        self.discharged_patients = [
            patient
            for patient in self.patients
            if patient["estado"] in {"Alta", "Transferido"}
        ]
        self.active_patients = [
            patient
            for patient in self.patients
            if patient["estado"] not in {"Alta", "Transferido"}
        ]
        self.waiting_patients = [
            patient for patient in self.active_patients if patient["estado"] == "En_espera"
        ]

    def get_all_patients(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.active_patients[:limit]

    def get_global_state(self) -> Dict[str, Any]:
        return {
            "resources": self.resources,
            "active_patients": len(self.active_patients),
            "waiting_patients": len(self.waiting_patients),
            "discharged_patients": len(self.discharged_patients),
            "total_admissions": len(self.patients),
            "total_discharges": len(self.discharged_patients),
            "available_staff": len([s for s in self.staff if s["estado"] == "Disponible"]),
            "total_staff": len(self.staff),
            "alerts": self.alerts,
            "event_timeline": self.event_timeline[:50],
            "decision_trace": self.decision_trace[-50:],
        }

    def get_occupancy_percentage(self, resource_type: str) -> float:
        resource = self.resources.get(resource_type, {"total": 0, "available": 0})
        if resource["total"] == 0:
            return 0.0
        occupied = resource["total"] - resource["available"]
        return round((occupied / resource["total"]) * 100, 2)

    def add_alert(self, alert_message: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{now} - {alert_message}"
        self.alerts.append(entry)
        self.add_event("ALERT_RAISED", {"message": alert_message})
        print(f"[ALERT] {entry}")

    def add_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "payload": payload,
        }
        self.event_timeline.insert(0, event)
        if len(self.event_timeline) > 200:
            self.event_timeline.pop()

    def record_decision(
        self,
        patient_id: Optional[str],
        event: str,
        agent: str,
        decision: str,
        reason: str,
        source_data: Dict[str, Any],
    ) -> None:
        trace = {
            "patient_id": patient_id,
            "event": event,
            "agent": agent,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "decision": decision,
            "reason": reason,
            "source_data": source_data,
        }
        self.decision_trace.append(trace)
        if len(self.decision_trace) > 200:
            self.decision_trace.pop(0)

    def persist_patient(self, patient: Dict[str, Any]) -> None:
        path = self.data_dir / "persisted_patients.json"
        existing = []
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8") or "[]")
            except Exception:
                existing = []
        existing.append(patient)
        path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_patient(self, patient: Dict[str, Any]) -> None:
        patient = self._normalize_patient(patient)
        if not patient["id_paciente"]:
            patient["id_paciente"] = f"P{datetime.now().strftime('%Y%m%d%H%M%S')[-8:]}"
        if not patient.get("timestamp"):
            patient["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not patient.get("estado"):
            patient["estado"] = "En_espera"

        self.patients.insert(0, patient)
        self.refresh_derived_state()
        self.persist_patient(patient)
        self.add_event("PATIENT_ADDED", {"patient": patient})
        print(f"[STATE] Patient added -> {patient['id_paciente']}")

    def allocate_resource(self, priority: str, patient: Dict[str, Any]) -> Optional[str]:
        preferences = ["ICU", "EMERGENCY", "GENERAL", "PEDIATRICS", "SURGERY"]
        if priority == "NORMAL":
            preferences = ["GENERAL", "PEDIATRICS", "EMERGENCY"]
        elif priority == "HIGH":
            preferences = ["EMERGENCY", "ICU", "GENERAL"]
        elif priority == "CRITICAL":
            preferences = ["ICU", "EMERGENCY", "GENERAL"]

        for resource_type in preferences:
            resource = self.resources.get(resource_type)
            if resource and resource.get("available", 0) > 0:
                resource["available"] -= 1
                resource["occupied"] += 1
                patient["bed_type"] = resource_type
                patient["departamento_asignado"] = self._map_resource_to_department(resource_type)
                patient["estado"] = "En_atencion"
                self.refresh_derived_state()
                self.add_event(
                    "RESOURCE_ALLOCATED",
                    {
                        "patient": patient,
                        "resource_type": resource_type,
                        "available": resource["available"],
                    },
                )
                return resource_type

        self.add_alert(
            f"No hay recursos disponibles para paciente {patient['id_paciente']} con prioridad {priority}."
        )
        return None

    def _map_resource_to_department(self, resource_type: str) -> str:
        mapping = {
            "ICU": "UCI",
            "GENERAL": "Hospitalización",
            "PEDIATRICS": "Pediatría",
            "EMERGENCY": "Emergencias",
            "SURGERY": "Cirugía",
        }
        return mapping.get(resource_type, resource_type)

    def get_available_staff(self, specialty: Optional[str] = None) -> List[Dict[str, Any]]:
        candidates = [
            staff
            for staff in self.staff
            if staff["estado"] == "Disponible"
        ]
        if specialty:
            specialty_lower = specialty.lower()
            filtered = [
                staff
                for staff in candidates
                if specialty_lower in str(staff["especialidad"]).lower()
                or specialty_lower in str(staff["rol"]).lower()
            ]
            if filtered:
                return filtered
        return candidates

    def assign_staff(self, patient: Dict[str, Any], specialty: str) -> Optional[Dict[str, Any]]:
        candidates = self.get_available_staff(specialty)
        if not candidates:
            candidates = self.get_available_staff()
        if not candidates:
            self.add_alert(f"No hay personal disponible para paciente {patient['id_paciente']}." )
            return None

        staff_member = candidates[0]
        staff_member["estado"] = "Ocupado"
        staff_member["pacientes_atendidos_turno"] += 1
        patient["medico_asignado"] = staff_member["nombre"]
        self.refresh_derived_state()
        self.add_event(
            "STAFF_ASSIGNED",
            {
                "patient": patient,
                "staff": staff_member,
            },
        )
        return staff_member

    def select_staff_specialty(self, patient: Dict[str, Any], priority: str) -> str:
        symptom_text = str(patient.get("sintomas", "")).lower()
        department = str(patient.get("departamento_asignado", "")).lower()

        if "cardio" in symptom_text or "corazón" in symptom_text or "cardiologia" in department:
            return "Cardiologia"
        if "traumat" in symptom_text or "fractura" in symptom_text or "traumatologia" in department:
            return "Traumatologia"
        if "pediatr" in symptom_text or "niño" in symptom_text or "pediatria" in department:
            return "Pediatria"
        if priority == "CRITICAL":
            return "Medicina Intensiva"
        if priority == "HIGH":
            return "Medicina General"
        return "Medicina General"

    def get_state_snapshot(self) -> Dict[str, Any]:
        return {
            "patients": self.get_all_patients(200),
            "global_state": self.get_global_state(),
            "resources": self.resources,
            "staff": self.staff,
            "events": self.event_timeline[:50],
            "decisions": self.decision_trace[-50:],
        }
