// src/client/pages/PaymentSuccess.jsx
import React, { useEffect, useState } from "react";
import { useParams, useLocation, Link } from "react-router-dom";
import { bookingService } from "../services/bookingService";

const fmtVND = new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" });

export default function PaymentSuccess() {
  const { bookingId } = useParams();
  const { state } = useLocation();
  const [orderCode, setOrderCode] = useState(state?.order_code || "");
  const [amount, setAmount] = useState(
    typeof state?.amount === "number" ? state.amount : null
  );

  useEffect(() => {
    // Phòng khi user F5/đi thẳng vào URL
    if (orderCode && amount != null) return;
    (async () => {
      try {
        const data = await bookingService.getById(bookingId);
        setOrderCode(data.order_code || "");
        setAmount(typeof data.total_amount === "number" ? data.total_amount : null);
      } catch {
        /* ignore */
      }
    })();
  }, [bookingId, orderCode, amount]);

  const copy = (t) => navigator.clipboard.writeText(String(t));

  return (
    <div className="container" style={{ maxWidth: 820, padding: "24px 0" }}>
      <div className="text-center mb-4">
        <div className="display-6">✅ Thanh toán thành công!</div>
        <div className="text-muted mt-2">Đơn #{bookingId} đã được xác nhận.</div>
      </div>

      <div className="card shadow-sm mb-3">
        <div className="card-body">
          <div className="row g-3">
            <div className="col-md-6">
              <div className="d-flex justify-content-between">
                <span>Mã nội dung</span>
                <span>
                  <code>{orderCode || "—"}</code>
                  {orderCode && (
                    <button
                      className="btn btn-sm btn-outline-secondary ms-2"
                      onClick={() => copy(orderCode)}
                    >
                      Copy
                    </button>
                  )}
                </span>
              </div>
            </div>
            <div className="col-md-6">
              <div className="d-flex justify-content-between">
                <span>Số tiền</span>
                <span className="fw-semibold text-primary">
                  {amount != null ? fmtVND.format(amount) : "—"}
                </span>
              </div>
            </div>
          </div>

          <hr />
          <div className="d-flex gap-2">
            <Link to="/user/bookings" className="btn btn-primary rounded-pill">
              Xem lịch sử đặt chỗ
            </Link>
            <Link to="/" className="btn btn-outline-secondary rounded-pill">
              Về trang chủ
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
