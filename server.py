# 1) Remplacer server.py par la version Google Sheets (sans pandas)
cat > server.py << 'PY'
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import os, json

import gspread
from google.oauth2.service_account import Credentials

COLUMNS = ["horodatage","nb_patients","duree_distribution_min","repas","nb_personnes","notes_libres","source_message"]

REPAS_ALIASES = {
    "petit déjeuner": {"petit déjeuner","petit-dejeuner","petit dejeuner","breakfast","matin","pdj"},
    "midi": {"midi","déjeuner","dejeuner","repas de midi","lunch"},
    "soir": {"soir","dîner","diner","souper","repas du soir","dinner"},
}

def normalize_repas(v: str) -> Optional[str]:
    if not v: return None
    t = v.strip().lower()
    for canon, aliases in REPAS_ALIASES.items():
        if t == canon or t in aliases: return canon
    tt = f" {t} "
    for canon, aliases in REPAS_ALIASES.items():
        for a in set(list(aliases)+[canon]):
            if f" {a} " in tt: return canon
    return None

class AppendPayload(BaseModel):
    horodatage: Optional[str] = None
    nb_patients: int = Field(..., ge=0)
    duree_distribution_min: int = Field(..., ge=0)
    repas: str
    nb_personnes: int = Field(..., ge=0)
    notes_libres: Optional[str] = ""
    source_message: Optional[str] = ""

    @validator("repas")
    def _repas(cls, v):
        canon = normalize_repas(v)
        if not canon:
            raise ValueError("repas doit être 'petit déjeuner', 'midi' ou 'soir' (synonymes acceptés).")
        return canon

API_SECRET = os.getenv("HUMETIME_API_SECRET", "")

app = FastAPI(title="Humetime Excel Action (Sheets)", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def get_sheet():
    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        raise RuntimeError("Env var GOOGLE_SERVICE_ACCOUNT_JSON manquante")
    info = json.loads(sa_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    sheet_id = os.getenv("SHEET_ID")
    if not sheet_id:
        raise RuntimeError("Env var SHEET_ID manquante")
    sheet_name = os.getenv("SHEET_NAME", "Feuille1")
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet(sheet_name)
    return ws

@app.post("/append")
def append_row(payload: AppendPayload, x_api_key: str = Header(default=None)):
    if API_SECRET and x_api_key != API_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        ws = get_sheet()
        data = payload.dict()
        if not data.get("horodatage"):
            data["horodatage"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [str(data.get(c, "")) for c in COLUMNS]
        ws.append_row(row, value_input_option="USER_ENTERED")
        return {"status":"ok", "appended": dict(zip(COLUMNS, row))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
PY

# 2) S’assurer que requirements.txt ne contient PAS pandas
cat > requirements.txt << 'REQ'
fastapi
uvicorn
gspread
google-auth
REQ

# 3) Commit & push
git add server.py requirements.txt
git commit -m "Use Google Sheets version (no pandas)"
git push
