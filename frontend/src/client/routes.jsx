// src/client/routes.jsx
import React, { Suspense, lazy } from "react";
import { Routes, Route } from "react-router-dom";
import ClientLayout from "./components/layout/ClientLayout";
import Booking from "./pages/Booking";
import Payment from "./pages/Payment";
import PaymentSuccess from "./pages/PaymentSuccess";  
import PaymentSuccessPage from "./pages/PaymentSuccessPage";  
import MoMoCallback from "./pages/MoMoCallback";  
import Contact from "./pages/Contact";
import UserProfile from "./pages/UserProfile";
import BookingHistory from "./pages/BookingHistory";  
import BookingDetail from "./pages/BookingDetail";  
import AuthPage from "./pages/Auth";

const Home = lazy(() => import("./pages/Home"));
const Tours = lazy(() => import("./pages/Tours"));
const TourDetail = lazy(() => import("./pages/TourDetail"));
const Recommendations = lazy(() => import("./pages/Recommendations"));

const withSuspense = (node) => (
  <Suspense
    fallback={(
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: "35vh" }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    )}
  >
    {node}
  </Suspense>
);


export default function ClientRoutes() {
  return (
    <Routes>
      <Route path="/" element={<ClientLayout />}>
        <Route index element={withSuspense(<Home />)} />
        <Route path="tours" element={withSuspense(<Tours />)} />
        <Route path="tours/:id" element={withSuspense(<TourDetail />)} />
        <Route path="booking/:id" element={<Booking />} />
        <Route path="payment/:bookingId" element={<Payment />} />
        <Route path="payment/:bookingId/success" element={<PaymentSuccess />} /> {/* <-- THÊM */}
        <Route path="payment-success" element={<PaymentSuccessPage />} /> {/* <-- PayPal success route */}
        <Route path="payment/momo/callback" element={<MoMoCallback />} /> {/* <-- MoMo callback route */}
        <Route path="contact" element={<Contact />} />
        <Route path="user" element={<UserProfile />} />
        <Route path="bookings" element={<BookingHistory />} /> {/* <-- Booking History route */}
        <Route path="user/bookings" element={<BookingHistory />} /> {/* <-- Alias route */}
        <Route path="booking-details/:id" element={<BookingDetail />} /> {/* <-- Booking Detail route */}
        <Route path="recommendations" element={withSuspense(<Recommendations />)} />
      </Route>
      <Route path="/auth" element={<AuthPage />} />
    </Routes>









  );
}