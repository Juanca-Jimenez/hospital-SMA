import React from "react";

const AgentStatus = ({ events = [] }) => {
  console.log("AgentStatus render - eventos recibidos:", events.length);

  const knownAgents = [
    "TriageAgent",
    "ResourceAgent",
    "StaffAgent",
    "ForecastAgent",
    "WorkflowAgent",
    "QualityAgent",
    "OrchestratorAgent",
  ];

  const lastActionByAgent = {};

  events.forEach((event) => {
    let agent = null;
    switch (event.event_type) {
      case "PATIENT_ADDED":
      case "PATIENT_ARRIVED":
        agent = "Sistema";
        break;
      case "PATIENT_TRIAGED":
        agent = "TriageAgent";
        break;
      case "RESOURCE_ALLOCATED":
        agent = "ResourceAgent";
        break;
      case "STAFF_ASSIGNED":
        agent = "StaffAgent";
        break;
      case "SATURATION_WARNING":
        agent = "ForecastAgent";
        break;
      case "WORKFLOW_ALERT":
        agent = "WorkflowAgent";
        break;
      case "CRITICAL_ALERT":
        agent = "QualityAgent";
        break;
      case "ORCHESTRATOR_OBSERVATION":
        agent = "OrchestratorAgent";
        break;
      default:
        agent = event.payload?.agent || null;
    }

    if (agent && !lastActionByAgent[agent]) {
      let actionDescription = "";
      switch (event.event_type) {
        case "PATIENT_TRIAGED":
          actionDescription = `Triaje: ${event.payload.priority}`;
          break;
        case "RESOURCE_ALLOCATED":
          actionDescription = `Asignó cama ${event.payload.bed_type}`;
          break;
        case "STAFF_ASSIGNED":
          actionDescription = `Asignó a ${event.payload.staff?.nombre || "medico"}`;
          break;
        case "SATURATION_WARNING":
          actionDescription = `Saturacion ${event.payload.occupancy}%`;
          break;
        case "ORCHESTRATOR_OBSERVATION":
          actionDescription = `Observo evento`;
          break;
        default:
          actionDescription = event.event_type.replace(/_/g, " ");
      }
      lastActionByAgent[agent] = {
        timestamp: event.timestamp,
        description: actionDescription,
      };
    }
  });

  const formatTime = (timestamp) => {
    if (!timestamp) return "";
    const date = new Date(timestamp);
    return date.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  };

  return (
    <div className="agent-status-card">
      <h3 className="agent-status-title">Estado de agentes</h3>
      <div className="agent-list">
        {knownAgents.map((agent) => {
          const lastAction = lastActionByAgent[agent];
          const hasAction = !!lastAction;
          return (
            <div key={agent} className={`agent-item ${hasAction ? "active" : "inactive"}`}>
              <div className="agent-name">{agent}</div>
              {hasAction ? (
                <div className="agent-last-action">
                  <span className="action-desc">{lastAction.description}</span>
                  <span className="action-time">{formatTime(lastAction.timestamp)}</span>
                </div>
              ) : (
                <div className="agent-no-action">Sin actividad reciente</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AgentStatus;