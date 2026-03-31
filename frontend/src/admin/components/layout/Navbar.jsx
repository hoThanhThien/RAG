import React from "react";
import "./Navbar.css";
import { useAuth } from "../../../client/context/AuthContext";
import { useNavigate } from "react-router-dom";

const Navbar = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <div className="admin-navbar shadow-sm">
      <div className="admin-navbar__left">
        <h2 className="mb-0">
  <i className="bi bi-layout-text-sidebar me-2"></i> Admin Panel
</h2>
      </div>
      <div className="admin-navbar__right">
        <span className="admin-navbar__user">
  <i className="bi bi-person-circle me-1"></i> Xin chào, Admin
</span>
        <button className="admin-navbar__logout" onClick={handleLogout}>
  <i className="bi bi-box-arrow-right me-1"></i> Đăng xuất
</button>
      </div>
    </div>
  );
};

export default Navbar;
