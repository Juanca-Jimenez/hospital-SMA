import random
from datetime import datetime

from rules import (
    classify_priority,
    should_generate_critical_alert,
    detect_saturation,
)


# ==========================================================
# BASE AGENT
# ==========================================================

class BaseAgent:

    def __init__(self, name, event_bus):

        self.name = name

        self.event_bus = event_bus

        print(f"[AGENT INITIALIZED] {self.name}")


# ==========================================================
# TRIAGE AGENT
# ==========================================================

class TriageAgent(BaseAgent):

    def __init__(self, event_bus):

        super().__init__("TriageAgent", event_bus)

        self.event_bus.subscribe(
            "PATIENT_ARRIVED",
            self.handle_patient,
        )

    async def handle_patient(self, patient):

        priority = classify_priority(patient)

        print(
            f"[TRIAGE] Patient {patient['id_paciente']} "
            f"classified as {priority}"
        )

        await self.event_bus.publish(
            "PATIENT_TRIAGED",
            {
                "patient": patient,
                "priority": priority,
                "timestamp": str(datetime.now()),
            },
        )


# ==========================================================
# RESOURCE AGENT
# ==========================================================

class ResourceAgent(BaseAgent):

    def __init__(self, event_bus, state_manager):

        super().__init__("ResourceAgent", event_bus)

        self.state_manager = state_manager

        self.event_bus.subscribe(
            "PATIENT_TRIAGED",
            self.allocate_resource,
        )

    async def allocate_resource(self, data):

        patient = data["patient"]

        priority = data["priority"]

        bed = self.state_manager.allocate_resource(priority)

        if bed:

            print(
                f"[RESOURCE] Bed allocated to "
                f"{patient['id_paciente']} -> {bed}"
            )

        else:

            print(
                f"[RESOURCE] No beds available for "
                f"{patient['id_paciente']}"
            )

        await self.event_bus.publish(
            "RESOURCE_ALLOCATED",
            {
                "patient": patient,
                "priority": priority,
                "bed": bed,
                "timestamp": str(datetime.now()),
            },
        )


# ==========================================================
# STAFF AGENT
# ==========================================================

class StaffAgent(BaseAgent):

    def __init__(self, event_bus):

        super().__init__("StaffAgent", event_bus)

        self.event_bus.subscribe(
            "RESOURCE_ALLOCATED",
            self.assign_staff,
        )

    async def assign_staff(self, data):

        patient = data["patient"]

        assigned_staff = random.choice(
            [
                "Dr. Garcia",
                "Dr. Martinez",
                "Nurse Laura",
                "Dr. Ramirez",
            ]
        )

        print(
            f"[STAFF] {assigned_staff} assigned to "
            f"{patient['id_paciente']}"
        )

        await self.event_bus.publish(
            "STAFF_ASSIGNED",
            {
                "patient": patient,
                "staff": assigned_staff,
                "timestamp": str(datetime.now()),
            },
        )


# ==========================================================
# FORECAST AGENT
# ==========================================================

class ForecastAgent(BaseAgent):

    def __init__(self, event_bus, state_manager):

        super().__init__("ForecastAgent", event_bus)

        self.state_manager = state_manager

        self.event_bus.subscribe(
            "RESOURCE_ALLOCATED",
            self.forecast_load,
        )

    async def forecast_load(self, data):

        icu_occupancy = (
            self.state_manager.get_occupancy_percentage("ICU")
        )

        if detect_saturation(icu_occupancy):

            print(
                f"[FORECAST] ICU saturation risk -> "
                f"{icu_occupancy}%"
            )

            await self.event_bus.publish(
                "SATURATION_WARNING",
                {
                    "resource": "ICU",
                    "occupancy": icu_occupancy,
                    "timestamp": str(datetime.now()),
                },
            )


# ==========================================================
# WORKFLOW AGENT
# ==========================================================

class WorkflowAgent(BaseAgent):

    def __init__(self, event_bus):

        super().__init__("WorkflowAgent", event_bus)

        self.event_bus.subscribe(
            "PATIENT_TRIAGED",
            self.optimize_workflow,
        )

    async def optimize_workflow(self, data):

        priority = data["priority"]

        patient = data["patient"]

        if priority == "CRITICAL":

            print(
                f"[WORKFLOW] Critical fast-track activated "
                f"for {patient['id_paciente']}"
            )

            await self.event_bus.publish(
                "WORKFLOW_ALERT",
                {
                    "patient": patient,
                    "action": "FAST_TRACK",
                    "timestamp": str(datetime.now()),
                },
            )


# ==========================================================
# QUALITY AGENT
# ==========================================================

class QualityAgent(BaseAgent):

    def __init__(self, event_bus, state_manager):

        super().__init__("QualityAgent", event_bus)

        self.state_manager = state_manager

        self.event_bus.subscribe(
            "RESOURCE_ALLOCATED",
            self.monitor_quality,
        )

        self.event_bus.subscribe(
            "SATURATION_WARNING",
            self.handle_saturation,
        )

    async def monitor_quality(self, data):

        priority = data["priority"]

        bed = data["bed"]

        patient = data["patient"]

        critical_alert = (
            should_generate_critical_alert(
                priority,
                bed,
            )
        )

        if critical_alert:

            alert_message = (
                f"Critical patient without ICU: "
                f"{patient['id_paciente']}"
            )

            self.state_manager.add_alert(alert_message)

            print(f"[QUALITY ALERT] {alert_message}")

            await self.event_bus.publish(
                "CRITICAL_ALERT",
                {
                    "message": alert_message,
                    "timestamp": str(datetime.now()),
                },
            )

    async def handle_saturation(self, data):

        occupancy = data["occupancy"]

        print(
            f"[QUALITY] Saturation warning received -> "
            f"{occupancy}%"
        )


# ==========================================================
# ORCHESTRATOR AGENT
# ==========================================================

class OrchestratorAgent(BaseAgent):

    def __init__(self, event_bus):

        super().__init__("OrchestratorAgent", event_bus)

        self.event_bus.subscribe(
            "PATIENT_ARRIVED",
            self.observe_flow,
        )

    async def observe_flow(self, data):

        patient_id = data["id_paciente"]

        print(
            f"[ORCHESTRATOR] Monitoring patient flow -> "
            f"{patient_id}"
        )