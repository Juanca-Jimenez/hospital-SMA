// src/components/PatientForm.jsx
import { useState, useCallback } from "react";
import { sendPatient } from "../services/websocket";

// ─── Constantes clínicas ───────────────────────────────────────────────────
const MOTIVOS = ["Dolor", "Respiratorio", "Trauma", "Neurológico", "Digestivo", "Control", "Fiebre", "Otro"];

const SINTOMAS_OPCIONES = [
  "Dolor torácico",
  "Dificultad respiratoria",
  "Fiebre",
  "Tos",
  "Dolor abdominal",
  "Mareo",
  "Dolor pierna",
  "Fractura",
  "Pérdida conciencia",
  "Náuseas",
  "Cansancio",
  "Apendicitis",      // para cirugía
  "Colecistitis",     // para cirugía
  "Hernia",           // para cirugía
  "Abdomen agudo",    // para cirugía
];

const DOLOR_LABELS = {
  0: "Sin dolor",
  1: "Muy leve",
  2: "Leve",
  3: "Moderado leve",
  4: "Moderado",
  5: "Moderado intenso",
  6: "Intenso",
  7: "Muy intenso",
  8: "Severo",
  9: "Casi máximo",
  10: "Máximo dolor",
};

const INITIAL_FORM = {
  edad: "",
  genero: "Masculino",
  motivo_consulta: "",
  sintomas: [],
  otrosSintomas: "",      // texto libre adicional
  sistolica: "",
  diastolica: "",
  temperatura: "",
  frecuencia: "",
  spo2: "",
  dolor: 0,
};

// ─── Helper de validación ──────────────────────────────────────────────────
function validate(form) {
  const errors = {};

  if (form.edad === "" || Number(form.edad) < 0 || Number(form.edad) > 110) {
    errors.edad = "Ingresa una edad válida (0–110)";
  }
  if (!form.motivo_consulta) {
    errors.motivo_consulta = "Selecciona un motivo de consulta";
  }
  // Al menos un síntoma (checkbox u otros)
  if (form.sintomas.length === 0 && !form.otrosSintomas.trim()) {
    errors.sintomas = "Selecciona al menos un síntoma o escribe otros síntomas";
  }

  const sis = Number(form.sistolica);
  const dia = Number(form.diastolica);
  if (!form.sistolica || sis < 80 || sis > 220) {
    errors.sistolica = "Sistólica: 80–220 mmHg";
  }
  if (!form.diastolica || dia < 40 || dia > 140) {
    errors.diastolica = "Diastólica: 40–140 mmHg";
  }

  const temp = Number(form.temperatura);
  if (!form.temperatura || temp < 34 || temp > 42) {
    errors.temperatura = "Temperatura: 34–42 °C";
  }

  const fc = Number(form.frecuencia);
  if (!form.frecuencia || fc < 30 || fc > 220) {
    errors.frecuencia = "Frecuencia cardiaca: 30–220 lpm";
  }

  const spo2 = Number(form.spo2);
  if (!form.spo2 || spo2 < 60 || spo2 > 100) {
    errors.spo2 = "SpO₂: 60–100%";
  }

  return errors;
}

