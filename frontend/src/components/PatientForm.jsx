// src/components/PatientForm.jsx

import { useState } from "react";
import { sendPatient } from "../services/websocket";

function PatientForm() {
  const [formData, setFormData] = useState({
    edad: "",
    genero: "Masculino",
    nivel_urgencia: "3",
    sintomas: "",
    presion: "",
    temperatura: "",
    frecuencia_cardiaca: "",
    saturacion_oxigeno: "",
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    sendPatient({
      edad: Number(formData.edad),
      genero: formData.genero,
      nivel_urgencia: Number(formData.nivel_urgencia),
      sintomas: formData.sintomas,
      signos_vitales: {
        presion: formData.presion,
        temperatura: formData.temperatura,
        frecuencia_cardiaca: formData.frecuencia_cardiaca,
        saturacion_oxigeno: formData.saturacion_oxigeno,
      },
      estado: "En_espera",
    });

    setFormData({
      edad: "",
      genero: "Masculino",
      nivel_urgencia: "3",
      sintomas: "",
      presion: "",
      temperatura: "",
      frecuencia_cardiaca: "",
      saturacion_oxigeno: "",
    });
  };

  return (
    <div className="bg-white p-5 rounded-xl shadow-md">
      <h2 className="text-xl font-bold mb-4">
        Nuevo Paciente
      </h2>

      <form onSubmit={handleSubmit} className="space-y-3">

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
          rows={3}
        />

        <input
          type="text"
          name="presion"
          placeholder="Presión arterial (ej. 120/80)"
          value={formData.presion}
          onChange={handleChange}
          className="w-full border p-2 rounded"
        />

        <div className="grid grid-cols-2 gap-2">
          <input
            type="text"
            name="temperatura"
            placeholder="Temperatura (°C)"
            value={formData.temperatura}
            onChange={handleChange}
            className="w-full border p-2 rounded"
          />
          <input
            type="text"
            name="frecuencia_cardiaca"
            placeholder="Frecuencia cardiaca"
            value={formData.frecuencia_cardiaca}
            onChange={handleChange}
            className="w-full border p-2 rounded"
          />
        </div>

        <input
          type="text"
          name="saturacion_oxigeno"
          placeholder="Saturación de oxígeno (%)"
          value={formData.saturacion_oxigeno}
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