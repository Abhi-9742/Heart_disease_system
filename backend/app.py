import os
import io
import json
import tempfile
import datetime
from typing import Optional

import joblib
import numpy as np
import mysql.connector
from mysql.connector import Error

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

# PDF + plot
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
import matplotlib.pyplot as plt

# ENV
from dotenv import load_dotenv
load_dotenv()

# -------------- CONFIG -----------------
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "heart_disease")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-secret")
MODEL_PATH = os.getenv("MODEL_PATH", "models/heart_model.pkl")
SCALER_PATH = os.getenv("SCALER_PATH", "models/scaler.pkl")

REPORTS_DIR = os.path.join(os.getcwd(), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# -------------- FLASK APP -----------------
app = Flask(__name__)
CORS(app)

# ---------- DB Connection ----------
def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        autocommit=False
    )

# ---------- Load Model ----------
try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
except Exception as e:
    model = None
    scaler = None
    print("Model load failed:", e)


# --------- JWT HELPERS ----------
def create_token(user_id: int):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except Exception:
        raise Exception("Invalid token")


def get_current_user():
    auth = request.headers.get("Authorization")
    if not auth:
        return None

    token = auth.replace("Bearer ", "")
    try:
        data = decode_token(token)
        return data["user_id"]
    except:
        return None


# --------- Advice Builder ----------
def build_advice(prediction, confidence):
    if prediction == 1:
        diagnosis = "High risk of heart disease"
        treatment = [
            "Consult a cardiologist immediately",
            "Consider BP/cholesterol medication",
            "ECG/ECHO and stress test recommended",
            "Regular follow-up required"
        ]
        precautions = [
            "Quit smoking/alcohol",
            "Daily exercise 30 to 45 mins",
            "Reduce salt and saturated fats",
            "Stress management & proper sleep",
        ]
    else:
        diagnosis = "Low risk of heart disease"
        treatment = [
            "No immediate treatment required",
            "Keep healthy habits"
        ]
        precautions = [
            "Balanced diet",
            "Daily walking/exercise",
            "Reduce salt & processed food",
            "Regular health checkups"
        ]

    return diagnosis, treatment, precautions


# ---------- ROUTES ----------

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("SELECT id FROM users WHERE email=%s", (data["email"],))
        if cur.fetchone():
            return jsonify({"error": "User already exists"}), 400

        hashed = generate_password_hash(data["password"], method="pbkdf2:sha256")
        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (%s,%s,%s)",
            (data.get("name"), data["email"], hashed),
        )
        conn.commit()
        return jsonify({"message": "Registered"})
    finally:
        cur.close()
        conn.close()


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("SELECT id, password, name FROM users WHERE email=%s", (data["email"],))
        row = cur.fetchone()
        if not row or not check_password_hash(row["password"], data["password"]):
            return jsonify({"error": "Invalid credentials"}), 401

        token = create_token(row["id"])
        return jsonify({
            "token": token,
            "user": {"id": row["id"], "name": row["name"]}
        })
    finally:
        cur.close()
        conn.close()


@app.route("/predict", methods=["POST"])
def predict():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500

    fields = ["age","sex","cp","trestbps","chol","fbs","restecg",
              "thalach","exang","oldpeak","slope","ca","thal"]
    values = [data[k] for k in fields]

    X = scaler.transform([values])
    pred = int(model.predict(X)[0])
    try:
        confidence = float(np.max(model.predict_proba(X)))
    except:
        confidence = None

    diagnosis, treatment, precautions = build_advice(pred, confidence)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO predictions (user_id, prediction, diagnosis, treatment, precautions, confidence, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            user_id, pred, diagnosis,
            json.dumps(treatment), json.dumps(precautions),
            confidence, datetime.datetime.utcnow()
        ))
        pred_id = cur.lastrowid
        conn.commit()
    finally:
        cur.close()
        conn.close()

    return jsonify({
        "prediction": pred,
        "confidence": confidence,
        "diagnosis": diagnosis,
        "treatment": treatment,
        "precautions": precautions,
        "prediction_id": pred_id
    })


