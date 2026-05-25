function PatientsTable({ patients, loading }) {
  return (
    <div className="panel table-panel">
      <div className="panel-header">
        <div>
          <h2>Pacientes hospitalarios</h2>
          <p className="panel-subtitle">Pacientes activos del sistema.</p>
        </div>
        <span className="badge">{patients.length} registros</span>
      </div>

      {loading ? (
        <div className="empty-state">Cargando datos...</div>
      ) : patients.length === 0 ? (
        <div className="empty-state">No se encontraron pacientes.</div>
      ) : (
        <div className="table-scroll">
          <table className="patient-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Edad</th>
                <th>Género</th>
                <th>Urgencia</th>
                <th>Síntomas</th>
                <th>Departamento</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((patient, index) => (
                <tr key={index}>
                  <td>{patient.id_paciente}</td>
                  <td>{patient.edad}</td>
                  <td>{patient.genero}</td>
                  <td>
                    <span className={`urgency-badge urgency-${patient.nivel_urgencia}`}>
                      {patient.nivel_urgencia}
                    </span>
                  </td>
                  <td>{patient.sintomas}</td>
                  <td>{patient.departamento || "Pendiente"}</td>
                  <td>
                    <span className={`status-badge status-${patient.estado}`}>
                      {patient.estado}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default PatientsTable