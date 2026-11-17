// 📁 src/pages/Auth.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, loginWithGoogle, register } from "../services/authService";
import { useAuth } from "../context/AuthContext";
import loginImg from "../../assets/Vinh-Ha-Long.jpg";
import registerImg from "../../assets/Phu-sy.jpg";

import "../../styles/Auth.css";

const DEMO_GOOGLE_ACCOUNTS = [
  {
    email: "google.traveler@gmail.com",
    full_name: "Nguyễn Minh Khôi",
  },
  {
    email: "user2@gmail.com",
    full_name: "User 2",
  },
];

export default function AuthPage() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirm_password: "",
    phone: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Google Demo Modal (khi chạy local chưa cấu hình VITE_GOOGLE_CLIENT_ID)
  const [showGoogleModal, setShowGoogleModal] = useState(false);
  const [googleForm, setGoogleForm] = useState({
    email: "google.traveler@gmail.com",
    full_name: "Nguyễn Minh Khôi",
  });

  const { setUser } = useAuth();
  const googleClientId = (import.meta.env.VITE_GOOGLE_CLIENT_ID || "").trim();

  const finishAuthSuccess = (res) => {
    setUser(res.user);
    if (Number(res.user?.role_id) === 1) {
      navigate("/admin");
    } else {
      navigate("/");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");

    if (isLogin) {
      setLoading(true);
      try {
        const res = await login({
          email: form.email.trim(),
          password: form.password,
        });
        if (res.success) {
          finishAuthSuccess(res);
        } else {
          setError(res.message);
        }
      } finally {
        setLoading(false);
      }
      return;
    }

    // Validate đăng ký
    if (form.password.length < 6) {
      setError("Mật khẩu phải có ít nhất 6 ký tự.");
      return;
    }
    if (form.password !== form.confirm_password) {
      setError("Mật khẩu xác nhận không khớp.");
      return;
    }
    if (form.phone && !/^[0-9+\-\s]{8,15}$/.test(form.phone.trim())) {
      setError("Số điện thoại không hợp lệ.");
      return;
    }

    setLoading(true);
    try {
      const res = await register({
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        password: form.password,
        phone: form.phone.trim(),
      });
      if (res.success) {
        setSuccessMsg(res.message || "Đăng ký thành công!");
        finishAuthSuccess(res);
      } else {
        setError(res.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const completeGoogleAuth = async (payload) => {
    setLoading(true);
    setError("");
    setSuccessMsg("");
    try {
      const res = await loginWithGoogle(payload);
      if (res.success) {
        setShowGoogleModal(false);
        finishAuthSuccess(res);
      } else {
        setError(res.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleButtonClick = () => {
    setError("");
    setSuccessMsg("");

    if (googleClientId) {
      if (window.google?.accounts?.oauth2) {
        const tokenClient = window.google.accounts.oauth2.initTokenClient({
          client_id: googleClientId,
          scope: "openid email profile",
          callback: async (tokenResponse) => {
            if (tokenResponse?.error || !tokenResponse?.access_token) {
              setError("Xác thực Google bị hủy hoặc không thành công.");
              setLoading(false);
              return;
            }
            await completeGoogleAuth({ access_token: tokenResponse.access_token });
          },
        });
        setLoading(true);
        tokenClient.requestAccessToken();
        return;
      }
      setError("Thư viện Google Identity chưa sẵn sàng. Vui lòng thử lại sau vài giây.");
      return;
    }

    // Chế độ local / chưa cấu hình Client ID: mở popup chọn tài khoản Google nhanh
    setShowGoogleModal(true);
  };

  const handleGoogleModalSubmit = async (e) => {
    e.preventDefault();
    if (!googleForm.email.trim()) {
      setError("Vui lòng nhập email Google.");
      return;
    }
    await completeGoogleAuth({
      email: googleForm.email.trim(),
      full_name: googleForm.full_name.trim(),
    });
  };

  return (
    <div className="auth-wrapper">
      <button
        type="button"
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
              {successMsg && <div className="auth-success">{successMsg}</div>}

              {!isLogin && (
                <>
                  <div className="auth-name-row">
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
                  </div>
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

              <div className="auth-password-field">
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Mật khẩu (tối thiểu 6 ký tự)"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                />
                <button
                  type="button"
                  className="auth-eye-btn"
                  onClick={() => setShowPassword((prev) => !prev)}
                  aria-label="Hiện hoặc ẩn mật khẩu"
                >
                  <i className={`bi ${showPassword ? "bi-eye-slash" : "bi-eye"}`} />
                </button>
              </div>

              {!isLogin && (
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Xác nhận mật khẩu"
                  value={form.confirm_password}
                  onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
                  required
                />
              )}

              <button type="submit" className="submit-btn" disabled={loading}>
                {loading
                  ? "Đang xử lý..."
                  : isLogin
                  ? "Đăng nhập"
                  : "Đăng ký tài khoản"}
              </button>

              <div className="auth-divider">
                <span>hoặc</span>
              </div>

              <button
                type="button"
                className="google-auth-btn"
                onClick={handleGoogleButtonClick}
                disabled={loading}
              >
                <svg className="google-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    fill="#4285F4"
                    d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17Z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.11-6.72-4.96H1.29v3.14C3.26 21.3 7.31 24 12 24Z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.28 14.24c-.24-.72-.38-1.49-.38-2.24s.14-1.52.38-2.24V6.62H1.29C.47 8.24 0 10.06 0 12s.47 3.76 1.29 5.38l3.99-3.14Z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.26 2.7 1.29 6.62l3.99 3.14c.95-2.85 3.6-4.96 6.72-4.96Z"
                  />
                </svg>
                <span>{isLogin ? "Đăng nhập với Google" : "Đăng ký với Google"}</span>
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
                type="button"
                className="toggle-btn"
                onClick={() => {
                  setError("");
                  setSuccessMsg("");
                  setIsLogin(!isLogin);
                }}
              >
                {isLogin ? "Đăng ký ngay" : "Đăng nhập"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Modal chọn tài khoản Google khi chạy local chưa gắn GOOGLE_CLIENT_ID */}
      {showGoogleModal && (
        <div className="google-modal-backdrop" onClick={() => setShowGoogleModal(false)}>
          <div className="google-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="google-modal-header">
              <h5>
                <i className="bi bi-google text-danger me-2" />
                {isLogin ? "Đăng nhập bằng Google" : "Đăng ký bằng Google"}
              </h5>
              <button
                type="button"
                className="btn-close"
                aria-label="Đóng"
                onClick={() => setShowGoogleModal(false)}
              />
            </div>

            <p className="text-muted small mb-3">
              Chưa cấu hình <code>VITE_GOOGLE_CLIENT_ID</code> — chọn nhanh hoặc nhập email Google để kiểm thử luồng tự động đăng ký / đăng nhập qua <code>HttpOnly Cookie</code>:
            </p>

            <div className="d-flex flex-column gap-2 mb-3">
              {DEMO_GOOGLE_ACCOUNTS.map((acc) => (
                <button
                  key={acc.email}
                  type="button"
                  className="google-account-chip"
                  disabled={loading}
                  onClick={() => completeGoogleAuth(acc)}
                >
                  <div>
                    <div className="fw-semibold">{acc.full_name}</div>
                    <div className="small text-muted">{acc.email}</div>
                  </div>
                  <i className="bi bi-arrow-right-circle text-primary fs-5" />
                </button>
              ))}
            </div>

            <form onSubmit={handleGoogleModalSubmit} className="d-flex flex-column gap-2">
              <input
                type="email"
                className="form-control"
                placeholder="Email Google khác..."
                value={googleForm.email}
                onChange={(e) => setGoogleForm({ ...googleForm, email: e.target.value })}
                required
              />
              <input
                type="text"
                className="form-control"
                placeholder="Họ và tên hiển thị"
                value={googleForm.full_name}
                onChange={(e) => setGoogleForm({ ...googleForm, full_name: e.target.value })}
              />
              <div className="d-flex justify-content-end gap-2 mt-2">
                <button
                  type="button"
                  className="btn btn-light"
                  onClick={() => setShowGoogleModal(false)}
                >
                  Hủy
                </button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? "Đang xác thực..." : "Tiếp tục với Google"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
