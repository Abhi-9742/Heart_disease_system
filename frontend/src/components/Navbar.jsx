import { Link, useNavigate } from "react-router-dom";

export default function Navbar() {
  const navigate = useNavigate();

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  return (
      <nav className="bg-rose-600 p-4 text-white flex justify-between items-center shadow-lg">
      <h1 className="text-xl font-bold">❤️ Heart Disease Predictor</h1>

      <div className="space-x-6">
        <Link to="/home">Home</Link>
        <Link to="/about">About</Link>
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/predict">Predict</Link>
        

        <button
          onClick={logout}
          className="bg-red-500 px-4 py-1 rounded hover:bg-red-700"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}
