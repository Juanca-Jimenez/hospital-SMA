// src/components/AdmissionFlow.jsx
// Panel de seguimiento clínico rediseñado - Estructura jerárquica y clara
import { useState, useEffect } from "react";
import { fetchDepartments, sendAction } from "../services/websocket";

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

function TransferDialog({ patientId, currentDepartment, onClose }) {
  const [departments, setDepartments] = useState([]);
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    const loadDepartments = async () => {
      try {
        const data = await fetchDepartments();
        if (!mounted) return;
        const options = Array.isArray(data.departments) ? data.departments : [];
        const filtered = options.filter((dept) => dept.departamento !== currentDepartment);
        setDepartments(filtered);
        setSelectedDepartment(filtered[0]?.departamento || "");
      } catch (err) {
        setError("No se pudieron cargar los departamentos");
      }
    };
    loadDepartments();
    return () => { mounted = false; };
  }, [currentDepartment]);

  const handleConfirm = () => {
    if (!selectedDepartment) return;
    setLoading(true);
    sendAction("TRANSFER", patientId, { destination: selectedDepartment });
    setTimeout(() => {
      setLoading(false);
      onClose();
    }, 800);
  };

  return (
    <div className="cf-transfer-dialog">
      <div className="cf-transfer-header">
        <h4>Transferir paciente</h4>
        <button className="cf-transfer-close" onClick={onClose} aria-label="Cerrar">×</button>
      </div>

      <div className="cf-transfer-body">
        <p>Departamento actual: <strong>{currentDepartment || "Pendiente"}</strong></p>

        {error && <div className="cf-transfer-error">{error}</div>}

        <div className="cf-transfer-label">
          Seleccione el nuevo departamento
        </div>

        <div className="cf-transfer-grid">
          {departments.length === 0 ? (
            <div className="cf-transfer-empty">No hay departamentos disponibles</div>
          ) : (
            departments.map((dept) => {
              const occupied = dept.ocupados ?? 0;
              const total = dept.total ?? 0;
              const available = Math.max((dept.disponibles ?? total - occupied), 0);
              const occupancyPct = total > 0 ? Math.round((occupied / total) * 100) : 0;
              const isSelected = selectedDepartment === dept.departamento;

              return (
                <button
                  key={dept.departamento}
                  type="button"
                  className={`cf-transfer-option ${isSelected ? "selected" : ""}`}
                  onClick={() => setSelectedDepartment(dept.departamento)}
                >
                  <div className="cf-transfer-option-top">
                    <strong>{dept.departamento}</strong>
                    <span className="cf-transfer-option-badge">{available} libres</span>
                  </div>
                  <div className="cf-transfer-option-meta">
                    <span>{occupied}/{total} ocupadas</span>
                    <span>{occupancyPct}% ocupación</span>
                  </div>
                  <div className="cf-transfer-capacity-bar">
                    <div
                      className="cf-transfer-capacity-fill"
                      style={{ width: `${occupancyPct}%` }}
                    />
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      <div className="cf-transfer-actions">
        <button className="cf-action-btn cf-action-btn-secondary" onClick={onClose} disabled={loading}>
          Cancelar
        </button>
        <button
          className="cf-action-btn cf-action-btn-primary"
          onClick={handleConfirm}
          disabled={loading || !selectedDepartment}
        >
          {loading ? "Transferiendo..." : "Confirmar transferencia"}
        </button>
      </div>
    </div>
  );
}

// 5. ACCIONES DISPONIBLES
function AvailableActions({ patientId, isComplete, estado, currentDepartment }) {
  const [loading, setLoading] = useState(null);
  const [showTransferDialog, setShowTransferDialog] = useState(false);
  
  const isDischarge = estado?.includes("Alta");
  
  const actions = !isDischarge ? [
    { key: "REEVALUATE", label: "🩺 Reevaluar", color: "primary" },
    { key: "TRANSFER", label: "🏥 Transferir", color: "secondary" },
    { key: "ESCALATE", label: "⬆️ Escalar", color: "warning" },
  ] : [];

  const handleAction = (actionKey) => {
    if (actionKey === "TRANSFER") {
      setShowTransferDialog(true);
      return;
    }
    setLoading(actionKey);
    sendAction(actionKey, patientId);
    setTimeout(() => setLoading(null), 1200);
  };

  if (!isComplete || actions.length === 0) return null;

  return (
    <>
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

      {showTransferDialog && (
        <TransferDialog
          patientId={patientId}
          currentDepartment={currentDepartment}
          onClose={() => setShowTransferDialog(false)}
        />
      )}
    </>
  );
}

// 6. IMPACTO HOSPITALARIO
function HospitalImpact({ metrics }) {
  return (
    <div className="cf-impact">
      CLASIFICACIÓN HOSPITALARIA
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
          currentDepartment={result?.department || result?.departamento}
        />
      )}
      {metrics && <HospitalImpact metrics={metrics} />}
    </div>
  );
}

export default AdmissionFlow;
