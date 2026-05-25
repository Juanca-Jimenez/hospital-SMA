import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


class HospitalStateManager:
    """
    Single Source of Truth del hospital.
    Soporta el nuevo payload clínico (vitales estructurados, sintomas[],
    motivo_consulta, dolor) y el payload legado.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir or Path(__file__).resolve().parent / "data")

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

    # ─── Carga inicial ─────────────────────────────────────────────────────

    def load_initial_state(self):
        self.load_historic_metrics()
        self.load_resources()
        self.load_staff()
        self.load_patients()
        self.refresh_derived_state()

    def load_patients(self):
        path = self.data_dir / "pacientes.csv"
        if not path.exists():
            return
        df = pd.read_csv(path)
        for row in df.to_dict(orient="records"):
            patient = self._normalize_patient(row)
            self.patients.append(patient)

    def load_resources(self):
        path = self.data_dir / "recursos.csv"
        self.resources = {}
        if not path.exists():
            return
        df = pd.read_csv(path)
        for row in df.to_dict(orient="records"):
            dept = str(row.get("departamento", "")).strip()
            total = int(row.get("total") or 0)
            ocupados = int(row.get("ocupados") or 0)
            disponibles = total - ocupados
            rtype = self._map_department_to_resource(dept)
            self.resources[rtype] = {
                "total": total,
                "occupied": ocupados,
                "available": disponibles,
                "departamento": dept,
                "detail": [{"departamento": dept, "total": total,
                             "available": disponibles, "occupied": ocupados}],
            }

    def load_staff(self):
        path = self.data_dir / "personal.csv"
        self.staff = []
        if not path.exists():
            return
        df = pd.read_csv(path)
        for row in df.to_dict(orient="records"):
            self.staff.append({
                "id_empleado": str(row.get("id_empleado", "")).strip(),
                "nombre": str(row.get("nombre") or row.get("id_empleado") or "Personal"),
                "rol": str(row.get("rol") or "General"),
                "especialidad": str(row.get("especialidad") or "General"),
                "departamento_1": str(row.get("departamento_1") or "Hospitalizacion"),
                "departamento_2": str(row.get("departamento_2") or "Emergencias"),
                "estado": str(row.get("estado") or "Disponible"),
                "pacientes_atendidos_turno": int(row.get("pacientes_atendidos_turno") or 0),
            })

    def load_historic_metrics(self):
        path = self.data_dir / "metricas.csv"
        self.historic_metrics = []
        if not path.exists():
            return
        df = pd.read_csv(path)
        self.historic_metrics = df.to_dict(orient="records")

    # ─── Normalización de paciente ─────────────────────────────────────────

    def _normalize_patient(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convierte ambos formatos (nuevo clínico y legado CSV) a estructura interna.
        """
        p = dict(patient)

        p["id_paciente"] = str(p.get("id_paciente", "")).strip()
        p["edad"] = int(p.get("edad") or 0)
        p["genero"] = str(p.get("genero") or "No definido")
        p["estado"] = str(p.get("estado") or "En_espera")

        # ── Nuevo payload clínico ─────────────────────────────────────
        if "motivo_consulta" in p or "vitales" in p:
            # Síntomas como lista
            sintomas = p.get("sintomas", [])
            if isinstance(sintomas, list):
                p["sintomas"] = sintomas
            else:
                p["sintomas"] = [s.strip() for s in str(sintomas).split(",") if s.strip()]

            p["motivo_consulta"] = str(p.get("motivo_consulta") or "")
            p["dolor"] = int(p.get("dolor") or 0)

            # Vitales estructurados
            vitales = p.get("vitales") or {}
            if isinstance(vitales, str):
                try:
                    vitales = json.loads(vitales)
                except Exception:
                    vitales = {}
            p["vitales"] = vitales

            # Legado: nivel_urgencia calculado del dolor para compat.
            p.setdefault("nivel_urgencia", 3)

        else:
            # ── Formato legado CSV ────────────────────────────────────
            p["nivel_urgencia"] = int(p.get("nivel_urgencia") or 5)
            sintomas = p.get("sintomas", "")
            p["sintomas"] = str(sintomas) if sintomas else "No informado"

        p["departamento"] = str(p.get("departamento") or "Pendiente")
        p["medico_asignado"] = p.get("medico_asignado") or None
        p["bed_type"] = p.get("bed_type") or None
        p["cama"] = p.get("cama") or None
        p["prioridad"] = p.get("prioridad") or None

        return p

    # ─── Estado derivado ───────────────────────────────────────────────────

    def refresh_derived_state(self):
        self.discharged_patients = [
            p for p in self.patients if p["estado"] in {"Alta", "Transferido"}
        ]
        self.active_patients = [
            p for p in self.patients if p["estado"] not in {"Alta", "Transferido"}
        ]
        self.waiting_patients = [
            p for p in self.active_patients
            if p["estado"] in {"En_espera", "En_evaluacion", "En_triaje"}
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
            "alerts": self.alerts[-20:],
            "event_timeline": self.event_timeline[:50],
            "decision_trace": self.decision_trace[-50:],
        }

    # ─── Pacientes ─────────────────────────────────────────────────────────

    def add_patient(self, patient: Dict[str, Any]) -> None:
        patient = self._normalize_patient(patient)
        if not patient["id_paciente"]:
            patient["id_paciente"] = f"P{datetime.now().strftime('%H%M%S')}"
        if not patient.get("timestamp"):
            patient["timestamp"] = datetime.now().isoformat()
        if not patient.get("estado"):
            patient["estado"] = "En_evaluacion"

        self.patients.insert(0, patient)
        self.refresh_derived_state()
        self.persist_patient(patient)
        self.add_event("PATIENT_ADDED", {"patient": patient})
        print(f"[STATE] Patient added → {patient['id_paciente']}")

    def update_patient_field(self, patient_id: str, field: str, value: Any) -> None:
        """Actualiza un campo de un paciente en la lista en memoria."""
        for p in self.patients:
            if p.get("id_paciente") == patient_id:
                p[field] = value
        self.refresh_derived_state()

    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        for p in self.patients:
            if p.get("id_paciente") == patient_id:
                return p
        return None

    # ─── Recursos ──────────────────────────────────────────────────────────

    def get_occupancy_percentage(self, resource_type: str) -> float:
        r = self.resources.get(resource_type, {"total": 0, "available": 0})
        if r["total"] == 0:
            return 0.0
        occupied = r["total"] - r["available"]
        return round((occupied / r["total"]) * 100, 2)

    def allocate_resource(self, priority: str, patient: Dict[str, Any]) -> Optional[str]:
        if priority == "NORMAL":
            prefs = ["GENERAL", "PEDIATRICS", "EMERGENCY"]
        elif priority == "MEDIUM":
            prefs = ["GENERAL", "EMERGENCY", "ICU"]
        elif priority == "HIGH":
            prefs = ["EMERGENCY", "ICU", "GENERAL"]
        else:  # CRITICAL
            prefs = ["ICU", "EMERGENCY", "GENERAL"]

        for rtype in prefs:
            r = self.resources.get(rtype)
            if r and r.get("available", 0) > 0:
                r["available"] -= 1
                r["occupied"] += 1
                dept = self._map_resource_to_department(rtype)
                patient["bed_type"] = rtype
                patient["departamento_asignado"] = dept
                patient["estado"] = "Cama_asignada"
                # Generar ID de cama
                prefix = dept[:3].upper().replace("Á", "A").replace("É", "E")
                bed_id = f"{prefix}-{random.randint(1, 30):02d}"
                patient["bed_id"] = bed_id
                patient["cama"] = bed_id
                self.refresh_derived_state()
                self.add_event("RESOURCE_ALLOCATED", {
                    "patient": patient,
                    "resource_type": rtype,
                    "available": r["available"],
                })
                return rtype

        self.add_alert(
            f"No hay recursos para {patient['id_paciente']} con prioridad {priority}."
        )
        return None

    # ─── Personal ──────────────────────────────────────────────────────────

    def get_available_staff(self, specialty: Optional[str] = None) -> List[Dict[str, Any]]:
        candidates = [s for s in self.staff if s["estado"] == "Disponible"]
        if specialty:
            sl = specialty.lower()
            filtered = [
                s for s in candidates
                if sl in str(s["especialidad"]).lower() or sl in str(s["rol"]).lower()
            ]
            if filtered:
                return filtered
        return candidates

    def assign_staff(self, patient: Dict[str, Any], specialty: str) -> Optional[Dict[str, Any]]:
        candidates = self.get_available_staff(specialty)
        if not candidates:
            candidates = self.get_available_staff()
        if not candidates:
            self.add_alert(f"No hay personal disponible para {patient['id_paciente']}.")
            return None

        # Preferir médicos/doctores
        doctors = [s for s in candidates if "medic" in s["rol"].lower() or "doctor" in s["rol"].lower()]
        member = doctors[0] if doctors else candidates[0]
        member["estado"] = "Ocupado"
        member["pacientes_atendidos_turno"] = member.get("pacientes_atendidos_turno", 0) + 1
        patient["medico_asignado"] = member["id_empleado"]
        self.refresh_derived_state()
        self.add_event("STAFF_ASSIGNED", {"patient": patient, "staff": member})
        return member

    def assign_nurse(self, patient: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Asigna un enfermero disponible al paciente."""
        nurses = [
            s for s in self.staff
            if s["estado"] == "Disponible"
            and ("enferm" in s["rol"].lower() or "nurse" in s["rol"].lower())
        ]
        if not nurses:
            # Si no hay enfermeros específicos, tomar cualquier disponible
            nurses = [s for s in self.staff if s["estado"] == "Disponible"]
        if not nurses:
            return None
        nurse = nurses[0]
        nurse["estado"] = "Ocupado"
        nurse["pacientes_atendidos_turno"] = nurse.get("pacientes_atendidos_turno", 0) + 1
        patient["enfermero_asignado"] = nurse["id_empleado"]
        return nurse

    def select_staff_specialty(self, patient: Dict[str, Any], priority: str) -> str:
        motivo = str(patient.get("motivo_consulta", "")).lower()
        sintomas = patient.get("sintomas", [])
        if isinstance(sintomas, list):
            sint_text = " ".join(sintomas).lower()
        else:
            sint_text = str(sintomas).lower()
        dept = str(patient.get("departamento_asignado", "")).lower()

        if "cardio" in sint_text or "torácico" in sint_text or "cardiologia" in dept:
            return "Cardiologia"
        if "traumat" in sint_text or "fractura" in sint_text:
            return "Traumatologia"
        if "neurológico" in motivo or "conciencia" in sint_text:
            return "Neurologia"
        if "pediatr" in dept:
            return "Pediatria"
        if priority == "CRITICAL":
            return "Medicina Intensiva"
        if priority == "HIGH":
            return "Medicina General"
        return "Medicina General"

    # ─── Alertas y eventos ─────────────────────────────────────────────────

    def add_alert(self, alert_message: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.alerts.append(f"{now} - {alert_message}")
        self.add_event("ALERT_RAISED", {"message": alert_message})
        print(f"[ALERT] {alert_message}")

    def add_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "payload": payload,
        }
        self.event_timeline.insert(0, event)
        if len(self.event_timeline) > 500:
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
        self.decision_trace.append({
            "patient_id": patient_id,
            "event": event,
            "agent": agent,
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "reason": reason,
            "source_data": source_data,
        })
        if len(self.decision_trace) > 500:
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
        path.write_text(json.dumps(existing, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    # ─── Acciones de simulación ────────────────────────────────────────────

    def simulate_hour(self, patient_id: str) -> Dict[str, Any]:
        """Simula el paso de 1 hora: actualiza estado del paciente."""
        patient = self.get_patient(patient_id)
        if not patient:
            return {"error": "Paciente no encontrado"}

        old_estado = patient.get("estado", "")
        transitions = {
            "Personal_asignado": "En_atencion",
            "En_atencion": "En_observacion",
            "En_observacion": "Mejorando",
            "Mejorando": "Alta_pendiente",
        }
        new_estado = transitions.get(old_estado, old_estado)
        self.update_patient_field(patient_id, "estado", new_estado)
        self.add_event("SIMULATION_TICK", {
            "patient_id": patient_id,
            "old_estado": old_estado,
            "new_estado": new_estado,
        })
        return {"patient_id": patient_id, "old_estado": old_estado, "new_estado": new_estado}

    def escalate_patient(self, patient_id: str) -> Dict[str, Any]:
        """Escala la prioridad del paciente al siguiente nivel."""
        patient = self.get_patient(patient_id)
        if not patient:
            return {"error": "Paciente no encontrado"}

        escalation = {"NORMAL": "MEDIUM", "MEDIUM": "HIGH", "HIGH": "CRITICAL", "CRITICAL": "CRITICAL"}
        old_priority = patient.get("prioridad", "NORMAL")
        new_priority = escalation.get(old_priority, "HIGH")
        self.update_patient_field(patient_id, "prioridad", new_priority)
        self.add_event("PATIENT_ESCALATED", {
            "patient_id": patient_id,
            "old_priority": old_priority,
            "new_priority": new_priority,
        })
        return {"patient_id": patient_id, "old_priority": old_priority, "new_priority": new_priority}

    def transfer_patient(self, patient_id: str, destination: str) -> Dict[str, Any]:
        """Transfiere al paciente a otro departamento."""
        patient = self.get_patient(patient_id)
        if not patient:
            return {"error": "Paciente no encontrado"}

        self.update_patient_field(patient_id, "departamento_asignado", destination)
        self.update_patient_field(patient_id, "estado", "Transferido_interno")
        self.add_event("PATIENT_TRANSFERRED", {
            "patient_id": patient_id,
            "destination": destination,
        })
        return {"patient_id": patient_id, "destination": destination}

    def discharge_patient(self, patient_id: str) -> Dict[str, Any]:
        """Da de alta al paciente y libera sus recursos."""
        patient = self.get_patient(patient_id)
        if not patient:
            return {"error": "Paciente no encontrado"}

        # Liberar cama
        bed_type = patient.get("bed_type")
        if bed_type and bed_type in self.resources:
            r = self.resources[bed_type]
            r["available"] = min(r["available"] + 1, r["total"])
            r["occupied"] = max(r["occupied"] - 1, 0)

        # Liberar personal
        medico_id = patient.get("medico_asignado")
        enfermero_id = patient.get("enfermero_asignado")
        for s in self.staff:
            if s["id_empleado"] in (medico_id, enfermero_id):
                s["estado"] = "Disponible"

        self.update_patient_field(patient_id, "estado", "Alta")
        self.refresh_derived_state()
        self.add_event("PATIENT_DISCHARGED", {"patient_id": patient_id})
        return {"patient_id": patient_id, "estado": "Alta"}

    # ─── Helpers de mapeo ──────────────────────────────────────────────────

    def _map_department_to_resource(self, dept: str) -> str:
        mapping = {
            "Emergencias": "EMERGENCY",
            "UCI": "ICU",
            "Hospitalizacion": "GENERAL",
            "Hospitalización": "GENERAL",
            "Pediatria": "PEDIATRICS",
            "Pediatría": "PEDIATRICS",
            "Cirugia": "SURGERY",
            "Cirugía": "SURGERY",
            "Consulta_Externa": "GENERAL",
            "Cardiologia": "GENERAL",
            "Radiologia": "GENERAL",
        }
        return mapping.get(dept, "GENERAL")

    def _map_resource_to_department(self, rtype: str) -> str:
        mapping = {
            "ICU": "UCI",
            "GENERAL": "Hospitalización",
            "PEDIATRICS": "Pediatría",
            "EMERGENCY": "Urgencias",
            "SURGERY": "Cirugía",
        }
        return mapping.get(rtype, rtype)

    def get_state_snapshot(self) -> Dict[str, Any]:
        return {
            "patients": self.get_all_patients(200),
            "global_state": self.get_global_state(),
            "resources": self.resources,
            "staff": self.staff,
            "events": self.event_timeline[:50],
            "decisions": self.decision_trace[-50:],
        }
