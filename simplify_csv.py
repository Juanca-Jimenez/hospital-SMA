#!/usr/bin/env python3
"""
Script para simplificar los CSV del hospital.
Crea 4 archivos CSV esenciales a partir de los datos actuales.
"""

import pandas as pd
import os
from pathlib import Path

# Rutas
DATA_DIR = Path(__file__).resolve().parent / "backend" / "data"

def create_simplified_patients():
    """Crear pacientes.csv simplificado"""
    print("Procesando pacientes...")
    
    # Leer datos originales
    df = pd.read_csv(DATA_DIR / "pacientes_admisiones.csv")
    
    # Seleccionar columnas esenciales
    simplified = df[['id_paciente', 'edad', 'genero', 'nivel_urgencia', 'sintomas', 'departamento_asignado', 'estado']].copy()
    simplified.columns = ['id_paciente', 'edad', 'genero', 'nivel_urgencia', 'sintomas', 'departamento', 'estado']
    
    # Limpieza básica
    simplified['id_paciente'] = simplified['id_paciente'].astype(str).str.strip()
    simplified['edad'] = simplified['edad'].astype(int)
    simplified['genero'] = simplified['genero'].astype(str).str.strip()
    simplified['nivel_urgencia'] = simplified['nivel_urgencia'].astype(int)
    simplified['sintomas'] = simplified['sintomas'].astype(str).str.strip()
    simplified['departamento'] = simplified['departamento'].astype(str).str.strip()
    simplified['estado'] = simplified['estado'].astype(str).str.strip()
    
    # Guardar
    simplified.to_csv(DATA_DIR / "pacientes.csv", index=False)
    print(f"✓ pacientes.csv creado ({len(simplified)} pacientes)")


def create_simplified_recursos():
    """Crear recursos.csv simplificado"""
    print("Procesando recursos...")
    
    # Leer datos originales
    df = pd.read_csv(DATA_DIR / "recursos_disponibilidad.csv")
    
    # Agrupar por departamento
    resources = df.groupby('departamento').agg({
        'total_disponible': 'sum',
        'ocupados': 'sum'
    }).reset_index()
    
    resources.columns = ['departamento', 'total', 'ocupados']
    
    # Limpieza
    resources['departamento'] = resources['departamento'].astype(str).str.strip()
    resources['total'] = resources['total'].astype(int)
    resources['ocupados'] = resources['ocupados'].astype(int)
    
    # Guardar
    resources.to_csv(DATA_DIR / "recursos.csv", index=False)
    print(f"✓ recursos.csv creado ({len(resources)} departamentos)")


def create_simplified_personal():
    """Crear personal.csv simplificado"""
    print("Procesando personal...")
    
    # Leer datos originales
    df = pd.read_csv(DATA_DIR / "personal_turnos.csv")
    
    # Seleccionar columnas esenciales
    simplified = df[['id_empleado', 'rol', 'especialidad', 'estado']].copy()
    
    # Asignar departamentos primarios basados en especialidad
    especialidad_depto = {
        'Neurologia': 'Consulta_Externa',
        'Neumologia': 'Consulta_Externa',
        'Emergencias': 'Emergencias',
        'Oncologia': 'Consulta_Externa',
        'Gastroenterologia': 'Consulta_Externa',
        'Pediatria': 'Pediatria',
        'Cardiologia': 'Cardiologia',
        'Traumatologia': 'Cirugia',
        'Enfermeria': 'Hospitalizacion',
    }
    
    simplified['departamento_1'] = simplified['especialidad'].map(especialidad_depto).fillna('Hospitalizacion')
    
    # Departamento secundario (alternativa)
    departamentos = ['Emergencias', 'UCI', 'Hospitalizacion', 'Consulta_Externa', 'Pediatria']
    simplified['departamento_2'] = simplified['departamento_1'].apply(
        lambda x: [d for d in departamentos if d != x][0] if len([d for d in departamentos if d != x]) > 0 else 'UCI'
    )
    
    # Normalizar estado
    simplified['estado'] = simplified['estado'].map({
        'Ocupado': 'Disponible',
        'Disponible': 'Disponible',
        'Descanso': 'Descanso',
        'Fuera_turno': 'Descanso'
    }).fillna(simplified['estado'])
    
    # Limpieza
    simplified['id_empleado'] = simplified['id_empleado'].astype(str).str.strip()
    simplified['rol'] = simplified['rol'].astype(str).str.strip()
    simplified['especialidad'] = simplified['especialidad'].astype(str).str.strip()
    
    # Guardar
    simplified.to_csv(DATA_DIR / "personal.csv", index=False)
    print(f"✓ personal.csv creado ({len(simplified)} empleados)")


def create_simplified_metricas():
    """Crear metricas.csv simplificado"""
    print("Procesando métricas...")
    
    # Leer datos originales para obtener estadísticas
    pacientes_df = pd.read_csv(DATA_DIR / "pacientes_admisiones.csv")
    recursos_df = pd.read_csv(DATA_DIR / "recursos_disponibilidad.csv")
    
    # Calcular métricas actuales
    pacientes_activos = len(pacientes_df[pacientes_df['estado'].isin(['En_espera', 'En_atencion'])])
    total_capacidad = recursos_df['total_disponible'].sum()
    ocupados = recursos_df['ocupados'].sum()
    ocupacion_pct = round((ocupados / total_capacidad * 100) if total_capacidad > 0 else 0, 1)
    casos_criticos = len(pacientes_df[pacientes_df['nivel_urgencia'] <= 2])
    casos_criticos_pct = round((casos_criticos / len(pacientes_df) * 100) if len(pacientes_df) > 0 else 0, 1)
    
    # Crear dataframe
    metricas = pd.DataFrame([{
        'pacientes_activos': pacientes_activos,
        'ocupacion_pct': ocupacion_pct,
        'casos_criticos_pct': casos_criticos_pct
    }])
    
    # Guardar
    metricas.to_csv(DATA_DIR / "metricas.csv", index=False)
    print(f"✓ metricas.csv creado")
    print(f"  - Pacientes activos: {pacientes_activos}")
    print(f"  - Ocupación: {ocupacion_pct}%")
    print(f"  - Casos críticos: {casos_criticos_pct}%")


def main():
    print("=" * 60)
    print("Simplificación de CSV del Hospital SMA")
    print("=" * 60 + "\n")
    
    try:
        create_simplified_patients()
        create_simplified_recursos()
        create_simplified_personal()
        create_simplified_metricas()
        
        print("\n" + "=" * 60)
        print("✓ Simplificación completada exitosamente")
        print("=" * 60)
        print("\nArchivos creados:")
        print("  1. pacientes.csv (id, edad, genero, urgencia, sintomas, depto, estado)")
        print("  2. recursos.csv (departamento, total, ocupados)")
        print("  3. personal.csv (id, rol, especialidad, depto_1, depto_2, estado)")
        print("  4. metricas.csv (pacientes_activos, ocupacion_pct, casos_criticos_pct)")
        print("\nLos archivos originales se conservan para referencia.")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
