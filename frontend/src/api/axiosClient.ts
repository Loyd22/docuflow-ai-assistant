import axios from "axios";


// This gets the backend URL from the frontend .env file.
// If the .env value is missing, it will use localhost:8000.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";


// This creates one reusable Axios client for all backend API requests.
const axiosClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});


export default axiosClient;