// ─── Componente principal ──────────────────────────────────────────────────
function PatientForm({ onResult }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const set = (field, value) => setForm((f) => ({ ...f, [field]: value }));

  const toggleSintoma = useCallback(
    (s) => {
      setForm((f) => {
        if (f.sintomas.includes(s)) {
          return { ...f, sintomas: f.sintomas.filter((x) => x !== s) };
        }
        // Máximo 3 síntomas de checkbox (sin contar otrosSintomas)
        if (f.sintomas.length >= 3) return f;
        return { ...f, sintomas: [...f.sintomas, s] };
      });
    },
    []
  );

  const showToast = (msg, type = "success") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const errs = validate(form);
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    setLoading(true);

    // Combinar síntomas seleccionados + texto de otros síntomas
    let sintomasList = [...form.sintomas];
    if (form.otrosSintomas.trim()) {
      // Dividir por comas o espacios simples
      const otros = form.otrosSintomas.split(/[,;]+/).map(s => s.trim()).filter(s => s);
      sintomasList.push(...otros);
    }

    const payload = {
      edad: Number(form.edad),
      genero: form.genero,
      motivo_consulta: form.motivo_consulta === "Otro" ? "" : form.motivo_consulta,
      sintomas: sintomasList,
      vitales: {
        presion: {
          sistolica: Number(form.sistolica),
          diastolica: Number(form.diastolica),
        },
        temperatura: Number(form.temperatura),
        frecuencia: Number(form.frecuencia),
        spo2: Number(form.spo2),
      },
      dolor: Number(form.dolor),
    };

    sendPatient(payload);
    showToast("Paciente ingresado correctamente ✓");
    setLoading(false);

    if (onResult) onResult(payload);
    // No limpiar el formulario (opcional)
  };

  const dolorLabel = DOLOR_LABELS[form.dolor] || "";
  const dolorColor =
    form.dolor <= 2 ? "#22c55e" : form.dolor <= 5 ? "#f59e0b" : form.dolor <= 7 ? "#f97316" : "#ef4444";

  return (
    <div className="pf-wrapper">
      {/* Toast */}
      {toast && (
        <div className={`pf-toast pf-toast--${toast.type}`} role="status">
          {toast.msg}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="pf-form">
        <div className="pf-form-header">
          <div className="pf-form-header-icon">🏥</div>
          <div>
            <h2 className="pf-form-title">Admisión de paciente</h2>
            <p className="pf-form-subtitle">Complete los datos clínicos para el triaje</p>
          </div>
        </div>

        {/* ── Sección A: Información básica ── */}
        <section className="pf-section">
          <h3 className="pf-section-title">
            <span className="pf-section-num">A</span>Información básica
          </h3>
          <div className="pf-row-2">
            <div className="pf-field">
              <label className="pf-label" htmlFor="pf-edad">
                Edad <span className="pf-req">*</span>
              </label>
              <input
                id="pf-edad"
                type="number"
                className={`pf-input${errors.edad ? " pf-input--error" : ""}`}
                placeholder="0–110"
                min={0}
                max={110}
                value={form.edad}
                onChange={(e) => set("edad", e.target.value)}
              />
              {errors.edad && <p className="pf-error">{errors.edad}</p>}
            </div>

            <div className="pf-field">
              <label className="pf-label" htmlFor="pf-genero">
                Género
              </label>
              <select
                id="pf-genero"
                className="pf-input"
                value={form.genero}
                onChange={(e) => set("genero", e.target.value)}
              >
                <option>Masculino</option>
                <option>Femenino</option>
                <option>Otro</option>
              </select>
            </div>
          </div>
        </section>

        {/* ── Sección B: Motivo de consulta ── */}
        <section className="pf-section">
          <h3 className="pf-section-title">
            <span className="pf-section-num">B</span>Motivo de consulta
          </h3>
          <div className="pf-field">
            <label className="pf-label" htmlFor="pf-motivo">
              Motivo <span className="pf-req">*</span>
            </label>
            <select
              id="pf-motivo"
              className={`pf-input${errors.motivo_consulta ? " pf-input--error" : ""}`}
              value={form.motivo_consulta}
              onChange={(e) => set("motivo_consulta", e.target.value)}
            >
              <option value="">— Seleccionar —</option>
              {MOTIVOS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
            {errors.motivo_consulta && <p className="pf-error">{errors.motivo_consulta}</p>}
          </div>
        </section>

        {/* ── Sección C: Síntomas ── */}
        <section className="pf-section">
          <h3 className="pf-section-title">
            <span className="pf-section-num">C</span>Síntomas
            <span className="pf-section-hint">máximo 3 de la lista + texto libre</span>
          </h3>
          <div className="pf-chips">
            {SINTOMAS_OPCIONES.map((s) => {
              const selected = form.sintomas.includes(s);
              const disabled = !selected && form.sintomas.length >= 3;
              return (
                <button
                  key={s}
                  type="button"
                  className={`pf-chip${selected ? " pf-chip--active" : ""}${disabled ? " pf-chip--disabled" : ""}`}
                  onClick={() => toggleSintoma(s)}
                  disabled={disabled}
                  aria-pressed={selected}
                >
                  {s}
                </button>
              );
            })}
          </div>
          <div className="pf-field" style={{ marginTop: "0.75rem" }}>
            <label className="pf-label" htmlFor="pf-otros-sintomas">
              Otros síntomas (separados por comas)
            </label>
            <input
              id="pf-otros-sintomas"
              type="text"
              className="pf-input"
              placeholder="Ej: apendicitis, colecistitis, dolor agudo"
              value={form.otrosSintomas}
              onChange={(e) => set("otrosSintomas", e.target.value)}
            />
          </div>
          {errors.sintomas && <p className="pf-error">{errors.sintomas}</p>}
        </section>

        {/* ── Sección D: Signos vitales ── */}
        <section className="pf-section">
          <h3 className="pf-section-title">
            <span className="pf-section-num">D</span>Signos vitales
          </h3>

          <div className="pf-vital-group">
            <span className="pf-vital-label">Presión arterial (mmHg)</span>
            <div className="pf-row-2">
              <div className="pf-field">
                <label className="pf-label" htmlFor="pf-sistolica">
                  Sistólica <span className="pf-req">*</span>
                </label>
                <input
                  id="pf-sistolica"
                  type="number"
                  className={`pf-input${errors.sistolica ? " pf-input--error" : ""}`}
                  placeholder="80–220"
                  min={80}
                  max={220}
                  value={form.sistolica}
                  onChange={(e) => set("sistolica", e.target.value)}
                />
                {errors.sistolica && <p className="pf-error">{errors.sistolica}</p>}
              </div>
              <div className="pf-field">
                <label className="pf-label" htmlFor="pf-diastolica">
                  Diastólica <span className="pf-req">*</span>
                </label>
                <input
                  id="pf-diastolica"
                  type="number"
                  className={`pf-input${errors.diastolica ? " pf-input--error" : ""}`}
                  placeholder="40–140"
                  min={40}
                  max={140}
                  value={form.diastolica}
                  onChange={(e) => set("diastolica", e.target.value)}
                />
                {errors.diastolica && <p className="pf-error">{errors.diastolica}</p>}
              </div>
            </div>
          </div>

          <div className="pf-row-3">
            <div className="pf-field">
              <label className="pf-label" htmlFor="pf-temp">
                Temperatura °C <span className="pf-req">*</span>
              </label>
              <input
                id="pf-temp"
                type="number"
                step="0.1"
                className={`pf-input${errors.temperatura ? " pf-input--error" : ""}`}
                placeholder="34–42"
                min={34}
                max={42}
                value={form.temperatura}
                onChange={(e) => set("temperatura", e.target.value)}
              />
              {errors.temperatura && <p className="pf-error">{errors.temperatura}</p>}
            </div>
            <div className="pf-field">
              <label className="pf-label" htmlFor="pf-fc">
                Frec. cardiaca (lpm) <span className="pf-req">*</span>
              </label>
              <input
                id="pf-fc"
                type="number"
                className={`pf-input${errors.frecuencia ? " pf-input--error" : ""}`}
                placeholder="30–220"
                min={30}
                max={220}
                value={form.frecuencia}
                onChange={(e) => set("frecuencia", e.target.value)}
              />
              {errors.frecuencia && <p className="pf-error">{errors.frecuencia}</p>}
            </div>
            <div className="pf-field">
              <label className="pf-label" htmlFor="pf-spo2">
                SpO₂ (%) <span className="pf-req">*</span>
              </label>
              <input
                id="pf-spo2"
                type="number"
                className={`pf-input${errors.spo2 ? " pf-input--error" : ""}`}
                placeholder="60–100"
                min={60}
                max={100}
                value={form.spo2}
                onChange={(e) => set("spo2", e.target.value)}
              />
              {errors.spo2 && <p className="pf-error">{errors.spo2}</p>}
            </div>
          </div>
        </section>

        {/* ── Sección E: Dolor ── */}
        <section className="pf-section">
          <h3 className="pf-section-title">
            <span className="pf-section-num">E</span>Escala de dolor
          </h3>
          <div className="pf-pain-container">
            <div className="pf-pain-header">
              <span className="pf-pain-num" style={{ color: dolorColor }}>
                {form.dolor}
              </span>
              <span className="pf-pain-desc" style={{ color: dolorColor }}>
                {dolorLabel}
              </span>
            </div>
            <input
              id="pf-dolor"
              type="range"
              min={0}
              max={10}
              step={1}
              value={form.dolor}
              onChange={(e) => set("dolor", Number(e.target.value))}
              className="pf-slider"
              style={{ "--slider-color": dolorColor }}
            />
            <div className="pf-pain-scale">
              <span>0 – Sin dolor</span>
              <span>10 – Máximo</span>
            </div>
          </div>
        </section>

        <button type="submit" className="pf-submit" disabled={loading} id="pf-submit-btn">
          {loading ? (
            <span className="pf-spinner" />
          ) : (
            <>
              <span className="pf-submit-icon">✚</span>
              Ingresar paciente
            </>
          )}
        </button>
      </form>
    </div>
  );
}

export default PatientForm;