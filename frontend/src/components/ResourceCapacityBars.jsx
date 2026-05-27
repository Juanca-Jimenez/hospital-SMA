// src/components/ResourceCapacityBars.jsx
import { useEffect } from "react";

function CapacityBar({ label, used, total, unit = "" }) {
  const percentage = total > 0 ? Math.round((used / total) * 100) : 0;
  const available = Math.max(0, total - used);
  
  // Determinar color según ocupación
  let colorClass = "capacity-low";
  if (percentage >= 90) {
    colorClass = "capacity-critical";
  } else if (percentage >= 70) {
    colorClass = "capacity-high";
  } else if (percentage >= 50) {
    colorClass = "capacity-medium";
  }

  return (
    <div className="capacity-bar-container">
      <div className="capacity-header">
        <span className="capacity-label">{label}</span>
        <span className="capacity-stats">
          {used}/{total} {unit && `(${unit})`}
        </span>
      </div>
      <div className="capacity-bar-wrapper">
        <div className={`capacity-bar ${colorClass}`} style={{ width: `${percentage}%` }}>
          <span className="capacity-percentage">{percentage}%</span>
        </div>
      </div>
      <div className="capacity-footer">
        <span className="available-text">Disponibles: {available}</span>
      </div>
    </div>
  );
}

function ResourceCapacityBars({ metrics, staffData = [], patients = [] }) {
  const resources = metrics.resources || {};
  const staff = staffData || [];

  // Datos de recursos - Manejo robusto de los datos
  const icu = resources.ICU || { total: 0, occupied: 0, available: 0 };
  const general = resources.GENERAL || { total: 0, occupied: 0, available: 0 };
  const other = resources.OTHER || { total: 0, occupied: 0, available: 0 };

  // Calcular pacientes sin cama asignada (pendientes de triaje o en triaje)
  const patientsWithoutBed = patients.filter((p) => {
    const estado = p.estado || p.estado;
    return estado && ["En_evaluacion", "En_triaje", "TRIAGED"].includes(estado) && !p.cama && !p.bed_id;
  }).length;

  // Debug: log de los recursos recibidos
  useEffect(() => {
    console.log("[ResourceCapacityBars] Recursos actualizados:", {
      ICU: icu,
      GENERAL: general,
      OTHER: other,
      patientsWithoutBed,
      totalPatients: patients.length,
      metrics: metrics
    });
  }, [metrics, patientsWithoutBed]);

  // Datos de personal
  const availableStaff = staff.filter((s) => s.estado === "Disponible").length;
  const totalStaff = staff.length || 0;

  // Camas totales
  const totalBeds = (icu.total || 0) + (general.total || 0) + (other.total || 0);
  const occupiedBeds = (icu.occupied || 0) + (general.occupied || 0) + (other.occupied || 0);

  return (
    <div className="resource-capacity-section">
      <div className="capacity-header-title">
        <h3 className="capacity-title">📊 Capacidad de Recursos</h3>
        <p className="capacity-subtitle">Estado actual de camas, equipos y personal</p>
      </div>

      <div className="capacity-grid">
        {/* Camas UCI */}
        <div className="capacity-item">
          <CapacityBar
            label="🏥 Camas UCI"
            used={icu.occupied || 0}
            total={icu.total || 0}
            unit="camas"
          />
        </div>

        {/* Camas Generales */}
        <div className="capacity-item">
          <CapacityBar
            label="🛏️ Camas Generales"
            used={general.occupied || 0}
            total={general.total || 0}
            unit="camas"
          />
        </div>

        {/* Otras Camas/Recursos */}
        {(other.total > 0 || other.occupied > 0) && (
          <div className="capacity-item">
            <CapacityBar
              label="🔧 Otros Recursos"
              used={other.occupied || 0}
              total={other.total || 0}
              unit="recursos"
            />
          </div>
        )}

        {/* Total de Camas */}
        <div className="capacity-item">
          <CapacityBar
            label="💼 Total de Camas"
            used={occupiedBeds}
            total={totalBeds}
            unit="camas"
          />
        </div>

        {/* Personal Disponible */}
        <div className="capacity-item">
          <CapacityBar
            label="👥 Personal Médico"
            used={totalStaff - availableStaff}
            total={totalStaff}
            unit="personal"
          />
        </div>
      </div>

      {/* Resumen rápido */}
      <div className="capacity-summary">
        <div className="summary-stat">
          <span className="summary-label">Ocupación General:</span>
          <span className="summary-value">
            {totalBeds > 0 ? Math.round((occupiedBeds / totalBeds) * 100) : 0}%
          </span>
        </div>
        <div className="summary-stat">
          <span className="summary-label">Camas Disponibles:</span>
          <span className="summary-value">{totalBeds - occupiedBeds}</span>
        </div>
        <div className="summary-stat">
          <span className="summary-label">Pacientes sin cama:</span>
          <span className="summary-value" style={{ color: patientsWithoutBed > 0 ? '#f59e0b' : '#10b981' }}>
            {patientsWithoutBed}
          </span>
        </div>
        <div className="summary-stat">
          <span className="summary-label">Personal Disponible:</span>
          <span className="summary-value">{availableStaff}/{totalStaff}</span>
        </div>
      </div>
    </div>
  );
}

export default ResourceCapacityBars;
