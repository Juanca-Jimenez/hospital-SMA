// src/components/HospitalMetrics.jsx

function HospitalMetrics({ metrics, patientsCount = 0 }) {
  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="metric-label">Pacientes cargados</div>
        <div className="metric-value">{patientsCount}</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Pacientes activos</div>
        <div className="metric-value">{metrics.active_patients || 0}</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Admisiones</div>
        <div className="metric-value">{metrics.total_admissions || 0}</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Altas</div>
        <div className="metric-value">{metrics.total_discharges || 0}</div>
      </div>
    </div>
  )
}

export default HospitalMetrics;