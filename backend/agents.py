import random
from datetime import datetime
from typing import Any, Dict

from backend.rules import (
    classify_priority,
    build_triage_reasons,
    build_triage_factors,
    estimated_wait_time,
    detect_saturation,
    should_generate_critical_alert,
)


class BaseAgent:
    def __init__(self, name: str, event_bus: Any, state_manager: Any = None):
        self.name = name
        self.event_bus = event_bus
        self.state_manager = state_manager
        print(f"[AGENT INITIALIZED] {self.name}")


# ─── TriageAgent ────────────────────────────────────────────────────────────

class TriageAgent(BaseAgent):
    def __init__(self, event_bus: Any, state_manager: Any):
        super().__init__("TriageAgent", event_bus, state_manager)
        self.event_bus.subscribe("PATIENT_ARRIVED", self.handle_patient)

    async def handle_patient(self, patient: Dict[str, Any]):
        priority = classify_priority(patient)
        reasons = build_triage_reasons(patient, priority)
        factors = build_triage_factors(patient)
        wait = estimated_wait_time(priority)

        # Actualizar estado en el state manager
        patient["prioridad"] = priority
        patient["estado"] = "En_triaje"
        self.state_manager.update_patient_field(
            patient.get("id_paciente"), "prioridad", priority
        )
        self.state_manager.update_patient_field(
            patient.get("id_paciente"), "estado", "En_triaje"
        )

        self.state_manager.record_decision(
            patient_id=patient.get("id_paciente"),
            event="PATIENT_TRIAGED",
            agent=self.name,
            decision=priority,
            reason=" | ".join(reasons),
            source_data={
                "sintomas": patient.get("sintomas"),
                "vitales": patient.get("vitales"),
                "dolor": patient.get("dolor"),
            },
        )

        await self.event_bus.publish(
            "PATIENT_TRIAGED",
            {
                "patient": patient,
                "priority": priority,
                "reasons": reasons,
                "factors": factors,
                "estimated_time": wait,
                "timestamp": datetime.now().isoformat(),
            },
        )


# ─── ResourceAgent ──────────────────────────────────────────────────────────

class ResourceAgent(BaseAgent):
    def __init__(self, event_bus: Any, state_manager: Any):
        super().__init__("ResourceAgent", event_bus, state_manager)
        self.event_bus.subscribe("PATIENT_TRIAGED", self.allocate_resource)

    async def allocate_resource(self, data: Dict[str, Any]):
        patient = data["patient"]
        priority = data["priority"]
        bed = self.state_manager.allocate_resource(priority, patient)

        dept = patient.get("departamento_asignado", "Pendiente")
        bed_id = patient.get("bed_id") or (
            f"{dept[:3].upper()}-{random.randint(1,30):02d}" if bed else None
        )
        patient["bed_id"] = bed_id

        reason = (
            f"Cama {bed_id} asignada en {dept} por prioridad {priority}."
            if bed
            else "No se encontró recurso disponible; se generó alerta."
        )

        self.state_manager.update_patient_field(
            patient.get("id_paciente"), "estado", "Cama_asignada"
        )
        self.state_manager.update_patient_field(
            patient.get("id_paciente"), "cama", bed_id
        )

        self.state_manager.record_decision(
            patient_id=patient.get("id_paciente"),
            event="RESOURCE_ALLOCATED",
            agent=self.name,
            decision=bed or "NO_RESOURCE",
            reason=reason,
            source_data={"priority": priority},
        )

        await self.event_bus.publish(
            "RESOURCE_ALLOCATED",
            {
                "patient": patient,
                "priority": priority,
                "bed_type": bed,
                "bed_id": bed_id,
                "department": dept,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            },
        )


# ─── StaffAgent ─────────────────────────────────────────────────────────────

class StaffAgent(BaseAgent):
    def __init__(self, event_bus: Any, state_manager: Any):
        super().__init__("StaffAgent", event_bus, state_manager)
        self.event_bus.subscribe("RESOURCE_ALLOCATED", self.assign_staff)

    async def assign_staff(self, data: Dict[str, Any]):
        patient = data["patient"]
        priority = data["priority"]
        specialty = self.state_manager.select_staff_specialty(patient, priority)
        staff = self.state_manager.assign_staff(patient, specialty)

        decision = staff["id_empleado"] if staff else "NO_STAFF"
        reason = (
            f"Se asignó {staff['id_empleado']} (especialidad: {staff['especialidad']})."
            if staff
            else "No se encontró personal disponible."
        )

        # Buscar enfermero adicional
        nurse = self.state_manager.assign_nurse(patient)
        nurse_id = nurse["id_empleado"] if nurse else None

        self.state_manager.update_patient_field(
            patient.get("id_paciente"), "estado", "Personal_asignado"
        )

        self.state_manager.record_decision(
            patient_id=patient.get("id_paciente"),
            event="STAFF_ASSIGNED",
            agent=self.name,
            decision=decision,
            reason=reason,
            source_data={"specialty_requested": specialty},
        )

        await self.event_bus.publish(
            "STAFF_ASSIGNED",
            {
                "patient": patient,
                "staff": staff,
                "nurse": nurse,
                "medico_id": decision,
                "enfermero_id": nurse_id,
                "specialty": specialty,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            },
        )


# ─── ForecastAgent ──────────────────────────────────────────────────────────

