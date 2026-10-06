import { useState } from "react";
import API from "../services/api";
import { useNavigate, Link } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const res = await API.post("/login", form);
      localStorage.setItem("token", res.data.token);
      navigate("/home");
    } catch (err) {
      alert("Invalid credentials");
    }
  };

  return (
    <div className="relative flex justify-center items-center h-screen overflow-hidden bg-gray-900">

      {/* ✅ ECG Animated Background */}
      <div className="absolute inset-0 flex items-center justify-center">
        <svg
          viewBox="0 0 1000 200"
          className="w-full h-full opacity-20"
          preserveAspectRatio="none"
        >
          <polyline
            points="0,100 100,100 120,40 140,160 160,60 180,140 200,100 1000,100"
            fill="none"
            stroke="#00ffcc"
            strokeWidth="4"
            strokeDasharray="500"
            strokeDashoffset="500"
            style={{
              animation: "ecgMove 2s linear infinite"
            }}
          />
        </svg>
      </div>

      {/* ✅ Animation Style */}
      <style>
        {`
          @keyframes ecgMove {
            to {
              stroke-dashoffset: 0;
            }
          }
        `}
      </style>

      {/* ✅ Login Form */}
      <form
        onSubmit={handleSubmit}
        className="relative z-10 bg-white/90 backdrop-blur-lg p-8 rounded-2xl shadow-xl w-96 space-y-4"
      >
        <h2 className="text-2xl text-center font-bold text-gray-800">
          🫀 Heart Predictor Login
        </h2>

        <input
          type="email"
          placeholder="Email"
          className="w-full border p-2 rounded"
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />

        <input
          type="password"
          placeholder="Password"
          className="w-full border p-2 rounded"
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />

        <button className="w-full bg-blue-600 text-white p-2 rounded">
          Login
        </button>

        <p className="text-center">
          No account?{" "}
          <Link to="/register" className="text-blue-600 font-semibold">
            Register
          </Link>
        </p>
      </form>
    </div>
  );
}
