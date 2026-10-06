import { useState } from "react";
import API from "../services/api";
import jsPDF from "jspdf";

import {
  PieChart, Pie, Cell, Tooltip,
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer
} from "recharts";

/* ===========================
   ECG ANIMATION COMPONENT
=========================== */
function ECGLine() {
  return (
    <div style={{ textAlign: "center", marginBottom: "10px" }}>
      <svg width="100%" height="60" viewBox="0 0 800 60">
        <polyline
          points="0,30 80,30 100,10 120,50 140,10 160,50 180,30 260,30 280,15 300,45 320,30 800,30"
          fill="none"
          stroke="#ef4444"
          strokeWidth="4"
          strokeDasharray="400"
          strokeDashoffset="400"
          style={{ animation: "ecgWave 1.2s linear infinite" }}
        />
        <style>{`
          @keyframes ecgWave { to { stroke-dashoffset: 0; } }
        `}</style>
      </svg>
    </div>
  );
}

export default function Predict() {
  const [form, setForm] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  /* ===========================
     SUBMIT HANDLER
  =========================== */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const token = localStorage.getItem("token");

      const res = await API.post("/predict", form, {
        headers: { Authorization: token }
      });

      setResult(res.data);

      /* ✅ Save Prediction History (MATCHES DASHBOARD) */
      const oldHistory =
        JSON.parse(localStorage.getItem("predictionHistory")) || [];

      const newEntry = {
        id: Date.now(),

        // ✅ Raw backend prediction number (Dashboard needs this)
        prediction: res.data.prediction,

        // ✅ Save full form for name and age
        formData: {
          name: form.name,
          age: form.age,
          sex: form.sex
        },

        diagnosis: res.data.diagnosis,
        time: new Date().toISOString()
      };
 
      localStorage.setItem(
      "predictionHistory",
      JSON.stringify([newEntry, ...oldHistory])
      );


    } catch (error) {
      alert("Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  /* ===========================
     PDF DOWNLOAD
  =========================== */
  const downloadPDF = () => {
    const doc = new jsPDF();

    doc.setFontSize(18);
    doc.text("Heart Disease Prediction Report", 20, 20);

    doc.setFontSize(12);
    doc.text(`Name: ${form.name}`, 20, 35);
    doc.text(`Age: ${form.age}`, 20, 45);
    doc.text(`Sex: ${form.sex === "1" ? "Male" : "Female"}`, 20, 55);

    doc.text(
      `Risk Status: ${result.prediction === 1 ? "High Risk" : "Low Risk"}`,
      20,
      70
    );

    doc.text(`Diagnosis: ${result.diagnosis}`, 20, 80);

    let y = 95;
    doc.text("Parameters:", 20, y);

    Object.entries(form).forEach(([key, val], i) => {
      if (key === "name") return;
      doc.text(`${key.toUpperCase()}: ${val}`, 20, y + 10 + i * 7);
    });

    y += Object.keys(form).length * 7 + 20;

    doc.text("Treatment:", 20, y);
    y += 8;

    result.treatment?.forEach((t, i) => {
      doc.text(`- ${t}`, 20, y + i * 7);
    });

    y += (result.treatment?.length || 0) * 7 + 10;

    doc.text("Precautions:", 20, y);
    result.precautions?.forEach((p, i) => {
      doc.text(`- ${p}`, 20, y + (i + 1) * 7);
    });

    doc.save("Heart_Prediction_Report.pdf");
  };

  /* ===========================
     CHART DATA
  =========================== */
  const pieData = result ? [
    { name: "Risk", value: result.prediction === 1 ? 75 : 25 },
    { name: "Safe", value: result.prediction === 1 ? 25 : 75 }
  ] : [];

  const barData = result ? [
    { name: "Cholesterol", value: Number(form.chol) || 0 },
    { name: "Blood Pressure", value: Number(form.trestbps) || 0 },
    { name: "Heart Rate", value: Number(form.thalach) || 0 },
    { name: "Oldpeak", value: Number(form.oldpeak) || 0 }
  ] : [];

  const COLORS = ["#ef4444", "#22c55e"];

  return (
    <div style={styles.page}>

      {/* ✅ FORM */}
      {!result && !loading && (
        <form onSubmit={handleSubmit} style={styles.form}>
          <h2 style={styles.title}>🫀 Heart Disease Prediction</h2>

          {Object.keys(formFields).map((key) => (
            <input
              key={key}
              type={key === "name" ? "text" : "number"}
              placeholder={key.toUpperCase()}
              style={styles.input}
              onChange={(e) =>
                setForm({ ...form, [key]: e.target.value })
              }
              required
            />
          ))}

          <button style={styles.btn}>Predict</button>
        </form>
      )}

      {/* ✅ LOADING ECG */}
      {loading && (
        <div style={styles.loaderWrap}>
          <ECGLine />
          <p style={styles.loaderText}>Analyzing heart signals...</p>
        </div>
      )}

      {/* ✅ RESULT FULL PAGE */}
      {result && !loading && (
        <div style={styles.resultPage}>

          <ECGLine />

          <h2 style={styles.resultTitle}>
            {result.prediction === 1 ? "🔴 HIGH RISK" : "🟢 LOW RISK"}
          </h2>

          <p style={styles.diagnosis}>
            {result.diagnosis}
          </p>

          <div style={{ height: "250px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" innerRadius={50} outerRadius={80}>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div style={{ height: "250px", marginTop: "20px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <h3 style={styles.sectionTitle}>Treatment</h3>
          <ul>
            {result.treatment?.map((t, i) => <li key={i}>{t}</li>)}
          </ul>

          <h3 style={styles.sectionTitle}>Precautions</h3>
          <ul>
            {result.precautions?.map((p, i) => <li key={i}>{p}</li>)}
          </ul>

          <div style={styles.actionRow}>
            <button onClick={downloadPDF} style={styles.pdfBtn}>
              📄 Download PDF
            </button>
            <button
              onClick={() => { setResult(null); setForm({}); }}
              style={styles.backBtn}
            >
              🔄 New Prediction
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ===========================
   FORM FIELDS
=========================== */
const formFields = {
  name: "",
  age: "",
  sex: "",
  cp: "",
  trestbps: "",
  chol: "",
  fbs: "",
  restecg: "",
  thalach: "",
  exang: "",
  oldpeak: "",
  slope: "",
  ca: "",
  thal: ""
};

/* ===========================
   STYLES
=========================== */
const styles = {
  page: {
    minHeight: "100vh",
    backgroundImage:
      "url('https://t4.ftcdn.net/jpg/05/64/05/49/360_F_564054980_NpVuWxBcFSXyvaBYdB2zPFSKTol5f2XV.jpg')",
    backgroundSize: "cover",
    backgroundPosition: "center",
    backgroundRepeat: "no-repeat",
    padding: "30px"
  },
  
  form: {
    maxWidth: "500px",
    margin: "0 auto",
    padding: "25px",
    borderRadius: "20px",
    background: "white",
    boxShadow: "0 10px 30px rgba(0,0,0,0.07)"
  },
  title: {
    textAlign: "center",
    fontSize: "22px",
    fontWeight: "800",
    marginBottom: "16px"
  },
  input: {
    width: "100%",
    padding: "12px",
    borderRadius: "12px",
    border: "1px solid #ddd",
    marginBottom: "10px"
  },
  btn: {
    width: "100%",
    padding: "12px",
    background: "red",
    color: "white",
    fontWeight: "700",
    border: "none",
    borderRadius: "12px",
    cursor: "pointer"
  },
  loaderWrap: {
    minHeight: "80vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center"
  },
  loaderText: {
    marginTop: "10px",
    fontWeight: "600",
    color: "#334155"
  },
  resultPage: {
    maxWidth: "900px",
    margin: "0 auto",
    background: "white",
    padding: "25px",
    borderRadius: "18px",
    boxShadow: "0 20px 40px rgba(0,0,0,0.08)"
  },
  resultTitle: {
    textAlign: "center",
    fontSize: "26px",
    fontWeight: "900"
  },
  diagnosis: {
    textAlign: "center",
    fontWeight: "600",
    color: "#374151",
    marginBottom: "10px"
  },
  sectionTitle: {
    marginTop: "20px",
    fontSize: "18px",
    fontWeight: "800"
  },
  actionRow: {
    marginTop: "20px",
    display: "flex",
    justifyContent: "center",
    gap: "10px"
  },
  pdfBtn: {
    background: "#16a34a",
    color: "#fff",
    padding: "12px 18px",
    borderRadius: "12px",
    border: "none",
    fontWeight: "700",
    cursor: "pointer"
  },
  backBtn: {
    background: "#ef4444",
    color: "#fff",
    padding: "12px 18px",
    borderRadius: "12px",
    border: "none",
    fontWeight: "700",
    cursor: "pointer"
  }
};
