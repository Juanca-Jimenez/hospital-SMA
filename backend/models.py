from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class VitalSigns(BaseModel):
    heart_rate: int
    blood_pressure: str
    spo2: int
    temperature: float


class Patient(BaseModel):
    id_paciente: str
    timestamp: Optional[str] = None

    edad: int
    genero: str

    nivel_urgencia: int

    sintomas: str

    signos_vitales: Optional[Dict[str, Any]] = None

    tiempo_espera_min: Optional[int] = 0

    departamento_asignado: Optional[str] = None

    estado: str


class Resource(BaseModel):
    tipo_recurso: str
    departamento: str

    total_disponible: int
    ocupados: int
    disponibles: int

    proximo_disponible_min: Optional[int] = None


class Staff(BaseModel):
    id_empleado: str
    nombre: str

    rol: str
    especialidad: str

    estado: str

    horas_trabajadas_consecutivas: int

    pacientes_atendidos_turno: int


class AgentEvent(BaseModel):
    event_type: str

    timestamp: datetime

    source_agent: str

    payload: Dict[str, Any]


class DecisionTrace(BaseModel):
    timestamp: datetime

    agent_name: str

    decision: str

    reason: str

    patient_id: Optional[str] = None