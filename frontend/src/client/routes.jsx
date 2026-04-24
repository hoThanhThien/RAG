// src/client/routes.jsx
import React from "react";
import { Routes, Route } from "react-router-dom";
import ClientLayout from "./components/layout/ClientLayout";
import Home from "./pages/Home";
import Tours from "./pages/Tours";
import TourDetail from "./pages/TourDetail";
import Booking from "./pages/Booking";
import Payment from "./pages/Payment";
import PaymentSuccess from "./pages/PaymentSuccess";  
import PaymentSuccessPage from "./pages/PaymentSuccessPage";  
import MoMoCallback from "./pages/MoMoCallback";  
import Contact from "./pages/Contact";
import UserProfile from "./pages/UserProfile";
import BookingHistory from "./pages/BookingHistory";  
import BookingDetail from "./pages/BookingDetail";  
import Recommendations from "./pages/Recommendations";
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
        <Route path="recommendations" element={<Recommendations />} />
      </Route>
      <Route path="/auth" element={<AuthPage />} />
    </Routes>









  );
}