import React from "react";
import AdminRoutes from "./routes";
import { AuthProvider } from "../client/context/AuthContext"; // ✅ import đúng path

export default function AdminApp() {
  return (
    <AuthProvider>
      <AdminRoutes />
    </AuthProvider>
  );
}
