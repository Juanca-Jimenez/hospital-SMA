#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import json
import pandas as pd
from datetime import datetime, timedelta

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

SINTOMAS = {
    "Emergencias": ["Dolor torácico", "Dificultad respiratoria", "Accidente cerebrovascular", "Trauma severo", "Envenenamiento"],
    "UCI": ["Falla multiorgánica", "Sepsis severa", "Trauma craneoencefálico", "Insuficiencia respiratoria", "Shock cardiogénico"],
    "Consulta_Externa": ["Dolor muscular", "Gastroenteritis", "Infección respiratoria", "Alergia", "Dolor lumbar"],
    "Hospitalizacion": ["Neumonía", "Infección urinaria", "Diabetes descompensada", "Hipertensión no controlada", "Insuficiencia cardíaca"],
    "Cirugia": ["Fractura femoral", "Apendicitis aguda", "Colecistitis", "Hernia inguinal", "Tumor abdominal"]
}

URGENCIA_DIST = {
    "Emergencias": {1: 5, 2: 15, 3: 30, 4: 35, 5: 15},
    "UCI": {1: 30, 2: 40, 3: 20, 4: 10, 5: 0},
    "Consulta_Externa": {4: 50, 5: 50},
    "Hospitalizacion": {2: 20, 3: 40, 4: 40},
    "Cirugia": {2: 15, 3: 55, 4: 30}
}

ESTADOS = ["En_atencion", "En_espera", "Transferido", "Alta"]

def generate_pacientes():
    """Generar dataframe de pacientes"""
    data = []
    id_counter = 1
    
    departamentos_orden = ["Emergencias", "UCI", "Consulta_Externa", "Hospitalizacion", "Cirugia"]
    departamentos = {"Emergencias": 20, "UCI": 10, "Consulta_Externa": 18, "Hospitalizacion": 22, "Cirugia": 12}
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for dept in departamentos_orden:
        count = departamentos[dept]
        
        for _ in range(count):
            dist = URGENCIA_DIST[dept]
            urgencia = random.choices(list(dist.keys()), weights=list(dist.values()), k=1)[0]
            
            edad = random.randint(18, 85)
            genero = random.choice(["M", "F"])
            sintoma = random.choice(SINTOMAS[dept])
            
            if urgencia <= 2:
                pa = "{}/{}".format(random.randint(140, 180), random.randint(90, 110))
                temp = round(random.uniform(35.5, 40.2), 1)
                fc = random.randint(110, 160)
                spo2 = random.randint(80, 92)
            elif urgencia == 3:
                pa = "{}/{}".format(random.randint(120, 145), random.randint(80, 95))
                temp = round(random.uniform(36.5, 38.5), 1)
                fc = random.randint(85, 110)
                spo2 = random.randint(93, 97)
            else:
                pa = "{}/{}".format(random.randint(110, 130), random.randint(70, 85))
                temp = round(random.uniform(36.0, 37.5), 1)
                fc = random.randint(60, 90)
                spo2 = random.randint(97, 100)
            
            signos_dict = {
                "presion": pa,
                "temperatura": temp,
                "frecuencia_cardiaca": fc,
                "saturacion_oxigeno": spo2
            }
            signos_json = json.dumps(signos_dict)
            
            estado = random.choice(ESTADOS)
            tiempo_espera = random.randint(5, 150) if estado == "En_espera" else random.randint(0, 20)
            
            id_pad = str(id_counter).zfill(6)
            
            data.append({
                "timestamp": timestamp,
                "id_paciente": id_pad,
                "edad": edad,
                "genero": genero,
                "nivel_urgencia": urgencia,
                "sintomas": sintoma,
                "signos_vitales": signos_json,
                "tiempo_espera_min": tiempo_espera,
                "departamento_asignado": dept,
                "estado": estado
            })
            id_counter += 1
    
    return pd.DataFrame(data)

def generate_recursos():
    """Generar dataframe de recursos"""
    data = []
    
    capacidades = {
        "Emergencias": {"Cama_Emergencia": 30},
        "UCI": {"Cama_UCI": 20},
        "Consulta_Externa": {"Cama_General": 20},
        "Hospitalizacion": {"Cama_General": 35},
        "Cirugia": {"Quirofano": 15}
    }
    
    ocupacion = {
        "Emergencias": 20,
        "UCI": 10,
        "Consulta_Externa": 18,
        "Hospitalizacion": 22,
        "Cirugia": 12
    }
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for dept, resources in capacidades.items():
        for resource_type, total in resources.items():
            ocu = ocupacion[dept]
            avail = total - ocu
            data.append({
                "timestamp": timestamp,
                "tipo_recurso": resource_type,
                "departamento": dept,
                "total_disponible": total,
                "ocupados": ocu,
                "disponibles": avail,
                "proximo_disponible_min": 0
            })
    
    return pd.DataFrame(data)

