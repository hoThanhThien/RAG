// 📁 src/client/components/layout/ClientLayout.jsx
import React from "react";
import Header from "../Header";
import Footer from "../Footer";
import GoToTop from "../GoToTop";
import SupportChat from "../SupportChat";
import { Outlet } from "react-router-dom";

export default function ClientLayout() {
  return (
    <>
      <Header />
      <main style={{ paddingTop: 'var(--header-h)' }}>
        <Outlet />
      </main>
      <Footer />
      <SupportChat /> {/* Thêm bong bóng chat ở cuối */}
      <GoToTop />
    </>
  );
}
