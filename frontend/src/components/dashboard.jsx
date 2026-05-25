import { useEffect, useState } from "react";

import Navbar from "./navbar";
import PatientForm from "./PatientForm";
import EventTimeline from "./EventTimeLine"; // Asegúrate que el nombre del archivo coincida (EventTimeline.jsx o EventTimeLine.jsx)
import HospitalMetrics from "./HospitalMetrics";
import AgentStatus from "./AgentStatus";
import PatientsTable from "./PatientsTable";

import { connectWebSocket, fetchPatients, fetchDepartments, fetchResources, fetchStaff, fetchMetrics } from "../services/websocket";
import "../styles/dashboard.css";

function Dashboard() {
  const [events, setEvents] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [patients, setPatients] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [resources, setResources] = useState([]);
  const [staff, setStaff] = useState([]);
  const [historicalMetrics, setHistoricalMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    let wsUnsubscribe = null;

    const loadAllData = async () => {
      try {
        // Cargar todos los datos en paralelo
        const [patientsData, deptData, resourcesData, staffData, metricsData] = await Promise.all([
          fetchPatients(100),
          fetchDepartments(),
          fetchResources(),
          fetchStaff(),
          fetchMetrics(),
        ]);

        if (!mounted) return;

        setPatients(patientsData.patients || []);
        setDepartments(deptData.departments || []);
        setResources(resourcesData.resources || []);
        setStaff(staffData.staff || []);
        setHistoricalMetrics(metricsData.metrics || []);
      } catch (err) {
        console.error(err);
        setError("No se pudieron cargar los datos desde los CSV.");
      } finally {
        if (mounted) setLoading(false);
      }
    };

    loadAllData();

    // Conectar WebSocket
    wsUnsubscribe = connectWebSocket((data) => {
      if (!mounted) return;

      // Garantizar timestamp
      const eventWithTimestamp = {
        ...data,
        timestamp: data.timestamp || new Date().toISOString(),
      };

      if (data.event_type === "INITIAL_SNAPSHOT") {
        console.log("INITIAL_SNAPSHOT recibido, eventos:", data.events?.length);
        setPatients(data.patients || []);
        setMetrics(data.global_state || {});
        // Cargar eventos históricos
        const historicalEvents = (data.events || []).map((ev) => ({
          ...ev,
          timestamp: ev.timestamp || new Date().toISOString(),
        }));
        setEvents(historicalEvents.slice(0, 200));
        return;
      }

      // Nuevo evento
      setEvents((prev) => {
        const newEvents = [eventWithTimestamp, ...prev];
        return newEvents.slice(0, 200);
      });

      const patient = data.payload?.patient;
      if (patient) {
        setPatients((prev) => [
          patient,
          ...prev.filter((item) => item.id_paciente !== patient.id_paciente),
        ]);
      }

      if (data.global_state) {
        setMetrics(data.global_state);
      }
    });

    return () => {
      mounted = false;
      if (wsUnsubscribe && typeof wsUnsubscribe === "function") wsUnsubscribe();
    };
  }, []);

  return (
    <div className="dashboard-shell">
      <Navbar />

      <div className="dashboard-content">
        <div className="dashboard-hero panel">
          <div>
            <p className="eyebrow">Tablero hospitalario</p>
            <h1 className="hero-title">Pacientes desde CSV</h1>
            <p className="hero-copy">
              Visualiza los pacientes, departamentos, recursos y personal cargados desde los archivos CSV y monitorea
              los eventos en tiempo real.
            </p>
          </div>

          <div className="hero-status">
            {loading
              ? "Cargando datos..."
              : `${patients.length} pacientes, ${departments.length} departamentos, ${resources.length} recursos, ${staff.length} personal`}
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
            <AgentStatus events={events} />
            <PatientForm />
          </div>
        </div>

        <PatientsTable patients={patients} loading={loading} />
      </div>
    </div>
  );
}

export default Dashboard;
