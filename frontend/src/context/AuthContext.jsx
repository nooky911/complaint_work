import { createContext, useState, useEffect, useContext } from "react";
import api from "../api/api";

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuth, setIsAuth] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchUser = async () => {
    try {
      const res = await api.get("/users/me");
      setUser(res.data);
      setIsAuth(true);
    } catch (err) {
      setUser(null);
      setIsAuth(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const login = async () => {
    await fetchUser();
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch (error) {
      console.error("Ошибка при выходе", error);
    } finally {
      setUser(null);
      setIsAuth(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{ user, isAuth, login, logout, loading, setUser }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
