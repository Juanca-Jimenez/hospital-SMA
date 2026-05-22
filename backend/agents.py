import random
from datetime import datetime
from typing import Any, Dict

from backend.rules import (
    classify_priority,
    detect_saturation,
    should_generate_critical_alert,
)


class BaseAgent:
    def __init__(self, name: str, event_bus: Any, state_manager: Any = None):
        self.name = name
        self.event_bus = event_bus
        self.state_manager = state_manager
        print(f"[AGENT INITIALIZED] {self.name}")


class TriageAgent(BaseAgent):
    def __init__(self, event_bus: Any, state_manager: Any):
        super().__init__("TriageAgent", event_bus, state_manager)
        self.event_bus.subscribe("PATIENT_ARRIVED", self.handle_patient)

    async def handle_patient(self, patient: Dict[str, Any]):
        priority = classify_priority(patient)
        reason = self._build_reason(patient, priority)

        self.state_manager.record_decision(
            patient_id=patient.get("id_paciente"),
            event="PATIENT_TRIAGED",
            agent=self.name,
            decision=priority,
            reason=reason,
            source_data={
                "sintomas": patient.get("sintomas"),
                "signos_vitales": patient.get("signos_vitales"),
            },
        )

        await self.event_bus.publish(
            "PATIENT_TRIAGED",
            {
                "patient": patient,
                "priority": priority,
                "reason": reason,
                "rules_applied": ["nivel_urgencia", "sintomas", "signos_vitales"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

    def _build_reason(self, patient: Dict[str, Any], priority: str) -> str:
        if priority == "CRITICAL":
            return "Nivel 1: paciente con signos críticos o urgencia máxima"
        if priority == "HIGH":
            return "Urgencia alta detectada por síntomas severos"
        return "Clasificación estándar basada en síntomas y urgencia"


class ResourceAgent(BaseAgent):
    def __init__(self, event_bus: Any, state_manager: Any):
        super().__init__("ResourceAgent", event_bus, state_manager)
        self.event_bus.subscribe("PATIENT_TRIAGED", self.allocate_resource)

    async def allocate_resource(self, data: Dict[str, Any]):
        patient = data["patient"]
        priority = data["priority"]
        bed = self.state_manager.allocate_resource(priority, patient)

        reason = (
            f"Asignado a {patient['departamento_asignado']} por prioridad {priority}."
            if bed
            else "No se encontró recurso disponible, se generó alerta."
        )

        self.state_manager.record_decision(
            patient_id=patient.get("id_paciente"),
            event="RESOURCE_ALLOCATED",
            agent=self.name,
            decision=bed or "NO_RESOURCE",
            reason=reason,
            source_data={
                "priority": priority,
                "available_resources": self.state_manager.resources,
            },
        )

        await self.event_bus.publish(
            "RESOURCE_ALLOCATED",
            {
                "patient": patient,
                "priority": priority,
                "bed": bed,
                "reason": reason,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )


class StaffAgent(BaseAgent):
    def __init__(self, event_bus: Any, state_manager: Any):
        super().__init__("StaffAgent", event_bus, state_manager)
        self.event_bus.subscribe("RESOURCE_ALLOCATED", self.assign_staff)

    async def assign_staff(self, data: Dict[str, Any]):
        patient = data["patient"]
        priority = data["priority"]
        specialty = self.state_manager.select_staff_specialty(patient, priority)
        staff = self.state_manager.assign_staff(patient, specialty)

        decision = staff["nombre"] if staff else "NO_STAFF"
        reason = (
            f"Se asignó {staff['nombre']} ({staff['especialidad']})."
            if staff
            else "No se encontró personal disponible."
        )

        self.state_manager.record_decision(
            patient_id=patient.get("id_paciente"),
            event="STAFF_ASSIGNED",
            agent=self.name,
            decision=decision,
            reason=reason,
            source_data={
                "specialty_requested": specialty,
                "available_staff": self.state_manager.get_available_staff(specialty),
            },
        )

        await self.event_bus.publish(
            "STAFF_ASSIGNED",
            {
                "patient": patient,
                "staff": staff,
                "specialty": specialty,
                "reason": reason,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )


class ForecastAgent(BaseAgent):
    def __init__(self, event_bus: Any, state_manager: Any):
        super().__init__("ForecastAgent", event_bus, state_manager)
        self.event_bus.subscribe("RESOURCE_ALLOCATED", self.forecast_load)

    async def forecast_load(self, data: Dict[str, Any]):
        icu_occupancy = self.state_manager.get_occupancy_percentage("ICU")
        if detect_saturation(icu_occupancy):
            warning = f"Riesgo de saturación UCI: {icu_occupancy}%"
            self.state_manager.record_decision(
                patient_id=data["patient"].get("id_paciente"),
                event="SATURATION_WARNING",
                agent=self.name,
                decision="SATURATION_WARNING",
                reason=warning,
                source_data={
                    "icu_occupancy": icu_occupancy,
                    "historic_metrics": self.state_manager.historic_metrics[:3],
                },
            )

            await self.event_bus.publish(
                "SATURATION_WARNING",
                {
                    "resource": "ICU",
                    "occupancy": icu_occupancy,
                    "warning": warning,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            )


class WorkflowAgent(BaseAgent):
    def __init__(self, event_bus: Any, state_manager: Any):
        super().__init__("WorkflowAgent", event_bus, state_manager)
        self.event_bus.subscribe("RESOURCE_ALLOCATED", self.optimize_workflow)

    async def optimize_workflow(self, data: Dict[str, Any]):
        state = self.state_manager.get_global_state()
        patient = data["patient"]

        if state["waiting_patients"] > 8 or state["resources"].get("EMERGENCY", {}).get("available", 0) < 3:
            action = "REDISTRIBUTION"
            reason = (
                "Se detectó congestión en urgencias y pacientes en espera; se sugiere redistribuir camas."
            )
            self.state_manager.record_decision(
                patient_id=patient.get("id_paciente"),
                event="WORKFLOW_ALERT",
                agent=self.name,
                decision=action,
                reason=reason,
                source_data={
                    "waiting_patients": state["waiting_patients"],
                    "emergency_available": state["resources"].get("EMERGENCY", {}).get("available", 0),
                },
            )

            await self.event_bus.publish(
                "WORKFLOW_ALERT",
                {
                    "patient": patient,
                    "action": action,
                    "reason": reason,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            )


class QualityAgent(BaseAgent):
    def __init__(self, event_bus: Any, state_manager: Any):
        super().__init__("QualityAgent", event_bus, state_manager)
        self.event_bus.subscribe("PATIENT_TRIAGED", self.validate_triage)
        self.event_bus.subscribe("RESOURCE_ALLOCATED", self.validate_allocation)
        self.event_bus.subscribe("STAFF_ASSIGNED", self.validate_staff)
        self.event_bus.subscribe("SATURATION_WARNING", self.handle_saturation)

    async def validate_triage(self, data: Dict[str, Any]):
        patient = data["patient"]
        if data["priority"] == "CRITICAL" and patient.get("id_paciente"):
            self.state_manager.record_decision(
                patient_id=patient.get("id_paciente"),
                event="QUALITY_CHECK",
                agent=self.name,
                decision="TRIAGE_VALIDATED",
                reason="Pacientes críticos verificados contra criterios de prioridad.",
                source_data={"triage": data},
            )

    async def validate_allocation(self, data: Dict[str, Any]):
        patient = data["patient"]
        if should_generate_critical_alert(data["priority"], data["bed"]):
            alert = f"Paciente crítico {patient['id_paciente']} sin cama UCI disponible."
            self.state_manager.add_alert(alert)
            await self.event_bus.publish(
                "CRITICAL_ALERT",
                {
                    "message": alert,
                    "patient": patient,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            )

    async def validate_staff(self, data: Dict[str, Any]):
        if not data.get("staff"):
            alert = f"No se pudo asignar personal al paciente {data['patient']['id_paciente']}"
            self.state_manager.add_alert(alert)

    async def handle_saturation(self, data: Dict[str, Any]):
        self.state_manager.record_decision(
            patient_id=data.get("patient", {}).get("id_paciente"),
            event="QUALITY_CHECK",
            agent=self.name,
            decision="SATURATION_MONITORED",
            reason=f"Observada saturación del {data.get('occupancy')}% en UCI.",
            source_data={"forecast": data},
        )


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
        ]:
            self.event_bus.subscribe(event_name, self.observe_flow)

    async def observe_flow(self, data: Dict[str, Any]):
        patient_id = None
        if isinstance(data, dict):
            patient_id = data.get("patient", {}).get("id_paciente") or data.get("id_paciente")

        self.state_manager.add_event(
            "ORCHESTRATOR_OBSERVATION",
            {
                "patient_id": patient_id,
                "message": f"Orquestador observó evento para paciente {patient_id}",
            },
        )
