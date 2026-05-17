let socket = null
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"

export const connectWebSocket = (onMessage) => {
  socket = new WebSocket("ws://localhost:8000/ws")

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
  const response = await fetch(`${API_BASE}/api/patients?limit=${limit}`)
  if (!response.ok) {
    throw new Error("No se pudieron cargar los pacientes")
  }
  return response.json()
}

export const sendPatient = (patientData) => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(patientData))
  }
}