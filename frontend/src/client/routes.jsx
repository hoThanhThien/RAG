import React, { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import ClientLayout from "./components/layout/ClientLayout";

const Home = lazy(() => import("./pages/Home"));
const Tours = lazy(() => import("./pages/Tours"));
const TourDetail = lazy(() => import("./pages/TourDetail"));
const Booking = lazy(() => import("./pages/Booking"));
const Payment = lazy(() => import("./pages/Payment"));
const PaymentSuccess = lazy(() => import("./pages/PaymentSuccess"));
const PaymentSuccessPage = lazy(() => import("./pages/PaymentSuccessPage"));
const MoMoCallback = lazy(() => import("./pages/MoMoCallback"));
const Contact = lazy(() => import("./pages/Contact"));
const UserProfile = lazy(() => import("./pages/UserProfile"));
const BookingHistory = lazy(() => import("./pages/BookingHistory"));
const BookingDetail = lazy(() => import("./pages/BookingDetail"));
const Recommendations = lazy(() => import("./pages/Recommendations"));
const AuthPage = lazy(() => import("./pages/Auth"));

export default function ClientRoutes() {
  return (
    <Suspense
      fallback={
        <div className="text-center py-5">
          <div className="spinner-border text-primary" />
        </div>
      }
    >
      <Routes>
        <Route path="/" element={<ClientLayout />}>
          <Route index element={<Home />} />
          <Route path="tours" element={<Tours />} />
          <Route path="tours/:id" element={<TourDetail />} />
          <Route path="booking/:id" element={<Booking />} />
          <Route path="payment/:bookingId" element={<Payment />} />
          <Route path="payment/:bookingId/success" element={<PaymentSuccess />} />
          <Route path="payment-success" element={<PaymentSuccessPage />} />
          <Route path="payment/momo/callback" element={<MoMoCallback />} />
          <Route path="contact" element={<Contact />} />
          <Route path="user" element={<UserProfile />} />
          <Route path="bookings" element={<BookingHistory />} />
          <Route path="user/bookings" element={<BookingHistory />} />
          <Route path="booking-details/:id" element={<BookingDetail />} />
          <Route path="recommendations" element={<Recommendations />} />
        </Route>

        <Route path="/auth" element={<AuthPage />} />
      </Routes>
    </Suspense>
  );
}