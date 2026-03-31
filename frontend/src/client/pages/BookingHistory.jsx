import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import "../../styles/BookingHistory.css";

export default function BookingHistory() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all"); // all, pending, paid, cancelled

  useEffect(() => {
    if (!user) {
      navigate("/auth");
      return;
    }
    fetchBookings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const fetchBookings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get("/bookings/my-bookings");
      setBookings(response.data || []);
    } catch (err) {
      console.error("Error fetching bookings:", err);
      setError("Không thể tải lịch sử đặt tour. Vui lòng thử lại sau.");
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      Pending: { label: "Chờ thanh toán", class: "bg-warning text-dark" },
      Paid: { label: "Đã thanh toán", class: "bg-success" },
      Cancelled: { label: "Đã hủy", class: "bg-danger" },
      Confirmed: { label: "Đã xác nhận", class: "bg-primary" },
    };
    const info = statusMap[status] || { label: status, class: "bg-secondary" };
    return <span className={`badge ${info.class}`}>{info.label}</span>;
  };

  const filteredBookings = bookings.filter((booking) => {
    if (filter === "all") return true;
    if (filter === "pending") return booking.Status === "Pending";
    if (filter === "paid") return booking.Status === "Paid" || booking.Status === "Confirmed";
    if (filter === "cancelled") return booking.Status === "Cancelled";
    return true;
  });

  if (!user) {
    return (
      <div className="container py-5">
        <div className="alert alert-warning text-center">
          <h4>Bạn cần đăng nhập để xem lịch sử đặt tour</h4>
          <Link to="/auth" className="btn btn-primary mt-3">Đăng nhập ngay</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="booking-history-page">
      <div className="container py-5">
        {/* Header */}
        <div className="mb-4">
          <h1 className="fw-bold mb-2">
            <i className="bi bi-clock-history me-2"></i>
            Lịch sử đặt tour
          </h1>
          <p className="text-muted">Quản lý và theo dõi các tour bạn đã đặt</p>
        </div>

        {/* Filter Tabs */}
        <div className="card shadow-sm mb-4">
          <div className="card-body">
            <div className="btn-group w-100" role="group">
              <button
                type="button"
                className={`btn ${filter === "all" ? "btn-primary" : "btn-outline-primary"}`}
                onClick={() => setFilter("all")}
              >
                <i className="bi bi-list-ul me-1"></i>
                Tất cả ({bookings.length})
              </button>
              <button
                type="button"
                className={`btn ${filter === "pending" ? "btn-warning" : "btn-outline-warning"}`}
                onClick={() => setFilter("pending")}
              >
                <i className="bi bi-hourglass-split me-1"></i>
                Chờ thanh toán ({bookings.filter((b) => b.Status === "Pending").length})
              </button>
              <button
                type="button"
                className={`btn ${filter === "paid" ? "btn-success" : "btn-outline-success"}`}
                onClick={() => setFilter("paid")}
              >
                <i className="bi bi-check-circle me-1"></i>
                Đã thanh toán ({bookings.filter((b) => b.Status === "Paid" || b.Status === "Confirmed").length})
              </button>
              <button
                type="button"
                className={`btn ${filter === "cancelled" ? "btn-danger" : "btn-outline-danger"}`}
                onClick={() => setFilter("cancelled")}
              >
                <i className="bi bi-x-circle me-1"></i>
                Đã hủy ({bookings.filter((b) => b.Status === "Cancelled").length})
              </button>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-5">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Đang tải...</span>
            </div>
            <p className="mt-3 text-muted">Đang tải lịch sử đặt tour...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="alert alert-danger" role="alert">
            <i className="bi bi-exclamation-triangle me-2"></i>
            {error}
            <button className="btn btn-sm btn-outline-danger ms-3" onClick={fetchBookings}>
              <i className="bi bi-arrow-clockwise me-1"></i>Thử lại
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && filteredBookings.length === 0 && (
          <div className="card shadow-sm text-center py-5">
            <div className="card-body">
              <i className="bi bi-inbox display-1 text-muted mb-3"></i>
              <h3 className="text-muted">Chưa có booking nào</h3>
              <p className="text-muted mb-4">
                {filter === "all"
                  ? "Bạn chưa đặt tour nào. Hãy khám phá các tour hấp dẫn của chúng tôi!"
                  : `Không có booking nào ở trạng thái "${filter === "pending" ? "Chờ thanh toán" : filter === "paid" ? "Đã thanh toán" : "Đã hủy"}"`}
              </p>
              <Link to="/tours" className="btn btn-primary">
                <i className="bi bi-compass me-2"></i>Khám phá tour
              </Link>
            </div>
          </div>
        )}

        {/* Booking List */}
        {!loading && !error && filteredBookings.length > 0 && (
          <div className="row g-4">
            {filteredBookings.map((booking) => (
              <div key={booking.BookingID} className="col-12">
                <div className="card booking-card shadow-sm h-100">
                  <div className="card-body">
                    <div className="row">
                      {/* Tour Image */}
                      <div className="col-md-3">
                        {booking.TourImage ? (
                          <img
                            src={booking.TourImage}
                            alt={booking.TourTitle}
                            className="img-fluid rounded"
                            style={{ objectFit: "cover", height: "150px", width: "100%" }}
                          />
                        ) : (
                          <div
                            className="bg-secondary rounded d-flex align-items-center justify-content-center text-white"
                            style={{ height: "150px" }}
                          >
                            <i className="bi bi-image fs-1"></i>
                          </div>
                        )}
                      </div>

                      {/* Booking Info */}
                      <div className="col-md-6">
                        <div className="d-flex justify-content-between align-items-start mb-2">
                          <h5 className="card-title mb-1 fw-bold">{booking.TourTitle}</h5>
                          {getStatusBadge(booking.Status)}
                        </div>
                        
                        <div className="text-muted small mb-2">
                          <i className="bi bi-receipt me-1"></i>
                          Mã đơn: <span className="fw-bold">{booking.OrderCode}</span>
                        </div>

                        <div className="booking-details">
                          <div className="mb-2">
                            <i className="bi bi-calendar-check text-primary me-2"></i>
                            <span className="fw-semibold">Ngày đặt:</span> {new Date(booking.CreatedAt).toLocaleString("vi-VN")}
                          </div>
                          <div className="mb-2">
                            <i className="bi bi-calendar-event text-success me-2"></i>
                            <span className="fw-semibold">Ngày khởi hành:</span> {new Date(booking.DepartureDate).toLocaleDateString("vi-VN")}
                          </div>
                          <div className="mb-2">
                            <i className="bi bi-people text-info me-2"></i>
                            <span className="fw-semibold">Số người:</span> {booking.NumberOfGuests} người
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="col-md-3 d-flex flex-column justify-content-between">
                        <div>
                          <div className="text-end mb-3">
                            <div className="text-muted small">Tổng tiền</div>
                            <div className="fs-4 fw-bold text-primary">
                              {booking.TotalAmount?.toLocaleString("vi-VN")}đ
                            </div>
                          </div>
                        </div>

                        <div className="d-flex flex-column gap-2">
                          <Link
                            to={`/tours/${booking.TourID}`}
                            className="btn btn-outline-primary btn-sm"
                          >
                            <i className="bi bi-eye me-1"></i>Xem tour
                          </Link>
                          
                          {booking.Status === "Pending" && (
                            <Link
                              to={`/payment/${booking.BookingID}`}
                              className="btn btn-warning btn-sm"
                            >
                              <i className="bi bi-credit-card me-1"></i>Thanh toán
                            </Link>
                          )}

                          {(booking.Status === "Paid" || booking.Status === "Confirmed") && (
                            <button className="btn btn-success btn-sm" disabled>
                              <i className="bi bi-check-circle me-1"></i>Đã thanh toán
                            </button>
                          )}

                          {booking.Status === "Cancelled" && (
                            <button className="btn btn-secondary btn-sm" disabled>
                              <i className="bi bi-x-circle me-1"></i>Đã hủy
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Back to Profile */}
        <div className="text-center mt-5">
          <Link to="/user" className="btn btn-outline-secondary">
            <i className="bi bi-arrow-left me-2"></i>Quay lại trang cá nhân
          </Link>
        </div>
      </div>
    </div>
  );
}
