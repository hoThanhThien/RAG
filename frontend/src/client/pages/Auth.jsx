// 📁 src/pages/Auth.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, register } from "../services/authService";
import { useAuth } from "../context/AuthContext";
import loginImg from "../../assets/Vinh-Ha-Long.jpg";
import registerImg from "../../assets/Phu-sy.jpg";

import "../../styles/Auth.css";



export default function AuthPage() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    phone: ""
  });
  const [error, setError] = useState("");
  
  const { setUser } = useAuth();

 const handleSubmit = async (e) => {
  e.preventDefault();
  setError("");

  if (isLogin) {
    const res = await login(form);
    if (res.success) {
      setUser(res.user);

      // 🔐 Điều hướng theo role_id
      if (res.user?.role_id === 1) {
        navigate("/admin");
      } else {
        navigate("/");
      }
    } else {
      setError(res.message);
    }
  } else {
    const res = await register({ ...form, role_id: 3 });
    if (res.success) {
      setIsLogin(true);
    } else {
      setError(res.message);
    }
  }
};

  return (
    <div className="auth-wrapper">
        {/* ✅ Nút quay lại ở góc trái trên */}
    <button
      className="back-btn"
      onClick={() => navigate("/")}
    >
      ⬅️ Quay lại
    </button>
      <div className={`auth-container ${isLogin ? "login-mode" : "register-mode"}`}>
        <div className="auth-box">
          <div className="form-section">
            <form onSubmit={handleSubmit} className="auth-form">
              <h2>{isLogin ? "Đăng nhập" : "Đăng ký"}</h2>
              {error && <div className="auth-error">{error}</div>}

              {!isLogin && (
                <>
                  <input
                    type="text"
                    placeholder="Họ"
                    value={form.first_name}
                    onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                    required
                  />
                  <input
                    type="text"
                    placeholder="Tên"
                    value={form.last_name}
                    onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                    required
                  />
                  <input
                    type="text"
                    placeholder="Số điện thoại"
                    value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                    required
                  />
                </>
              )}

              <input
                type="email"
                placeholder="Email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
              <input
                type="password"
                placeholder="Mật khẩu"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
              />
              <button type="submit" className="submit-btn">
                {isLogin ? "Đăng nhập" : "Đăng ký"}
              </button>
            </form>
          </div>
          <div
            className="image-section"
            style={{ backgroundImage: `url(${isLogin ? loginImg : registerImg})` }}
          >
            <div className="image-content">
              <h2>{isLogin ? "Chào mừng trở lại!" : "Tạo tài khoản mới"}</h2>
              <p>{isLogin ? "Bạn chưa có tài khoản?" : "Đã có tài khoản?"}</p>
              <button
                className="toggle-btn"
                onClick={() => {
                  setError("");
                  setIsLogin(!isLogin);
                }}
              >
                {isLogin ? "Đăng ký ngay" : "Đăng nhập"}
              </button>
             
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
