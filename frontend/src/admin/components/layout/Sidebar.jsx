import React from "react";
import { Link, useLocation } from "react-router-dom";
import "./Sidebar.css";

const Sidebar = () => {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <aside className="sidebar shadow">
      <div className="sidebar-header">
        <h2 className="fw-bold mb-0 text-white">🎛️ Admin</h2>
      </div>
      <nav className="sidebar-nav">
        <ul>
          <li className={isActive("/admin") ? "active" : ""}>
            <Link to="/admin"><i className="bi bi-speedometer2 me-2" /> Dashboard</Link>
          </li>
          <li className={isActive("/admin/users") ? "active" : ""}>
            <Link to="/admin/users"><i className="bi bi-people-fill me-2" /> Người dùng</Link>
          </li>
          <li className={isActive("/admin/tours") ? "active" : ""}>
            <Link to="/admin/tours"><i className="bi bi-globe2 me-2" /> Tours</Link>
          </li>
          <li className={isActive("/admin/bookings") ? "active" : ""}>
            <Link to="/admin/bookings"><i className="bi bi-journal-check me-2" /> Đặt tours</Link>
          </li>
          <li className={isActive("/admin/categories") ? "active" : ""}>
            <Link to="/admin/categories"><i className="bi bi-tags-fill me-2" /> Danh mục</Link>
          </li>
          <li className={isActive("/admin/discounts") ? "active" : ""}>
            <Link to="/admin/discounts"><i className="bi bi-percent me-2" /> Giảm giá</Link>
          </li>
          <li className={isActive("/admin/support") ? "active" : ""}>
            <Link to="/admin/support"><i className="bi bi-chat-dots-fill me-2" /> Hỗ trợ</Link>
          </li>
          <li className={isActive("/admin/comments") ? "active" : ""}>
            <Link to="/admin/comments"><i className="bi bi-chat-left-text-fill me-2" /> Đánh giá</Link>
          </li>
          
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;