class ForecastAgent(BaseAgent):
    def __init__(self, event_bus: Any, state_manager: Any):
        super().__init__("ForecastAgent", event_bus, state_manager)
        self.event_bus.subscribe("STAFF_ASSIGNED", self.forecast_load)

    async def forecast_load(self, data: Dict[str, Any]):
        icu_occupancy = self.state_manager.get_occupancy_percentage("ICU")
        emer_occupancy = self.state_manager.get_occupancy_percentage("EMERGENCY")

        forecast_payload = {
            "icu_occupancy": icu_occupancy,
            "emergency_occupancy": emer_occupancy,
            "timestamp": datetime.now().isoformat(),
            "patient_id": data["patient"].get("id_paciente"),
        }

        if detect_saturation(icu_occupancy):
            warning = f"Riesgo de saturación UCI: {icu_occupancy}%"
            self.state_manager.add_alert(warning)
            await self.event_bus.publish(
                "SATURATION_WARNING",
                {
                    "resource": "ICU",
                    "occupancy": icu_occupancy,
                    "warning": warning,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        await self.event_bus.publish("FORECAST_UPDATED", forecast_payload)


# ─── WorkflowAgent ──────────────────────────────────────────────────────────

class WorkflowAgent(BaseAgent):
    def __init__(self, event_bus: Any, state_manager: Any):
        super().__init__("WorkflowAgent", event_bus, state_manager)
        self.event_bus.subscribe("RESOURCE_ALLOCATED", self.optimize_workflow)

    async def optimize_workflow(self, data: Dict[str, Any]):
        state = self.state_manager.get_global_state()
        patient = data["patient"]

        waiting = state["waiting_patients"]
        emer_avail = state["resources"].get("EMERGENCY", {}).get("available", 99)

        if waiting > 8 or emer_avail < 3:
            action = "REDISTRIBUTION"
            reason = (
                "Congestión detectada en urgencias: se sugiere redistribuir camas."
            )
            self.state_manager.record_decision(
                patient_id=patient.get("id_paciente"),
                event="WORKFLOW_ALERT",
                agent=self.name,
                decision=action,
                reason=reason,
                source_data={"waiting_patients": waiting, "emergency_available": emer_avail},
            )
            await self.event_bus.publish(
                "WORKFLOW_ALERT",
                {
                    "patient": patient,
                    "action": action,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat(),
                },
            )


# ─── QualityAgent ───────────────────────────────────────────────────────────

class QualityAgent(BaseAgent):
    def __init__(self, event_bus: Any, state_manager: Any):
        super().__init__("QualityAgent", event_bus, state_manager)
        self.event_bus.subscribe("PATIENT_TRIAGED", self.validate_triage)
        self.event_bus.subscribe("RESOURCE_ALLOCATED", self.validate_allocation)
        self.event_bus.subscribe("STAFF_ASSIGNED", self.validate_staff)
        self.event_bus.subscribe("SATURATION_WARNING", self.handle_saturation)

    async def validate_triage(self, data: Dict[str, Any]):
        patient = data["patient"]
        if data["priority"] == "CRITICAL":
            self.state_manager.record_decision(
                patient_id=patient.get("id_paciente"),
                event="QUALITY_CHECK",
                agent=self.name,
                decision="TRIAGE_VALIDATED",
                reason="Paciente crítico verificado contra criterios de prioridad.",
                source_data={"triage": data},
            )

    async def validate_allocation(self, data: Dict[str, Any]):
        patient = data["patient"]
        if should_generate_critical_alert(data["priority"], data.get("bed_type")):
            alert = f"Paciente crítico {patient['id_paciente']} sin cama UCI disponible."
            self.state_manager.add_alert(alert)
            await self.event_bus.publish(
                "CRITICAL_ALERT",
                {
                    "message": alert,
                    "patient": patient,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    async def validate_staff(self, data: Dict[str, Any]):
        if not data.get("staff"):
            alert = f"No se pudo asignar personal al paciente {data['patient']['id_paciente']}"
            self.state_manager.add_alert(alert)

    async def handle_saturation(self, data: Dict[str, Any]):
        self.state_manager.record_decision(
            patient_id=data.get("patient_id"),
            event="QUALITY_CHECK",
            agent=self.name,
            decision="SATURATION_MONITORED",
            reason=f"Saturación del {data.get('occupancy')}% en UCI observada.",
            source_data={"forecast": data},
        )


# ─── OrchestratorAgent ──────────────────────────────────────────────────────

class OrchestratorAgent(BaseAgent):
    def __init__(self, event_bus: Any, state_manager: Any):
        super().__init__("OrchestratorAgent", event_bus, state_manager)
        for event_name in [
            "PATIENT_ARRIVED",
            "PATIENT_TRIAGED",
            "RESOURCE_ALLOCATED",
            "STAFF_ASSIGNED",
            "SATURATION_WARNING",
            "WORKFLOW_ALERT",
            "CRITICAL_ALERT",
            "FORECAST_UPDATED",
        ]:
            self.event_bus.subscribe(event_name, self.observe_flow)

    async def observe_flow(self, data: Dict[str, Any]):
        patient_id = None
        if isinstance(data, dict):
            patient_id = (
                data.get("patient", {}).get("id_paciente")
                or data.get("id_paciente")
                or data.get("patient_id")
            )

        self.state_manager.add_event(
            "ORCHESTRATOR_OBSERVATION",
            {
                "patient_id": patient_id,
                "message": f"Orquestador observó evento para paciente {patient_id}",
            },
        )
