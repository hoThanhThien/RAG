// src/client/routes.jsx
import React from "react";
import { Routes, Route } from "react-router-dom";
import ClientLayout from "./components/layout/ClientLayout";
import Home from "./pages/Home";
import Tours from "./pages/Tours";
import TourDetail from "./pages/TourDetail";
import Booking from "./pages/Booking";
import Payment from "./pages/Payment";
import PaymentSuccess from "./pages/PaymentSuccess";  // <-- THÊM
import PaymentSuccessPage from "./pages/PaymentSuccessPage";  // <-- THÊM PayPal success page
import MoMoCallback from "./pages/MoMoCallback";  // <-- THÊM MoMo callback page
import Contact from "./pages/Contact";
import UserProfile from "./pages/UserProfile";
import BookingHistory from "./pages/BookingHistory";  // <-- THÊM Booking History
import BookingDetail from "./pages/BookingDetail";  // <-- THÊM Booking Detail
import AuthPage from "./pages/Auth";

export default function ClientRoutes() {
  return (
    <Routes>
      <Route path="/" element={<ClientLayout />}>
        <Route index element={<Home />} />
        <Route path="tours" element={<Tours />} />
        <Route path="tours/:id" element={<TourDetail />} />
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
      </Route>
      <Route path="/auth" element={<AuthPage />} />
    </Routes>
  );
}
