// src/components/AgentStatus.jsx

const agents = [
  "TriageAgent",
  "ResourceAgent",
  "StaffAgent",
  "ForecastAgent",
  "WorkflowAgent",
  "QualityAgent",
];

function AgentStatus() {
  return (
    <div className="bg-white p-5 rounded-xl shadow-md">
      <h2 className="text-xl font-bold mb-4">
        Estado de Agentes
      </h2>

      <div className="space-y-2">
        {agents.map((agent) => (
          <div
            key={agent}
            className="flex items-center justify-between border-b py-2"
          >
            <span>{agent}</span>

            <span className="text-green-600 font-bold">
              ● ONLINE
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AgentStatus;