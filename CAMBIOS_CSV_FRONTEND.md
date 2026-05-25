# Carga de CSV al Frontend - Cambios Realizados

## Resumen
Se han realizado cambios significativos en el backend y frontend para cargar correctamente los archivos CSV y exponerlos a través de API REST. Los datos ahora se cargan en paralelo en el dashboard del hospital.

## Cambios en el Backend (`backend/main.py`)

### Nuevos Endpoints REST

1. **`GET /api/patients`** - Ya existía
   - Retorna lista de pacientes desde el CSV `pacientes_admisiones.csv`

2. **`GET /api/departments`** (NUEVO)
   - Obtiene métricas de departamentos desde `operaciones_departamentos.csv`
   - Retorna los datos más recientes por departamento
   - Ejemplo: `http://localhost:8000/api/departments`

3. **`GET /api/resources`** (NUEVO)
   - Obtiene disponibilidad de recursos desde `recursos_disponibilidad.csv`
   - Incluye camas, quirófanos, equipos, etc.
   - Ejemplo: `http://localhost:8000/api/resources`

4. **`GET /api/staff`** (NUEVO)
   - Obtiene información del personal desde `personal_turnos.csv`
   - Incluye médicos, enfermeros, turnos y estado
   - Ejemplo: `http://localhost:8000/api/staff`

5. **`GET /api/metrics`** (NUEVO)
   - Obtiene métricas históricas desde `historico_metricas.csv`
   - Retorna los últimos 100 registros
   - Ejemplo: `http://localhost:8000/api/metrics`

### Características
- Todos los endpoints manejan valores NaN/None correctamente
- Incluyen manejo de errores completo
- Retornan JSON con `count` para facilitar el uso en el frontend

## Cambios en el Frontend

### `src/services/websocket.js`
Se agregaron nuevas funciones de utilidad:
- `fetchDepartments()` - Carga departamentos
- `fetchResources()` - Carga recursos
- `fetchStaff()` - Carga personal
- `fetchMetrics()` - Carga métricas históricas

Todas las funciones:
- Usan la variable de entorno `VITE_API_URL`
- Retornan JSON parseado
- Lanzan errores descriptivos si fallan

### `src/components/dashboard.jsx`
Se actualizó el componente principal:
- **Carga en paralelo**: Usa `Promise.all()` para cargar todos los datos simultáneamente
- **Nuevos estados**: `departments`, `resources`, `staff`, `historicalMetrics`
- **Mejor mensaje de estado**: Muestra cantidad de registros por tipo
- **Manejo de errores**: Mensajes claros si algo falla

```javascript
// Carga paralela de todos los datos
const [patientsData, deptData, resourcesData, staffData, metricsData] = await Promise.all([
  fetchPatients(100),
  fetchDepartments(),
  fetchResources(),
  fetchStaff(),
  fetchMetrics(),
]);
```

### Variables de Entorno

Se crearon archivos `.env` y `.env.production`:
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Archivos CSV Disponibles

| CSV | Descripción | Registros |
|-----|-------------|-----------|
| `pacientes_admisiones.csv` | Pacientes con datos clínicos | ~100-200 |
| `operaciones_departamentos.csv` | Métricas por departamento | Últimas por dpto |
| `recursos_disponibilidad.csv` | Disponibilidad de recursos | 5 tipos |
| `personal_turnos.csv` | Personal y turnos | ~50 personas |
| `historico_metricas.csv` | Series temporales de métricas | Histórico |

## Instrucciones de Uso

### Iniciar el Servidor Backend
```bash
cd hospital-SMA
.venv\Scripts\Activate
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Iniciar el Frontend
```bash
cd frontend
npm install  # si es primera vez
npm run dev -- --host localhost --port 5174
```

### Probar los Endpoints
```bash
python test_csv_endpoints.py
```

## Diagnóstico

Si los datos no se cargan:

1. **Verificar que el backend está activo**
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **Verificar que los CSV existen**
   - `backend/data/pacientes_admisiones.csv`
   - `backend/data/operaciones_departamentos.csv`
   - `backend/data/recursos_disponibilidad.csv`
   - `backend/data/personal_turnos.csv`
   - `backend/data/historico_metricas.csv`

3. **Ver errores en la consola del navegador**
   - F12 → Console → Ver mensajes de error

4. **Verificar variables de entorno**
   - Asegurar que `frontend/.env` exista con las URLs correctas

## Comportamiento Esperado

- **Al cargar el dashboard**: Se muestran 7 tipos de datos (pacientes, departamentos, recursos, personal, métricas)
- **Websocket**: Sigue recibiendo eventos en tiempo real
- **Actualizaciones**: Los datos se actualizan cuando llegan nuevos eventos
- **Performance**: La carga paralela mejora significativamente el rendimiento

## Posibles Mejoras Futuras

1. Agregar paginación a los endpoints
2. Agregar filtros (por departamento, estado, etc.)
3. Cacheo en el frontend para optimizar
4. Sincronización automática con WebSocket
5. Visualizaciones específicas para cada tipo de dato
