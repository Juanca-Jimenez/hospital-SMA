let socket = null;
const API_BASE = "http://localhost:8000/api";
const WS_BASE = "ws://localhost:8000";

export const connectWebSocket = (onMessage) => {
  socket = new WebSocket(`${WS_BASE}/ws`);

  socket.onopen = () => {
    console.log("[WS] Conectado");
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error("[WS] Error parseando mensaje:", e);
    }
  };

  socket.onerror = (error) => {
    console.error("[WS] Error:", error);
  };

  socket.onclose = () => {
    console.log("[WS] Desconectado");
  };

  // Retornar función de limpieza
  return () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.close();
    }
  };
};

// ─── Enviar nuevo paciente (payload clínico) ───────────────────────────────
// Formato:
// {
//   edad: number,
//   genero: string,
//   motivo_consulta: string,
//   sintomas: string[],
//   vitales: {
//     presion: { sistolica: number, diastolica: number },
//     temperatura: number,
//     frecuencia: number,
//     spo2: number
//   },
//   dolor: number
// }
export const sendPatient = (patientData) => {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    console.warn("[WS] Socket no disponible, reintentando en 800ms...");
    setTimeout(() => sendPatient(patientData), 800);
    return;
  }
  socket.send(
    JSON.stringify({
      action: "NEW_PATIENT",
      patient: patientData,
    })
  );
};

// ─── Enviar acción de simulación ───────────────────────────────────────────
// Acciones: SIMULATE_HOUR | ESCALATE | TRANSFER | DISCHARGE
export const sendAction = (action, patientId, extra = {}) => {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    console.warn("[WS] Socket no disponible para acción:", action);
    setTimeout(() => sendAction(action, patientId, extra), 800);
    return;
  }
  socket.send(
    JSON.stringify({
      action,
      patient_id: patientId,
      ...extra,
    })
  );
};


// ─── Fetches REST ──────────────────────────────────────────────────────────
export const fetchPatients = async (limit = 100) => {
  const response = await fetch(`${API_BASE}/patients?limit=${limit}`);
  if (!response.ok) throw new Error("No se pudieron cargar los pacientes");
  return response.json();
};

export const fetchDepartments = async () => {
  const response = await fetch(`${API_BASE}/departments`);
  if (!response.ok) throw new Error("No se pudieron cargar los departamentos");
  return response.json();
};

export const fetchResources = async () => {
  const response = await fetch(`${API_BASE}/resources`);
  if (!response.ok) throw new Error("No se pudieron cargar los recursos");
  return response.json();
};

export const fetchStaff = async () => {
  const response = await fetch(`${API_BASE}/staff`);
  if (!response.ok) throw new Error("No se pudieron cargar el personal");
  return response.json();
};

export const fetchMetrics = async () => {
  const response = await fetch(`${API_BASE}/metrics`);
  if (!response.ok) throw new Error("No se pudieron cargar las métricas");
  return response.json();
};