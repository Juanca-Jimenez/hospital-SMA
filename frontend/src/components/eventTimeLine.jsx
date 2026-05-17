function EventTimeline({ events }) {

  return (

    <div className="bg-white p-5 rounded-xl shadow-md h-[700px] overflow-y-auto">

      <h2 className="text-xl font-bold mb-4">
        Actividad Multiagente
      </h2>

      <div className="space-y-4">

        {events.map((event, index) => (

          <div
            key={index}
            className="border-l-4 border-blue-600 bg-gray-50 p-3 rounded"
          >

            <div className="font-bold text-blue-700">
              {event.event_type}
            </div>

            <pre className="text-sm mt-2 whitespace-pre-wrap">
              {JSON.stringify(event.payload || event, null, 2)}
            </pre>

          </div>

        ))}

      </div>

    </div>
  )
}

export default EventTimeline