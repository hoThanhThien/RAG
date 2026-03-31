import React, { useMemo, useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate, Link } from "react-router-dom";
import "../../styles/UserProfile.css";
import { changePassword } from "../services/authService";
import { commentService } from "../services/commentService";

export default function UserProfile() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState({ type: "", text: "" });
  const [showPw, setShowPw] = useState({ old: false, nw: false, cf: false });

  const [myComments, setMyComments] = useState([]);
  const [showReviews, setShowReviews] = useState(false);

  useEffect(() => {
    commentService.listMyComments().then(setMyComments);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate("/auth");
  };

  const roleLabel = user?.role_name || (user?.role_id === 1 ? "Admin" : "User");

  const initials = useMemo(() => {
    const n = user?.full_name || user?.name || "";
    return n.split(" ").map((x) => x[0]).filter(Boolean).slice(0, 2).join("").toUpperCase();
  }, [user]);

  const score = useMemo(() => {
    let s = 0;
    if (newPw.length >= 8) s++;
    if (/[A-Z]/.test(newPw)) s++;
    if (/[a-z]/.test(newPw)) s++;
    if (/\d/.test(newPw)) s++;
    if (/[^A-Za-z0-9]/.test(newPw)) s++;
    return Math.min(s, 5);
  }, [newPw]);

  const validate = () => {
    if (!oldPw || !newPw || !confirmPw) return "Vui lòng nhập đầy đủ thông tin.";
    if (newPw !== confirmPw) return "Mật khẩu mới và xác nhận không khớp.";
    if (newPw.length < 8) return "Mật khẩu mới tối thiểu 8 ký tự.";
    if (newPw === oldPw) return "Mật khẩu mới không được trùng mật khẩu cũ.";
    return null;
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setAlert({ type: "", text: "" });
    const err = validate();
    if (err) return setAlert({ type: "danger", text: err });
    try {
      setLoading(true);
      await changePassword(oldPw, newPw);
      setAlert({ type: "success", text: "Đổi mật khẩu thành công." });
      setOldPw(""); setNewPw(""); setConfirmPw("");
    } catch (error) {
      const msg = error?.response?.data?.detail || "Đổi mật khẩu thất bại.";
      setAlert({ type: "danger", text: String(msg) });
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="container d-flex justify-content-center align-items-center vh-100">
        <div className="alert alert-warning text-center p-4 shadow">
          <h4 className="mb-3">Bạn chưa đăng nhập</h4>
          <Link to="/auth" className="btn btn-primary">Đăng nhập ngay</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container py-4">
      <div className="profile-cover rounded-4 shadow-sm mb-4"></div>

      <div className="card profile-card shadow border-0 rounded-4">
        <div className="card-body p-4 p-md-5">
          <div className="d-flex flex-column flex-md-row align-items-md-center gap-4">
            <div className="avatar-wrap shadow-sm">
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="avatar" className="avatar-img" />
              ) : (
                <div className="avatar-fallback">{initials || "U"}</div>
              )}
            </div>

            <div className="flex-grow-1">
              <div className="d-flex align-items-center gap-2 flex-wrap">
                <h3 className="mb-0">{user.full_name || user.name || "User"}</h3>
                <span className={`badge ${roleLabel === "Admin" ? "bg-danger-subtle text-danger" : "bg-primary-subtle text-primary"} rounded-pill`}>
                  <i className="bi bi-shield-check me-1"></i>
                  {roleLabel}
                </span>
              </div>
              <div className="text-muted mt-1">
                Thành viên từ: {new Date(user.created_at || Date.now()).toLocaleDateString()}
              </div>
            </div>

            <div className="d-flex gap-2">
              <button className="btn btn-outline-secondary" data-bs-toggle="modal" data-bs-target="#changePwModal">
                <i className="bi bi-key me-1"></i> Đổi mật khẩu
              </button>
            </div>
          </div>

          <div className="row g-3 mt-4">
            <div className="col-md-6">
              <div className="info-item">
                <div className="label"><i className="bi bi-envelope me-2"></i>Email</div>
                <div className="value">{user.email}</div>
              </div>
            </div>
            <div className="col-md-6">
              <div className="info-item">
                <div className="label"><i className="bi bi-telephone me-2"></i>Số điện thoại</div>
                <div className="value">{user.phone || "Chưa cập nhật"}</div>
              </div>
            </div>
          </div>

          <div className="row g-3 mt-3">
            <div className="col-6 col-md-6">
              <div className="stat-tile">
                <div className="stat-num">{user.booking_count ?? 0}</div>
                <div className="stat-label d-flex justify-content-between align-items-center">
                  <span>Lượt đặt tour</span>
                  <Link to="/bookings" className="btn btn-sm btn-outline-primary ms-2">
                    <i className="bi bi-clock-history me-1"></i>Xem
                  </Link>
                </div>
              </div>
            </div>
            <div className="col-6 col-md-6">
              <div className="stat-tile">
                <div className="stat-num">{myComments.length}</div>
                <div className="stat-label d-flex justify-content-between align-items-center">
                  <span>Đánh giá</span>
                  {myComments.length > 0 && (
                    <button
                      className="btn btn-sm btn-outline-primary ms-2"
                      onClick={() => setShowReviews(true)}
                    >
                      Xem
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="mt-4 pt-4 border-top">
            <div className="d-flex flex-wrap gap-2">
              <Link to="/bookings" className="btn btn-primary">
                <i className="bi bi-clock-history me-2"></i>Lịch sử đặt tour
              </Link>
              <Link to="/tours" className="btn btn-outline-primary">
                <i className="bi bi-compass me-2"></i>Khám phá tour
              </Link>
              <button className="btn btn-outline-danger ms-auto" onClick={handleLogout}>
                <i className="bi bi-box-arrow-right me-2"></i>Đăng xuất
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Modal Hiển thị Đánh giá */}
      {showReviews && (
  <>
    <div className="modal d-block" tabIndex="-1">
      <div className="modal-dialog modal-lg modal-dialog-centered">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title"><i className="bi bi-chat-left-text me-2"></i>Đánh giá của bạn</h5>
            <button type="button" className="btn-close" onClick={() => setShowReviews(false)}></button>
          </div>
          <div className="modal-body" style={{ maxHeight: "70vh", overflowY: "auto" }}>
            {myComments.length === 0 ? (
              <div className="text-muted">Bạn chưa đánh giá tour nào.</div>
            ) : (
              <ul className="list-group">
                {myComments.map((c) => (
                  <li key={c.id} className="list-group-item">
                    <div className="fw-bold">{c.tour_title || `Tour #${c.tour_id}`}</div>
                    <div className="text-muted small mb-1">
                      {new Date(c.created_at).toLocaleString()} –
                      <span className="ms-1">
                        {"⭐".repeat(c.rating)}{"☆".repeat(5 - c.rating)}
                      </span>
                    </div>
                    <div className="mb-2">{c.content}</div>
                    <Link to={`/tours/${c.tour_id}`} className="btn btn-sm btn-outline-success">
                      Xem tour
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
    <div className="modal-backdrop fade show"></div>
  </>
)}


      {/* Modal đổi mật khẩu - giữ nguyên */}
      <div className="modal fade" id="changePwModal" tabIndex="-1" aria-hidden="true">
        <div className="modal-dialog modal-dialog-centered">
          <form className="modal-content" onSubmit={onSubmit}>
            <div className="modal-header">
              <h5 className="modal-title"><i className="bi bi-key me-2"></i>Đổi mật khẩu</h5>
              <button type="button" className="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div className="modal-body">
              {alert.text && <div className={`alert alert-${alert.type}`}>{alert.text}</div>}
              {/* Mật khẩu hiện tại */}
              <div className="mb-3 position-relative">
                <label className="form-label">Mật khẩu hiện tại</label>
                <input type={showPw.old ? "text" : "password"} className="form-control pe-5"
                  value={oldPw} onChange={(e) => setOldPw(e.target.value)} required />
                <button type="button" className="btn btn-sm btn-link toggle-eye" onClick={() => setShowPw(s => ({...s, old: !s.old}))}>
                  <i className={`bi ${showPw.old ? "bi-eye-slash" : "bi-eye"}`} />
                </button>
              </div>
              {/* Mật khẩu mới */}
              <div className="mb-3 position-relative">
                <label className="form-label">Mật khẩu mới</label>
                <input type={showPw.nw ? "text" : "password"} className="form-control pe-5"
                  value={newPw} onChange={(e) => setNewPw(e.target.value)} required />
                <button type="button" className="btn btn-sm btn-link toggle-eye" onClick={() => setShowPw(s => ({...s, nw: !s.nw}))}>
                  <i className={`bi ${showPw.nw ? "bi-eye-slash" : "bi-eye"}`} />
                </button>
                <div className="progress mt-2" style={{ height: 6 }}>
                  <div className={`progress-bar ${score <= 2 ? "bg-danger" : score === 3 ? "bg-warning" : "bg-success"}`} style={{ width: `${(score / 5) * 100}%` }} />
                </div>
                <div className="form-text">Độ mạnh: {["Rất yếu", "Yếu", "Trung bình", "Khá", "Mạnh"][Math.max(score - 1, 0)]}</div>
              </div>
              {/* Xác nhận */}
              <div className="mb-2 position-relative">
                <label className="form-label">Xác nhận mật khẩu mới</label>
                <input type={showPw.cf ? "text" : "password"} className="form-control pe-5"
                  value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)} required />
                <button type="button" className="btn btn-sm btn-link toggle-eye" onClick={() => setShowPw(s => ({...s, cf: !s.cf}))}>
                  <i className={`bi ${showPw.cf ? "bi-eye-slash" : "bi-eye"}`} />
                </button>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-light" data-bs-dismiss="modal">Hủy</button>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? "Đang đổi..." : "Xác nhận"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
