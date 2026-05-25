#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import os

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

SINTOMAS = {
    "Urgencias": ["Dolor torácico", "Dificultad respiratoria", "Accidente cerebrovascular", "Trauma severo", "Envenenamiento"],
    "UCI": ["Falla multiorgánica", "Sepsis severa", "Trauma craneoencefálico", "Insuficiencia respiratoria", "Shock cardiogénico"],
    "Consulta_Externa": ["Dolor muscular", "Gastroenteritis", "Infección respiratoria", "Alergia", "Dolor lumbar"],
    "Hospitalizacion": ["Neumonía", "Infección urinaria", "Diabetes descompensada", "Hipertensión no controlada", "Insuficiencia cardíaca"],
    "Cirugia": ["Fractura femoral", "Apendicitis aguda", "Colecistitis", "Hernia inguinal", "Tumor abdominal"]
}

URGENCIA_DIST = {
    "Urgencias": {1: 5, 2: 15, 3: 30, 4: 35, 5: 15},
    "UCI": {1: 30, 2: 40, 3: 20, 4: 10, 5: 0},
    "Consulta_Externa": {4: 50, 5: 50},
    "Hospitalizacion": {2: 20, 3: 40, 4: 40},
    "Cirugia": {2: 15, 3: 55, 4: 30}
}

ESTADOS = ["En_atencion", "Asignado", "Hospitalizado", "Alta_proxima"]

def generate_pacientes():
    """Generar CSV de pacientes"""
    csv = "id_paciente,edad,genero,nivel_urgencia,sintomas,signos_vitales,departamento,estado\n"
    id_counter = 1
    ocupados_dept = {}
    
    departamentos_orden = ["Urgencias", "UCI", "Consulta_Externa", "Hospitalizacion", "Cirugia"]
    departamentos = {"Urgencias": 20, "UCI": 10, "Consulta_Externa": 18, "Hospitalizacion": 22, "Cirugia": 12}
    
    for dept in departamentos_orden:
        count = departamentos[dept]
        ocupados_dept[dept] = 0
        
        for _ in range(count):
            dist = URGENCIA_DIST[dept]
            urgencia = random.choices(list(dist.keys()), weights=list(dist.values()), k=1)[0]
            
            edad = random.randint(18, 85)
            genero = random.choice(["M", "F"])
            sintoma = random.choice(SINTOMAS[dept])
            
            if urgencia <= 2:
                pa = "{}/{}".format(random.randint(140, 180), random.randint(90, 110))
                temp = "{:.1f}".format(random.uniform(35.5, 40.2))
                fc = random.randint(110, 160)
                spo2 = random.randint(80, 92)
            elif urgencia == 3:
                pa = "{}/{}".format(random.randint(120, 145), random.randint(80, 95))
                temp = "{:.1f}".format(random.uniform(36.5, 38.5))
                fc = random.randint(85, 110)
                spo2 = random.randint(93, 97)
            else:
                pa = "{}/{}".format(random.randint(110, 130), random.randint(70, 85))
                temp = "{:.1f}".format(random.uniform(36.0, 37.5))
                fc = random.randint(60, 90)
                spo2 = random.randint(97, 100)
            
            signos = "PA={} | T={} | FC={} | SPO2={}".format(pa, temp, fc, spo2)
            estado = random.choice(ESTADOS)
            
            id_pad = str(id_counter).zfill(5)
            csv += "{},{},{},{},\"{}\",\"{}\",{},{}\n".format(
                id_pad, edad, genero, urgencia, sintoma, signos, dept, estado
            )
            ocupados_dept[dept] += 1
            id_counter += 1
    
    return csv, ocupados_dept

def generate_recursos(ocupados_dept):
    """Generar CSV de recursos"""
    capacidad = {"Urgencias": 30, "UCI": 20, "Consulta_Externa": 20, "Hospitalizacion": 35, "Cirugia": 15}
    csv = "departamento,total_camas,ocupadas,disponibles\n"
    
    departamentos_orden = ["Urgencias", "UCI", "Consulta_Externa", "Hospitalizacion", "Cirugia"]
    
    for dept in departamentos_orden:
        total = capacidad[dept]
        ocupadas = ocupados_dept[dept]
        disponibles = total - ocupadas
        csv += "{},{},{},{}\n".format(dept, total, ocupadas, disponibles)
    
    return csv

