// src/components/HospitalMetrics.jsx

function HospitalMetrics({ metrics }) {
  return (
    <div className="grid grid-cols-2 gap-4">

      <div className="bg-white p-4 rounded-xl shadow-md">
        <h3 className="text-gray-500">
          Pacientes Activos
        </h3>

        <p className="text-3xl font-bold">
          {metrics.active_patients || 0}
        </p>
      </div>

      <div className="bg-white p-4 rounded-xl shadow-md">
        <h3 className="text-gray-500">
          Alertas
        </h3>

        <p className="text-3xl font-bold text-red-600">
          {metrics.alerts?.length || 0}
        </p>
      </div>

      <div className="bg-white p-4 rounded-xl shadow-md">
        <h3 className="text-gray-500">
          Admisiones
        </h3>

        <p className="text-3xl font-bold">
          {metrics.total_admissions || 0}
        </p>
      </div>

      <div className="bg-white p-4 rounded-xl shadow-md">
        <h3 className="text-gray-500">
          Altas
        </h3>

        <p className="text-3xl font-bold">
          {metrics.total_discharges || 0}
        </p>
      </div>

    </div>
  );
}

export default HospitalMetrics;