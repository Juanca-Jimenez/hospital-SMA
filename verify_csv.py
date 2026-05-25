#!/usr/bin/env python3
"""
Script de Verificación - CSV Simplificados
Valida que todos los CSV estén correctos y los datos sean consistentes
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "backend" / "data"

def check_csv_files():
    """Verifica la existencia y estructura de todos los CSV"""
    print("=" * 70)
    print("VERIFICACIÓN DE CSV SIMPLIFICADOS")
    print("=" * 70)
    
    required_files = {
        "pacientes.csv": ["id_paciente", "edad", "genero", "nivel_urgencia", "sintomas", "departamento", "estado"],
        "recursos.csv": ["departamento", "total", "ocupados"],
        "personal.csv": ["id_empleado", "rol", "especialidad", "departamento_1", "departamento_2", "estado"],
        "metricas.csv": ["pacientes_activos", "ocupacion_pct", "casos_criticos_pct"],
    }
    
    all_ok = True
    
    for filename, expected_cols in required_files.items():
        path = DATA_DIR / filename
        print(f"\n📄 {filename}")
        
        if not path.exists():
            print(f"  ❌ NO EXISTE")
            all_ok = False
            continue
        
        try:
            df = pd.read_csv(path)
            print(f"  ✓ Existe")
            print(f"  ✓ Registros: {len(df)}")
            
            # Verificar columnas
            missing_cols = [col for col in expected_cols if col not in df.columns]
            if missing_cols:
                print(f"  ❌ Faltan columnas: {missing_cols}")
                all_ok = False
            else:
                print(f"  ✓ Columnas: {', '.join(expected_cols)}")
            
            # Verificar datos
            if len(df) == 0:
                print(f"  ⚠️  CSV vacío")
                all_ok = False
            else:
                print(f"  ✓ Datos presentes")
                
                # Mostrar preview
                print(f"  📋 Preview:")
                for idx, row in df.head(2).iterrows():
                    print(f"     Fila {idx + 1}: {dict(row)}")
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            all_ok = False
    
    # Verificar datos específicos
    print("\n" + "-" * 70)
    print("VALIDACIÓN DE DATOS")
    print("-" * 70)
    
    try:
        # Pacientes
        df_pac = pd.read_csv(DATA_DIR / "pacientes.csv")
        print(f"\n👥 PACIENTES")
        print(f"  Total: {len(df_pac)}")
        print(f"  Por urgencia:")
        for urgencia in sorted(df_pac['nivel_urgencia'].unique()):
            count = len(df_pac[df_pac['nivel_urgencia'] == urgencia])
            print(f"    Nivel {urgencia}: {count}")
        print(f"  Por estado:")
        for estado in df_pac['estado'].unique():
            count = len(df_pac[df_pac['estado'] == estado])
            print(f"    {estado}: {count}")
        
        # Recursos
        df_res = pd.read_csv(DATA_DIR / "recursos.csv")
        print(f"\n🏥 RECURSOS")
        print(f"  Departamentos: {len(df_res)}")
        total_camas = df_res['total'].sum()
        total_ocupados = df_res['ocupados'].sum()
        print(f"  Total camas: {total_camas}")
        print(f"  Ocupadas: {total_ocupados}")
        print(f"  Disponibles: {total_camas - total_ocupados}")
        print(f"  Ocupación: {round(total_ocupados/total_camas*100, 1)}%")
        print(f"  Por departamento:")
        for _, row in df_res.iterrows():
            ocu_pct = round(row['ocupados'] / row['total'] * 100, 1) if row['total'] > 0 else 0
            print(f"    {row['departamento']}: {row['ocupados']}/{row['total']} ({ocu_pct}%)")
        
        # Personal
        df_staff = pd.read_csv(DATA_DIR / "personal.csv")
        print(f"\n👨‍⚕️  PERSONAL")
        print(f"  Total: {len(df_staff)}")
        print(f"  Por rol:")
        for rol in df_staff['rol'].unique():
            count = len(df_staff[df_staff['rol'] == rol])
            print(f"    {rol}: {count}")
        print(f"  Disponibilidad:")
        disponibles = len(df_staff[df_staff['estado'] == 'Disponible'])
        descanso = len(df_staff[df_staff['estado'] == 'Descanso'])
        print(f"    Disponibles: {disponibles}")
        print(f"    En descanso: {descanso}")
        
        # Métricas
        df_met = pd.read_csv(DATA_DIR / "metricas.csv")
        print(f"\n📊 MÉTRICAS")
        if len(df_met) > 0:
            met = df_met.iloc[0]
            print(f"  Pacientes activos: {met['pacientes_activos']}")
            print(f"  Ocupación: {met['ocupacion_pct']}%")
            print(f"  Casos críticos: {met['casos_criticos_pct']}%")
        
    except Exception as e:
        print(f"❌ Error en validación: {str(e)}")
        all_ok = False
    
    print("\n" + "=" * 70)
    if all_ok:
        print("✅ TODOS LOS CSV ESTÁN CORRECTOS")
        print("=" * 70)
        return 0
    else:
        print("❌ ALGUNOS CSV TIENEN PROBLEMAS")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    exit(check_csv_files())