@app.route("/history", methods=["GET"])
def history():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            SELECT * FROM predictions WHERE user_id=%s ORDER BY timestamp DESC
        """, (user_id,))
        rows = cur.fetchall()

        for r in rows:
            r["treatment"] = json.loads(r["treatment"]) if r.get("treatment") else []
            r["precautions"] = json.loads(r["precautions"]) if r.get("precautions") else []

        return jsonify(rows)
    finally:
        cur.close()
        conn.close()


# -------- PDF helpers --------
def create_gauge_image(score, path):
    fig, ax = plt.subplots(figsize=(3,1.5))
    ax.axis("off")
    ax.barh([0], [1], color="#eee", height=0.6)
    ax.barh([0], [score], color=("#ef4444" if score > 0.5 else "#10b981"), height=0.6)
    ax.text(score, 0, f"{int(score*100)}%", va="center", ha="left", fontsize=10)
    plt.xlim(0, 1)
    plt.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def generate_pdf(filepath, title, user_name, rec, visual=False):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    elements = []

    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Paragraph(f"Patient: {user_name}", styles["Normal"]))
    elements.append(Paragraph(f"Date: {rec['created_at']}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    if visual:
        gauge_fd, gauge_path = tempfile.mkstemp(suffix=".png")
        os.close(gauge_fd)
        create_gauge_image(rec["confidence"] or 0.7, gauge_path)
        elements.append(RLImage(gauge_path, width=300, height=120))
        elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Prediction</b>", styles["Heading3"]))
    elements.append(Paragraph("High risk" if rec["prediction"] else "Low risk", styles["Normal"]))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("<b>Diagnosis</b>", styles["Heading3"]))
    elements.append(Paragraph(rec["diagnosis"], styles["Normal"]))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("<b>Treatment</b>", styles["Heading3"]))
    for t in rec["treatment"]:
        elements.append(Paragraph(f"• {t}", styles["Normal"]))

    elements.append(Paragraph("<b>Precautions</b>", styles["Heading3"]))
    for p in rec["precautions"]:
        elements.append(Paragraph(f"• {p}", styles["Normal"]))

    doc.build(elements)


@app.route("/report/simple/<int:prediction_id>")
def report_simple(prediction_id):
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("SELECT * FROM predictions WHERE id=%s", (prediction_id,))
        rec = cur.fetchone()

        if not rec or rec["user_id"] != user_id:
            return jsonify({"error": "Not allowed"}), 403

        rec["treatment"] = json.loads(rec["treatment"])
        rec["precautions"] = json.loads(rec["precautions"])
        rec["created_at"] = rec["created_at"].strftime("%Y-%m-%d %H:%M:%S")

        # user name
        cur.execute("SELECT name FROM users WHERE id=%s", (user_id,))
        u = cur.fetchone()
        user_name = u["name"]

        filename = f"report_simple_{user_id}_{prediction_id}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        generate_pdf(filepath, "Heart Disease Report", user_name, rec, visual=False)

        return send_file(filepath, as_attachment=True)
    finally:
        cur.close()
        conn.close()


@app.route("/report/visual/<int:prediction_id>")
def report_visual(prediction_id):
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("SELECT * FROM predictions WHERE id=%s", (prediction_id,))
        rec = cur.fetchone()

        if not rec or rec["user_id"] != user_id:
            return jsonify({"error": "Not allowed"}), 403

        rec["treatment"] = json.loads(rec["treatment"])
        rec["precautions"] = json.loads(rec["precautions"])
        rec["created_at"] = rec["created_at"].strftime("%Y-%m-%d %H:%M:%S")

        cur.execute("SELECT name FROM users WHERE id=%s", (user_id,))
        u = cur.fetchone()
        user_name = u["name"]

        filename = f"report_visual_{user_id}_{prediction_id}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        generate_pdf(filepath, "Heart Disease Report (Visual)", user_name, rec, visual=True)

        return send_file(filepath, as_attachment=True)
    finally:
        cur.close()
        conn.close()


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ------------ RUN ------------
if __name__ == "__main__":
    app.run(debug=True)
