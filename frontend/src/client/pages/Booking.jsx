// src/client/pages/Booking.jsx
import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { tourService } from "../services/tourService";
import { bookingService } from "../services/bookingService";

const fmtVND = new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" });

export default function Booking() {
  const { id } = useParams();
  const nav = useNavigate();

  const [tour, setTour] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    number_of_people: 1,
    discount_id: "", // để trống = null
  });

  useEffect(() => {
    (async () => {
      const t = await tourService.getById(id);
      setTour(t);
    })();
  }, [id]);

  const onChange = (e) => setForm((s) => ({ ...s, [e.target.name]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);

    const payload = {
      tour_id: Number(id),
      number_of_people: Math.max(1, Number(form.number_of_people || 1)),
      discount_id:
        String(form.discount_id || "").trim() === "" ? null : Number(form.discount_id),
    };

    try {
      const res = await bookingService.create(payload);
      setSaving(false);

      if (res.ok) {
        const { booking_id: bookingId, order_code, total_amount } = res.data || {};
        // ➜ sang trang thanh toán
        // sau khi bookingService.create() trả ok:
        nav(`/payment/${bookingId}`, { state: { order_code, total_amount } });
      } else {
        const msg =
          (res.error && (res.error.detail || res.error.message)) ||
          "Không thể đặt tour lúc này.";
        alert(msg);
      }
    } catch (err) {
      setSaving(false);
      alert(err?.response?.data?.detail || err.message || "Có lỗi xảy ra.");
    }
  };

  const estimated =
    tour && Number.isFinite(Number(tour.price))
      ? fmtVND.format(Number(tour.price) * Math.max(1, Number(form.number_of_people || 1)))
      : null;

  return (
    <div className="container" style={{ padding: "24px 0", maxWidth: 900 }}>
      <h3 className="mb-3">Đặt tour</h3>

      {tour && (
        <div className="alert alert-light d-flex align-items-center gap-3">
          <img
            src={tour.image_url}
            alt={tour.title}
            style={{ width: 90, height: 60, objectFit: "cover", borderRadius: 6 }}
            onError={(e) => { e.currentTarget.src = "/no-image.png"; }}
          />
          <div>
            <div className="fw-semibold">{tour.title}</div>
            <small className="text-muted">
              {tour.location} • {tour.duration_days || 0} days
            </small>
          </div>
          <div className="ms-auto text-end">
            <div className="fw-bold text-primary">
              {Number.isFinite(Number(tour.price)) ? fmtVND.format(tour.price) : tour.price}
            </div>
            {estimated && <small className="text-muted">Tạm tính: {estimated}</small>}
          </div>
        </div>
      )}

      <form onSubmit={submit} className="row g-3">
        <div className="col-md-4">
          <label className="form-label">Số người</label>
          <input
            name="number_of_people"
            type="number"
            min="1"
            className="form-control"
            value={form.number_of_people}
            onChange={onChange}
            required
          />
        </div>

        <div className="col-md-4">
          <label className="form-label">Mã giảm giá (ID)</label>
        <input
            name="discount_id"
            type="number"
            min="1"
            className="form-control"
            value={form.discount_id}
            onChange={onChange}
            placeholder="Để trống nếu không có"
          />
        </div>

        <div className="col-12 d-flex gap-2">
          <button disabled={saving} className="btn btn-primary rounded-pill">
            {saving ? "Đang đặt..." : "Xác nhận đặt tour"}
          </button>
          <Link to={`/tours/${id}`} className="btn btn-outline-secondary rounded-pill">
            Huỷ
          </Link>
        </div>
      </form>
    </div>
  );
}
