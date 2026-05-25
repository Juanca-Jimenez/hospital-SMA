# CSV Simplificados - Hospital SMA

## Resumen de Cambios

Se han simplificado completamente los CSV del proyecto manteniendo solo los datos esenciales para el dashboard y la simulación multiagente. Se pasó de 5 archivos complejos a 4 archivos simples y claros.

## Nuevos CSV (Estado Actual)

### 1. `pacientes.csv` - Pacientes Activos
**Propósito**: Estado actual de pacientes en el hospital

**Campos**:
- `id_paciente` (string): Identificador único
- `edad` (int): Edad del paciente
- `genero` (string): F/M
- `nivel_urgencia` (int): 1-5 (1=crítico, 5=leve)
- `sintomas` (string): Descripción de síntomas
- `departamento` (string): Dpto actual asignado
- `estado` (string): En_espera, En_atencion, Alta, Transferido

**Ejemplo**:
```
id_paciente,edad,genero,nivel_urgencia,sintomas,departamento,estado
1,21,F,4,Dificultad respiratoria,Emergencias,Alta
2,45,M,1,Envenenamiento,Emergencias,En_atencion
```

**Registros**: 82 pacientes activos

---

### 2. `recursos.csv` - Capacidad Hospitalaria
**Propósito**: Disponibilidad actual de recursos por departamento

**Campos**:
- `departamento` (string): Nombre del departamento
- `total` (int): Camas/recursos totales
- `ocupados` (int): Camas/recursos en uso

**Cálculos automáticos**:
- `disponibles = total - ocupados`
- `ocupacion_pct = (ocupados / total) * 100`

**Ejemplo**:
```
departamento,total,ocupados
Emergencias,30,20
UCI,20,10
Hospitalizacion,35,22
```

**Departamentos**: 5 (Emergencias, UCI, Hospitalizacion, Cirugia, Consulta_Externa)

---

### 3. `personal.csv` - Personal del Hospital
**Propósito**: Personal disponible y sus asignaciones

**Campos**:
- `id_empleado` (string): ID único (D001, E001, etc)
- `rol` (string): Doctor o Enfermero
- `especialidad` (string): Especialidad médica
- `departamento_1` (string): Departamento primario
- `departamento_2` (string): Departamento secundario (para flexibilidad)
- `estado` (string): Disponible o Descanso

**Ejemplo**:
```
id_empleado,rol,especialidad,departamento_1,departamento_2,estado
D001,Doctor,Neurologia,Consulta_Externa,Emergencias,Descanso
E001,Enfermero,Enfermeria,Hospitalizacion,UCI,Disponible
```

**Total**: 55 empleados (20 doctores, 35 enfermeros)

---

### 4. `metricas.csv` - Resumen del Hospital
**Propósito**: Indicadores consolidados actuales

**Campos**:
- `pacientes_activos` (int): Cantidad de pacientes activos
- `ocupacion_pct` (float): Porcentaje de ocupación general
- `casos_criticos_pct` (float): Porcentaje de casos críticos

**Ejemplo**:
```
pacientes_activos,ocupacion_pct,casos_criticos_pct
41,68.3,26.8
```

**Registros**: 1 (resumen actual)

---

## Cambios en el Backend

### state_manager.py
- **Actualizado**: `load_patients()` → Lee de `pacientes.csv`
- **Actualizado**: `load_resources()` → Lee de `recursos.csv` (estructura simplificada)
- **Actualizado**: `load_staff()` → Lee de `personal.csv` (sin turnos, solo estado)
- **Actualizado**: `load_historic_metrics()` → Lee de `metricas.csv`
- **Nuevo método**: `_map_department_to_resource()` → Mapea departamentos a tipos de recursos
- **Simplificado**: `_normalize_patient()` → Elimina parseo de JSON y cálculos complejos

### main.py
- **Actualizado**: `/api/departments` → Retorna recursos por departamento
- **Actualizado**: `/api/resources` → Retorna disponibilidad simplificada
- **Actualizado**: `/api/staff` → Retorna personal simplificado
- **Actualizado**: `/api/metrics` → Retorna único registro de métricas

## Cambios en el Frontend

### PatientsTable.jsx
- Cambio: `departamento_asignado` → `departamento`
- Eliminado: Columna `tiempo_espera_min` (no calculable sin timestamp)
- Agregados: Columnas `edad`, `genero`, `sintomas`
- Mejorado: Estilos condicionales para urgencia y estado

## Flujo de Datos

```
CSV Files (estado actual)
    ↓
Backend (state_manager.py)
    ↓
API Endpoints (/api/*)
    ↓
Frontend Components
    ↓
Dashboard Display
```

## Ventajas de la Simplificación

✅ **Menor tamaño**: CSV más pequeños y fáciles de mantener
✅ **Menos redundancia**: Elimina datos históricos y calculables
✅ **Mayor rendimiento**: Carga más rápida de datos
✅ **Claridad**: Estructura muy clara y comprensible
✅ **Mantenibilidad**: Cambios más fáciles en el futuro
✅ **Escalabilidad**: Base sólida para agregar nuevas funcionalidades

## Compatibilidad con Agentes Multiagente

Los CSV simplificados mantienen todos los datos necesarios para:

1. **TriageAgent**: Usa `nivel_urgencia`, `sintomas`, `departamento`
2. **ResourceAgent**: Usa `recursos.csv` para asignación
3. **StaffAgent**: Usa `personal.csv` para staff assignment
4. **ForecastAgent**: Usa `metricas.csv` para predicciones
5. **WorkflowAgent**: Usa `estado` y `departamento` de pacientes
6. **QualityAgent**: Usa métricas generales
7. **OrchestratorAgent**: Orquesta entre todos

## Generación de nuevos CSV

Para regenerar los CSV simplificados desde los datos originales:

```bash
python simplify_csv.py
```

Este script:
1. Lee los CSV antiguos
2. Extrae solo datos esenciales
3. Genera los 4 nuevos CSV
4. Conserva los originales para referencia

## Monitoreo y Actualización

Para actualizar métricas del hospital:

```python
# Cálculos automáticos:
- ocupacion_pct se calcula al cargar en el endpoint
- disponibles = total - ocupados
- casos_criticos_pct se calcula desde pacientes.csv
```

No se requieren scripts complejos; los datos se cargan bajo demanda.

---

**Versión**: 2.0 (Simplificada)
**Fecha**: 2026-05-25
**Estado**: Producción
