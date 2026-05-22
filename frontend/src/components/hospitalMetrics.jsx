// src/components/HospitalMetrics.jsx

function HospitalMetrics({ metrics, patientsCount = 0 }) {
  const icu = metrics.resources?.ICU || {}
  const general = metrics.resources?.GENERAL || {}

  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="metric-label">Pacientes activos</div>
        <div className="metric-value">{metrics.active_patients || 0}</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Pacientes en espera</div>
        <div className="metric-value">{metrics.waiting_patients || 0}</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Camas UCI libres</div>
        <div className="metric-value">{icu.available ?? 0}</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Personal disponible</div>
        <div className="metric-value">{metrics.available_staff || 0}</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Ocupación UCI</div>
        <div className="metric-value">{icu.total ? `${Math.round(((icu.total - icu.available) / icu.total) * 100)}%` : "0%"}</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Alertas activas</div>
        <div className="metric-value">{metrics.alerts?.length || 0}</div>
      </div>
    </div>
  )
}

export default HospitalMetrics;