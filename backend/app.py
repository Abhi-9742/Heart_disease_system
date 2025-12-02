# app.py - FastAPI backend with prediction, history, and two PDF report endpoints (simple + visual)
import os
import io
import json
import tempfile
import datetime
from typing import List, Optional, Dict, Any

import joblib
import numpy as np
import mysql.connector
from mysql.connector import Error
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

# PDF and plotting
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import matplotlib.pyplot as plt

# load env/config
from dotenv import load_dotenv
load_dotenv()

# ---------- CONFIG ----------
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "heart_disease")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-secret")
MODEL_PATH = os.getenv("MODEL_PATH", "models/heart_model.pkl")
SCALER_PATH = os.getenv("SCALER_PATH", "models/scaler.pkl")
REPORTS_DIR = os.path.join(os.getcwd(), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# ---------- FASTAPI APP ----------
app = FastAPI(title="Heart Disease API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- DB helpers ----------
def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        autocommit=False
    )

# ---------- Load model & scaler ----------
try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
except Exception as e:
    model = None
    scaler = None
    print("Warning: could not load model/scaler:", e)

# ---------- Pydantic models ----------
class RegisterIn(BaseModel):
    name: Optional[str] = None
    email: str
    password: str

class LoginIn(BaseModel):
    email: str
    password: str

class PredictIn(BaseModel):
    # Accept named fields for clarity; order below should match training
    age: float
    sex: float
    cp: float
    trestbps: float
    chol: float
    fbs: float
    restecg: float
    thalach: float
    exang: float
    oldpeak: float
    slope: float
    ca: float
    thal: float

# ---------- Auth helpers ----------
def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    token = authorization if not authorization.startswith("Bearer ") else authorization.split(" ", 1)[1]
    data = decode_token(token)
    return data["user_id"]

# ---------- Utility: advice builder ----------
def build_advice(prediction: int, confidence: Optional[float] = None):
    if prediction == 1:
        diagnosis = "High risk of heart disease"
        treatment = [
            "Consult a cardiologist as soon as possible",
            "Consider cholesterol / blood pressure medication as recommended by doctor",
            "Undergo ECG, ECHO, and stress test as advised",
            "Regular follow-up and monitoring"
        ]
        precautions = [
            "Stop smoking and avoid alcohol",
            "Adopt regular aerobic exercise (30-45 min daily)",
            "Reduce salt and saturated fat intake",
            "Manage stress and ensure good sleep",
            "Follow doctor's prescriptions"
        ]
    else:
        diagnosis = "Low risk of heart disease"
        treatment = [
            "No immediate invasive treatment required",
            "Maintain regular checkups and healthy habits"
        ]
        precautions = [
            "Balanced diet and regular exercise (≥30 min/day)",
            "Avoid processed food and excessive salt",
            "Maintain healthy weight and sleep schedule",
            "Monitor blood pressure and cholesterol periodically"
        ]
    # borderline note
    if confidence is not None and prediction == 1 and confidence < 0.6:
        treatment.insert(0, "Borderline result — repeat test and consult physician for confirmation")
    return diagnosis, treatment, precautions

# ---------- Routes: register / login ----------
@app.post("/register")
def register(data: RegisterIn):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id FROM users WHERE email=%s", (data.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="User already exists")
        hashed = generate_password_hash(data.password, method="pbkdf2:sha256")
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s,%s,%s)", (data.name, data.email, hashed))
        conn.commit()
        return {"message": "Registered"}
    finally:
        cur.close()
        conn.close()

@app.post("/login")
def login(data: LoginIn):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, password, name FROM users WHERE email=%s LIMIT 1", (data.email,))
        row = cur.fetchone()
        if not row or not check_password_hash(row["password"], data.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_token(row["id"])
        return {"token": token, "user": {"id": row["id"], "name": row["name"]}}
    finally:
        cur.close()
        conn.close()

# ---------- Route: predict ----------
@app.post("/predict")
def predict(data: PredictIn, user_id: int = Depends(get_current_user)):
    if model is None or scaler is None:
        raise HTTPException(status_code=500, detail="Model not loaded on server")

    # Create ordered feature vector (must match training)
    required_fields = ["age","sex","cp","trestbps","chol","fbs","restecg","thalach","exang","oldpeak","slope","ca","thal"]
    values = [getattr(data, f) for f in required_fields]

    X = scaler.transform([values])
    pred = int(model.predict(X)[0])
    confidence = None
    try:
        confidence = float(np.max(model.predict_proba(X)))
    except Exception:
        confidence = None

    diagnosis, treatment, precautions = build_advice(pred, confidence)

    # store in DB (treatment/precautions stored as JSON text)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO predictions (user_id, prediction, diagnosis, treatment, precautions, confidence, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (user_id, pred, diagnosis, json.dumps(treatment), json.dumps(precautions), confidence, datetime.datetime.utcnow())
        )
        pred_id = cur.lastrowid
        conn.commit()
    finally:
        cur.close()
        conn.close()

    return {
        "prediction": pred,
        "confidence": confidence,
        "diagnosis": diagnosis,
        "treatment": treatment,
        "precautions": precautions,
        "prediction_id": pred_id
    }

