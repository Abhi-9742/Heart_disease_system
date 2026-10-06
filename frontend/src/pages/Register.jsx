import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import API from "../services/api";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      await API.post("/register", form);
      navigate("/");
    } catch (err) {
      alert("Email already exists");
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
      
      <form className="bg-white p-8 rounded-xl shadow-lg w-96 space-y-4"
        onSubmit={handleSubmit}
      >
        <h2 className="text-2xl font-bold text-center">Register</h2>

        <input
          type="text"
          placeholder="Name"
          className="w-full border p-2 rounded"
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />

        <input
          type="email"
          placeholder="Email"
          className="w-full border p-2 rounded"
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />

        <input
          type="password"
          placeholder="Password"
          className="w-full border p-2 rounded"
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />

        <button className="w-full bg-blue-600 text-white p-2 rounded">
          Register
        </button>

        <p className="text-center">
          Already have an account?{" "}
          <Link to="/login" className="text-blue-600 font-semibold">Login</Link>
        </p>
      </form>
    </div>
  );
}
