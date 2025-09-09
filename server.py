# -*- coding: utf-8 -*-
"""
API locale Humetime
- POST /append : ajoute une ligne au tableur Excel iCloud.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import pandas as pd
import os

# >>> Chemin Excel cible (iCloud) <<<
OUTPUT_XLSX = r"/Users/admin/Library/Mobile Documents/com~apple~CloudDocs/00 etc./03 Projets/Humetime/distribution_log.xlsx"

COLUMNS = [
    "horodatage",
    "nb_patients",
    "duree_distribution_min",
    "repas",
    "nb_personnes",
    "notes_libres",
    "source_message",
]

REPAS_ALIASES = {
    "petit déjeuner": {"petit déjeuner","petit-dejeuner","petit dejeuner","breakfast","matin","pdj"},
    "midi": {"midi","déjeuner","dejeuner","repas de midi","lunch"},
    "soir": {"soir","dîner","diner","souper","repas du soir","dinner"},
}

def normalize_repas(value: str) -> Optional[str]:
    if not value:
        return None
    t = value.strip().lower()
    for canon, aliases in REPAS_ALIASES.items():
        if t == canon or t in aliases:
            return canon
    tt = f" {t} "
    for canon, aliases in REPAS_ALIASES.items():
        for a in set(list(aliases) + [canon]):
            if f" {a} " in tt:
                return canon
    return None

class AppendPayload(BaseModel):
    horodatage: Optional[str] = None
    nb_patients: int = Field(..., ge=0)
    duree_distribution_min: int = Field(..., ge=0)
    repas: str = Field(..., description="petit déjeuner | midi | soir (synonymes acceptés)")
    nb_personnes: int = Field(..., ge=0)
    notes_libres: Optional[str] = ""
    source_message: Optional[str] = ""

    @validator("repas")
    def _valide_repas(cls, v):
        canon = normalize_repas(v)
        if not canon:
            raise ValueError("repas doit être 'petit déjeuner', 'midi' ou 'soir' (synonymes acceptés).")
        return canon

app = FastAPI(title="Humetime Excel Action", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ensure_excel():
    folder = os.path.dirname(OUTPUT_XLSX)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    if not os.path.exists(OUTPUT_XLSX):
        pd.DataFrame(columns=COLUMNS).to_excel(OUTPUT_XLSX, index=False)

@app.post("/append")
def append_row(payload: AppendPayload):
    try:
        ensure_excel()
        data = payload.dict()
        if not data.get("horodatage"):
            data["horodatage"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        df = pd.read_excel(OUTPUT_XLSX) if os.path.exists(OUTPUT_XLSX) else pd.DataFrame(columns=COLUMNS)
        for c in COLUMNS:
            if c not in data:
                data[c] = ""
        df = pd.concat([df, pd.DataFrame([data])[COLUMNS]], ignore_index=True)
        df.to_excel(OUTPUT_XLSX, index=False)
        return {"status": "ok", "appended": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
