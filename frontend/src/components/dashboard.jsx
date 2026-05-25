import { useEffect, useState, useRef, useCallback } from "react";

import Navbar from "./navbar";
import PatientForm from "./PatientForm";
import AdmissionFlow from "./AdmissionFlow";
import EventTimeline from "./EventTimeLine";
import HospitalMetrics from "./HospitalMetrics";
import AgentStatus from "./AgentStatus";
import PatientsTable from "./PatientsTable";

import {
  connectWebSocket,
  fetchPatients,
  fetchDepartments,
  fetchResources,
  fetchStaff,
  fetchMetrics,
} from "../services/websocket";
import "../styles/dashboard.css";

// Eventos que pertenecen al flujo de un paciente específico
const PATIENT_FLOW_EVENTS = new Set([
  "PATIENT_ARRIVED",
  "PATIENT_ADDED",
  "PATIENT_TRIAGED",
  "RESOURCE_ALLOCATED",
  "STAFF_ASSIGNED",
  "FORECAST_UPDATED",
  "SIMULATION_TICK",
  "PATIENT_ESCALATED",
  "PATIENT_TRANSFERRED",
  "PATIENT_DISCHARGED",
  "CRITICAL_ALERT",
  "WORKFLOW_ALERT",
]);

function Dashboard() {
  // ── Estado global ────────────────────────────────────────────────────────
  const [events, setEvents]               = useState([]);
  const [metrics, setMetrics]             = useState({});
  const [patients, setPatients]           = useState([]);
  const [loading, setLoading]             = useState(true);
  const [error, setError]                 = useState("");

  // ── Estado del flujo de admisión activo ──────────────────────────────────
  const [activePatientId, setActivePatientId]     = useState(null);
  const [patientEvents, setPatientEvents]         = useState([]);
  const [admissionResult, setAdmissionResult]     = useState(null);
  const [isProcessing, setIsProcessing]           = useState(false);

  // Ref para el id activo (evita closure stale en el WS callback)
  const activePatientIdRef = useRef(null);
  const patientEventsRef   = useRef([]);

  useEffect(() => {
    activePatientIdRef.current = activePatientId;
  }, [activePatientId]);

  // ── Carga inicial de datos REST ──────────────────────────────────────────
  useEffect(() => {
    let mounted = true;

    const loadAll = async () => {
      try {
        const [patientsData] = await Promise.all([
          fetchPatients(100),
          fetchDepartments(),
          fetchResources(),
          fetchStaff(),
          fetchMetrics(),
        ]);
        if (!mounted) return;
        setPatients(patientsData.patients || []);
      } catch (err) {
        console.error(err);
        setError("No se pudieron cargar los datos desde los CSV.");
      } finally {
        if (mounted) setLoading(false);
      }
    };

    loadAll();

    // ── WebSocket ────────────────────────────────────────────────────────
    const wsUnsubscribe = connectWebSocket((data) => {
      if (!mounted) return;

      const ts = data.timestamp || new Date().toISOString();
      const eventWithTs = { ...data, timestamp: ts };

      // ── Snapshot inicial ──────────────────────────────────────────────
      if (data.event_type === "INITIAL_SNAPSHOT") {
        setPatients(data.patients || []);
        setMetrics(data.global_state || {});
        const hist = (data.events || []).map((ev) => ({
          ...ev,
          timestamp: ev.timestamp || ts,
        }));
        setEvents(hist.slice(0, 200));
        return;
      }

      // ── Actualizar lista global de eventos ────────────────────────────
      setEvents((prev) => [eventWithTs, ...prev].slice(0, 200));

      // ── Actualizar métricas globales ──────────────────────────────────
      if (data.global_state) setMetrics(data.global_state);

      // ── Actualizar tabla de pacientes ─────────────────────────────────
      const patFromPayload =
        data.payload?.patient ||
        (data.event_type === "PATIENT_ARRIVED" ? data.payload : null);
      if (patFromPayload) {
        setPatients((prev) => [
          patFromPayload,
          ...prev.filter((p) => p.id_paciente !== patFromPayload.id_paciente),
        ]);
      }

      // ── Flujo del paciente activo ─────────────────────────────────────
      const evPatientId =
        data.payload?.patient?.id_paciente ||
        data.payload?.patient_id ||
        data.payload?.id_paciente ||
        data.payload?.patient?.patient_id;

      const currentActive = activePatientIdRef.current;

      // Cuando un nuevo paciente LLEGA → inicializar flujo
      if (
        data.event_type === "PATIENT_ARRIVED" ||
        data.event_type === "PATIENT_ADDED"
      ) {
        const newId = evPatientId || data.payload?.id_paciente;
        if (newId) {
          activePatientIdRef.current = newId;
          setActivePatientId(newId);
          patientEventsRef.current = [eventWithTs];
          setPatientEvents([eventWithTs]);
          setAdmissionResult({
            id_paciente: newId,
            priority: null,
            department: null,
            bed_id: null,
            medico: null,
            enfermero: null,
            estado: "En evaluación",
            reasons: [],
            factors: [],
            estimated_time: null,
          });
          setIsProcessing(true);
        }
        return;
      }

      // Para eventos de flujo: solo acumular si son del paciente activo
      if (
        PATIENT_FLOW_EVENTS.has(data.event_type) &&
        currentActive &&
        (!evPatientId || evPatientId === currentActive)
      ) {
        patientEventsRef.current = [...patientEventsRef.current, eventWithTs];
        setPatientEvents([...patientEventsRef.current]);

        // Enriquecer resultado según evento
        if (data.event_type === "PATIENT_TRIAGED") {
          setAdmissionResult((prev) => ({
            ...(prev || {}),
            id_paciente: evPatientId || currentActive,
            priority: data.payload?.priority,
            reasons: data.payload?.reasons || [],
            factors: data.payload?.factors || [],
            estimated_time: data.payload?.estimated_time,
            estado: "Triaje completado",
          }));
        }

        if (data.event_type === "RESOURCE_ALLOCATED") {
          setAdmissionResult((prev) => ({
            ...(prev || {}),
            department: data.payload?.department,
            bed_id: data.payload?.bed_id,
            estado: "Cama asignada",
          }));
        }

        if (data.event_type === "STAFF_ASSIGNED") {
          setAdmissionResult((prev) => ({
            ...(prev || {}),
            medico: data.payload?.medico_id || data.payload?.staff?.id_empleado,
            enfermero: data.payload?.enfermero_id || data.payload?.nurse?.id_empleado,
            estado: "Personal asignado",
          }));
        }

        if (
          data.event_type === "FORECAST_UPDATED" ||
          data.event_type === "SIMULATION_TICK"
        ) {
          setIsProcessing(false);
          setAdmissionResult((prev) => ({
            ...(prev || {}),
            estado: data.payload?.result?.new_estado || "Atención iniciada",
          }));
        }

        if (data.event_type === "PATIENT_ESCALATED") {
          setAdmissionResult((prev) => ({
            ...(prev || {}),
            priority: data.payload?.new_priority,
            estado: `Prioridad escalada → ${data.payload?.new_priority}`,
          }));
        }

        if (data.event_type === "PATIENT_DISCHARGED") {
          setAdmissionResult((prev) => ({
            ...(prev || {}),
            estado: "Alta",
          }));
          setIsProcessing(false);
        }
      }
    });

    return () => {
      mounted = false;
      if (typeof wsUnsubscribe === "function") wsUnsubscribe();
    };
  }, []);

  // Callback: el formulario acaba de enviar un paciente
  const handleNewPatientSent = useCallback(() => {
    // Resetear flujo anterior para esperar el nuevo PATIENT_ARRIVED
    setActivePatientId(null);
    setPatientEvents([]);
    setAdmissionResult(null);
    setIsProcessing(true);
    patientEventsRef.current = [];
    activePatientIdRef.current = null;
  }, []);

  return (
    <div className="dashboard-shell">
      <Navbar />

      <div className="dashboard-content">
        {/* Hero */}
        <div className="dashboard-hero panel">
          <div>
            <p className="eyebrow">Sistema Multiagente</p>
            <h1 className="hero-title">Admisión Hospitalaria</h1>
            <p className="hero-copy">
              Ingresa un paciente y observa cómo los agentes toman decisiones
              en tiempo real: triaje, asignación de cama y personal.
            </p>
          </div>
          <div className="hero-status">
            {loading
              ? "Cargando datos…"
              : `${patients.length} pacientes activos`}
          </div>
        </div>

        {error && <div className="alert-banner">{error}</div>}

        {/* Métricas */}
        <div className="metrics-row">
          <HospitalMetrics metrics={metrics} patientsCount={patients.length} />
        </div>

        {/* Grid principal */}
        <div className="dashboard-grid">
          {/* Columna izquierda: timeline global de agentes */}
          <div className="dashboard-main-panel">
            <EventTimeline events={events} />
          </div>

          {/* Columna derecha: formulario + flujo activo */}
          <div className="dashboard-side-panel">
            <AgentStatus events={events} />

            {/* Formulario de admisión */}
            <PatientForm onResult={handleNewPatientSent} />

            {/* Panel de flujo multiagente del paciente activo */}
            {(isProcessing || activePatientId) && (
              <AdmissionFlow
                patientId={activePatientId}
                patientEvents={patientEvents}
                result={admissionResult}
                isProcessing={isProcessing}
              />
            )}
          </div>
        </div>

        {/* Tabla de pacientes */}
        <PatientsTable patients={patients} loading={loading} />
      </div>
    </div>
  );
}

export default Dashboard;