def generate_personal():
    """Generar CSV de personal"""
    nombres_doctores = ["Carlos", "Miguel", "Ana", "Juan", "Laura", "Ricardo", "Sofia", "Andrés", "Patricia", "Fernando", 
                       "Isabel", "Gabriel", "Elena", "Luis", "Marta", "Diego", "Raquel", "Oscar", "Verónica", "Héctor"]
    
    nombres_enfermeros = ["María", "José", "Carmen", "Pedro", "Rosa", "Juan", "Cristina", "Marco", "Daniela", "Raúl", 
                         "Alejandra", "Sergio", "Adriana", "Mateo", "Valentina", "Javier", "Lorena", "Bruno", "Sandra", "Victor", 
                         "Andrea", "Alfonso", "Beatriz", "Gustavo", "Catalina", "Rodrigo", "Diana", "Esteban", "Elvira", "Fernando", 
                         "Fabiana", "Gerardo", "Georgina", "Gonzalo", "Gloria"]
    
    especialidades = ["Cardiologia", "Traumatologia", "Neurologia", "Pediatria", "Emergencias", "Neumologia", "Gastroenterologia", "Oncologia"]
    departamentos_staff = ["Urgencias", "UCI", "Consulta_Externa", "Hospitalizacion", "Cirugia"]
    
    csv = "id_empleado,nombre,rol,especialidad,departamento_1,departamento_2,turno,dias,estado\n"
    id_emp = 1
    
    # 20 Doctores
    for i in range(20):
        nombre = "Dr. " + nombres_doctores[i % len(nombres_doctores)]
        esp = random.choice(especialidades)
        dept1 = random.choice(departamentos_staff)
        dept2 = random.choice([d for d in departamentos_staff if d != dept1])
        turno = random.choice(["06:00-18:00", "18:00-06:00"])
        dias = "Lun-Mar-Mie-Jue"
        estado = random.choice(["Disponible", "Atendiendo", "Descanso"])
        csv += "D{:03d},{},Doctor,{},{},{},{},{},{}\n".format(id_emp, nombre, esp, dept1, dept2, turno, dias, estado)
        id_emp += 1
    
    # 35 Enfermeros
    for i in range(35):
        nombre = "Enf. " + nombres_enfermeros[i % len(nombres_enfermeros)]
        esp = "Enfermeria"
        dept1 = random.choice(departamentos_staff)
        dept2 = random.choice([d for d in departamentos_staff if d != dept1])
        turno = random.choice(["06:00-18:00", "18:00-06:00"])
        dias = "Mar-Jue-Vie-Sab"
        estado = random.choice(["Disponible", "Atendiendo", "Descanso", "Fuera_turno"])
        csv += "E{:03d},{},Enfermero,{},{},{},{},{},{}\n".format(id_emp, nombre, esp, dept1, dept2, turno, dias, estado)
        id_emp += 1
    
    return csv

def generate_metricas():
    """Generar CSV de metricas historicas"""
    dias_semana = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
    csv = "dia,pacientes_activos,ocupacion_pct,casos_criticos_pct\n"
    
    for dia in dias_semana:
        pacientes_activos = 75 + random.randint(-5, 10)
        ocupacion = round(((pacientes_activos * 100) / 120), 1)
        casos_criticos = round((random.randint(15, 35)), 1)
        csv += "{},{},{},{}\n".format(dia, pacientes_activos, ocupacion, casos_criticos)
    
    return csv

# Main
if __name__ == "__main__":
    print("Generando archivos CSV...")
    
    # Generar pacientes
    csv_pacientes, ocupados_dept = generate_pacientes()
    print("TOTAL PACIENTES: {}".format(len(csv_pacientes.split('\n')) - 2))
    
    # Generar recursos
    csv_recursos = generate_recursos(ocupados_dept)
    
    # Generar personal
    csv_personal = generate_personal()
    
    # Generar metricas
    csv_metricas = generate_metricas()
    
    # Escribir archivos
    base_path = "backend/data/"
    
    with open(base_path + "pacientes_admisiones.csv", "w", encoding="utf-8") as f:
        f.write(csv_pacientes)
    print("OK: pacientes_admisiones.csv")
    
    with open(base_path + "recursos_disponibilidad.csv", "w", encoding="utf-8") as f:
        f.write(csv_recursos)
    print("OK: recursos_disponibilidad.csv")
    
    with open(base_path + "personal_turnos.csv", "w", encoding="utf-8") as f:
        f.write(csv_personal)
    print("OK: personal_turnos.csv")
    
    with open(base_path + "historico_metricas.csv", "w", encoding="utf-8") as f:
        f.write(csv_metricas)
    print("OK: historico_metricas.csv")
    
    print("\nArchivos generados exitosamente!")
