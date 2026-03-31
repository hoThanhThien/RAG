import React, { useState, useEffect, useRef } from "react";
import { NavLink, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Header() {
  const [navActive, setNavActive] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const header = document.querySelector('.header');
    const updateVar = () => {
      if (header) {
        document.documentElement.style.setProperty('--header-h', `${header.offsetHeight}px`);
      }
    };
    updateVar();
    const ro = new ResizeObserver(updateVar);
    if (header) ro.observe(header);
    window.addEventListener('resize', updateVar);
    return () => {
      ro.disconnect();
      window.removeEventListener('resize', updateVar);
    };
  }, []);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const navClass = ({ isActive }) =>
    "nav-link text-dark fw-semibold px-0 py-2" + (isActive ? " active" : "");

  return (
    <header
      className="header position-fixed w-100"
      style={{
        top: 0,
        zIndex: 1050,
        background: "rgba(255,255,255,0.98)",
        backdropFilter: "blur(15px)",
        borderBottom: "1px solid rgba(0,0,0,0.1)",
        minHeight: "80px",
      }}
    >
      <div className="container">
        <div className="d-flex justify-content-between align-items-center" style={{ height: 80 }}>
          {/* Logo */}
          <div className="d-flex flex-column justify-content-center">
            <Link to="/" className="text-decoration-none" onClick={() => setNavActive(false)}>
              <h1 className="logo fw-bold text-primary fs-2 mb-0">Tourest</h1>
            </Link>
            <p className="tagline text-muted mb-0" style={{ fontSize: "0.65rem" }}>
              Công ty chuyên cung cấp dịch vụ du lịch chất lượng trọn gói
            </p>
          </div>

          {/* Mobile nav toggle */}
          <button
            className="btn d-lg-none border-0 bg-transparent p-2"
            onClick={() => setNavActive(!navActive)}
          >
            <i className={`bi ${navActive ? "bi-x" : "bi-list"}`}></i>
          </button>

          {/* Nav items */}
          <nav className={`${navActive ? "d-flex" : "d-none"} d-lg-flex align-items-center`} style={{ gap: 16 }}>
            <ul className="d-flex flex-column flex-lg-row align-items-center gap-3 list-unstyled mb-0">
              <li><NavLink to="/" className={navClass}>Home</NavLink></li>
              <li><NavLink to="/?scroll=about" className="nav-link text-dark fw-semibold px-0 py-2">About Us</NavLink></li>
              <li><NavLink to="/?scroll=tours" className="nav-link text-dark fw-semibold px-0 py-2">TOUR NỔI BẬT</NavLink></li>
              <li><NavLink to="/?scroll=destinations" className="nav-link text-dark fw-semibold px-0 py-2">ĐIỂM ĐẾN</NavLink></li>
              <li><NavLink to="/?scroll=blog" className="nav-link text-dark fw-semibold px-0 py-2">Blog</NavLink></li>
              <li><a href="/contact" className="nav-link text-dark fw-semibold px-0 py-2">Contact Us</a></li>
              <li>
                <NavLink to="/tours" className="btn btn-primary rounded-pill fw-semibold px-3 py-2">
                  Booking Now
                </NavLink>
              </li>

              {/* Avatar + dropdown */}
              {user ? (
                <li className="position-relative" ref={dropdownRef}>
                  <div
                    className="d-flex align-items-center gap-2"
                    style={{ cursor: "pointer" }}
                    onClick={() => setDropdownOpen(!dropdownOpen)}
                  >
                    <img
                      src={`https://ui-avatars.com/api/?name=${encodeURIComponent(user.full_name || "User")}&background=random`}
                      alt="Avatar"
                      width="32"
                      height="32"
                      className="rounded-circle"
                    />
                    <span className="text-dark fw-semibold small">
                        Hi, {user.full_name?.split(" ")[0] || "Guest"}
                    </span>


                  </div>

                  {dropdownOpen && (
                    <div
                      className="position-absolute bg-white shadow-sm rounded"
                      style={{ right: 0, top: "110%", minWidth: "150px", zIndex: 2000 }}
                    >
                      <Link to="/user" className="dropdown-item px-3 py-2 text-dark text-decoration-none d-block">
                        Hồ sơ cá nhân
                      </Link>
                      <button className="dropdown-item px-3 py-2 text-danger bg-white border-0 w-100 text-start" onClick={handleLogout}>
                        Đăng xuất
                      </button>
                    </div>
                  )}
                </li>
              ) : (
                <>
                  <li><Link to="/auth" className="btn btn-outline-primary btn-sm">Login</Link></li>
                  <li><Link to="/auth" className="btn btn-primary btn-sm">Register</Link></li>
                </>
              )}
            </ul>
          </nav>
        </div>
      </div>
    </header>
  );
}
