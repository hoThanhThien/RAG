// src/client/pages/Payment.jsx
import React, { useEffect, useMemo, useState, useRef, useCallback } from "react";
import { useParams, useLocation, Link, useNavigate } from "react-router-dom";
import { bookingService } from "../services/bookingService";
import { api } from "../services/api";
import PayPalButton from "../components/PayPalButton";
import MoMoPayment from "../components/MoMoPayment";
import { useAuth } from "../context/AuthContext";
import "../../styles/PaymentStyles.css";

const fmtVND = new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" });

export default function Payment() {
  const { bookingId } = useParams();
  const { state } = useLocation();
  const nav = useNavigate();

  const [info, setInfo] = useState({
    order_code: state?.order_code || "",
    total_amount: state?.total_amount ?? null,
    provider: "manualqr",
  });
  const [status, setStatus] = useState("Pending");
  const [pulling, setPulling] = useState(false);
  const [polling, setPolling] = useState(true);
  const [paymentMethod, setPaymentMethod] = useState("bank"); // "bank" hoặc "paypal"
  const [paymentError, setPaymentError] = useState("");
  const timer = useRef(null);
  const { user } = useAuth();

  // đảm bảo có payment record (đơn cũ mở lại)
  useEffect(() => {
    (async () => {
      try {
        const r = await api.post("/payments/init", { booking_id: Number(bookingId) });
        console.log('Payment init response:', r.data);
        const responseData = r.data;
        setInfo((s) => ({
          ...s,
          order_code: responseData?.order_code || s.order_code,
          total_amount: responseData?.amount ?? s.total_amount,
          provider: responseData?.provider || s.provider,
        }));
      } catch (err) {
        console.error('Failed to init payment:', err);
      }
    })();
  }, [bookingId]);

  // nếu không có state -> load lại từ booking
  useEffect(() => {
    if (state?.order_code) return;
    let alive = true;
    (async () => {
      try {
        const data = await bookingService.getById(bookingId);
        console.log('Booking data loaded:', data);
        if (!alive) return;
        setInfo((s) => ({
          ...s,
          order_code: data.OrderCode || data.order_code || "",
          total_amount: data.TotalAmount ?? data.total_amount ?? null,
        }));
      } catch (err) {
        console.error('Failed to load booking:', err);
      }
    })();
    return () => { alive = false; };
  }, [bookingId, state?.order_code]);

  const pullOnce = useCallback(async () => {
    try {
      setPulling(true);
      const r = await api.post("/payments/pull", { booking_id: Number(bookingId) });
      setStatus(r.data?.payment_status || "Pending");
    } catch (err) {
      console.error("Pull status error:", err);
      // Nếu lỗi 403/401, dừng polling
      if (err.response?.status === 403 || err.response?.status === 401) {
        setPolling(false);
      }
    } finally {
      setPulling(false);
    }
  }, [bookingId]);

  // bật polling mỗi 3s
  useEffect(() => {
    if (!polling) return;
    // gọi ngay 1 lần rồi setInterval
    pullOnce();
    timer.current = setInterval(pullOnce, 3000);
    return () => timer.current && clearInterval(timer.current);
  }, [polling, pullOnce]);

  // khi Paid -> chuyển qua trang Success
  useEffect(() => {
    if (status === "Paid") {
      if (timer.current) clearInterval(timer.current);
      nav(`/payment/${bookingId}/success`, {
        replace: true,
        state: { order_code: info.order_code, amount: Number(info.total_amount || 0) }
      });
    }
  }, [status, bookingId, info.order_code, info.total_amount, nav]);

  const bank = useMemo(() => ({
    code: import.meta.env.VITE_BANK_CODE || "",
    name: import.meta.env.VITE_BANK_NAME || "Ngân hàng",
    account: import.meta.env.VITE_BANK_ACCOUNT || "0123456789",
    holder: import.meta.env.VITE_BANK_HOLDER || "TEN CHU TK",
  }), []);

  const amount = Number(info.total_amount || 0) || 0;
  const order  = info.order_code || "";
  const vietqr =
    bank.code && bank.account
      ? `https://img.vietqr.io/image/${bank.code}-${bank.account}-compact.png?amount=${amount||""}&addInfo=${encodeURIComponent(order)}&accountName=${encodeURIComponent(bank.holder)}`
      : "";

  const copy = (t) => navigator.clipboard.writeText(String(t)).then(() => alert("Đã sao chép!"));

  // Xử lý khi PayPal thanh toán thành công
  const handlePayPalSuccess = (paymentData) => {
    console.log('PayPal payment successful:', paymentData);
    setStatus("Paid");
    setPaymentError("");
    alert('Thanh toán thành công! Đơn đặt tour của bạn đã được xác nhận.');
    
    // Chuyển hướng đến trang thành công sau 2 giây
    setTimeout(() => {
      nav('/payment-success', { 
        state: { 
          bookingId, 
          paymentData 
        } 
      });
    }, 2000);
  };

  // Xử lý khi có lỗi PayPal
  const handlePayPalError = (errorMessage) => {
    setPaymentError(errorMessage);
    console.error('PayPal error:', errorMessage);
  };

  // Xử lý khi user hủy thanh toán PayPal
  const handlePayPalCancel = () => {
    alert('Bạn đã hủy thanh toán PayPal. Bạn có thể thử lại bất kỳ lúc nào.');
  };

  return (
    <div className="container" style={{ maxWidth: 860, padding: "24px 0" }}>
      <div className="d-flex align-items-center gap-2 mb-3">
        <h3 className="mb-0">Thanh toán đơn #{bookingId}</h3>
        <span className="ms-auto small text-muted">
          {polling ? "Đang tự kiểm tra…" : "Tự kiểm tra đã tắt"}
        </span>
      </div>

      {/* Thông tin đơn hàng */}
      <div className="card shadow-sm mb-3">
        <div className="card-body">
          <div className="row">
            <div className="col-md-6">
              <div className="mb-2">
                <strong>Nội dung:</strong> <code>{order || "—"}</code>
                <button className="btn btn-sm btn-outline-secondary ms-2" onClick={() => copy(order)} disabled={!order}>Copy</button>
              </div>
              <div className="mb-2">
                <strong>Số tiền:</strong>{" "}
                <span className="text-primary fw-bold">
                  {amount ? fmtVND.format(amount) : "—"}
                </span>
                <button className="btn btn-sm btn-outline-secondary ms-2" onClick={() => copy(amount)} disabled={!amount}>Copy</button>
              </div>
            </div>
            <div className="col-md-6">
              <div className="mb-2">
                <strong>Trạng thái:</strong>{" "}
                {status === "Paid"
                  ? <span className="badge bg-success">Đã thanh toán</span>
                  : <span className="badge bg-warning text-dark">Chờ thanh toán</span>}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Chọn phương thức thanh toán */}
      <div className="card shadow-sm mb-3">
        <div className="card-header">
          <h5 className="mb-0">Chọn phương thức thanh toán</h5>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-4">
              <div className="form-check p-3 border rounded">
                <input 
                  className="form-check-input" 
                  type="radio" 
                  name="paymentMethod" 
                  id="bankTransfer" 
                  value="bank"
                  checked={paymentMethod === 'bank'}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                />
                <label className="form-check-label w-100" htmlFor="bankTransfer">
                  <strong>Chuyển khoản ngân hàng</strong>
                  <div className="text-muted small">Quét mã QR hoặc chuyển khoản thủ công</div>
                </label>
              </div>
            </div>
            <div className="col-md-4">
              <div className="form-check p-3 border rounded">
                <input 
                  className="form-check-input" 
                  type="radio" 
                  name="paymentMethod" 
                  id="momo" 
                  value="momo"
                  checked={paymentMethod === 'momo'}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                />
                <label className="form-check-label w-100" htmlFor="momo">
                  <strong>Ví MoMo</strong>
                  <div className="text-muted small">Thanh toán nhanh qua ví điện tử</div>
                </label>
              </div>
            </div>
            <div className="col-md-4">
              <div className="form-check p-3 border rounded">
                <input 
                  className="form-check-input" 
                  type="radio" 
                  name="paymentMethod" 
                  id="paypal" 
                  value="paypal"
                  checked={paymentMethod === 'paypal'}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                />
                <label className="form-check-label w-100" htmlFor="paypal">
                  <strong>PayPal</strong>
                  <div className="text-muted small">Thanh toán quốc tế an toàn</div>
                </label>
              </div>
            </div>
          </div>

          {/* Debug: Hiển thị thông tin authentication */}
          <div className="alert alert-info mt-3">
            <strong>Debug:</strong> User logged in: {user ? '✅ Yes' : '❌ No'}
            {user && <span> | User: {user.Username || user.email}</span>}
            <br />
            <strong>API URL:</strong> {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}
            <br />
            <button 
              className="btn btn-sm btn-outline-info mt-2" 
              onClick={async () => {
                try {
                  console.log('Testing API connection...');
                  const token = localStorage.getItem('access_token');
                  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/payments/paypal/create`, {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                      'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ booking_id: parseInt(bookingId) })
                  });
                  console.log('API Response:', response.status, response.statusText);
                  const data = await response.text();
                  console.log('API Data:', data);
                  alert(`API Test: ${response.status} ${response.statusText}\nData: ${data.substring(0, 200)}`);
                } catch (err) {
                  console.error('API Test Error:', err);
                  alert(`API Test Error: ${err.message}`);
                }
              }}
            >
              🔍 Test API Connection
            </button>
          </div>

          {/* Hiển thị lỗi nếu có */}
          {paymentError && (
            <div className="alert alert-danger mt-3">
              <i className="fas fa-exclamation-circle"></i> {paymentError}
            </div>
          )}
        </div>
      </div>

      {/* Nội dung thanh toán theo phương thức được chọn */}
      {paymentMethod === 'bank' && (
        <div className="card shadow-sm mb-3">
          <div className="card-header bg-primary text-white">
            <h5 className="mb-0">Thanh toán chuyển khoản</h5>
          </div>
          <div className="card-body d-flex flex-wrap gap-3 align-items-start">
            <div className="me-auto">
              <div className="d-flex flex-wrap gap-2 mb-3">
                <button className="btn btn-sm btn-outline-primary" onClick={pullOnce} disabled={pulling}>
                  {pulling ? "Đang kiểm tra…" : "Kiểm tra ngay"}
                </button>
                {polling ? (
                  <button className="btn btn-sm btn-outline-secondary" onClick={() => setPolling(false)}>
                    Tạm dừng tự kiểm tra
                  </button>
                ) : (
                  <button className="btn btn-sm btn-outline-secondary" onClick={() => setPolling(true)}>
                    Tiếp tục tự kiểm tra
                  </button>
                )}
              </div>
            </div>

            {vietqr ? (
              <div className="text-center">
                <img src={vietqr} alt="QR thanh toán" style={{ width: 220 }} />
                <div className="small text-muted mt-1">Quét QR, ghi đúng <b>nội dung</b></div>
              </div>
            ) : (
              <div className="alert alert-warning mb-0">
                Chưa cấu hình <code>VITE_BANK_CODE</code>/<code>VITE_BANK_ACCOUNT</code> nên không thể hiện QR.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Thanh toán PayPal */}
      {paymentMethod === 'paypal' && status !== "Paid" && (
        <div className="card shadow-sm mb-3">
          <div className="card-header" style={{ backgroundColor: '#ffc439', color: '#000' }}>
            <h5 className="mb-0">
              <i className="fab fa-paypal"></i> Thanh toán PayPal
            </h5>
          </div>
          <div className="card-body">
            <div className="alert alert-info">
              <i className="fas fa-info-circle"></i>
              <strong> Lưu ý:</strong> Số tiền sẽ được tự động chuyển đổi sang USD theo tỷ giá hiện tại.
            </div>
            
            {!user ? (
              <div className="alert alert-warning text-center">
                <h5><i className="fas fa-exclamation-triangle"></i> Cần đăng nhập</h5>
                <p>Bạn cần đăng nhập để sử dụng PayPal thanh toán.</p>
                <Link to="/auth" className="btn btn-primary">
                  <i className="fas fa-sign-in-alt"></i> Đăng nhập ngay
                </Link>
              </div>
            ) : (
              <>
                {/* Thông tin thanh toán */}
                <div className="card bg-light mb-3">
                  <div className="card-body">
                    <h6 className="card-title mb-3">
                      <i className="fas fa-user-circle"></i> Thông tin thanh toán
                    </h6>
                    <div className="row">
                      <div className="col-md-6 mb-2">
                        <small className="text-muted">Họ tên:</small>
                        <p className="mb-0 fw-bold">{user.full_name}</p>
                      </div>
                      <div className="col-md-6 mb-2">
                        <small className="text-muted">Email:</small>
                        <p className="mb-0 fw-bold">{user.email}</p>
                      </div>
                      <div className="col-md-6 mb-2">
                        <small className="text-muted">Số điện thoại:</small>
                        <p className="mb-0 fw-bold">{user.phone || 'Chưa cập nhật'}</p>
                      </div>
                      <div className="col-md-6 mb-2">
                        <small className="text-muted">Số tiền thanh toán:</small>
                        <p className="mb-0 fw-bold text-danger">{fmtVND.format(amount)}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="row">
                  <div className="col-md-8 mx-auto">
                    <PayPalButton
                      bookingId={parseInt(bookingId)}
                      amount={amount}
                      onSuccess={handlePayPalSuccess}
                      onError={handlePayPalError}
                      onCancel={handlePayPalCancel}
                      disabled={status === 'Paid'}
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Thanh toán MoMo */}
      {paymentMethod === 'momo' && status !== "Paid" && (
        <div className="card shadow-sm mb-3">
          <div className="card-header" style={{ backgroundColor: '#a50064', color: '#fff' }}>
            <h5 className="mb-0">
              <i className="fas fa-wallet"></i> Thanh toán MoMo
            </h5>
          </div>
          <div className="card-body">
            <MoMoPayment 
              bookingID={parseInt(bookingId)}
              amount={amount}
              onCancel={() => setPaymentMethod('bank')}
            />
          </div>
        </div>
      )}

      {/* Thông báo thanh toán thành công */}
      {status === "Paid" && (
        <div className="alert alert-success">
          <i className="fas fa-check-circle"></i>
          <strong> Thanh toán thành công!</strong> Đơn đặt tour của bạn đã được xác nhận.
        </div>
      )}

      <div className="d-flex gap-2">
        <Link to="/" className="btn btn-outline-secondary rounded-pill">Về trang chủ</Link>
        <Link to="/user/bookings" className="btn btn-outline-primary rounded-pill">Xem lịch sử đặt chỗ</Link>
      </div>
    </div>
  );
}
