// src/components/PatientForm.jsx

import { useState } from "react";
import { sendPatient } from "../services/websocket";

function PatientForm() {
  const [formData, setFormData] = useState({
    id_paciente: "",
    edad: "",
    genero: "Masculino",
    nivel_urgencia: 3,
    sintomas: "",
    estado: "En atención",
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    sendPatient(formData);

    setFormData({
      id_paciente: "",
      edad: "",
      genero: "Masculino",
      nivel_urgencia: 3,
      sintomas: "",
      estado: "En atención",
    });
  };

  return (
    <div className="bg-white p-5 rounded-xl shadow-md">
      <h2 className="text-xl font-bold mb-4">
        Nuevo Paciente
      </h2>

      <form onSubmit={handleSubmit} className="space-y-3">

        <input
          type="text"
          name="id_paciente"
          placeholder="ID Paciente"
          value={formData.id_paciente}
          onChange={handleChange}
          className="w-full border p-2 rounded"
          required
        />

        <input
          type="number"
          name="edad"
          placeholder="Edad"
          value={formData.edad}
          onChange={handleChange}
          className="w-full border p-2 rounded"
          required
        />

        <select
          name="genero"
          value={formData.genero}
          onChange={handleChange}
          className="w-full border p-2 rounded"
        >
          <option>Masculino</option>
          <option>Femenino</option>
        </select>

        <select
          name="nivel_urgencia"
          value={formData.nivel_urgencia}
          onChange={handleChange}
          className="w-full border p-2 rounded"
        >
          <option value="1">1 - Crítico</option>
          <option value="2">2 - Alto</option>
          <option value="3">3 - Medio</option>
          <option value="4">4 - Bajo</option>
          <option value="5">5 - No urgente</option>
        </select>

        <textarea
          name="sintomas"
          placeholder="Síntomas"
          value={formData.sintomas}
          onChange={handleChange}
          className="w-full border p-2 rounded"
        />

        <button
          type="submit"
          className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700"
        >
          Ingresar Paciente
        </button>

      </form>
    </div>
  );
}

export default PatientForm;