// src/components/Dashboard.jsx

import { useEffect, useState } from "react";

import Navbar from "./Navbar";
import PatientForm from "./PatientForm";
import EventTimeline from "./EventTimeline";
import HospitalMetrics from "./HospitalMetrics";
import AgentStatus from "./AgentStatus";

import { connectWebSocket } from "../services/websocket";

function Dashboard() {

  const [events, setEvents] = useState([]);

  const [metrics, setMetrics] = useState({});

  useEffect(() => {

    connectWebSocket((data) => {

      setEvents((prev) => [data, ...prev]);

      if (data.global_state) {
        setMetrics(data.global_state);
      }
    });

  }, []);

  return (
    <div>

      <Navbar />

      <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">

        <div className="space-y-6">
          <PatientForm />
          <AgentStatus />
        </div>

        <div className="lg:col-span-2">
          <EventTimeline events={events} />
        </div>

      </div>

      <div className="p-6">
        <HospitalMetrics metrics={metrics} />
      </div>

    </div>
  );
}

export default Dashboard;