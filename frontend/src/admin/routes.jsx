import React, { Suspense, lazy } from "react";
import { Routes, Route } from "react-router-dom";
import AdminLayout from "./components/layout/AdminLayout";
import ProtectedRoute from "./components/ProtectedRoute";

const Home = lazy(() => import("./views/Home"));
const UserList = lazy(() => import("./views/UserList"));
const TourList = lazy(() => import("./views/TourList"));
const BookingList = lazy(() => import("./views/BookingList"));
const GuideList = lazy(() => import("./views/GuideList"));
const CategoryList = lazy(() => import("./views/CategoryList"));
const DiscountList = lazy(() => import("./views/DiscountList"));
const PaymentList = lazy(() => import("./views/PaymentList"));
const PhotoList = lazy(() => import("./views/PhotoList"));
const RoleList = lazy(() => import("./views/RoleList"));
const TourGuideList = lazy(() => import("./views/TourGuideList"));
const TourScheduleList = lazy(() => import("./views/TourScheduleList"));
const SupportList = lazy(() => import("./views/SupportList"));
const SupportChat = lazy(() => import("./views/SupportChat"));
const CommentList = lazy(() => import("./views/CommentList"));
const ClusteringView = lazy(() => import("./views/ClusteringView"));

const withSuspense = (node) => (
  <Suspense
    fallback={(
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: "40vh" }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    )}
  >
    {node}
  </Suspense>
);


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
        <Route index element={withSuspense(<Home />)} />
        <Route path="clustering" element={withSuspense(<ClusteringView />)} />
        <Route path="users" element={withSuspense(<UserList />)} />
        <Route path="tours" element={withSuspense(<TourList />)} />
        <Route path="bookings" element={withSuspense(<BookingList />)} />
        <Route path="guides" element={withSuspense(<GuideList />)} />
        <Route path="categories" element={withSuspense(<CategoryList />)} />
        <Route path="discounts" element={withSuspense(<DiscountList />)} />
        <Route path="payments" element={withSuspense(<PaymentList />)} />
        <Route path="photos" element={withSuspense(<PhotoList />)} />
        <Route path="roles" element={withSuspense(<RoleList />)} />
        <Route path="tour-guides" element={withSuspense(<TourGuideList />)} />
        <Route path="tour-schedules" element={withSuspense(<TourScheduleList />)} />
        <Route path="support" element={withSuspense(<SupportList />)} />
        <Route path="support/:thread_id" element={withSuspense(<SupportChat />)} />
        <Route path="comments" element={withSuspense(<CommentList />)} />

        
      </Route>
    </Routes>
  );
};

export default AdminRoutes;
