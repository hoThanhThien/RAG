// src/App.jsx
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import ClientApp from "./client/ClientApp";
import AdminApp from "./admin/AdminApp";
import "bootstrap/dist/css/bootstrap.min.css";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/admin/*" element={<AdminApp />} />
        <Route path="/*" element={<ClientApp />} />
      </Routes>
    </Router>
  );
}

export default App;
