import React from "react";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import { Outlet } from "react-router-dom";
import "./adminLayout.css";

class AdminErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Admin page render error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="alert alert-danger m-4">
          <h5 className="mb-2">Không thể hiển thị trang quản trị</h5>
          <p className="mb-3">Dữ liệu vừa tải có vấn đề. Vui lòng tải lại trang.</p>
          <button className="btn btn-primary" onClick={() => window.location.reload()}>
            Tải lại
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

const AdminLayout = () => {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />
      <div style={{ marginLeft: "220px", width: "100%" }}>
        <Navbar />
        <div style={{ padding: "20px" }}>
          <AdminErrorBoundary>
            <Outlet />
          </AdminErrorBoundary>
        </div>
      </div>
    </div>
  );
};

export default AdminLayout;
