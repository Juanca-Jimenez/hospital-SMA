from typing import Dict, List


class HospitalStateManager:
    """
    Single Source of Truth del hospital.
    Mantiene el estado global operativo.
    """

    def __init__(self):

        # =========================
        # RECURSOS
        # =========================

        self.resources = {
            "ICU": {
                "total": 10,
                "available": 10,
            },

            "GENERAL": {
                "total": 50,
                "available": 50,
            },

            "SURGERY": {
                "total": 5,
                "available": 5,
            }
        }

        # =========================
        # PERSONAL
        # =========================

        self.staff = []

        # =========================
        # PACIENTES
        # =========================

        self.active_patients: List[Dict] = []

        self.waiting_patients: List[Dict] = []

        self.discharged_patients: List[Dict] = []

        # =========================
        # MÉTRICAS
        # =========================

        self.total_admissions = 0

        self.total_discharges = 0

        self.alerts = []

    # ==================================================
    # PACIENTES
    # ==================================================

    def add_patient(self, patient: Dict):

        self.active_patients.append(patient)

        self.total_admissions += 1

        print(f"[STATE] Patient added -> {patient['id_paciente']}")

    def discharge_patient(self, patient_id: str):

        patient_to_remove = None

        for patient in self.active_patients:

            if patient["id_paciente"] == patient_id:
                patient_to_remove = patient
                break

        if patient_to_remove:

            self.active_patients.remove(patient_to_remove)

            self.discharged_patients.append(patient_to_remove)

            self.total_discharges += 1

            print(f"[STATE] Patient discharged -> {patient_id}")

    # ==================================================
    # RECURSOS
    # ==================================================

    def allocate_resource(self, priority: str):

        """
        Asigna cama según prioridad.
        """

        if priority == "CRITICAL":

            if self.resources["ICU"]["available"] > 0:

                self.resources["ICU"]["available"] -= 1

                print("[STATE] ICU bed allocated")

                return "ICU"

            return None

        if self.resources["GENERAL"]["available"] > 0:

            self.resources["GENERAL"]["available"] -= 1

            print("[STATE] General bed allocated")

            return "GENERAL"

        return None

    def release_resource(self, resource_type: str):

        if resource_type in self.resources:

            self.resources[resource_type]["available"] += 1

            print(f"[STATE] Resource released -> {resource_type}")

    # ==================================================
    # ALERTAS
    # ==================================================

    def add_alert(self, alert_message: str):

        self.alerts.append(alert_message)

        print(f"[ALERT] {alert_message}")

    # ==================================================
    # MÉTRICAS
    # ==================================================

    def get_occupancy_percentage(self, resource_type: str):

        resource = self.resources[resource_type]

        occupied = (
            resource["total"] - resource["available"]
        )

        percentage = (
            occupied / resource["total"]
        ) * 100

        return round(percentage, 2)

    def get_global_state(self):

        return {
            "resources": self.resources,

            "active_patients": len(self.active_patients),

            "waiting_patients": len(self.waiting_patients),

            "discharged_patients": len(self.discharged_patients),

            "total_admissions": self.total_admissions,

            "total_discharges": self.total_discharges,

            "alerts": self.alerts,
        }