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
        Soporta de manera cruzada y simultánea llaves en español e inglés.
        Genera un objeto estandarizado y mantiene llaves en ambos idiomas.
        """
        p = dict(patient)

        # 1. ID del paciente
        pid = str(p.get("id") or p.get("patientId") or p.get("id_paciente") or "").strip()
        p["id"] = p["patientId"] = p["id_paciente"] = pid

        # 2. Edad
        age = p.get("age")
        if age is None:
            age = p.get("edad")
        p["age"] = p["edad"] = int(age) if age is not None and str(age).isdigit() else 0

        # 3. Dolor
        pain = p.get("painLevel")
        if pain is None:
            pain = p.get("dolor")
        p["painLevel"] = p["dolor"] = int(pain) if pain is not None else 0

        # 4. Urgencia / Prioridad
        urg = p.get("urgencyLevel") or p.get("prioridad") or p.get("nivel_urgencia")
        if isinstance(urg, int) or (isinstance(urg, str) and urg.isdigit()):
            val = int(urg)
            if val == 1:
                urg = "CRITICAL"
            elif val == 2:
                urg = "HIGH"
            elif val == 3:
                urg = "MEDIUM"
            else:
                urg = "LOW"
        elif isinstance(urg, str):
            urg = urg.strip().upper()
            if urg == "NORMAL":
                urg = "LOW"
        else:
            urg = "LOW"
        
        p["urgencyLevel"] = p["prioridad"] = p["nivel_urgencia"] = urg

        # 5. Oxígeno (SpO2)
        vitales = p.get("vitales") or {}
        if isinstance(vitales, str):
            try:
                vitales = json.loads(vitales)
            except Exception:
                vitales = {}
        
        o2 = p.get("oxygen") or p.get("spo2") or vitales.get("spo2")
        if o2 is None:
            raw = str(p.get("signos_vitales", "")).lower()
            for token in raw.replace(",", " ").split():
                try:
                    val = float(token)
                    if 50 < val <= 100:
                        o2 = val
                        break
                except ValueError:
                    pass
        if o2 is None:
            o2 = 99.0
        p["oxygen"] = p["spo2"] = float(o2)

        # 6. Temperatura
        temp = p.get("temperature") or p.get("temperatura") or vitales.get("temperatura")
        if temp is None:
            temp = 37.0
        p["temperature"] = p["temperatura"] = float(temp)

        # 7. Frecuencia cardiaca
        hr = p.get("heartRate") or p.get("frecuencia") or vitales.get("frecuencia")
        if hr is None:
            hr = 80.0
        p["heartRate"] = p["frecuencia"] = float(hr)

        # 8. Presión arterial
        press_raw = p.get("pressure") or p.get("presion") or vitales.get("presion") or {}
        sis, dia = 120, 80
        if isinstance(press_raw, dict):
            sis = press_raw.get("sistolica") or press_raw.get("systolic") or 120
            dia = press_raw.get("diastolica") or press_raw.get("diastolic") or 80
        elif isinstance(press_raw, str) and "/" in press_raw:
            try:
                parts = press_raw.split("/")
                sis = int(parts[0].strip())
                dia = int(parts[1].strip())
            except Exception:
                pass
        
        press_dict = {"sistolica": int(sis), "diastolica": int(dia)}
        p["pressure"] = p["presion"] = press_dict

        # Estructura vitales estructurada para compatibilidad
        p["vitales"] = {
            "presion": press_dict,
            "temperatura": p["temperature"],
            "frecuencia": p["heartRate"],
            "spo2": p["oxygen"]
        }

        # 9. Síntomas
        sint = p.get("symptoms") or p.get("sintomas") or []
        if isinstance(sint, str):
            sint = [s.strip() for s in sint.split(",") if s.strip()]
        elif not isinstance(sint, list):
            sint = []
        p["symptoms"] = p["sintomas"] = [str(s).strip() for s in sint]

        # 10. Motivo de consulta
        motivo = p.get("motivo_consulta") or p.get("diagnosis") or p.get("diagnostico") or "Consulta general"
        p["motivo_consulta"] = p["diagnosis"] = str(motivo).strip()

        # 11. Movilidad y conciencia (valores por defecto)
        p["mobility"] = p.get("mobility", "NORMAL")
        p["consciousness"] = p.get("consciousness", "NORMAL")

        # 12. Estado
        state = p.get("state") or p.get("estado") or "REGISTERED"
        prev = p.get("previousState") or p.get("estado_previo") or state
        p["state"] = p["estado"] = state
        p["previousState"] = p["estado_previo"] = prev

        # 13. Asignaciones
        p["departamento"] = p.get("departamento") or "Pendiente"
        p["medico_asignado"] = p.get("medico_asignado") or None
        p["enfermero_asignado"] = p.get("enfermero_asignado") or None
        p["bed_type"] = p.get("bed_type") or None
        p["cama"] = p.get("cama") or None

        return p

    def calculate_priority_score(self, patient: Dict[str, Any]) -> int:
        """
        Calcula el puntaje de apoyo clínico (no decide por sí mismo).
        """
        score = 0
        p = self._normalize_patient(patient)
        
        # Dolor
        dolor = p.get("painLevel", 0)
        if 0 <= dolor <= 2:
            score += 0
        elif 3 <= dolor <= 4:
            score += 1
        elif 5 <= dolor <= 6:
            score += 2
        elif 7 <= dolor <= 8:
            score += 4
        elif 9 <= dolor <= 10:
            score += 6
            
        # Edad
        edad = p.get("age", 0)
        if edad < 18:
            score += 1
        elif 18 <= edad <= 65:
            score += 0
        else: # > 65
            score += 2
            
        # Oxígeno
        o2 = p.get("oxygen", 99.0)
        if o2 >= 95.0:
            score += 0
        elif 90.0 <= o2 <= 94.0:
            score += 2
        else:
            score += 5
            
        # Urgencia
        urg = p.get("urgencyLevel", "LOW")
        if urg == "LOW":
            score += 0
        elif urg == "MEDIUM":
            score += 2
        elif urg == "HIGH":
            score += 4
        elif urg == "CRITICAL":
            score += 7
            
        # Temperatura
        temp = p.get("temperature", 37.0)
        if temp < 38.0:
            score += 0
        elif 38.0 <= temp <= 39.0:
            score += 1
        else:
            score += 2
            
        return score

    def evaluate_clinical_conditions(self, patient: Dict[str, Any]) -> int:
        """
        Evalúa criticidad clínica basada en los 5 pilares médicos.
        Retorna la cantidad de condiciones críticas encontradas.
        """
        p = self._normalize_patient(patient)
        critical_count = 0
        sintomas = [s.lower() for s in p.get("symptoms", [])]
        diag = str(p.get("diagnosis", "")).lower()
        
        # A. Respiración comprometida
        if p.get("oxygen", 99.0) < 90.0 or "dificultad respiratoria" in sintomas:
            critical_count += 1
            
        # B. Estado neurológico
        if (p.get("consciousness") == "ALTERED" or 
            "pérdida conciencia" in sintomas or 
            "confusion severa" in sintomas or
            "confusión severa" in sintomas):
            critical_count += 1
            
        # C. Inestabilidad hemodinámica
        presion = p.get("pressure", {})
        sis = presion.get("sistolica", 120)
        dia = presion.get("diastolica", 80)
        hr = p.get("heartRate", 80)
        if sis < 90 or sis > 180 or dia < 50 or dia > 110 or hr > 140 or hr < 45:
            critical_count += 1
            
        # D. Dolor extremo
        if p.get("painLevel", 0) >= 9:
            critical_count += 1
            
        # E. Diagnóstico severo
        diagnosticos_severos = ["neumonía grave", "pneumonia", "trauma severo", "sepsis", "falla respiratoria", "shock", "insuficiencia respiratoria"]
        if any(d in diag for d in diagnosticos_severos) or "fractura" in sintomas:
            critical_count += 1
            
        return critical_count

    def determine_clinical_area(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decisión clínica central del flujo hospitalario considerando múltiples variables.
        Aplica reglas clínicas reales, score de apoyo, regla anti-UCI y validación de transiciones.
        Retorna el payload obligatorio esperado por la especificación.
        Incluye detección de Cirugía y mejora de Consulta Externa.
        """
        p = self._normalize_patient(patient)
        
        # Score clínico de apoyo
        score = self.calculate_priority_score(p)
        critical_count = self.evaluate_clinical_conditions(p)
        
        # Variables locales
        pain = p.get("painLevel", 0)
        urg = p.get("urgencyLevel", "LOW")
        o2 = p.get("oxygen", 99.0)
        temp = p.get("temperature", 37.0)
        sintomas = [s.lower() for s in p.get("symptoms", [])]
        motivo = str(p.get("motivo_consulta", "")).lower()
        diag = str(p.get("diagnosis", "")).lower()
        consciousness = p.get("consciousness", "NORMAL")
        
        # --- CRITERIOS PARA CIRUGÍA (patología quirúrgica) ---
        palabras_cirugia = [
            "apendicitis", "colecistitis", "apendice", "vesicula", "hernia",
            "quirurgico", "cirugia", "operatorio", "fractura expuesta",
            "peritonitis", "abdomen agudo", "apendice"
        ]
        if any(palabra in sintomas or palabra in motivo or palabra in diag for palabra in palabras_cirugia):
            recommended_area = "SURGERY"
            justification = ["Patología quirúrgica probable"]
            explanation = "Paciente con síntomas compatibles con necesidad de intervención quirúrgica. Se deriva a Cirugía."
            wait_times = {"SURGERY": "15–30 min"}
            return {
                "patientId": p.get("id"),
                "previousState": p.get("previousState", "REGISTERED"),
                "newState": "SURGERY",
                "priorityScore": score,
                "recommendedArea": "SURGERY",
                "estimatedWaitTime": wait_times.get("SURGERY", "A definir"),
                "justification": justification,
                "explanation": explanation
            }
        
        # --- CRITERIOS PARA UCI (muy restrictivo) ---
        presion = p.get("pressure", {})
        sis = presion.get("sistolica", 120)
        dia = presion.get("diastolica", 80)
        is_pressure_critical = (sis < 90 or sis > 180 or dia < 50 or dia > 110)
        is_respiration_compromised = (o2 < 90.0 or "dificultad respiratoria" in sintomas)
        
        has_icu_lethal_indicator = (
            o2 < 90.0 or
            consciousness == "ALTERED" or
            is_pressure_critical or
            is_respiration_compromised
        )
        
        is_icu_eligible = (
            urg == "CRITICAL" and
            has_icu_lethal_indicator and
            (
                critical_count >= 3 or
                any(d in diag for d in ["neumonía", "sepsis", "falla respiratoria", "shock"]) or
                any(m in motivo for m in ["trauma", "neurológico", "respiratorio", "shock"])
            )
        )
        
        # --- FLUJO DE DECISIÓN JERÁRQUICA ---
        if is_icu_eligible:
            recommended_area = "ICU"
            justification = ["Paciente en estado crítico general"]
            if o2 < 90:
                justification.append("Hipoxia severa")
            if consciousness == "ALTERED":
                justification.append("Estado de conciencia alterado")
            if pain >= 9:
                justification.append("Dolor insoportable")
            explanation = "Paciente crítico con inestabilidad extrema de signos vitales, requiere vigilancia en UCI."
        elif score > 12:
            # Propuesto por score pero no cumple criterios estrictos de UCI
            recommended_area = "HOSPITALIZATION"
            justification = ["Puntaje de gravedad elevado"]
            if any(m in motivo for m in ["dolor", "digestivo"]):
                justification.append("Motivo de consulta de bajo riesgo")
            justification.append("No cumple criterios UCI restrictivos")
            explanation = "Paciente con score elevado, pero la consulta y los signos no justifican ingreso a UCI. Se ingresa a Hospitalización por seguridad."
        elif pain >= 7 and (urg == "HIGH" or any(d in diag for d in ["neumonía", "fractura", "trauma"])):
            recommended_area = "HOSPITALIZATION"
            justification = []
            if pain >= 7:
                justification.append("Dolor severo")
            if urg == "HIGH":
                justification.append("Urgencia alta")
            if any(d in diag for d in ["neumonía", "fractura", "trauma"]):
                justification.append("Diagnóstico severo")
            explanation = "Paciente requiere terapia de soporte continua y control de dolor en Hospitalización."
        elif (5 <= pain <= 7) or (p.get("age", 0) > 65) or (temp >= 38.5) or (o2 < 95.0) or (urg == "MEDIUM"):
            recommended_area = "OBSERVATION"
            justification = []
            if 5 <= pain <= 7:
                justification.append("Dolor moderado")
            if p.get("age", 0) > 65:
                justification.append("Paciente de edad avanzada")
            if temp >= 38.5:
                justification.append("Fiebre alta")
            if o2 < 95.0:
                justification.append("Saturación de oxígeno levemente baja")
            if urg == "MEDIUM":
                justification.append("Urgencia media")
            explanation = "Paciente requiere observación y reevaluación a corto plazo para monitorizar evolución."
        else:
            # Consulta Externa (mejorado)
            low_risk_motive = any(keyword in motivo for keyword in [
                "dolor", "digestivo", "control", "consulta general", "fiebre", "gripe",
                "náuseas", "mareo", "chequeo", "seguimiento", "rutina", "vacuna", "cefalea"
            ])
            is_consultation_eligible = (
                pain <= 4 and
                urg in ["LOW", "MEDIUM"] and
                o2 >= 95.0 and
                not any(s in sintomas for s in ["dificultad respiratoria", "pérdida conciencia", "dolor torácico"]) and
                not any(d in diag for d in ["neumonía", "sepsis", "fractura", "trauma", "falla"]) and
                low_risk_motive
            )
            if is_consultation_eligible:
                recommended_area = "CONSULTATION"
                justification = ["Síntomas leves", "Signos vitales estables"]
                explanation = "Paciente estable, con cuadro clínico leve. Apto para Consulta Externa."
            else:
                recommended_area = "OBSERVATION"
                justification = [f"Asignación basada en Score Clínico ({score})"]
                explanation = f"Paciente asignado a Observación basado en el puntaje de prioridad acumulado."
        
        # --- REGLA ANTI-UCI (OBLIGATORIA) ---
        if recommended_area == "ICU" and pain < 7 and urg != "CRITICAL":
            self.add_alert(f"ICU_BLOCKED_BY_CLINICAL_POLICY para paciente {p.get('id')}")
            self.add_event("ICU_BLOCKED_BY_CLINICAL_POLICY", {"patient_id": p.get("id"), "score": score})
            if score < 8:
                recommended_area = "OBSERVATION"
                justification = ["Desviado de UCI por política clínica", "Dolor no severo y urgencia no crítica"]
                explanation = "Bloqueado de UCI por política clínica (dolor no severo y urgencia no crítica). Redirigido a Observación."
            else:
                recommended_area = "HOSPITALIZATION"
                justification = ["Desviado de UCI por política clínica", "Puntaje de prioridad elevado"]
                explanation = "Bloqueado de UCI por política clínica (dolor no severo y urgencia no crítica). Redirigido a Hospitalización por score elevado."

        # --- MÁQUINA DE ESTADOS (VALIDACIÓN DE TRANSICIONES) ---
        prev_state = str(p.get("previousState") or p.get("estado") or "REGISTERED").upper()
        if prev_state in ["EN_ESPERA", "EN_EVALUACION", "REGISTERED"]:
            prev_state = "REGISTERED"
        elif prev_state in ["EN_TRIAJE", "TRIAGED"]:
            prev_state = "TRIAGED"
        elif prev_state in ["CONSULTA", "CONSULTATION"]:
            prev_state = "CONSULTATION"
        elif prev_state in ["OBSERVACION", "OBSERVATION", "EN_OBSERVACION"]:
            prev_state = "OBSERVATION"
        elif prev_state in ["HOSPITALIZACION", "HOSPITALIZATION"]:
            prev_state = "HOSPITALIZATION"
        elif prev_state in ["UCI", "ICU"]:
            prev_state = "ICU"
        elif prev_state in ["ALTA", "DISCHARGED", "TRANSFERIDO"]:
            prev_state = "DISCHARGED"
            
        # Transición prohibida a ICU
        if recommended_area == "ICU" and prev_state in ["REGISTERED", "CONSULTATION", "DISCHARGED"]:
            alert_msg = f"Transición prohibida detectada: {prev_state} -> ICU para {p.get('id')}. Desviando paciente de forma segura."
            self.add_alert(alert_msg)
            self.add_event("STATE_TRANSITION_BLOCKED", {
                "patient_id": p.get("id"),
                "previous_state": prev_state,
                "proposed_state": "ICU"
            })
            if prev_state == "CONSULTATION":
                recommended_area = "OBSERVATION"
                justification = ["Desviado de UCI: Transición desde Consulta prohibida"]
                explanation = f"Bloqueada transición {prev_state} -> ICU. Redirigido a Observación por seguridad clínica."
            elif prev_state == "REGISTERED":
                recommended_area = "OBSERVATION"
                justification = ["Desviado de UCI: Paciente sin triaje/admisión formal en área"]
                explanation = f"Bloqueada transición {prev_state} -> ICU. Debe ser ingresado primero a Observación para estabilización."
            elif prev_state == "DISCHARGED":
                recommended_area = "OBSERVATION"
                justification = ["Rechazada transición de Alta a UCI"]
                explanation = "Un paciente dado de alta no puede ir directo a UCI. Requiere re-admisión a Observación."

        wait_times = {
            "CONSULTATION": "30–60 min",
            "OBSERVATION": "15–30 min",
            "HOSPITALIZATION": "< 15 min",
            "ICU": "Inmediato",
            "SURGERY": "15–30 min"
        }
        
        if not justification:
            justification.append("Criterio clínico general")
            
        return {
            "patientId": p.get("id"),
            "previousState": prev_state,
            "newState": recommended_area,
            "priorityScore": score,
            "recommendedArea": recommended_area,
            "estimatedWaitTime": wait_times.get(recommended_area, "A definir"),
            "justification": justification,
            "explanation": explanation
        }

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
        self.add_event("PATIENT_ADDED", {"patient": patient})
        print(f"[STATE] Patient added → {patient['id_paciente']}")

    def update_patient_field(self, patient_id: str, field: str, value: Any) -> None:
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

    def allocate_resource(self, priority: str, patient: Dict[str, Any], recommended_area: Optional[str] = None) -> Optional[str]:
        if not recommended_area:
            recommended_area = patient.get("recommendedArea") or "OBSERVATION"
            
        if recommended_area == "ICU":
            prefs = ["ICU", "EMERGENCY", "GENERAL"]
        elif recommended_area == "HOSPITALIZATION":
            prefs = ["GENERAL", "SURGERY", "EMERGENCY"]
        elif recommended_area == "CONSULTATION":
            prefs = ["CONSULTATION", "GENERAL"]
        elif recommended_area == "SURGERY":
            prefs = ["SURGERY", "GENERAL", "EMERGENCY"]
        else: # OBSERVATION
            prefs = ["EMERGENCY", "GENERAL"]

        for rtype in prefs:
            r = self.resources.get(rtype)
            if r and r.get("available", 0) > 0:
                r["available"] -= 1
                r["occupied"] += 1
                dept = self._map_resource_to_department(rtype)
                patient["bed_type"] = rtype
                patient["departamento_asignado"] = dept
                patient["department"] = dept
                patient["estado"] = recommended_area
                patient["state"] = recommended_area
                prefix = dept[:3].upper().replace("Á", "A").replace("É", "E").replace("Ó", "O")
                bed_id = f"{prefix}-{random.randint(1, 30):02d}"
                patient["bed_id"] = bed_id
                patient["cama"] = bed_id
                self.refresh_derived_state()
                self.add_event("RESOURCE_ALLOCATED", {
                    "patient": patient,
                    "resource_type": rtype,
                    "available": r["available"],
                    "department": dept,
                    "bed_id": bed_id
                })
                return rtype

        self.add_alert(
            f"No hay recursos para {patient.get('id_paciente')} con área recomendada {recommended_area}."
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

        doctors = [s for s in candidates if "medic" in s["rol"].lower() or "doctor" in s["rol"].lower()]
        member = doctors[0] if doctors else candidates[0]
        member["estado"] = "Ocupado"
        member["pacientes_atendidos_turno"] = member.get("pacientes_atendidos_turno", 0) + 1
        patient["medico_asignado"] = member["id_empleado"]
        self.refresh_derived_state()
        self.add_event("STAFF_ASSIGNED", {"patient": patient, "staff": member})
        return member

    def assign_nurse(self, patient: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        area = patient.get("recommendedArea")
        role_pref = "enfermera de uci" if area == "ICU" else "enferm"
        
        nurses = [
            s for s in self.staff
            if s["estado"] == "Disponible"
            and (role_pref in s["rol"].lower() or "nurse" in s["rol"].lower())
        ]
        if not nurses:
            nurses = [
                s for s in self.staff
                if s["estado"] == "Disponible"
                and ("enferm" in s["rol"].lower() or "nurse" in s["rol"].lower())
            ]
        if not nurses:
            nurses = [s for s in self.staff if s["estado"] == "Disponible"]
        if not nurses:
            return None
        nurse = nurses[0]
        nurse["estado"] = "Ocupado"
        nurse["pacientes_atendidos_turno"] = nurse.get("pacientes_atendidos_turno", 0) + 1
        patient["enfermero_asignado"] = nurse["id_empleado"]
        return nurse

    def select_staff_specialty(self, patient: Dict[str, Any], priority: str) -> str:
        area = patient.get("recommendedArea")
        if area == "ICU":
            return "Medicina Intensiva"
        elif area == "HOSPITALIZATION":
            motivo = str(patient.get("diagnosis", "")).lower()
            sintomas = [s.lower() for s in patient.get("symptoms", [])]
            sint_text = " ".join(sintomas)
            if "cardio" in sint_text or "torácico" in sint_text:
                return "Cardiología"
            if "traumat" in sint_text or "fractura" in sint_text:
                return "Traumatología"
            return "Cirugía"
        elif area == "OBSERVATION":
            return "Medicina Interna"
        elif area == "SURGERY":
            return "Cirugía"
        else: # CONSULTATION
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
        patient = self.get_patient(patient_id)
        if not patient:
            return {"error": "Paciente no encontrado"}
        bed_type = patient.get("bed_type")
        if bed_type and bed_type in self.resources:
            r = self.resources[bed_type]
            r["available"] = min(r["available"] + 1, r["total"])
            r["occupied"] = max(r["occupied"] - 1, 0)
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
            "Cirugia": "SURGERY",
            "Cirugía": "SURGERY",
            "Consulta_Externa": "CONSULTATION",
            "Cardiologia": "GENERAL",
            "Radiologia": "GENERAL",
        }
        return mapping.get(dept, "GENERAL")

    def _map_resource_to_department(self, rtype: str) -> str:
        mapping = {
            "ICU": "UCI",
            "GENERAL": "Hospitalización",
            "EMERGENCY": "Emergencias",
            "SURGERY": "Cirugía",
            "CONSULTATION": "Consulta_Externa",
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