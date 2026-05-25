"""
Reglas clínicas y operacionales del sistema.
Soporta el nuevo payload clínico con vitales estructurados,
sintomas como array, dolor y motivo_consulta.
"""

from typing import Any, Dict, List


# ─── Helpers ───────────────────────────────────────────────────────────────

def _get_spo2(patient: Dict[str, Any]) -> float:
    """Extrae SpO2 del payload nuevo (vitales.spo2) o del campo legado."""
    vitales = patient.get("vitales") or {}
    if isinstance(vitales, dict):
        v = vitales.get("spo2")
        if v is not None:
            return float(v)
    # fallback campo legacy
    raw = str(patient.get("signos_vitales", "")).lower()
    for token in raw.replace(",", " ").split():
        try:
            val = float(token)
            if 50 < val <= 100:
                return val
        except ValueError:
            pass
    return 99.0


def _get_fc(patient: Dict[str, Any]) -> float:
    vitales = patient.get("vitales") or {}
    if isinstance(vitales, dict):
        v = vitales.get("frecuencia")
        if v is not None:
            return float(v)
    return 80.0


def _get_presion_sistolica(patient: Dict[str, Any]) -> float:
    vitales = patient.get("vitales") or {}
    if isinstance(vitales, dict):
        presion = vitales.get("presion") or {}
        if isinstance(presion, dict):
            v = presion.get("sistolica")
            if v is not None:
                return float(v)
    return 120.0


def _get_temperatura(patient: Dict[str, Any]) -> float:
    vitales = patient.get("vitales") or {}
    if isinstance(vitales, dict):
        v = vitales.get("temperatura")
        if v is not None:
            return float(v)
    return 37.0


def _get_dolor(patient: Dict[str, Any]) -> int:
    return int(patient.get("dolor", 0))


def _get_edad(patient: Dict[str, Any]) -> int:
    return int(patient.get("edad", 0))


def _get_sintomas(patient: Dict[str, Any]) -> List[str]:
    s = patient.get("sintomas", [])
    if isinstance(s, list):
        return [x.lower() for x in s]
    return str(s).lower().split(",")


def _get_motivo(patient: Dict[str, Any]) -> str:
    return str(patient.get("motivo_consulta", "")).lower()


# ─── Clasificación de prioridad (nueva lógica clínica) ────────────────────

def classify_priority(patient: Dict[str, Any]) -> str:
    """
    Clasifica prioridad usando el payload clínico estructurado.
    Retorna: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'NORMAL'
    Compatible con payload legado (nivel_urgencia).
    """
    reasons = []

    # ── Compat. legado ──────────────────────────────────────────────────
    urgencia_legacy = patient.get("nivel_urgencia")
    if urgencia_legacy is not None:
        urgencia_legacy = int(urgencia_legacy)
        if urgencia_legacy == 1:
            return "CRITICAL"
        if urgencia_legacy == 2:
            return "HIGH"

    # ── Signos vitales ──────────────────────────────────────────────────
    spo2 = _get_spo2(patient)
    fc = _get_fc(patient)
    sistolica = _get_presion_sistolica(patient)
    temp = _get_temperatura(patient)
    dolor = _get_dolor(patient)
    edad = _get_edad(patient)
    sintomas = _get_sintomas(patient)
    motivo = _get_motivo(patient)

    # CRÍTICO
    if spo2 < 85:
        reasons.append(f"SpO₂ crítica ({spo2}%)")
    if fc < 40 or fc > 170:
        reasons.append(f"FC fuera de rango ({fc} lpm)")
    if sistolica < 85 or sistolica > 200:
        reasons.append(f"PA crítica ({sistolica} mmHg)")
    if temp > 40.5 or temp < 35:
        reasons.append(f"Temperatura crítica ({temp}°C)")
    if dolor >= 9:
        reasons.append(f"Dolor máximo ({dolor}/10)")
    if "pérdida conciencia" in sintomas:
        reasons.append("Pérdida de conciencia")
    if "fractura" in sintomas and dolor >= 7:
        reasons.append("Fractura con dolor severo")

    if len(reasons) >= 2:
        return "CRITICAL"
    if reasons:
        # Un solo factor crítico aislado → HIGH
        pass

    # ALTA
    high_flags = []
    if spo2 < 92:
        high_flags.append(f"SpO₂ baja ({spo2}%)")
    if dolor >= 7:
        high_flags.append(f"Dolor intenso ({dolor}/10)")
    if "dolor torácico" in sintomas or "dificultad respiratoria" in sintomas:
        high_flags.append("Síntoma cardiaco/respiratorio")
    if edad >= 70:
        high_flags.append(f"Edad avanzada ({edad} años)")
    if motivo in ("neurológico", "trauma"):
        high_flags.append(f"Motivo {motivo}")
    if fc > 140 or fc < 50:
        high_flags.append(f"FC alterada ({fc})")
    if temp > 39.5:
        high_flags.append(f"Fiebre alta ({temp}°C)")

    all_flags = reasons + high_flags
    if len(all_flags) >= 2:
        if reasons:
            return "CRITICAL"
        return "HIGH"
    if all_flags:
        return "HIGH"

    # MEDIUM
    medium_flags = []
    if spo2 < 95:
        medium_flags.append("SpO₂ levemente baja")
    if dolor >= 5:
        medium_flags.append("Dolor moderado")
    if temp > 38.5:
        medium_flags.append("Fiebre moderada")
    if "mareo" in sintomas or "náuseas" in sintomas:
        medium_flags.append("Síntomas moderados")
    if edad >= 60:
        medium_flags.append("Edad de riesgo")

    if medium_flags:
        return "MEDIUM"

    return "NORMAL"


