import {
  createContext,
  useState,
  useEffect,
  useContext,
  useCallback,
} from "react";
import api from "../api/api";
import { queryClient } from "../providers/QueryProvider";

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuth, setIsAuth] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    try {
      const res = await api.get("/users/me");
      setUser(res.data);
      setIsAuth(true);
    } catch (err) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        setUser(null);
        setIsAuth(false);
        queryClient.clear();
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
    const timer = setInterval(fetchUser, 60000);
    window.addEventListener("focus", fetchUser);
    return () => {
      clearInterval(timer);
      window.removeEventListener("focus", fetchUser);
    };
  }, [fetchUser]);

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
      queryClient.clear();
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

// Контекст и его хук сохраняют единый публичный интерфейс для существующих страниц
// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext);
