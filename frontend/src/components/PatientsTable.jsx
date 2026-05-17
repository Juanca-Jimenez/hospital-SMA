function PatientsTable({ patients, loading }) {
  return (
    <div className="panel table-panel">
      <div className="panel-header">
        <div>
          <h2>Pacientes hospitalarios</h2>
          <p className="panel-subtitle">Registros cargados desde el CSV de admisiones.</p>
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
                <th>Departamento</th>
                <th>Espera (min)</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((patient, index) => (
                <tr key={index}>
                  <td>{patient.id_paciente}</td>
                  <td>{patient.edad}</td>
                  <td>{patient.genero}</td>
                  <td>{patient.nivel_urgencia}</td>
                  <td>{patient.departamento_asignado}</td>
                  <td>{patient.tiempo_espera_min}</td>
                  <td>{patient.estado}</td>
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