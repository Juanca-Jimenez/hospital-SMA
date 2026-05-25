#!/usr/bin/env python3
"""
Script para probar que los endpoints de CSV estén funcionando correctamente.
Ejecuta este script después de iniciar el servidor backend.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(name, endpoint):
    """Prueba un endpoint y muestra los resultados"""
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        print(f"\n✓ {name}")
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                count = data.get("count", len(data))
                print(f"  Registros: {count}")
                if "error" in data:
                    print(f"  Error: {data['error']}")
            else:
                print(f"  Datos: {type(data)}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"\n✗ {name}")
        print(f"  Error: No se pudo conectar a {BASE_URL}")
        return False
    except Exception as e:
        print(f"\n✗ {name}")
        print(f"  Error: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("Prueba de Endpoints CSV para Hospital SMA")
    print("=" * 60)
    
    endpoints = [
        ("Pacientes", "/api/patients"),
        ("Departamentos", "/api/departments"),
        ("Recursos", "/api/resources"),
        ("Personal", "/api/staff"),
        ("Métricas", "/api/metrics"),
        ("Estado Global", "/api/state"),
        ("Health Check", "/api/health"),
    ]
    
    results = []
    for name, endpoint in endpoints:
        results.append(test_endpoint(name, endpoint))
    
    print("\n" + "=" * 60)
    print(f"Resumen: {sum(results)}/{len(results)} endpoints funcionando")
    print("=" * 60)
    
    if all(results):
        print("\n✓ Todos los endpoints están funcionando correctamente!")
        return 0
    else:
        print("\n✗ Algunos endpoints no están funcionando. Verifica el servidor.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
