import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../services/api';
import '../../styles/BookingDetail.css';

const BookingDetail = () => {
    const { id } = useParams();
    const [booking, setBooking] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchBookingDetail = async () => {
            try {
                setLoading(true);
                setError(null);
                console.log('Fetching booking detail for ID:', id);
                const response = await api.get(`/bookings/${id}`);
                console.log('Booking detail response:', response.data);
                setBooking(response.data);
            } catch (err) {
                console.error('Error fetching booking detail:', err);
                console.error('Error response:', err.response);
                setError(err.response?.data?.detail || 'Không thể tải thông tin đặt tour. Vui lòng thử lại sau.');
            } finally {
                setLoading(false);
            }
        };

        if (id) {
            fetchBookingDetail();
        }
    }, [id]);

    const getStatusBadge = (status) => {
        const statusConfig = {
            'Pending': { class: 'warning', text: 'Chờ thanh toán', icon: 'bi-clock-history' },
            'Confirmed': { class: 'success', text: 'Đã thanh toán', icon: 'bi-check-circle-fill' },
            'Paid': { class: 'success', text: 'Đã thanh toán', icon: 'bi-check-circle-fill' },
            'Cancelled': { class: 'danger', text: 'Đã hủy', icon: 'bi-x-circle-fill' }
        };
        const config = statusConfig[status] || statusConfig['Pending'];
        return (
            <span className={`badge bg-${config.class} status-badge`}>
                <i className={`bi ${config.icon} me-1`}></i>
                {config.text}
            </span>
        );
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(amount);
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('vi-VN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    if (loading) {
        return (
            <div className="container py-5">
                <div className="text-center">
                    <div className="spinner-border text-primary" role="status">
                        <span className="visually-hidden">Loading...</span>
                    </div>
                    <p className="mt-3">Đang tải thông tin...</p>
                </div>
            </div>
        );
    }

    if (error || !booking) {
        return (
            <div className="container py-5">
                <div className="alert alert-danger">
                    <i className="bi bi-exclamation-triangle me-2"></i>
                    {error || 'Không tìm thấy thông tin đặt tour'}
                </div>
                <Link to="/bookings" className="btn btn-primary">
                    <i className="bi bi-arrow-left me-2"></i>
                    Quay lại danh sách
                </Link>
            </div>
        );
    }

    return (
        <div className="booking-detail-page">
            <div className="container py-4">
                {/* Header */}
                <div className="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h2 className="mb-2">Chi tiết đặt tour</h2>
                        <p className="text-muted mb-0">
                            Mã đặt tour: <strong>#{booking.BookingID}</strong>
                        </p>
                    </div>
                    <div>
                        {getStatusBadge(booking.Status)}
                    </div>
                </div>

                <div className="row">
                    {/* Thông tin tour */}
                    <div className="col-lg-8">
                        <div className="card mb-4">
                            <div className="card-header bg-primary text-white">
                                <h5 className="mb-0">
                                    <i className="bi bi-map me-2"></i>
                                    Thông tin tour
                                </h5>
                            </div>
                            <div className="card-body">
                                <div className="row">
                                    <div className="col-md-4 mb-3">
                                        {booking.TourImage ? (
                                            <img 
                                                src={booking.TourImage.startsWith('http') 
                                                    ? booking.TourImage 
                                                    : booking.TourImage.startsWith('/uploads/')
                                                    ? `http://localhost:8000${booking.TourImage}`
                                                    : `http://localhost:8000/uploads/${booking.TourImage}`
                                                }
                                                alt={booking.TourName}
                                                className="img-fluid rounded"
                                                onError={(e) => {
                                                    console.error('Image load error:', e.target.src);
                                                    e.target.src = 'https://via.placeholder.com/300x200?text=No+Image';
                                                }}
                                            />
                                        ) : (
                                            <img 
                                                src="https://via.placeholder.com/300x200?text=No+Image"
                                                alt="No tour image"
                                                className="img-fluid rounded"
                                            />
                                        )}
                                    </div>
                                    <div className="col-md-8">
                                        <h4 className="mb-3">{booking.TourName}</h4>
                                        <div className="tour-info">
                                            <p className="mb-2">
                                                <i className="bi bi-calendar-check text-primary me-2"></i>
                                                <strong>Ngày khởi hành:</strong> {formatDate(booking.DepartureDate)}
                                            </p>
                                            <p className="mb-2">
                                                <i className="bi bi-clock text-primary me-2"></i>
                                                <strong>Thời gian:</strong> {booking.Duration}
                                            </p>
                                            <p className="mb-2">
                                                <i className="bi bi-people text-primary me-2"></i>
                                                <strong>Số người:</strong> {booking.NumberOfPeople} người
                                            </p>
                                            <p className="mb-2">
                                                <i className="bi bi-geo-alt text-primary me-2"></i>
                                                <strong>Điểm xuất phát:</strong> {booking.DepartureLocation || 'Chưa cập nhật'}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Thông tin khách hàng */}
                        <div className="card mb-4">
                            <div className="card-header bg-info text-white">
                                <h5 className="mb-0">
                                    <i className="bi bi-person me-2"></i>
                                    Thông tin khách hàng
                                </h5>
                            </div>
                            <div className="card-body">
                                <div className="row">
                                    <div className="col-md-6 mb-3">
                                        <label className="text-muted small">Họ và tên</label>
                                        <p className="mb-0 fw-bold">{booking.FullName}</p>
                                    </div>
                                    <div className="col-md-6 mb-3">
                                        <label className="text-muted small">Email</label>
                                        <p className="mb-0">{booking.Email}</p>
                                    </div>
                                    <div className="col-md-6 mb-3">
                                        <label className="text-muted small">Số điện thoại</label>
                                        <p className="mb-0">{booking.Phone}</p>
                                    </div>
                                    <div className="col-md-6 mb-3">
                                        <label className="text-muted small">Ngày đặt</label>
                                        <p className="mb-0">{formatDate(booking.BookingDate)}</p>
                                    </div>
                                </div>
                                {booking.SpecialRequests && (
                                    <div className="mt-3">
                                        <label className="text-muted small">Yêu cầu đặc biệt</label>
                                        <p className="mb-0 border-start border-primary border-3 ps-3">
                                            {booking.SpecialRequests}
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Thông tin thanh toán */}
                    <div className="col-lg-4">
                        <div className="card mb-4 sticky-top" style={{ top: '20px' }}>
                            <div className="card-header bg-success text-white">
                                <h5 className="mb-0">
                                    <i className="bi bi-credit-card me-2"></i>
                                    Thanh toán
                                </h5>
                            </div>
                            <div className="card-body">
                                <div className="d-flex justify-content-between mb-2">
                                    <span>Giá tour:</span>
                                    <span className="fw-bold">{formatCurrency(booking.TotalAmount)}</span>
                                </div>
                                <hr />
                                <div className="d-flex justify-content-between mb-3">
                                    <span className="fw-bold">Tổng cộng:</span>
                                    <span className="fw-bold text-danger fs-5">{formatCurrency(booking.TotalAmount)}</span>
                                </div>
                                
                                <div className="payment-status">
                                    <p className="mb-2">
                                        <strong>Trạng thái:</strong>
                                    </p>
                                    {getStatusBadge(booking.Status)}
                                </div>

                                {booking.Status === 'Pending' && (
                                    <div className="mt-3">
                                        <Link 
                                            to={`/payment/${booking.BookingID}`}
                                            className="btn btn-primary w-100"
                                        >
                                            <i className="bi bi-credit-card me-2"></i>
                                            Thanh toán ngay
                                        </Link>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Hỗ trợ */}
                        <div className="card">
                            <div className="card-body text-center">
                                <i className="bi bi-headset text-primary" style={{ fontSize: '2rem' }}></i>
                                <h6 className="mt-3">Cần hỗ trợ?</h6>
                                <p className="small text-muted mb-3">
                                    Liên hệ với chúng tôi nếu bạn cần trợ giúp
                                </p>
                                <Link to="/contact" className="btn btn-outline-primary btn-sm">
                                    <i className="bi bi-telephone me-2"></i>
                                    Liên hệ hỗ trợ
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="mt-4 text-center">
                    <Link to="/bookings" className="btn btn-secondary me-2">
                        <i className="bi bi-arrow-left me-2"></i>
                        Quay lại danh sách
                    </Link>
                    <Link to="/" className="btn btn-outline-primary">
                        <i className="bi bi-house me-2"></i>
                        Về trang chủ
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default BookingDetail;
