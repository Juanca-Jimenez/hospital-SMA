import { useEffect, useState } from "react"

import Navbar from "./navbar"
import PatientForm from "./PatientForm"
import EventTimeline from "./EventTimeLine"
import HospitalMetrics from "./HospitalMetrics"
import AgentStatus from "./AgentStatus"
import PatientsTable from "./PatientsTable"

import { connectWebSocket, fetchPatients } from "../services/websocket"
import "../styles/dashboard.css"

function Dashboard() {
  const [events, setEvents] = useState([])
  const [metrics, setMetrics] = useState({})
  const [patients, setPatients] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let mounted = true

    const loadPatients = async () => {
      try {
        const data = await fetchPatients(100)
        if (!mounted) return
        setPatients(data.patients || [])
      } catch (err) {
        console.error(err)
        setError("No se pudieron cargar los pacientes desde el CSV.")
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadPatients()

    connectWebSocket((data) => {
      if (data.event_type === "INITIAL_PATIENTS") {
        setPatients(data.patients || [])
        setMetrics(data.global_state || {})
        return
      }

      setEvents((prev) => [data, ...prev])

      if (data.patient) {
        setPatients((prev) => [data.patient, ...prev])
      }

      if (data.global_state) {
        setMetrics(data.global_state)
      }
    })

    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="dashboard-shell">
      <Navbar />

      <div className="dashboard-content">
        <div className="dashboard-hero panel">
          <div>
            <p className="eyebrow">Tablero hospitalario</p>
            <h1 className="hero-title">Pacientes desde CSV</h1>
            <p className="hero-copy">
              Visualiza los pacientes cargados desde el archivo CSV y monitorea los eventos en tiempo real.
            </p>
          </div>

          <div className="hero-status">
            {loading ? "Cargando pacientes..." : `${patients.length} pacientes cargados`}
          </div>
        </div>

        {error && <div className="alert-banner">{error}</div>}

        <div className="metrics-row">
          <HospitalMetrics metrics={metrics} patientsCount={patients.length} />
        </div>

        <div className="dashboard-grid">
          <div className="dashboard-main-panel">
            <EventTimeline events={events} />
          </div>
          <div className="dashboard-side-panel">
            <AgentStatus />
            <PatientForm />
          </div>
        </div>

        <PatientsTable patients={patients} loading={loading} />
      </div>
    </div>
  )
}

export default Dashboard