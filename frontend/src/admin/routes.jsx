import React from "react";
import { Routes, Route } from "react-router-dom";
import AdminLayout from "./components/layout/AdminLayout";

import Home from "./views/Home";
import UserList from "./views/UserList";
import TourList from "./views/TourList";
import BookingList from "./views/BookingList";
import GuideList from "./views/GuideList";
import CategoryList from "./views/CategoryList";
import DiscountList from "./views/DiscountList";
import PaymentList from "./views/PaymentList";
import PhotoList from "./views/PhotoList";
import RoleList from "./views/RoleList";
import TourGuideList from "./views/TourGuideList";
import TourScheduleList from "./views/TourScheduleList";
import ProtectedRoute from "./components/ProtectedRoute";
import SupportList from "./views/SupportList";
import SupportChat from "./views/SupportChat";
import CommentList from "./views/CommentList";


const AdminRoutes = () => {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <ProtectedRoute allowedRoles={[1]}>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Home />} />
        <Route path="users" element={<UserList />} />
        <Route path="tours" element={<TourList />} />
        <Route path="bookings" element={<BookingList />} />
        <Route path="guides" element={<GuideList />} />
        <Route path="categories" element={<CategoryList />} />
        <Route path="discounts" element={<DiscountList />} />
        <Route path="payments" element={<PaymentList />} />
        <Route path="photos" element={<PhotoList />} />
        <Route path="roles" element={<RoleList />} />
        <Route path="tour-guides" element={<TourGuideList />} />
        <Route path="tour-schedules" element={<TourScheduleList />} />
        <Route path="support" element={<SupportList />} />
        <Route path="support/:thread_id" element={<SupportChat />} />
        <Route path="comments" element={<CommentList />} />

        
      </Route>
    </Routes>
  );
};

export default AdminRoutes;
