import { createContext, useContext, useEffect, useState } from "react";
import {
  getCurrentUser,
  logout as handleLogout,
} from "../services/authService";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // Thêm loading

  useEffect(() => {
    const fetchUser = async () => {
      // ✅ Kiểm tra token trước khi gọi API
      const token = localStorage.getItem("access_token");
      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }
      
      try {
        const data = await getCurrentUser();
        setUser(data);
      } catch (err) {
        // Token không hợp lệ hoặc hết hạn -> xóa token
        localStorage.removeItem("access_token");
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, []);

  const logout = async () => {
    await handleLogout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
