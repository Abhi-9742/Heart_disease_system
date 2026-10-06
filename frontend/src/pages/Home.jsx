import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";

export default function Home() {

  /* ===========================
     FLOATING MEDICAL ICONS
  =========================== */
  useEffect(() => {
    const icons = ["❤️", "🩺", "💉", "💊"];

    const interval = setInterval(() => {
      const icon = document.createElement("div");
      icon.innerHTML = icons[Math.floor(Math.random() * icons.length)];

      icon.style.position = "fixed";
      icon.style.left = Math.random() * window.innerWidth + "px";
      icon.style.top = "100vh";
      icon.style.fontSize = "22px";
      icon.style.opacity = "0.6";
      icon.style.animation = "floatUp 6s linear forwards";
      icon.style.pointerEvents = "none";
      icon.style.zIndex = "1";

      document.body.appendChild(icon);
      setTimeout(() => icon.remove(), 6000);
    }, 700);

    const style = document.createElement("style");
    style.innerHTML = `
      @keyframes floatUp {
        0% { transform: translateY(0); opacity: 1; }
        100% { transform: translateY(-120vh); opacity: 0; }
      }
    `;
    document.head.appendChild(style);

    return () => {
      clearInterval(interval);
      style.remove();
    };
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(to bottom, #fff5f5, #ffffff)",
        padding: "20px",
        fontFamily: "Arial, sans-serif",
        position: "relative",
        overflow: "hidden"
      }}
    >

      {/* ✅ Faint ECG Background */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "url('https://t4.ftcdn.net/jpg/05/64/05/49/360_F_564054980_NpVuWxBcFSXyvaBYdB2zPFSKTol5f2XV.jpg')",
          backgroundRepeat: "repeat-x",
          backgroundSize: "contain",
          opacity: 0.3,
          pointerEvents: "none",
          zIndex: 0
        }}
      ></div>

      <div style={{ position: "relative", zIndex: 2 }}>

        <Navbar />

        {/* HEADER */}
        <div style={{ textAlign: "center", marginTop: "30px" }}>
          <h1
            style={{
              fontSize: "42px",
              fontWeight: "bold",
              color: "#b30000",
            }}
          >
            Heart Disease Predictor
          </h1>

          
          <p
            style={{
              fontSize: "18px",
              color: "black",
              maxWidth: "700px",
              margin: "10px auto",
              lineHeight: "1.6",
            }}
          >
            A smart, AI-powered tool that analyzes clinical parameters to estimate
            the likelihood of heart disease. Designed for early screening and
            awareness to help you take control of your heart health.
          </p>
        </div>

        {/* FEATURES */}
        <div
          style={{
            marginTop: "40px",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "20px",
            width: "90%",
            margin: "auto",
          }}
        >
          {[
            {
              icon: "🩺",
              title: "AI-Based Prediction",
              desc: "Machine learning analyzes your health parameters for accurate risk estimation.",
            },
            {
              icon: "📊",
              title: "Health Dashboard",
              desc: "View your previous predictions and track health trends.",
            },
            {
              icon: "❤️",
              title: "Risk Awareness",
              desc: "Understand symptoms, factors, and ways to prevent heart disease.",
            },
            {
              icon: "⚡",
              title: "Fast & Reliable",
              desc: "Get instant results with medically verified parameters.",
            },
          ].map((f, i) => (
            <div
              key={i}
              style={{
                background: "white",
                borderRadius: "20px",
                padding: "25px",
                textAlign: "center",
                boxShadow: "0px 4px 15px rgba(0,0,0,0.1)",
                transition: "0.3s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "scale(1.05)";
                e.currentTarget.style.boxShadow =
                  "0px 6px 20px rgba(255,0,0,0.2)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "scale(1)";
                e.currentTarget.style.boxShadow =
                  "0px 4px 15px rgba(0,0,0,0.1)";
              }}
            >
              <div style={{ fontSize: "40px" }}>{f.icon}</div>
              <h3
                style={{
                  fontSize: "20px",
                  fontWeight: "bold",
                  marginTop: "10px",
                  color: "#b30000",
                }}
              >
                {f.title}
              </h3>
              <p style={{ marginTop: "8px", color: "#555" }}>{f.desc}</p>
            </div>
          ))}
        </div>

        {/* BUTTONS */}
        <div style={{ textAlign: "center", marginTop: "50px" }}>
          <Link to="/predict">
            <button style={btnStyle}>🔍 Start Prediction</button>
          </Link>

          <Link to="/about">
            <button style={btnStyle}>📘 About</button>
          </Link>

          <Link to="/dashboard">
            <button style={{ ...btnStyle, background: "#990000" }}>
              📊 Dashboard
            </button>
          </Link>
        </div>

        {/* FOOTER */}
        <div
          style={{
            marginTop: "60px",
            textAlign: "center",
            color: "#777",
            fontSize: "14px",
          }}
        >
          © {new Date().getFullYear()} Heart Disease Predictor • AI Health Tool
        </div>
      </div>
    </div>
  );
}

/* ✅ Button Style */
const btnStyle = {
  padding: "12px 24px",
  margin: "10px",
  background: "#b30000",
  color: "white",
  border: "none",
  borderRadius: "12px",
  fontSize: "16px",
  cursor: "pointer",
};
