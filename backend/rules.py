"""
Reglas clínicas y operacionales del sistema.
Aquí vive la lógica de decisión.
"""


def classify_priority(patient):

    urgency = int(patient["nivel_urgencia"])

    symptoms = str(patient["sintomas"]).lower()

    vital_signs = str(patient.get("signos_vitales", "")).lower()

    # =====================================
    # NIVEL 1 -> CRÍTICO
    # =====================================

    if urgency == 1:
        return "CRITICAL"

    # =====================================
    # SÍNTOMAS GRAVES
    # =====================================

    critical_keywords = [
        "paro",
        "infarto",
        "convuls",
        "shock",
        "hemorrag",
        "insuficiencia respiratoria",
    ]

    for keyword in critical_keywords:

        if keyword in symptoms:
            return "CRITICAL"

    # =====================================
    # SIGNOS VITALES CRÍTICOS
    # =====================================

    if "spo2" in vital_signs:

        if "70" in vital_signs or "75" in vital_signs:
            return "CRITICAL"

    # =====================================
    # ALTA PRIORIDAD
    # =====================================

    high_keywords = [
        "dolor toracico",
        "fractura",
        "fiebre alta",
        "dificultad respiratoria",
    ]

    for keyword in high_keywords:

        if keyword in symptoms:
            return "HIGH"

    # =====================================
    # PRIORIDAD NORMAL
    # =====================================

    return "NORMAL"


# ==========================================================
# REGLAS DE ALERTAS
# ==========================================================

def should_generate_critical_alert(priority, bed):

    if priority == "CRITICAL" and bed is None:
        return True

    return False


# ==========================================================
# REGLAS DE SATURACIÓN
# ==========================================================

def detect_saturation(occupancy_percentage):

    if occupancy_percentage >= 90:
        return True

    return False


# ==========================================================
# REGLAS DE PERSONAL
# ==========================================================

def staff_fatigue(hours_worked):

    if hours_worked >= 12:
        return True

    return False