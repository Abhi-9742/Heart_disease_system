import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";

export default function Dashboard() {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    // ✅ Get history from localStorage
    const data =
      JSON.parse(localStorage.getItem("predictionHistory")) || [];

    setHistory(data);
  }, []);

  return (
    <>
      <Navbar />

      <div className="p-6 bg-gray-100 min-h-screen">
        <h2 className="text-3xl font-bold mb-6 text-center">
          Prediction History
        </h2>

        {history.length === 0 ? (
          <p className="text-center text-gray-500">
            No prediction history found.
          </p>
        ) : (
          <div className="overflow-auto bg-white rounded-xl shadow-lg">
            <table className="w-full text-center">
              <thead className="bg-rose-600 p-4 text-white">
                <tr>
                  <th className="p-3">#</th>
                  <th className="p-3">Name</th>
                  <th className="p-3">Age</th>
                  <th className="p-3">Sex</th>
                  <th className="p-3">Risk</th>
                  <th className="p-3">Time</th>
                </tr>
              </thead>

              <tbody>
                {history.map((h, i) => (
                  <tr key={i} className="border-b hover:bg-gray-100">
                    <td className="p-2">{i + 1}</td>

                    {/* ✅ Name from form data */}
                    <td className="p-2 font-medium">
                      {h.formData?.name || "Unknown"}
                    </td>

                    {/* ✅ Age from form data */}
                    <td className="p-2">
                      {h.formData?.age || "-"}
                    </td>
                    
                    {/* ✅ Sex from form data */}
                    <td className="p-2">
                      {h.formData?.sex === "1"
                        ? "Male"
                        : h.formData?.sex === "0"
                        ? "Female"
                        : "-"}
                    </td>


                    {/* ✅ Risk from prediction */}
                    <td
                      className={`p-2 font-semibold ${
                        h.prediction === 1
                          ? "text-red-600"
                          : "text-green-600"
                      }`}
                    >
                      {h.prediction === 1
                        ? "High Risk"
                        : "Low Risk"}
                    </td>

                    <td className="p-2 text-sm text-gray-500">
                      {new Date(h.time).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
