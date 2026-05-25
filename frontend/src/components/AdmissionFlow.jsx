// src/components/AdmissionFlow.jsx
// Panel de seguimiento en tiempo real del flujo multiagente por paciente
import { useState } from "react";
import { sendAction } from "../services/websocket";

// ─── Definición de pasos del flujo ─────────────────────────────────────────
const STEPS = [
  {
    key: "arrived",
    label: "Ingreso recibido",
    icon: "🚑",
    events: ["PATIENT_ARRIVED", "PATIENT_ADDED"],
    agent: "Sistema",
  },
  {
    key: "triaged",
    label: "Triaje completado",
    icon: "🩺",
    events: ["PATIENT_TRIAGED"],
    agent: "TriageAgent",
  },
  {
    key: "bed",
    label: "Cama asignada",
    icon: "🛏️",
    events: ["RESOURCE_ALLOCATED"],
    agent: "ResourceAgent",
  },
  {
    key: "staff",
    label: "Personal asignado",
    icon: "👨‍⚕️",
    events: ["STAFF_ASSIGNED"],
    agent: "StaffAgent",
  },
  {
    key: "care",
    label: "Atención iniciada",
    icon: "💊",
    events: ["FORECAST_UPDATED", "SIMULATION_TICK"],
    agent: "ForecastAgent",
  },
];

// Estilos por prioridad
const PRIORITY_META = {
  CRITICAL: { label: "CRÍTICO", color: "#ef4444", bg: "rgba(239,68,68,0.12)", border: "rgba(239,68,68,0.4)" },
  HIGH:     { label: "ALTA",    color: "#f97316", bg: "rgba(249,115,22,0.12)", border: "rgba(249,115,22,0.4)" },
  MEDIUM:   { label: "MEDIA",   color: "#f59e0b", bg: "rgba(245,158,11,0.12)", border: "rgba(245,158,11,0.4)" },
  NORMAL:   { label: "NORMAL",  color: "#22c55e", bg: "rgba(34,197,94,0.12)",  border: "rgba(34,197,94,0.4)" },
};

