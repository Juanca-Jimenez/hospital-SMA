let socket = null
// Usar URLs explícitas del backend
const API_BASE = "http://localhost:8000/api"
const WS_BASE = "ws://localhost:8000"

export const connectWebSocket = (onMessage) => {
  socket = new WebSocket(`${WS_BASE}/ws`)

  socket.onopen = () => {
    console.log("WebSocket Connected")
  }

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    onMessage(data)
  }

  socket.onerror = (error) => {
    console.error(error)
  }

  socket.onclose = () => {
    console.log("WebSocket Closed")
  }
}

export const fetchPatients = async (limit = 100) => {
  const response = await fetch(`${API_BASE}/patients?limit=${limit}`)
  if (!response.ok) {
    throw new Error("No se pudieron cargar los pacientes")
  }
  return response.json()
}

export const fetchDepartments = async () => {
  const response = await fetch(`${API_BASE}/departments`)
  if (!response.ok) {
    throw new Error("No se pudieron cargar los departamentos")
  }
  return response.json()
}

export const fetchResources = async () => {
  const response = await fetch(`${API_BASE}/resources`)
  if (!response.ok) {
    throw new Error("No se pudieron cargar los recursos")
  }
  return response.json()
}

export const fetchStaff = async () => {
  const response = await fetch(`${API_BASE}/staff`)
  if (!response.ok) {
    throw new Error("No se pudieron cargar el personal")
  }
  return response.json()
}

export const fetchMetrics = async () => {
  const response = await fetch(`${API_BASE}/metrics`)
  if (!response.ok) {
    throw new Error("No se pudieron cargar las métricas")
  }
  return response.json()
}

export const sendPatient = (patientData) => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ action: "NEW_PATIENT", patient: patientData }))
  }
}