// src/client/ClientApp.jsx
import React from "react";
import ClientRoutes from "./routes";
import { AuthProvider } from "./context/AuthContext";

function ClientApp() {
  return (
    <AuthProvider>
      <ClientRoutes />
    </AuthProvider>
  );
}

export default ClientApp;
