// src/components/AdmissionFlow.jsx
// Panel de seguimiento clínico rediseñado - Estructura jerárquica y clara
import { useState } from "react";
import { sendAction } from "../services/websocket";

const STEPS = [
  { key: "arrived", label: "Ingreso", icon: "🚑", events: ["PATIENT_ARRIVED", "PATIENT_ADDED"] },
  { key: "triaged", label: "Triaje", icon: "🩺", events: ["PATIENT_TRIAGED"] },
  { key: "bed", label: "Recurso", icon: "🛏️", events: ["RESOURCE_ALLOCATED"] },
  { key: "staff", label: "Personal", icon: "👨‍⚕️", events: ["STAFF_ASSIGNED"] },
  { key: "care", label: "Atención", icon: "💊", events: ["FORECAST_UPDATED", "SIMULATION_TICK"] },
];

const PRIORITY_CONFIG = {
  CRITICAL: { label: "CRÍTICO", icon: "🔴", color: "#ef4444" },
  HIGH:     { label: "ALTA", icon: "🔴", color: "#f97316" },
  MEDIUM:   { label: "MEDIA", icon: "🟡", color: "#f59e0b" },
  NORMAL:   { label: "NORMAL", icon: "🟢", color: "#22c55e" },
};

const CLINICAL_EVENTS = new Set([
  "PATIENT_ARRIVED", "PATIENT_ADDED", "PATIENT_TRIAGED", "PATIENT_ESCALATED",
  "RESOURCE_ALLOCATED", "STAFF_ASSIGNED", "PATIENT_TRANSFERRED", "PATIENT_DISCHARGED"
]);

function fmt(ts) {
  if (!ts) return "";
  return new Date(ts).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
}

// 1. RESUMEN CLÍNICO
function ClinicalSummary({ patientId, result }) {
  if (!result) return null;
  
  const priority = result.priority || "MEDIUM";
  const config = PRIORITY_CONFIG[priority] || PRIORITY_CONFIG.MEDIUM;
  
  const estado = result.estado?.toLowerCase().includes("alta") ? "Alta" :
                 result.estado?.toLowerCase().includes("atención") ? "En atención" :
                 result.estado?.toLowerCase().includes("triaje") ? "Evaluación" :
                 result.estado || "Procesando";

  return (
    <div className="cf-summary-card">
      <div className="cf-summary-header">
        <h4 className="cf-summary-pid">{patientId}</h4>
        <p className="cf-summary-subtitle">{result.motivo_consulta || "Admisión hospitalaria"}</p>
        <span className="cf-priority-badge" style={{ color: config.color }}></span>
      </div>

      <div className="cf-summary-details">
        <div className="cf-detail-item">
          <span className="cf-detail-label">Estado</span>
          <span className="cf-detail-value">{estado}</span>
        </div>
        <div className="cf-detail-item">
          <span className="cf-detail-label">Departamento</span>
          <span className="cf-detail-value">{result.department || "—"}</span>
        </div>
        <div className="cf-detail-item">
          <span className="cf-detail-label">Ubicación</span>
          <span className="cf-detail-value">{result.bed_id || "—"}</span>
        </div>
        <div className="cf-detail-item">
          <span className="cf-detail-label">Responsables</span>
          <div className="cf-staff-list">
            {result.medico && <span className="cf-staff-badge">👨‍⚕️ {result.medico}</span>}
            {result.enfermero && <span className="cf-staff-badge">👩‍⚕️ {result.enfermero}</span>}
            {!result.medico && !result.enfermero && <span className="cf-staff-badge">—</span>}
          </div>
        </div>
      </div>
    </div>
  );
}

// 2. BARRA DE PROGRESO
function ProgressBar({ completedEvents, currentEventType }) {
  return (
    <div className="cf-progress-container">
      {STEPS.map((step, idx) => {
        const done = step.events.some((e) => completedEvents.has(e));
        const active = !done && step.events.includes(currentEventType);
        
        return (
          <div key={step.key} className={`cf-progress-step ${done ? 'done' : active ? 'active' : 'pending'}`}>
            <div className="cf-step-icon">{done ? "✓" : step.icon}</div>
            <span className="cf-step-label">{step.label}</span>
          </div>
        );
      })}
    </div>
  );
}

