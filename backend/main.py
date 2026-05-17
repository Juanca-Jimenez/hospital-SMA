from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).resolve().parent / "data"
PATIENTS_CSV = DATA_DIR / "pacientes_admisiones.csv"


def read_patients(limit: int = 100):
    if not PATIENTS_CSV.exists():
        raise FileNotFoundError(f"Archivo de pacientes no encontrado: {PATIENTS_CSV}")

    df = pd.read_csv(PATIENTS_CSV)
    return df.head(limit).to_dict(orient="records")


@app.get("/api/patients")
def get_patients(limit: int = 100):
    try:
        patients = read_patients(limit)
        return {"patients": patients, "count": len(patients)}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al leer el CSV de pacientes: {exc}")


@app.get("/api/health")
def health():
    try:
        patients = read_patients(1)
        return {"status": "ok", "patients_available": len(patients)}
    except Exception:
        raise HTTPException(status_code=500, detail="El servicio de pacientes no está disponible")