# ---------- Route: history ----------
@app.get("/history")
def history(user_id: int = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT id AS prediction_id, prediction, diagnosis, treatment, precautions, confidence, report_path, created_at
            FROM predictions WHERE user_id=%s ORDER BY created_at DESC
        """, (user_id,))
        rows = cur.fetchall()
        # parse JSON columns
        for r in rows:
            if r.get("treatment"):
                try:
                    r["treatment"] = json.loads(r["treatment"])
                except:
                    r["treatment"] = []
            if r.get("precautions"):
                try:
                    r["precautions"] = json.loads(r["precautions"])
                except:
                    r["precautions"] = []
        return rows
    finally:
        cur.close()
        conn.close()

# ---------- PDF helpers ----------
def generate_simple_pdf(filepath: str, user_name: str, record: dict):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    elements = []
    elements.append(Paragraph("Heart Disease Diagnostic Report", styles["Title"]))
    elements.append(Spacer(1,8))
    elements.append(Paragraph(f"Patient: {user_name or 'Unknown'}", styles["Normal"]))
    elements.append(Paragraph(f"Date: {record.get('created_at')}", styles["Normal"]))
    elements.append(Spacer(1,8))

    elements.append(Paragraph("<b>Prediction</b>", styles["Heading3"]))
    elements.append(Paragraph("High risk" if record["prediction"]==1 else "Low risk", styles["Normal"]))
    elements.append(Spacer(1,6))

    elements.append(Paragraph("<b>Diagnosis</b>", styles["Heading3"]))
    elements.append(Paragraph(record.get("diagnosis",""), styles["Normal"]))
    elements.append(Spacer(1,6))

    elements.append(Paragraph("<b>Treatment Recommendations</b>", styles["Heading3"]))
    for t in record.get("treatment",[]):
        elements.append(Paragraph(f"• {t}", styles["Normal"]))
    elements.append(Spacer(1,6))

    elements.append(Paragraph("<b>Precautions</b>", styles["Heading3"]))
    for p in record.get("precautions",[]):
        elements.append(Paragraph(f"• {p}", styles["Normal"]))

    doc.build(elements)

def create_gauge_image(score: float, path: str):
    """
    score: 0..1 (0 low risk, 1 high risk).
    Saves a small PNG gauge to path.
    """
    fig, ax = plt.subplots(figsize=(3,1.5))
    ax.axis('off')
    # Draw a horizontal bar as the progress meter
    ax.barh([0], [1], color="#eee", height=0.6)
    color = "#10b981" if score < 0.5 else "#ef4444"
    ax.barh([0], [score], color=color, height=0.6)
    ax.text(score, 0, f" {int(score*100)}%", va='center', ha='left', fontsize=10, color="#111")
    plt.xlim(0,1)
    plt.tight_layout()
    fig.savefig(path, bbox_inches='tight', pad_inches=0)
    plt.close(fig)

def generate_visual_pdf(filepath: str, user_name: str, record: dict):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    elements = []
    elements.append(Paragraph("Heart Disease Diagnostic Report (Visual)", styles["Title"]))
    elements.append(Spacer(1,8))
    elements.append(Paragraph(f"Patient: {user_name or 'Unknown'}", styles["Normal"]))
    elements.append(Paragraph(f"Date: {record.get('created_at')}", styles["Normal"]))
    elements.append(Spacer(1,12))

    # Add gauge image
    score = record.get("confidence", 0.75)
    if score is None:
        score = 0.75 if record.get("prediction",0)==1 else 0.25
    gauge_fd, gauge_path = tempfile.mkstemp(suffix=".png")
    os.close(gauge_fd)
    create_gauge_image(float(score), gauge_path)
    # Insert image with reportlab Image flowable
    elements.append(RLImage(gauge_path, width=300, height=120))
    elements.append(Spacer(1,12))

    elements.append(Paragraph("<b>Prediction</b>", styles["Heading3"]))
    elements.append(Paragraph("High risk" if record["prediction"]==1 else "Low risk", styles["Normal"]))
    elements.append(Spacer(1,6))

    elements.append(Paragraph("<b>Diagnosis</b>", styles["Heading3"]))
    elements.append(Paragraph(record.get("diagnosis",""), styles["Normal"]))
    elements.append(Spacer(1,6))

    elements.append(Paragraph("<b>Treatment Recommendations</b>", styles["Heading3"]))
    for t in record.get("treatment",[]):
        elements.append(Paragraph(f"• {t}", styles["Normal"]))
    elements.append(Spacer(1,6))

    elements.append(Paragraph("<b>Precautions</b>", styles["Heading3"]))
    for p in record.get("precautions",[]):
        elements.append(Paragraph(f"• {p}", styles["Normal"]))

    doc.build(elements)
    # cleanup gauge image
    try:
        os.remove(gauge_path)
    except:
        pass

# ---------- Routes: report generation & download ----------
@app.get("/report/simple/{prediction_id}")
def report_simple(prediction_id: int, user_id: int = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM predictions WHERE id=%s LIMIT 1", (prediction_id,))
        rec = cur.fetchone()
        if not rec:
            raise HTTPException(status_code=404, detail="Prediction not found")
        if rec["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        # parse stored JSON fields
        try:
            treatment = json.loads(rec["treatment"]) if rec.get("treatment") else []
        except:
            treatment = []
        try:
            precautions = json.loads(rec["precautions"]) if rec.get("precautions") else []
        except:
            precautions = []

        record = {
            "prediction": rec["prediction"],
            "diagnosis": rec.get("diagnosis"),
            "treatment": treatment,
            "precautions": precautions,
            "confidence": rec.get("confidence"),
            "created_at": rec.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if isinstance(rec.get("created_at"), datetime.datetime) else str(rec.get("created_at"))
        }

        # generate filename and PDF
        filename = f"report_simple_user{user_id}_{prediction_id}_{int(datetime.datetime.utcnow().timestamp())}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)
        # get user name
        cur.execute("SELECT name FROM users WHERE id=%s", (user_id,))
        u = cur.fetchone()
        user_name = u["name"] if u else None

        generate_simple_pdf(filepath, user_name, record)

        # update DB with report_path
        cur.execute("UPDATE predictions SET report_path=%s WHERE id=%s", (filename, prediction_id))
        conn.commit()

        return FileResponse(filepath, filename=filename, media_type='application/pdf')
    finally:
        cur.close()
        conn.close()

@app.get("/report/visual/{prediction_id}")
def report_visual(prediction_id: int, user_id: int = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM predictions WHERE id=%s LIMIT 1", (prediction_id,))
        rec = cur.fetchone()
        if not rec:
            raise HTTPException(status_code=404, detail="Prediction not found")
        if rec["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        try:
            treatment = json.loads(rec["treatment"]) if rec.get("treatment") else []
        except:
            treatment = []
        try:
            precautions = json.loads(rec["precautions"]) if rec.get("precautions") else []
        except:
            precautions = []

        record = {
            "prediction": rec["prediction"],
            "diagnosis": rec.get("diagnosis"),
            "treatment": treatment,
            "precautions": precautions,
            "confidence": rec.get("confidence"),
            "created_at": rec.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if isinstance(rec.get("created_at"), datetime.datetime) else str(rec.get("created_at"))
        }

        filename = f"report_visual_user{user_id}_{prediction_id}_{int(datetime.datetime.utcnow().timestamp())}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        # get user name
        cur.execute("SELECT name FROM users WHERE id=%s", (user_id,))
        u = cur.fetchone()
        user_name = u["name"] if u else None

        generate_visual_pdf(filepath, user_name, record)

        # update DB with report_path
        cur.execute("UPDATE predictions SET report_path=%s WHERE id=%s", (filename, prediction_id))
        conn.commit()

        return FileResponse(filepath, filename=filename, media_type='application/pdf')
    finally:
        cur.close()
        conn.close()

# ---------- Health check ----------
@app.get("/health")
def health():
    return {"status": "ok"}

# ---------- Run (for uvicorn) ----------
# Run via: uvicorn app:app --reload --host 0.0.0.0 --port 5000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", reload=True)

