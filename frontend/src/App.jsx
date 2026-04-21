import React, { lazy, Suspense } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

const ClientApp = lazy(() => import("./client/ClientApp"));
const AdminApp = lazy(() => import("./admin/AdminApp"));

function App() {
  return (
    <Router>
      <Suspense fallback={<div>Loading...</div>}>
        <Routes>
          <Route path="/admin/*" element={<AdminApp />} />
          <Route path="/*" element={<ClientApp />} />
        </Routes>
      </Suspense>
    </Router>
  );
}

export default App;