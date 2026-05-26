# verify_redesign.py
import sys
from pathlib import Path

# Agregar backend al path
sys.path.append(str(Path(__file__).resolve().parent))

from backend.state_manager import HospitalStateManager

def run_tests():
    print("====================================================================")
    print("INICIANDO PRUEBAS DE VERIFICACIÓN DEL REDISEÑO DE STATE_MANAGER")
    print("====================================================================\n")

    # Iniciar StateManager
    sm = HospitalStateManager()

    # 1. CASO LEVE -> CONSULTATION
    # painLevel <= 4, oxygen >= 95, LOW urgency, no critical symptoms, no severe diagnosis
    leve = {
        "id": "P-LEVE",
        "edad": 30,
        "dolor": 3,
        "prioridad": "LOW",
        "spo2": 98.0,
        "temperatura": 37.2,
        "frecuencia": 75,
        "presion": {"sistolica": 115, "diastolica": 75},
        "sintomas": ["Tos", "Cansancio"],
        "motivo_consulta": "Gripe y control",
        "movilidad": "NORMAL",
        "conciencia": "NORMAL",
        "estado": "REGISTERED"
    }
    res_leve = sm.determine_clinical_area(leve)
    assert res_leve["newState"] == "CONSULTATION", f"Fallo Caso Leve: {res_leve['newState']}"
    print("OK - Caso Leve asignado a CONSULTATION correctamente!")
    print(f"  Score: {res_leve['priorityScore']} | Justificaciones: {res_leve['justification']}")
    print(f"  Explicacion: {res_leve['explanation']}\n")

    # 2. CASO MODERADO -> OBSERVATION
    # edad > 65, dolor moderado
    moderado = {
        "id": "P-MODERADO",
        "edad": 72,
        "dolor": 6,
        "prioridad": "MEDIUM",
        "spo2": 93.0,
        "temperatura": 38.4,
        "frecuencia": 95,
        "presion": {"sistolica": 135, "diastolica": 85},
        "sintomas": ["Dolor abdominal", "Nauseas"],
        "motivo_consulta": "Dolor abdominal agudo",
        "movilidad": "REDUCED",
        "conciencia": "NORMAL",
        "estado": "REGISTERED"
    }
    res_mod = sm.determine_clinical_area(moderado)
    assert res_mod["newState"] == "OBSERVATION", f"Fallo Caso Moderado: {res_mod['newState']}"
    print("OK - Caso Moderado asignado a OBSERVATION correctamente!")
    print(f"  Score: {res_mod['priorityScore']} | Justificaciones: {res_mod['justification']}")
    print(f"  Explicacion: {res_mod['explanation']}\n")

    # 3. CASO SERIO -> HOSPITALIZATION
    # painLevel >= 7, urgency == HIGH
    serio = {
        "id": "P-SERIO",
        "edad": 45,
        "dolor": 8,
        "prioridad": "HIGH",
        "spo2": 92.0,
        "temperatura": 38.9,
        "frecuencia": 105,
        "presion": {"sistolica": 145, "diastolica": 90},
        "sintomas": ["Fiebre", "Dificultad respiratoria"],
        "motivo_consulta": "Neumonia grave",
        "movilidad": "REDUCED",
        "conciencia": "NORMAL",
        "estado": "REGISTERED"
    }
    res_serio = sm.determine_clinical_area(serio)
    assert res_serio["newState"] == "HOSPITALIZATION", f"Fallo Caso Serio: {res_serio['newState']}"
    print("OK - Caso Serio asignado a HOSPITALIZATION correctamente!")
    print(f"  Score: {res_serio['priorityScore']} | Justificaciones: {res_serio['justification']}")
    print(f"  Explicacion: {res_serio['explanation']}\n")

    # 4. CASO CRITICO -> ICU
    # urgency == CRITICAL, oxygen < 90, consciousness alterada, dolor >= 9, etc.
    critico = {
        "id": "P-CRITICO",
        "edad": 55,
        "dolor": 9,
        "prioridad": "CRITICAL",
        "spo2": 88.0,
        "temperatura": 39.5,
        "frecuencia": 145,
        "presion": {"sistolica": 85, "diastolica": 45},
        "sintomas": ["Dificultad respiratoria", "Perdida conciencia"],
        "motivo_consulta": "Sepsis y falla multiorganica",
        "movilidad": "NONE",
        "conciencia": "ALTERED",
        "estado": "TRIAGED"  # Pasa por triage previo
    }
    res_critico = sm.determine_clinical_area(critico)
    assert res_critico["newState"] == "ICU", f"Fallo Caso Critico: {res_critico['newState']}"
    print("OK - Caso Critico asignado a ICU correctamente!")
    print(f"  Score: {res_critico['priorityScore']} | Justificaciones: {res_critico['justification']}")
    print(f"  Explicacion: {res_critico['explanation']}\n")

    # 5. CASO ANTI-UCI
    # painLevel < 7 Y urgencyLevel != CRITICAL -> PROHIBIDO ICU
    # En este caso, daremos un score alto (>13) pero con dolor < 7 y urgencia no critica (HIGH)
    anti_uci = {
        "id": "P-ANTI-UCI",
        "edad": 70,       # +2
        "dolor": 6,       # +2 (dolor < 7)
        "prioridad": "HIGH", # +4 (no CRITICAL)
        "spo2": 88.0,     # +5
        "temperatura": 39.2, # +2
        # score = 2+2+5+4+2 = 15 (sugeriria UCI por score, pero prohibido por politica anti-UCI!)
        "frecuencia": 120,
        "presion": {"sistolica": 110, "diastolica": 70},
        "sintomas": ["Tos", "Fiebre"],
        "motivo_consulta": "Infeccion respiratoria aguda",
        "movilidad": "NORMAL",
        "conciencia": "NORMAL",
        "estado": "TRIAGED"
    }
    res_anti = sm.determine_clinical_area(anti_uci)
    assert res_anti["newState"] in ["HOSPITALIZATION", "OBSERVATION"], f"Fallo Caso Anti-UCI: {res_anti['newState']}"
    assert res_anti["newState"] != "ICU", "Caso Anti-UCI fue enviado a UCI!"
    print("OK - Regla Anti-UCI validada correctamente!")
    print(f"  Puntaje calculado: {res_anti['priorityScore']} (Sugeriria UCI por puntaje)")
    print(f"  Area clinica redirigida: {res_anti['newState']}")
    print(f"  Justificaciones: {res_anti['justification']}")
    print(f"  Explicacion: {res_anti['explanation']}\n")

    # 6. MAQUINA DE ESTADOS: TRANSICION PROHIBIDA (CONSULTATION -> ICU)
    # Paciente con estado previo CONSULTATION que se intenta enviar a ICU
    transicion_prohibida = {
        "id": "P-TRANSICION",
        "edad": 55,
        "dolor": 9,
        "prioridad": "CRITICAL",
        "spo2": 88.0,
        "temperatura": 39.5,
        "frecuencia": 145,
        "presion": {"sistolica": 85, "diastolica": 45},
        "sintomas": ["Dificultad respiratoria", "Perdida conciencia"],
        "motivo_consulta": "Sepsis",
        "movilidad": "NONE",
        "conciencia": "ALTERED",
        "estado": "CONSULTATION" # Estado previo
    }
    res_trans = sm.determine_clinical_area(transicion_prohibida)
    assert res_trans["newState"] != "ICU", "Transicion invalida CONSULTATION -> ICU fue permitida!"
    print("OK - Transicion Prohibida Maquina de Estados validada correctamente!")
    print(f"  Estado previo: {res_trans['previousState']} | Estado asignado: {res_trans['newState']}")
    print(f"  Justificaciones: {res_trans['justification']}")
    print(f"  Explicacion: {res_trans['explanation']}\n")

    print("====================================================================")
    print("TODAS LAS PRUEBAS CLINICAS PASARON EXITOSAMENTE OK")
    print("====================================================================")

if __name__ == "__main__":
    run_tests()
