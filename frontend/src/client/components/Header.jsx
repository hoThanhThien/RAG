import React, { useState, useEffect, useRef, useCallback } from "react";
import { NavLink, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Header() {
  const [navActive, setNavActive] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // set header height (optimized)
  useEffect(() => {
    const header = document.querySelector(".header");

    if (!header) return;

    const updateVar = () => {
      document.documentElement.style.setProperty(
        "--header-h",
        `${header.offsetHeight}px`
      );
    };

    updateVar();

    const ro = new ResizeObserver(updateVar);
    ro.observe(header);

    return () => ro.disconnect();
  }, []);

  // click outside dropdown
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (!dropdownRef.current?.contains(e.target)) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () =>
      document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = useCallback(() => {
    logout();
    navigate("/");
  }, [logout, navigate]);

  const navClass = ({ isActive }) =>
    `nav-link text-dark fw-semibold px-0 py-2 ${
      isActive ? "active" : ""
    }`;

  return (
    <header
      className="header position-fixed w-100"
      style={{
        top: 0,
        zIndex: 1050,
        background: "rgba(255,255,255,0.98)",
        backdropFilter: "blur(15px)",
        borderBottom: "1px solid rgba(0,0,0,0.1)",
      }}
    >
      <div className="container">
        <div
          className="d-flex justify-content-between align-items-center"
          style={{ height: 80 }}
        >
          {/* Logo */}
          <Link to="/" className="text-decoration-none">
            <h1 className="fw-bold text-primary mb-0">Tourest</h1>
          </Link>

          {/* Mobile toggle */}
          <button
            className="btn d-lg-none"
            onClick={() => setNavActive((prev) => !prev)}
          >
            <i className={`bi ${navActive ? "bi-x" : "bi-list"}`} />
          </button>

          {/* Nav */}
          <nav
            className={`${navActive ? "d-flex" : "d-none"} d-lg-flex`}
            style={{ gap: 16 }}
          >
            <ul className="d-flex flex-column flex-lg-row gap-3 list-unstyled mb-0 align-items-center">
              <li><NavLink to="/" className={navClass}>Home</NavLink></li>
              <li><NavLink to="/?scroll=about" className={navClass}>About</NavLink></li>
              <li><NavLink to="/?scroll=tours" className={navClass}>Tours</NavLink></li>
              <li><NavLink to="/?scroll=destinations" className={navClass}>Destinations</NavLink></li>
              <li><NavLink to="/?scroll=blog" className={navClass}>Blog</NavLink></li>

              <li>
                <Link to="/contact" className="nav-link text-dark fw-semibold">
                  Contact
                </Link>
              </li>

              <li>
                <NavLink
                  to="/tours"
                  className="btn btn-primary rounded-pill px-3"
                >
                  Booking Now
                </NavLink>
              </li>

              {/* User */}
              {user ? (
                <li ref={dropdownRef} className="position-relative">
                  <div
                    className="d-flex align-items-center gap-2"
                    style={{ cursor: "pointer" }}
                    onClick={() => setDropdownOpen((prev) => !prev)}
                  >
                    <img
                      src={`https://ui-avatars.com/api/?name=${encodeURIComponent(
                        user.full_name || "User"
                      )}`}
                      alt="avatar"
                      width={32}
                      height={32}
                      loading="lazy"
                      className="rounded-circle"
                    />
                    <span className="fw-semibold small">
                      {user.full_name?.split(" ")[0]}
                    </span>
                  </div>

                  {dropdownOpen && (
                    <div
                      className="position-absolute bg-white shadow rounded"
                      style={{ right: 0, top: "110%", minWidth: 150 }}
                    >
                      <Link to="/user" className="dropdown-item">
                        Hồ sơ
                      </Link>
                      <button
                        className="dropdown-item text-danger"
                        onClick={handleLogout}
                      >
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

export default React.memo(Header);