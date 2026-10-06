import React from "react";

export default function About() {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(to bottom, #fffcfc, #ffe6e6)",
        padding: "20px",
        fontFamily: "Arial, sans-serif",
      }}
    >
    {/* ✅ Faint ECG Background */}
    <div
        style={{
          position: "fixed",
          inset: 0,
          backgroundImage:
            "url('https://t4.ftcdn.net/jpg/05/64/05/49/360_F_564054980_NpVuWxBcFSXyvaBYdB2zPFSKTol5f2XV.jpg')",
          backgroundRepeat: "no-repeat",
          backgroundPosition: "center",
          backgroundSize: "cover",
          opacity: 0.3,
          padding: "30px"
        }}
      ></div>

      {/* HEADER WITH ANIMATED ECG */}
      <div style={{ textAlign: "center", marginBottom: "40px" }}>
        <h1
          style={{
            fontSize: "36px",
            fontWeight: "bold",
            color: "#b30000",
            marginBottom: "10px",
          }}
        >
          About Heart Disease Predictor
        </h1>

        
      </div>

      {/* MAIN CONTENT */}
      <div
        style={{
          background: "white",
          borderRadius: "20px",
          padding: "30px",
          boxShadow: "0px 4px 20px rgba(255,0,0,0.2)",
          width: "85%",
          margin: "0 auto 40px auto",
        }}
      >
        <h2
          style={{
            fontSize: "24px",
            fontWeight: "bold",
            color: "#cc0000",
            marginBottom: "20px",
          }}
        >
          🔍 Overview
        </h2>

        <p style={{ fontSize: "16px", lineHeight: "1.6" }}>
          Heart disease is one of the leading causes of global mortality.
          Early detection drastically improves treatment outcomes and prevents
          complications. The <strong>Heart Disease Predictor</strong> uses a 
          trained machine learning model to estimate the likelihood of heart 
          disease based on key clinical features. This tool is intended for 
          awareness and early screening—not as a replacement for professional 
          medical diagnosis.
        </p>

        <h2
          style={{
            fontSize: "24px",
            fontWeight: "bold",
            marginTop: "30px",
            color: "#cc0000",
          }}
        >
          🧬 Medical Features Used in Prediction
        </h2>

        <div style={{ marginTop: "20px" }}>
          {[
            ["Age", "Represents the patient's age in years; risk increases with age."],
            ["Sex", "1 = Male, 0 = Female. Males generally have higher risk."],
            ["Chest Pain Type (cp)", "Indicates type of chest pain (0–3). Higher severity = higher risk."],
            ["Resting Blood Pressure (trestbps)", "Higher blood pressure puts strain on the heart."],
            ["Serum Cholesterol (chol)", "High cholesterol leads to artery blockage."],
            ["Fasting Blood Sugar (fbs)", "1 = >120 mg/dl; suggests diabetes risk."],
            ["Resting ECG (restecg)", "Shows electrical activity of the heart; abnormalities indicate issues."],
            ["Max Heart Rate (thalach)", "Lower values may indicate reduced heart performance."],
            ["Exercise-Induced Angina (exang)", "Chest pain triggered by exercise."],
            ["Oldpeak", "ST depression induced by exercise; measures heart stress."],
            ["Slope", "Direction of ST segment (0–2). Downsloping increases risk."],
            ["Major Vessels (ca)", "Number of vessels colored via fluoroscopy (0–3)."],
            ["Thalassemia (thal)", "Blood disorder affecting oxygen levels in the body."],
          ].map(([title, desc], i) => (
            <div
              key={i}
              style={{
                marginBottom: "18px",
                padding: "15px",
                background: "#fff5f5",
                borderRadius: "10px",
                borderLeft: "5px solid #cc0000",
              }}
            >
              <h3
                style={{
                  fontSize: "18px",
                  fontWeight: "bold",
                  color: "#b30000",
                }}
              >
                {title}
              </h3>
              <p style={{ marginTop: "5px", fontSize: "15px", lineHeight: "1.5" }}>
                {desc}
              </p>
            </div>
          ))}
        </div>

        <h2
          style={{
            fontSize: "24px",
            fontWeight: "bold",
            marginTop: "30px",
            color: "#cc0000",
          }}
        >
          ❤️ Why This Model Matters
        </h2>

        <ul style={{ marginTop: "15px", lineHeight: "1.6" }}>
          <li>Helps with early screening and awareness.</li>
          <li>Supports preventive healthcare.</li>
          <li>Encourages lifestyle improvements.</li>
          <li>Provides fast analysis using ML models.</li>
        </ul>

        <h2
          style={{
            fontSize: "24px",
            fontWeight: "bold",
            marginTop: "30px",
            color: "#cc0000",
          }}
        >
          ⚠️ Disclaimer
        </h2>
        <p style={{ marginTop: "10px", fontSize: "15px" }}>
          This predictor is a supportive tool and not a clinical diagnosis.
          Always consult a certified doctor for medical decisions.
        </p>
      </div>
    </div>
  );
}