def generate_personal():
    """Generar dataframe de personal"""
    data = []
    
    nombres_doctores = ["Carlos", "Miguel", "Ana", "Juan", "Laura", "Ricardo", "Sofia", "Andrés", "Patricia", "Fernando",
                       "Isabel", "Gabriel", "Elena", "Luis", "Marta", "Diego", "Raquel", "Oscar", "Verónica", "Héctor"]
    
    nombres_enfermeros = ["María", "José", "Carmen", "Pedro", "Rosa", "Juan", "Cristina", "Marco", "Daniela", "Raúl",
                         "Alejandra", "Sergio", "Adriana", "Mateo", "Valentina", "Javier", "Lorena", "Bruno", "Sandra", "Victor",
                         "Andrea", "Alfonso", "Beatriz", "Gustavo", "Catalina", "Rodrigo", "Diana", "Esteban", "Elvira", "Fernando",
                         "Fabiana", "Gerardo", "Georgina", "Gonzalo", "Gloria"]
    
    especialidades = ["Cardiologia", "Traumatologia", "Neurologia", "Pediatria", "Emergencias", "Neumologia", "Gastroenterologia", "Oncologia"]
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    id_emp = 1
    
    # 20 Doctores
    for i in range(20):
        nombre = "Dr. " + nombres_doctores[i % len(nombres_doctores)]
        esp = random.choice(especialidades)
        turno_inicio = random.choice(["06:00", "18:00"])
        turno_fin = "18:00" if turno_inicio == "06:00" else "06:00"
        horas = 12
        pacientes = random.randint(0, 8)
        estado = random.choice(["Disponible", "Ocupado", "Descanso"])
        
        data.append({
            "timestamp": timestamp,
            "id_empleado": "D{:03d}".format(id_emp),
            "nombre": nombre,
            "rol": "Doctor",
            "especialidad": esp,
            "turno_inicio": turno_inicio,
            "turno_fin": turno_fin,
            "horas_trabajadas_consecutivas": horas,
            "pacientes_atendidos_turno": pacientes,
            "estado": estado
        })
        id_emp += 1
    
    # 35 Enfermeros
    for i in range(35):
        nombre = "Enf. " + nombres_enfermeros[i % len(nombres_enfermeros)]
        turno_inicio = random.choice(["06:00", "18:00"])
        turno_fin = "18:00" if turno_inicio == "06:00" else "06:00"
        horas = 12
        pacientes = random.randint(2, 10)
        estado = random.choice(["Disponible", "Ocupado", "Descanso", "Fuera_turno"])
        
        data.append({
            "timestamp": timestamp,
            "id_empleado": "E{:03d}".format(id_emp),
            "nombre": nombre,
            "rol": "Enfermero",
            "especialidad": "Enfermeria",
            "turno_inicio": turno_inicio,
            "turno_fin": turno_fin,
            "horas_trabajadas_consecutivas": horas,
            "pacientes_atendidos_turno": pacientes,
            "estado": estado
        })
        id_emp += 1
    
    return pd.DataFrame(data)

def generate_metricas():
    """Generar dataframe de métricas históricas"""
    data = []
    
    departamentos = ["Emergencias", "UCI", "Consulta_Externa", "Hospitalizacion", "Cirugia"]
    base_date = datetime.now() - timedelta(days=7)
    
    for day_offset in range(7):
        current_date = base_date + timedelta(days=day_offset)
        timestamp = current_date.strftime("%Y-%m-%d 00:00:00")
        
        for dept in departamentos:
            pacientes = random.randint(5, 25)
            tiempo_espera = random.randint(10, 90)
            ocupacion = round((pacientes / 20) * 100, 1)
            criticos = random.randint(0, 8)
            altas = random.randint(0, 5)
            
            data.append({
                "timestamp": timestamp,
                "departamento": dept,
                "pacientes_activos": pacientes,
                "tiempo_espera_promedio_min": tiempo_espera,
                "tasa_ocupacion_pct": ocupacion,
                "casos_criticos": criticos,
                "altas_ultimas_2h": altas
            })
    
    return pd.DataFrame(data)

# Main
if __name__ == "__main__":
    print("Generando archivos CSV correctos con pandas...")
    
    base_path = "backend/data/"
    
    # Pacientes
    df_pacientes = generate_pacientes()
    df_pacientes.to_csv(base_path + "pacientes_admisiones.csv", index=False)
    print("OK: pacientes_admisiones.csv ({} lineas)".format(len(df_pacientes) + 1))
    
    # Recursos
    df_recursos = generate_recursos()
    df_recursos.to_csv(base_path + "recursos_disponibilidad.csv", index=False)
    print("OK: recursos_disponibilidad.csv ({} lineas)".format(len(df_recursos) + 1))
    
    # Personal
    df_personal = generate_personal()
    df_personal.to_csv(base_path + "personal_turnos.csv", index=False)
    print("OK: personal_turnos.csv ({} lineas)".format(len(df_personal) + 1))
    
    # Metricas
    df_metricas = generate_metricas()
    df_metricas.to_csv(base_path + "historico_metricas.csv", index=False)
    print("OK: historico_metricas.csv ({} lineas)".format(len(df_metricas) + 1))
    
    print("\nArchivos generados exitosamente!")
    print("Estructura compatible con backend.state_manager.py")
