hospital-SMA - Sistema Multiagente de Gestión Hospitalaria Integral

Descripción
-----------
Este proyecto es un prototipo de gestor hospitalario con arquitectura de backend en Python y frontend en React/Vite.
Incluye:
- Backend con FastAPI, WebSocket y agentes de simulación.
- Frontend con React + Vite para visualización de pacientes, transferencias y métricas.
- Datos iniciales en CSV y un flujo en tiempo real que actualiza el dashboard desde eventos.

Estructura del repositorio
--------------------------
- backend/           : Código servidor, agentes, gestión de estado y rutas API.
  - main.py          : Entrada principal de FastAPI y WebSocket.
  - state_manager.py : Lógica de estado hospitalario, pacientes y eventos.
  - agents.py        : Definición de agentes (triage, recursos, staff, etc.).
  - event_bus.py     : Publicación/subscripción de eventos.
  - rules.py         : Reglas de simulación y atención.
  - simulation.py    : Lógica para avanzar el tiempo y cambios de estado.
  - data/            : CSV de recursos, pacientes, personal y métricas.

- frontend/          : Aplicación React para interactuar con el sistema.
  - src/             : Componentes principales y estilos.
  - public/          : Archivos públicos del frontend.
  - package.json     : Dependencias y scripts de Vite.

- README.md          : Resumen rápido del proyecto.
- README.txt         : Esta guía de instalación completa.

Requisitos previos
------------------
- Python 3.11 o superior.
- Node.js 20+ y npm.

Instalación y ejecución
-----------------------
1. Clonar el repositorio
   git clone <URL_DEL_REPO>
   cd hospital-SMA

2. Preparar el backend
   - Crear y activar el entorno virtual:
     powershell:
       python -m venv .venv
       .\.venv\Scripts\Activate.ps1
     bash:
       python -m venv .venv
       source .venv/Scripts/activate

   - Instalar dependencias:
       pip install -r backend/requirements.txt

   - Ejecutar el servidor de desarrollo:
       uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

3. Preparar el frontend
   - Ir al directorio frontend:
       cd frontend

   - Instalar dependencias:
       npm install

   - Ejecutar la app React:
       npm run dev

4. Abrir la aplicación
   - Backend disponible en: http://localhost:8000
   - Frontend disponible en: http://localhost:5174

Características principales
--------------------------
- Registro de nuevos pacientes mediante WebSocket.
- Transferencia de pacientes entre departamentos.
- Simulación de avance de tiempo y escalado de prioridad.
- Dashboard reactivo con estado global y flujo de eventos.
- Consultas REST para pacientes, departamentos, recursos, personal y métricas.

API y endpoints relevantes
--------------------------
Backend expone estas rutas:
- GET /api/patients        : Lista de pacientes activos.
- GET /api/departments     : Información de departamentos y capacidades.
- GET /api/resources       : Recursos por departamento.
- GET /api/staff           : Personal hospitalario.
- GET /api/metrics         : Métricas generales.
- GET /api/state           : Estado global del hospital.
- GET /api/health          : Salud del servicio.
- WS  /ws                  : WebSocket para eventos en tiempo real.

Flujo de desarrollo
-------------------
- El frontend se conecta a través de WebSocket a `ws://localhost:8000/ws`.
- Las acciones del usuario se envían con un objeto JSON que incluye `action` y datos.
- El backend procesa acciones como `NEW_PATIENT`, `TRANSFER`, `DISCHARGE`, `ESCALATE`, `SIMULATE_HOUR`.
- El backend publica eventos como `PATIENT_ARRIVED`, `PATIENT_TRANSFERRED`, `PATIENT_DISCHARGED`, `SIMULATION_TICK`.
- El frontend actualiza el dashboard con el estado global y la línea de tiempo de eventos.

Notas importantes
-----------------
- El estado principal se mantiene en memoria durante la ejecución.
- Los datos iniciales se cargan desde los CSV en `backend/data/`.
- Si se desea limpiar el entorno, basta con eliminar el directorio `frontend/node_modules/` y el archivo `.venv`.

Sugerencias de uso
------------------
- Abrir dos terminales: uno para backend y otro para frontend.
- Primero arrancar `uvicorn` y luego `npm run dev`.
- Usar el panel React para crear y transferir pacientes.
- Verificar la consola del backend para eventos y logs de agentes.

Estructura de carpetas recomendada para trabajo
-----------------------------------------------
- backend/  : modificar lógica de agentes, reglas y estado.
- frontend/ : cambiar UI, componentes y estilos.
- backend/data/: actualizar CSV si se necesitan nuevos escenarios.

Contacto y mantenimiento
------------------------
- Este documento sirve como guía de instalación y uso.
- Para cambios en el proyecto, editar primero la documentación de `README.md` y mantenerla sincronizada con este archivo.
