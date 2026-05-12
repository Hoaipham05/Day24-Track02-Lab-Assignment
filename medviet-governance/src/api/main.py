# src/api/main.py
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "patients_raw.csv"


def _load_raw_data() -> pd.DataFrame:
    if not RAW_DATA_PATH.exists():
        raise HTTPException(status_code=404, detail="Raw patient data not found")
    return pd.read_csv(RAW_DATA_PATH)

# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Trả về raw patient data (chỉ admin được phép).
    Load từ data/raw/patients_raw.csv
    Trả về 10 records đầu tiên dưới dạng JSON.
    """
    df = _load_raw_data().head(10)
    return JSONResponse(content=df.to_dict(orient="records"))

# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Trả về anonymized data (ml_engineer và admin được phép).
    Load raw data → anonymize → trả về JSON.
    """
    df = _load_raw_data().head(10)
    anonymized_df = anonymizer.anonymize_dataframe(df)
    return JSONResponse(content=anonymized_df.to_dict(orient="records"))

# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Trả về aggregated metrics (data_analyst, ml_engineer, admin).
    Ví dụ: số bệnh nhân theo từng loại bệnh (không có PII).
    """
    df = _load_raw_data()
    metrics = (
        df.groupby("benh", dropna=False)
        .size()
        .reset_index(name="patient_count")
        .to_dict(orient="records")
    )
    return JSONResponse(content={"metrics": metrics})

# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Chỉ admin được xóa. Các role khác nhận 403.
    """
    return JSONResponse(content={"status": "deleted", "patient_id": patient_id})

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