def build_triage_reasons(patient: Dict[str, Any], priority: str) -> List[str]:
    """Devuelve lista de razones clínicas para la clasificación."""
    reasons = []
    spo2 = _get_spo2(patient)
    fc = _get_fc(patient)
    sistolica = _get_presion_sistolica(patient)
    temp = _get_temperatura(patient)
    dolor = _get_dolor(patient)
    edad = _get_edad(patient)
    sintomas = _get_sintomas(patient)
    motivo = _get_motivo(patient)

    if spo2 < 92:
        reasons.append(f"SpO₂ baja: {spo2}%")
    if fc > 130 or fc < 50:
        reasons.append(f"Frecuencia cardiaca anormal: {fc} lpm")
    if sistolica > 180 or sistolica < 90:
        reasons.append(f"Presión arterial anormal: {sistolica} mmHg")
    if temp > 39.0:
        reasons.append(f"Fiebre: {temp}°C")
    elif temp < 36.0:
        reasons.append(f"Hipotermia: {temp}°C")
    if dolor >= 7:
        reasons.append(f"Dolor severo: {dolor}/10")
    if edad >= 70:
        reasons.append(f"Paciente mayor: {edad} años")
    if "dolor torácico" in sintomas:
        reasons.append("Dolor torácico presente")
    if "dificultad respiratoria" in sintomas:
        reasons.append("Dificultad respiratoria")
    if "pérdida conciencia" in sintomas:
        reasons.append("Pérdida de conciencia")
    if "fractura" in sintomas:
        reasons.append("Fractura reportada")
    if motivo in ("neurológico", "trauma", "respiratorio"):
        reasons.append(f"Motivo de consulta: {motivo.capitalize()}")

    if not reasons:
        if priority == "NORMAL" or priority == "MEDIUM":
            reasons.append("Signos vitales dentro de rangos normales")
            reasons.append(f"Dolor tolerable ({dolor}/10)")

    return reasons


def build_triage_factors(patient: Dict[str, Any]) -> List[str]:
    """Factores evaluados durante el triaje."""
    factors = ["Edad", "Síntomas", "Signos vitales", "Disponibilidad hospitalaria"]
    if patient.get("motivo_consulta"):
        factors.insert(1, "Motivo de consulta")
    if patient.get("dolor", 0) >= 5:
        factors.append("Escala de dolor")
    return factors


def estimated_wait_time(priority: str) -> str:
    times = {
        "CRITICAL": "Inmediato",
        "HIGH": "< 15 min",
        "MEDIUM": "15–30 min",
        "NORMAL": "30–60 min",
    }
    return times.get(priority, "A definir")


# ─── Alertas ───────────────────────────────────────────────────────────────

def should_generate_critical_alert(priority: str, bed) -> bool:
    return priority == "CRITICAL" and bed is None


def detect_saturation(occupancy_percentage: float) -> bool:
    return occupancy_percentage >= 90


def staff_fatigue(hours_worked: float) -> bool:
    return hours_worked >= 12