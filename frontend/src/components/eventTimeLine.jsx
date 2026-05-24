// frontend/src/components/EventTimeline.jsx
import React from "react";

// Convierte un evento en una card con texto legible
const formatEventToCard = (event) => {
  const { event_type, payload, timestamp } = event;
  const time = timestamp
    ? new Date(timestamp).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : "";

  // Helper para obtener nombre de paciente desde diferentes estructuras
  const getPatientName = (p) => {
    if (!p) return "desconocido";
    return p.id_paciente || p.patient_id || "?";
  };

  // Helper para obtener datos del paciente desde payload (puede estar en payload.patient o directamente en payload)
  const getPatientData = (payload) => {
    return payload.patient || payload;
  };

  switch (event_type) {
    case "PATIENT_ARRIVED":
    case "PATIENT_ADDED":
      const patientData = getPatientData(payload);
      const eventTitle = event_type === "PATIENT_ADDED" ? "Paciente registrado" : "Nuevo paciente";
      return {
        title: eventTitle,
        agent: "Sistema",
        description: `Paciente ${getPatientName(patientData)} (${patientData.edad || "?"} años, ${patientData.genero || "?"}) – Urgencia ${patientData.nivel_urgencia || "?"}. Sintomas: "${patientData.sintomas || "ninguno"}"`,
        time,
        color: "blue",
      };

    case "PATIENT_TRIAGED":
      const priority = payload.priority;
      let priorityText = "";
      if (priority === "CRITICAL") priorityText = "CRITICO";
      else if (priority === "HIGH") priorityText = "ALTA";
      else priorityText = "NORMAL";
      return {
        title: "Triaje realizado",
        agent: "TriageAgent",
        description: `Paciente ${getPatientName(payload.patient)} clasificado como ${priorityText}. Razón: ${payload.reason || "reglas aplicadas"}`,
        time,
        color: priority === "CRITICAL" ? "red" : priority === "HIGH" ? "orange" : "green",
      };

    case "RESOURCE_ALLOCATED":
      return {
        title: "Recurso asignado",
        agent: "ResourceAgent",
        description: `Paciente ${getPatientName(payload.patient)} → Cama ${payload.bed_type} (${payload.department || payload.bed_type}). Prioridad: ${payload.priority}`,
        time,
        color: "purple",
      };

    case "STAFF_ASSIGNED":
      const staff = payload.staff;
      return {
        title: "Personal asignado",
        agent: "StaffAgent",
        description: `Paciente ${getPatientName(payload.patient)} atendido por ${staff?.nombre || "?"} (${staff?.especialidad || staff?.rol || "?"}). Razón: ${payload.reason || "especialista disponible"}`,
        time,
        color: "teal",
      };

    case "SATURATION_WARNING":
      return {
        title: "Alerta de saturacion",
        agent: "ForecastAgent",
        description: `Recurso ${payload.resource} al ${payload.occupancy}% de ocupación.`,
        time,
        color: "yellow",
      };

    case "WORKFLOW_ALERT":
      return {
        title: "Alerta de flujo",
        agent: "WorkflowAgent",
        description: `Paciente ${getPatientName(payload.patient)}: ${payload.action || "accion sugerida"}. Razón: ${payload.reason}`,
        time,
        color: "orange",
      };

    case "CRITICAL_ALERT":
      return {
        title: "ALERTA CRITICA",
        agent: "QualityAgent",
        description: payload.message || `Paciente ${getPatientName(payload.patient)} necesita atención inmediata.`,
        time,
        color: "red",
      };

    case "ORCHESTRATOR_OBSERVATION":
      return {
        title: "Observacion del orquestador",
        agent: "OrchestratorAgent",
        description: payload.message || `Evento observado para paciente ${payload.patient_id}`,
        time,
        color: "gray",
      };

    default:
      // Intentar obtener el nombre del agente desde el payload
      const agentName = payload?.agent || payload?.agent_name || "Agente";
      return {
        title: event_type.replace(/_/g, " "),
        agent: agentName,
        description: JSON.stringify(payload).slice(0, 120) + (JSON.stringify(payload).length > 120 ? "…" : ""),
        time,
        color: "gray",
      };
  }
};

// Componente Card individual
const EventCard = ({ event }) => {
  const { title, agent, description, time, color } = formatEventToCard(event);

  const colorClasses = {
    blue: "border-blue-500 bg-blue-50",
    red: "border-red-500 bg-red-50",
    orange: "border-orange-500 bg-orange-50",
    green: "border-green-500 bg-green-50",
    purple: "border-purple-500 bg-purple-50",
    teal: "border-teal-500 bg-teal-50",
    yellow: "border-yellow-500 bg-yellow-50",
    gray: "border-gray-400 bg-gray-50",
  };

  const bgClass = colorClasses[color] || colorClasses.gray;

  return (
    <div className={`event-card ${bgClass}`}>
      <div className="event-card-header">
        <span className="event-title">{title}</span>
        <span className="event-agent">por {agent}</span>
        <span className="event-time">{time}</span>
      </div>
      <p className="event-description">{description}</p>
    </div>
  );
};

// Componente principal: lista de eventos
const EventTimeline = ({ events = [] }) => {
  if (!events.length) {
    return <div className="event-timeline-empty">No hay actividad multiagente reciente.</div>;
  }

  return (
    <div className="event-timeline">
      <h3 className="event-timeline-title">Actividad multiagente</h3>
      <div className="event-list">
        {events.map((event, idx) => (
          <EventCard key={idx} event={event} />
        ))}
      </div>
    </div>
  );
};

export default EventTimeline;