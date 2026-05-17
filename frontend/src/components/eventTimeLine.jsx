// src/components/EventTimeline.jsx

function EventTimeline({ events }) {
  return (
    <div className="bg-white p-5 rounded-xl shadow-md h-[500px] overflow-y-auto">
      <h2 className="text-xl font-bold mb-4">
        Actividad de Agentes
      </h2>

      <div className="space-y-3">
        {events.map((event, index) => (
          <div
            key={index}
            className="border-l-4 border-blue-500 pl-3 py-2 bg-gray-50 rounded"
          >
            <p className="font-semibold">
              {event.event_type || "EVENT"}
            </p>

            <pre className="text-sm whitespace-pre-wrap">
              {JSON.stringify(event, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}

export default EventTimeline;
