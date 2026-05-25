// src/components/AdmissionResult.jsx
import React from "react";

// ─── Colores por prioridad ─────────────────────────────────────────────────
const PRIORITY_STYLE = {
  CRITICAL: { label: "CRÍTICO", cls: "ar-badge--critical", dot: "#ef4444" },
  HIGH: { label: "ALTA", cls: "ar-badge--high", dot: "#f97316" },
  MEDIUM: { label: "MEDIA", cls: "ar-badge--medium", dot: "#f59e0b" },
  LOW: { label: "BAJA", cls: "ar-badge--low", dot: "#22c55e" },
};

const TIMELINE_ICONS = {
  PATIENT_ARRIVED: "🚑",
  PATIENT_ADDED: "📋",
  PATIENT_TRIAGED: "🩺",
  RESOURCE_ALLOCATED: "🛏️",
  STAFF_ASSIGNED: "👨‍⚕️",
  MONITORING: "📊",
  CRITICAL_ALERT: "🚨",
  WORKFLOW_ALERT: "⚠️",
  DEFAULT: "📌",
};

function fmt(ts) {
  if (!ts) return "";
  return new Date(ts).toLocaleTimeString("es-ES", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function timelineLabel(event_type) {
  const map = {
    PATIENT_ARRIVED: "Ingreso",
    PATIENT_ADDED: "Registro",
    PATIENT_TRIAGED: "Triaje",
    RESOURCE_ALLOCATED: "Cama asignada",
    STAFF_ASSIGNED: "Médico asignado",
    MONITORING: "Monitoreo",
    CRITICAL_ALERT: "Alerta crítica",
    WORKFLOW_ALERT: "Alerta de flujo",
    SATURATION_WARNING: "Alerta saturación",
    ORCHESTRATOR_OBSERVATION: "Observación",
  };
  return map[event_type] || event_type.replace(/_/g, " ");
}

// ─── AdmissionResult ──────────────────────────────────────────────────────
function AdmissionResult({ result, patientEvents }) {
  if (!result) return null;

  const priority = result.priority || result.clasificacion || "MEDIUM";
  const pStyle = PRIORITY_STYLE[priority] || PRIORITY_STYLE.MEDIUM;

  return (
    <div className="ar-wrapper" aria-live="polite">
      {/* ── Panel resultado ── */}
      <div className="ar-card">
        <div className="ar-card-header">
          <h3 className="ar-title">Resultado de evaluación</h3>
          <span className={`ar-badge ${pStyle.cls}`}>
            <span className="ar-badge-dot" style={{ background: pStyle.dot }} />
            {pStyle.label}
          </span>
        </div>

        <div className="ar-grid">
          {/* Paciente */}
          <div className="ar-item">
            <span className="ar-item-label">Paciente</span>
            <span className="ar-item-value ar-mono">
              {result.id_paciente || result.patient_id || "—"}
            </span>
          </div>

          {/* Departamento */}
          <div className="ar-item">
            <span className="ar-item-label">Departamento</span>
            <span className="ar-item-value">
              {result.department || result.departamento || "—"}
            </span>
          </div>

          {/* Cama */}
          <div className="ar-item">
            <span className="ar-item-label">Cama asignada</span>
            <span className="ar-item-value ar-mono">
              {result.bed || result.cama || "—"}
            </span>
          </div>

          {/* Personal */}
          <div className="ar-item">
            <span className="ar-item-label">Personal asignado</span>
            <span className="ar-item-value ar-mono">
              {result.staff || result.personal || "—"}
            </span>
          </div>

          {/* Tiempo estimado */}
          <div className="ar-item">
            <span className="ar-item-label">Tiempo estimado</span>
            <span className="ar-item-value">
              {result.estimated_time || result.tiempo_estimado || "—"}
            </span>
          </div>

          {/* Estado */}
          <div className="ar-item">
            <span className="ar-item-label">Estado</span>
            <span className="ar-item-value">
              {result.estado || result.status || "En evaluación"}
            </span>
          </div>
        </div>

        {/* Razón */}
        {result.reason || result.razon ? (
          <div className="ar-reason">
            <span className="ar-reason-label">Razón de clasificación</span>
            <p className="ar-reason-text">{result.reason || result.razon}</p>
          </div>
        ) : null}

        {/* Factores */}
        {(result.factors || result.factores) && (
          <div className="ar-factors">
            <span className="ar-factors-label">Factores considerados</span>
            <div className="ar-factors-list">
              {(result.factors || result.factores).map((f, i) => (
                <span key={i} className="ar-factor-tag">
                  {f}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Timeline paciente ── */}
      {patientEvents && patientEvents.length > 0 && (
        <div className="ar-timeline">
          <h4 className="ar-timeline-title">Historial del paciente</h4>
          <div className="ar-timeline-list">
            {patientEvents.map((ev, idx) => {
              const icon = TIMELINE_ICONS[ev.event_type] || TIMELINE_ICONS.DEFAULT;
              const isLast = idx === patientEvents.length - 1;
              return (
                <div key={idx} className={`ar-tl-row${isLast ? " ar-tl-row--last" : ""}`}>
                  <div className="ar-tl-left">
                    <span className="ar-tl-time">{fmt(ev.timestamp)}</span>
                  </div>
                  <div className="ar-tl-connector">
                    <span className="ar-tl-icon">{icon}</span>
                    {!isLast && <div className="ar-tl-line" />}
                  </div>
                  <div className="ar-tl-right">
                    <span className="ar-tl-label">{timelineLabel(ev.event_type)}</span>
                    {ev.payload?.reason && (
                      <p className="ar-tl-detail">{ev.payload.reason}</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default AdmissionResult;
