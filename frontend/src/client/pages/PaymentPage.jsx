// src/client/pages/PaymentPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PayPalButton from '../components/PayPalButton';
import { bookingService } from '../services/bookingService';

const PaymentPage = () => {
  const { bookingId } = useParams();
  const navigate = useNavigate();
  
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('bank'); // 'bank' hoặc 'paypal'
  const [paymentStatus, setPaymentStatus] = useState('');

  useEffect(() => {
    const loadBookingDetails = async () => {
      try {
        setLoading(true);
        // Giả sử bạn có bookingService để lấy thông tin booking
        const bookingData = await bookingService.getBookingById(bookingId);
        setBooking(bookingData);
      } catch (error) {
        setError('Không thể tải thông tin đặt tour. Vui lòng thử lại.');
        console.error('Error loading booking:', error);
      } finally {
        setLoading(false);
      }
    };

    if (bookingId) {
      loadBookingDetails();
    }
  }, [bookingId]);

  // Xử lý khi PayPal thanh toán thành công
  const handlePayPalSuccess = (paymentData) => {
    console.log('PayPal payment successful:', paymentData);
    setPaymentStatus('success');
    
    // Hiển thị thông báo thành công
    alert('Thanh toán thành công! Đơn đặt tour của bạn đã được xác nhận.');
    
    // Chuyển hướng đến trang thành công
    setTimeout(() => {
      navigate('/booking-success', { 
        state: { 
          bookingId, 
          paymentData 
        } 
      });
    }, 2000);
  };

  // Xử lý khi có lỗi PayPal
  const handlePayPalError = (errorMessage) => {
    setError(errorMessage);
    setPaymentStatus('error');
  };

  // Xử lý khi user hủy thanh toán PayPal
  const handlePayPalCancel = () => {
    setPaymentStatus('cancelled');
    alert('Bạn đã hủy thanh toán. Bạn có thể thử lại bất kỳ lúc nào.');
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner">Đang tải thông tin...</div>
      </div>
    );
  }

  if (!booking) {
    return (
      <div className="error-container">
        <h3>Không tìm thấy thông tin đặt tour</h3>
        <button onClick={() => navigate('/bookings')} className="btn btn-primary">
          Quay lại danh sách đặt tour
        </button>
      </div>
    );
  }

  return (
    <div className="payment-page">
      <div className="container">
        <div className="row">
          <div className="col-lg-8">
            <div className="card">
              <div className="card-header">
                <h4>Thanh toán đặt tour</h4>
              </div>
              <div className="card-body">
                {/* Thông tin booking */}
                <div className="booking-info mb-4">
                  <h5>Thông tin đặt tour</h5>
                  <div className="row">
                    <div className="col-md-6">
                      <p><strong>Mã đơn:</strong> {booking.OrderCode}</p>
                      <p><strong>Tour:</strong> {booking.TourName}</p>
                      <p><strong>Số người:</strong> {booking.NumberOfPeople}</p>
                    </div>
                    <div className="col-md-6">
                      <p><strong>Ngày đặt:</strong> {new Date(booking.BookingDate).toLocaleDateString('vi-VN')}</p>
                      <p><strong>Tổng tiền:</strong> <span className="text-danger font-weight-bold">{booking.TotalAmount.toLocaleString('vi-VN')} VND</span></p>
                      <p><strong>Trạng thái:</strong> <span className="badge badge-warning">{booking.Status}</span></p>
                    </div>
                  </div>
                </div>

                {/* Chọn phương thức thanh toán */}
                <div className="payment-methods mb-4">
                  <h5>Chọn phương thức thanh toán</h5>
                  <div className="form-check">
                    <input 
                      className="form-check-input" 
                      type="radio" 
                      name="paymentMethod" 
                      id="bankTransfer" 
                      value="bank"
                      checked={paymentMethod === 'bank'}
                      onChange={(e) => setPaymentMethod(e.target.value)}
                    />
                    <label className="form-check-label" htmlFor="bankTransfer">
                      Chuyển khoản ngân hàng
                    </label>
                  </div>
                  <div className="form-check">
                    <input 
                      className="form-check-input" 
                      type="radio" 
                      name="paymentMethod" 
                      id="paypal" 
                      value="paypal"
                      checked={paymentMethod === 'paypal'}
                      onChange={(e) => setPaymentMethod(e.target.value)}
                    />
                    <label className="form-check-label" htmlFor="paypal">
                      PayPal (Thanh toán quốc tế)
                    </label>
                  </div>
                </div>

                {/* Hiển thị error nếu có */}
                {error && (
                  <div className="alert alert-danger" role="alert">
                    {error}
                  </div>
                )}

                {/* Thanh toán PayPal */}
                {paymentMethod === 'paypal' && (
                  <div className="paypal-payment">
                    <h5>Thanh toán qua PayPal</h5>
                    <p className="text-info">
                      Số tiền sẽ được tự động chuyển đổi sang USD theo tỷ giá hiện tại.
                    </p>
                    <PayPalButton
                      bookingId={parseInt(bookingId)}
                      amount={booking.TotalAmount}
                      onSuccess={handlePayPalSuccess}
                      onError={handlePayPalError}
                      onCancel={handlePayPalCancel}
                      disabled={paymentStatus === 'success'}
                    />
                  </div>
                )}

                {/* Thanh toán chuyển khoản */}
                {paymentMethod === 'bank' && (
                  <div className="bank-transfer">
                    <h5>Thông tin chuyển khoản</h5>
                    <div className="card bg-light">
                      <div className="card-body">
                        <p><strong>Ngân hàng:</strong> {import.meta.env.VITE_BANK_NAME}</p>
                        <p><strong>Số tài khoản:</strong> {import.meta.env.VITE_BANK_ACCOUNT}</p>
                        <p><strong>Chủ tài khoản:</strong> {import.meta.env.VITE_BANK_HOLDER}</p>
                        <p><strong>Nội dung chuyển khoản:</strong> <code>{booking.OrderCode}</code></p>
                        <p><strong>Số tiền:</strong> <span className="text-danger">{booking.TotalAmount.toLocaleString('vi-VN')} VND</span></p>
                      </div>
                    </div>
                    <div className="alert alert-info mt-3">
                      <strong>Lưu ý:</strong> Vui lòng chuyển khoản đúng số tiền và ghi đúng nội dung để hệ thống tự động xác nhận thanh toán.
                    </div>
                  </div>
                )}

                {/* Trạng thái thanh toán */}
                {paymentStatus === 'success' && (
                  <div className="alert alert-success">
                    <i className="fas fa-check-circle"></i> Thanh toán thành công! Đang chuyển hướng...
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="col-lg-4">
            <div className="card">
              <div className="card-header">
                <h5>Tóm tắt thanh toán</h5>
              </div>
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <span>Tổng tiền tour:</span>
                  <span>{booking.TotalAmount.toLocaleString('vi-VN')} VND</span>
                </div>
                <hr />
                <div className="d-flex justify-content-between font-weight-bold">
                  <span>Tổng cần thanh toán:</span>
                  <span className="text-danger">{booking.TotalAmount.toLocaleString('vi-VN')} VND</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentPage;