import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:5000",
});

// Automatically attach token for protected routes
API.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");

  if (token) {
    config.headers["Authorization"] = token;
  }

  return config;
});

export default API;

