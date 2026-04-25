import React, { Suspense, lazy } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";

const ClientApp = lazy(() => import("./client/ClientApp"));
const AdminApp = lazy(() => import("./admin/AdminApp"));

function AppFallback() {
  return (
    <div className="d-flex justify-content-center align-items-center" style={{ minHeight: "100vh" }}>
      <div className="text-center text-muted">
        <div className="spinner-border text-primary mb-3" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <div>Đang tải ứng dụng...</div>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Suspense fallback={<AppFallback />}>
        <Routes>
          <Route path="/admin/*" element={<AdminApp />} />
          <Route path="/*" element={<ClientApp />} />
        </Routes>
      </Suspense>

    </Router>
  );
}

export default App;