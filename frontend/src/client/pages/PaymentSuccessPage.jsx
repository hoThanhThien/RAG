// src/client/pages/PaymentSuccessPage.jsx
import React, { useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';

const PaymentSuccessPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const { bookingId, paymentData } = location.state || {};

  useEffect(() => {
    // Nếu không có dữ liệu, chuyển về trang chủ sau 5 giây
    if (!bookingId) {
      const timer = setTimeout(() => {
        navigate('/');
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [bookingId, navigate]);

  return (
    <div className="payment-success-page">
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-lg-8">
            <div className="card text-center">
              <div className="card-body p-5">
                {/* Icon thành công */}
                <div className="mb-4">
                  <i className="fas fa-check-circle text-success" style={{ fontSize: '4rem' }}></i>
                </div>
                
                <h2 className="text-success mb-3">Thanh toán thành công!</h2>
                
                {bookingId ? (
                  <>
                    <p className="lead mb-4">
                      Cảm ơn bạn đã thanh toán. Đơn đặt tour của bạn đã được xác nhận thành công.
                    </p>
                    
                    {/* Thông tin thanh toán */}
                    <div className="payment-details bg-light p-4 rounded mb-4">
                      <h5 className="mb-3">Chi tiết thanh toán</h5>
                      <div className="row">
                        <div className="col-md-6 text-left">
                          <p><strong>Mã đặt tour:</strong> {bookingId}</p>
                          {paymentData && (
                            <>
                              <p><strong>Mã giao dịch PayPal:</strong> {paymentData.orderID}</p>
                              {paymentData.transactionID && (
                                <p><strong>Transaction ID:</strong> {paymentData.transactionID}</p>
                              )}
                            </>
                          )}
                        </div>
                        <div className="col-md-6 text-left">
                          <p><strong>Trạng thái:</strong> <span className="text-success">Đã thanh toán</span></p>
                          <p><strong>Thời gian:</strong> {new Date().toLocaleString('vi-VN')}</p>
                        </div>
                      </div>
                    </div>

                    {/* Thông báo tiếp theo */}
                    <div className="alert alert-info">
                      <i className="fas fa-info-circle"></i>
                      <strong> Thông báo:</strong> Chúng tôi đã gửi email xác nhận đến địa chỉ email của bạn. 
                      Vui lòng kiểm tra hộp thư để xem chi tiết tour.
                    </div>

                    {/* Các hành động */}
                    <div className="action-buttons">
                      <Link to={`/booking-details/${bookingId}`} className="btn btn-primary me-3">
                        <i className="fas fa-eye"></i> Xem chi tiết đặt tour
                      </Link>
                      <Link to="/bookings" className="btn btn-outline-secondary me-3">
                        <i className="fas fa-list"></i> Danh sách đặt tour
                      </Link>
                      <Link to="/" className="btn btn-outline-primary">
                        <i className="fas fa-home"></i> Về trang chủ
                      </Link>
                    </div>
                  </>
                ) : (
                  <>
                    <p className="lead mb-4">
                      Không tìm thấy thông tin thanh toán. Bạn sẽ được chuyển về trang chủ sau ít phút.
                    </p>
                    <Link to="/" className="btn btn-primary">
                      <i className="fas fa-home"></i> Về trang chủ ngay
                    </Link>
                  </>
                )}
              </div>
            </div>

            {/* Hướng dẫn tiếp theo */}
            {bookingId && (
              <div className="card mt-4">
                <div className="card-header">
                  <h5><i className="fas fa-question-circle"></i> Bước tiếp theo</h5>
                </div>
                <div className="card-body">
                  <div className="row">
                    <div className="col-md-4 text-center mb-3">
                      <i className="fas fa-envelope text-primary" style={{ fontSize: '2rem' }}></i>
                      <h6 className="mt-2">1. Kiểm tra Email</h6>
                      <p className="small">Xem thông tin chi tiết tour trong email xác nhận</p>
                    </div>
                    <div className="col-md-4 text-center mb-3">
                      <i className="fas fa-suitcase text-primary" style={{ fontSize: '2rem' }}></i>
                      <h6 className="mt-2">2. Chuẩn bị hành lý</h6>
                      <p className="small">Tham khảo danh sách đồ cần thiết trong email</p>
                    </div>
                    <div className="col-md-4 text-center mb-3">
                      <i className="fas fa-phone text-primary" style={{ fontSize: '2rem' }}></i>
                      <h6 className="mt-2">3. Liên hệ hỗ trợ</h6>
                      <p className="small">Gọi hotline nếu cần hỗ trợ thêm thông tin</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentSuccessPage;