import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.PROD ? "/api/v1" : "http://localhost:8000/api/v1",
  withCredentials: true,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const isLoginRequest = error.config?.url?.includes("/auth/login");

      if (!isLoginRequest) {
        console.warn("Сессия истекла. Перенаправление на вход...");

        localStorage.removeItem("token");

        window.location.reload();
      }
    }
    return Promise.reject(error);
  },
);

export default api;