function fmt(ts) {
  if (!ts) return "";
  return new Date(ts).toLocaleTimeString("es-ES", {
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

// ─── Barra de progreso de pasos ─────────────────────────────────────────────
function StepBar({ completedEvents, currentEventType }) {
  return (
    <div className="af-steps">
      {STEPS.map((step, idx) => {
        const done = step.events.some((e) => completedEvents.has(e));
        const active = !done && step.events.includes(currentEventType);
        return (
          <div key={step.key} className={`af-step${done ? " af-step--done" : ""}${active ? " af-step--active" : ""}`}>
            <div className="af-step-connector" style={{ opacity: idx === 0 ? 0 : 1 }} />
            <div className="af-step-icon">{done ? "✓" : active ? <span className="af-pulse" /> : step.icon}</div>
            <div className="af-step-info">
              <span className="af-step-label">{step.label}</span>
              {done && <span className="af-step-agent">{step.agent}</span>}
              {active && <span className="af-step-agent af-step-agent--active">Procesando…</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Card de resultado final ────────────────────────────────────────────────
function ResultCard({ result }) {
  if (!result) return null;
  const priority = result.priority || "MEDIUM";
  const meta = PRIORITY_META[priority] || PRIORITY_META.MEDIUM;

  return (
    <div className="af-result">
      <div className="af-result-header" style={{ borderColor: meta.border, background: meta.bg }}>
        <div>
          <p className="af-result-pid">{result.id_paciente}</p>
          <p className="af-result-label">Resultado final</p>
        </div>
        <span className="af-priority-badge" style={{ color: meta.color, borderColor: meta.border, background: meta.bg }}>
          {meta.label}
        </span>
      </div>

      <div className="af-result-grid">
        <div className="af-result-item">
          <span className="af-ri-label">Departamento</span>
          <span className="af-ri-val">{result.department || "—"}</span>
        </div>
        <div className="af-result-item">
          <span className="af-ri-label">Cama</span>
          <span className="af-ri-val af-mono">{result.bed_id || result.cama || "—"}</span>
        </div>
        <div className="af-result-item">
          <span className="af-ri-label">Médico</span>
          <span className="af-ri-val af-mono">{result.medico || "—"}</span>
        </div>
        <div className="af-result-item">
          <span className="af-ri-label">Enfermero</span>
          <span className="af-ri-val af-mono">{result.enfermero || "—"}</span>
        </div>
        <div className="af-result-item">
          <span className="af-ri-label">Tiempo estimado</span>
          <span className="af-ri-val">{result.estimated_time || "—"}</span>
        </div>
        <div className="af-result-item">
          <span className="af-ri-label">Estado</span>
          <span className="af-ri-val">{result.estado || "En evaluación"}</span>
        </div>
      </div>

      {result.reasons && result.reasons.length > 0 && (
        <div className="af-reasons">
          <p className="af-reasons-label">Razón de clasificación</p>
          <ul className="af-reasons-list">
            {result.reasons.map((r, i) => (
              <li key={i} className="af-reason-item">
                <span className="af-reason-dot" style={{ background: meta.color }} />
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.factors && result.factors.length > 0 && (
        <div className="af-factors">
          <p className="af-factors-label">Factores considerados</p>
          <div className="af-factors-list">
            {result.factors.map((f, i) => (
              <span key={i} className="af-factor-tag">{f}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Timeline de eventos por paciente ───────────────────────────────────────
function PatientTimeline({ events }) {
  const [expanded, setExpanded] = useState(null);

  if (!events || events.length === 0) return null;

  const labelMap = {
    PATIENT_ARRIVED: "Ingreso",
    PATIENT_ADDED: "Registro",
    PATIENT_TRIAGED: "Triaje",
    RESOURCE_ALLOCATED: "Cama asignada",
    STAFF_ASSIGNED: "Personal asignado",
    FORECAST_UPDATED: "Pronóstico actualizado",
    SIMULATION_TICK: "Avance simulado",
    PATIENT_ESCALATED: "Prioridad escalada",
    PATIENT_TRANSFERRED: "Transferido",
    PATIENT_DISCHARGED: "Alta",
    SATURATION_WARNING: "Alerta saturación",
    CRITICAL_ALERT: "Alerta crítica",
    WORKFLOW_ALERT: "Alerta de flujo",
  };

  const iconMap = {
    PATIENT_ARRIVED: "🚑",
    PATIENT_ADDED: "📋",
    PATIENT_TRIAGED: "🩺",
    RESOURCE_ALLOCATED: "🛏️",
    STAFF_ASSIGNED: "👨‍⚕️",
    FORECAST_UPDATED: "📊",
    SIMULATION_TICK: "⏱️",
    PATIENT_ESCALATED: "⬆️",
    PATIENT_TRANSFERRED: "🔄",
    PATIENT_DISCHARGED: "✅",
    SATURATION_WARNING: "⚠️",
    CRITICAL_ALERT: "🚨",
    WORKFLOW_ALERT: "⚙️",
  };

  return (
    <div className="af-timeline">
      <h4 className="af-timeline-title">Historial del paciente</h4>
      <div className="af-tl-list">
        {events.map((ev, idx) => {
          const isLast = idx === events.length - 1;
          const isOpen = expanded === idx;
          const label = labelMap[ev.event_type] || ev.event_type.replace(/_/g, " ");
          const icon = iconMap[ev.event_type] || "📌";
          const hasDetail = ev.payload && Object.keys(ev.payload).length > 0;

          return (
            <div key={idx} className={`af-tl-row${isLast ? " af-tl-row--last" : ""}`}>
              <div className="af-tl-left">
                <span className="af-tl-time">{fmt(ev.timestamp)}</span>
              </div>
              <div className="af-tl-connector">
                <span className="af-tl-dot">{icon}</span>
                {!isLast && <div className="af-tl-line" />}
              </div>
              <div className="af-tl-right">
                <button
                  className="af-tl-label-btn"
                  onClick={() => setExpanded(isOpen ? null : idx)}
                  aria-expanded={isOpen}
                >
                  <span className="af-tl-label">{label}</span>
                  {hasDetail && (
                    <span className="af-tl-expand">{isOpen ? "▲" : "▼"}</span>
                  )}
                </button>
                {isOpen && hasDetail && (
                  <div className="af-tl-detail">
                    {ev.payload.reason && <p className="af-tl-reason">"{ev.payload.reason}"</p>}
                    {ev.payload.priority && (
                      <p>Prioridad: <strong>{ev.payload.priority}</strong></p>
                    )}
                    {ev.payload.department && (
                      <p>Departamento: <strong>{ev.payload.department}</strong></p>
                    )}
                    {ev.payload.bed_id && (
                      <p>Cama: <strong className="af-mono">{ev.payload.bed_id}</strong></p>
                    )}
                    {ev.payload.medico_id && (
                      <p>Médico: <strong className="af-mono">{ev.payload.medico_id}</strong></p>
                    )}
                    {ev.payload.message && <p>{ev.payload.message}</p>}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Botones de acción ──────────────────────────────────────────────────────
function SimActions({ patientId, onAction }) {
  const [loadingAction, setLoadingAction] = useState(null);

  const actions = [
    { key: "SIMULATE_HOUR", label: "⏱ Simular 1 hora", cls: "af-btn--sim" },
    { key: "ESCALATE",      label: "⬆ Escalar prioridad", cls: "af-btn--escalate" },
    { key: "TRANSFER",      label: "🔄 Transferir",  cls: "af-btn--transfer" },
    { key: "DISCHARGE",     label: "✅ Dar alta",    cls: "af-btn--discharge" },
  ];

  const handleAction = (actionKey) => {
    setLoadingAction(actionKey);
    sendAction(actionKey, patientId);
    if (onAction) onAction(actionKey, patientId);
    setTimeout(() => setLoadingAction(null), 1200);
  };

  return (
    <div className="af-actions">
      <p className="af-actions-label">Acciones de simulación</p>
      <div className="af-actions-grid">
        {actions.map((a) => (
          <button
            key={a.key}
            className={`af-btn ${a.cls}`}
            onClick={() => handleAction(a.key)}
            disabled={!!loadingAction}
            id={`af-btn-${a.key.toLowerCase()}`}
          >
            {loadingAction === a.key ? <span className="af-btn-spinner" /> : a.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Componente principal AdmissionFlow ─────────────────────────────────────
function AdmissionFlow({ patientId, patientEvents, result, isProcessing }) {
  if (!patientId) return null;

  const completedEvents = new Set((patientEvents || []).map((e) => e.event_type));
  const currentEvent = patientEvents && patientEvents.length > 0
    ? patientEvents[patientEvents.length - 1]?.event_type
    : null;

  const isComplete = completedEvents.has("STAFF_ASSIGNED") || completedEvents.has("FORECAST_UPDATED");

  return (
    <div className="af-wrapper" aria-live="polite">
      {/* Encabezado del panel */}
      <div className="af-header">
        <div className="af-header-left">
          <span className="af-header-icon">🏥</span>
          <div>
            <h3 className="af-header-title">Seguimiento del Paciente</h3>
            <p className="af-header-pid">
              <span className="af-mono">{patientId}</span>
              {isProcessing && !isComplete && (
                <span className="af-processing-label">
                  <span className="af-pulse-dot" /> Procesando admisión…
                </span>
              )}
              {isComplete && (
                <span className="af-complete-label">✓ Proceso completado</span>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Barra de pasos */}
      <StepBar completedEvents={completedEvents} currentEventType={currentEvent} />

      {/* Resultado cuando el triaje terminó */}
      {result && result.priority && <ResultCard result={result} />}

      {/* Timeline expandible */}
      <PatientTimeline events={patientEvents || []} />

      {/* Botones de acción (solo cuando el proceso terminó) */}
      {isComplete && patientId && (
        <SimActions patientId={patientId} />
      )}
    </div>
  );
}

export default AdmissionFlow;
