import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.PROD ? "/api/v1" : "http://localhost:8000/api/v1",
  withCredentials: true,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const isLoginRequest = error.config?.url?.includes("/auth/login");
      const isMeRequest = error.config?.url?.includes("/users/me");

      if (!isLoginRequest && !isMeRequest) {
        console.warn("Сессия отсутствует или истекла.");
      }
    }
    return Promise.reject(error);
  },
);

export default api;