// 3. EXPLICACIÓN DE DECISIÓN
function DecisionExplanation({ result, onToggle, isExpanded }) {
  if (!result || !result.reasons) return null;
  
  const reasons = Array.isArray(result.reasons) ? result.reasons.slice(0, 3) : [];
  const hasMore = Array.isArray(result.reasons) && result.reasons.length > 3;
  
  if (reasons.length === 0) return null;

  return (
    <details className="cf-decision" open={isExpanded}>
      <summary className="cf-decision-header" onClick={(e) => {
        e.preventDefault();
        onToggle();
      }}>
        <h3 className="cf-decision-title">¿Por qué esta decisión?</h3>
        <span className="cf-decision-toggle">▼</span>
      </summary>
      
      <div className="cf-decision-content">
        <div className="cf-reasons-list">
          {reasons.map((r, i) => (
            <div key={i} className="cf-reason-chip">
              {r}
            </div>
          ))}
        </div>
        
        {(hasMore || result.factors?.length > 0) && (
          <details className="cf-details-expandable" style={{ marginTop: '12px' }}>
            <summary style={{ cursor: 'pointer', color: '#6b21a8', fontWeight: 600, fontSize: '12px' }}>
              Ver análisis completo
            </summary>
            <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #e9d5ff' }}>
              {hasMore && (
                <>
                  <p style={{ fontSize: '12px', fontWeight: 700, color: '#6b21a8', margin: '0 0 8px' }}>Otras razones:</p>
                  {result.reasons.slice(3).map((r, i) => (
                    <div key={i} style={{ fontSize: '13px', color: '#334155', marginBottom: '6px' }}>• {r}</div>
                  ))}
                </>
              )}
              {result.factors?.length > 0 && (
                <>
                  <p style={{ fontSize: '12px', fontWeight: 700, color: '#6b21a8', margin: '12px 0 8px' }}>Factores considerados:</p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {result.factors.map((f, i) => (
                      <div key={i} style={{
                        padding: '6px 10px',
                        background: '#eff6ff',
                        color: '#1d4ed8',
                        fontSize: '12px',
                        fontWeight: 600,
                        borderRadius: '8px',
                        border: '1px solid #bfdbfe'
                      }}>{f}</div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </details>
        )}
      </div>
    </details>
  );
}

// 4. HISTORIAL CLÍNICO
function ClinicalHistory({ events }) {
  const [expanded, setExpanded] = useState(false);
  
  const clinicalEvents = (events || []).filter(e => CLINICAL_EVENTS.has(e.event_type));
  
  if (clinicalEvents.length === 0) return null;

  const eventLabels = {
    PATIENT_ARRIVED: "Ingreso",
    PATIENT_ADDED: "Registro",
    PATIENT_TRIAGED: "Triaje",
    RESOURCE_ALLOCATED: "Cama asignada",
    STAFF_ASSIGNED: "Personal asignado",
    PATIENT_ESCALATED: "Escalada de prioridad",
    PATIENT_TRANSFERRED: "Transferencia",
    PATIENT_DISCHARGED: "Alta",
  };

  return (
    <details className="cf-history" open={expanded} onChange={() => setExpanded(!expanded)}>
      <summary className="cf-history-header">
        <h3 className="cf-history-title">Actividad del sistema</h3>
        <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>{clinicalEvents.length} evento{clinicalEvents.length !== 1 ? 's' : ''}</span>
        <span className="cf-history-toggle">▼</span>
      </summary>
      
      <div className="cf-history-content">
        {clinicalEvents.map((ev, idx) => (
          <div key={idx} className="cf-history-event">
            <div className="cf-event-time">{fmt(ev.timestamp)}</div>
            <div className="cf-event-timeline">
              <div className="cf-event-dot">
                {eventLabels[ev.event_type] || ev.event_type}
              </div>
            </div>
          </div>
        ))}
      </div>
    </details>
  );
}

// 5. ACCIONES DISPONIBLES
function AvailableActions({ patientId, isComplete, estado }) {
  const [loading, setLoading] = useState(null);
  
  const isDischarge = estado?.includes("Alta");
  
  const actions = !isDischarge ? [
    { key: "REEVALUATE", label: "🩺 Reevaluar", color: "primary" },
    { key: "TRANSFER", label: "🏥 Transferir", color: "secondary" },
    { key: "ESCALATE", label: "⬆️ Escalar", color: "warning" },
  ] : [];

  const handleAction = (actionKey) => {
    setLoading(actionKey);
    sendAction(actionKey, patientId);
    setTimeout(() => setLoading(null), 1200);
  };

  if (!isComplete || actions.length === 0) return null;

  return (
    <div className="cf-actions">
      {actions.map((a) => (
        <button
          key={a.key}
          className={`cf-action-btn cf-action-btn-${a.color}`}
          onClick={() => handleAction(a.key)}
          disabled={!!loading}
        >
          {loading === a.key ? "..." : a.label}
        </button>
      ))}
    </div>
  );
}

// 6. IMPACTO HOSPITALARIO
function HospitalImpact({ metrics }) {
  return (
    <div className="cf-impact">
      <div className="cf-impact-item">
        <span className="cf-impact-label">Camas</span>
        <span className="cf-impact-value">{metrics?.occupied_beds || 0}/{metrics?.total_beds || 10}</span>
      </div>
      <div className="cf-impact-item">
        <span className="cf-impact-label">Ocupación</span>
        <span className="cf-impact-value">{Math.round((metrics?.occupancy_rate || 0) * 100)}%</span>
      </div>
      <div className="cf-impact-item">
        <span className="cf-impact-label">Personal</span>
        <span className="cf-impact-value">{metrics?.available_staff || 0}</span>
      </div>
    </div>
  );
}

// COMPONENTE PRINCIPAL
function AdmissionFlow({ patientId, patientEvents, result, isProcessing, metrics }) {
  if (!patientId) return null;

  const completedEvents = new Set((patientEvents || []).map((e) => e.event_type));
  const currentEvent = patientEvents && patientEvents.length > 0
    ? patientEvents[patientEvents.length - 1]?.event_type
    : null;

  const isComplete = completedEvents.has("STAFF_ASSIGNED") || completedEvents.has("FORECAST_UPDATED");
  const [expandedDecision, setExpandedDecision] = useState(false);

  return (
    <div className="cf-wrapper" aria-live="polite">
      {result && <ClinicalSummary patientId={patientId} result={result} />}
      <ProgressBar completedEvents={completedEvents} currentEventType={currentEvent} />
      <DecisionExplanation 
        result={result}
        isExpanded={expandedDecision}
        onToggle={() => setExpandedDecision(!expandedDecision)}
      />
      <ClinicalHistory events={patientEvents || []} />
      {isComplete && (
        <AvailableActions 
          patientId={patientId}
          isComplete={isComplete}
          estado={result?.estado}
        />
      )}
      {metrics && <HospitalImpact metrics={metrics} />}
    </div>
  );
}

export default AdmissionFlow;
