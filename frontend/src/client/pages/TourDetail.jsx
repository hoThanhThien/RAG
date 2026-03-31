// src/pages/TourDetail.jsx
import React, { useEffect, useMemo, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { tourService } from "../services/tourService";
import { commentService } from "../services/commentService";

const fmtVND = new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" });

function diffDays(start, end) {
  try {
    const s = new Date(start);
    const e = new Date(end);
    const ms = e - s;
    if (isNaN(ms)) return null;
    return Math.max(1, Math.round(ms / (1000 * 60 * 60 * 24)) + 1);
  } catch {
    return null;
  }
}

function Stars({ value = 0 }) {
  const v = Math.max(0, Math.min(5, Math.round(value)));
  return (
    <span className="d-inline-flex align-items-center gap-1">
      {Array.from({ length: 5 }, (_, i) => (
        <i key={i} className={`bi ${i + 1 <= v ? "bi-star-fill" : "bi-star"} text-warning`} />
      ))}
      <span className="small text-muted">
        {value?.toFixed ? value.toFixed(1) : value}/5
      </span>
    </span>
  );
}

function StarPicker({ value, onChange }) {
  return (
    <div className="d-inline-flex gap-1">
      {Array.from({ length: 5 }, (_, i) => {
        const n = i + 1;
        const active = n <= value;
        return (
          <button
            key={n}
            type="button"
            className="btn btn-sm p-0 border-0 bg-transparent"
            onClick={() => onChange(n)}
            aria-label={`Rating ${n}`}
            title={`${n} sao`}
          >
            <i className={`bi ${active ? "bi-star-fill" : "bi-star"} text-warning fs-5`} />
          </button>
        );
      })}
    </div>
  );
}

export default function TourDetail() {
  const { id } = useParams();
  const nav = useNavigate();

  const [tour, setTour] = useState(null);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState(0); // index ảnh đang xem

  // Comments state
  const [comments, setComments] = useState([]);
  const [cLoading, setCLoading] = useState(true);
  const [newContent, setNewContent] = useState("");
  const [newRating, setNewRating] = useState(5);
  const [submitting, setSubmitting] = useState(false);

  // Chỉ vote 1 lần?
  const [canRate, setCanRate] = useState(false);

  // load tour
  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoading(true);
      try {
        const data = await tourService.getById(id);
        if (mounted) setTour(data);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => (mounted = false);
  }, [id]);

  // load comments
  useEffect(() => {
    let alive = true;
    (async () => {
      setCLoading(true);
      try {
        const { items } = await commentService.listByTour(id, { page: 1, page_size: 100 });
        if (alive) {
          const sorted = items.sort((a, b) =>
            String(b.created_at).localeCompare(String(a.created_at))
          );
          setComments(sorted);
        }
      } finally {
        if (alive) setCLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [id]);

  // hỏi BE xem user còn quyền vote không
  useEffect(() => {
    let ok = true;
    (async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          if (ok) setCanRate(false);
          return;
        }
        const allowed = await commentService.canRate(id);
        if (ok) setCanRate(allowed);
      } catch {
        if (ok) setCanRate(false);
      }
    })();
    return () => {
      ok = false;
    };
  }, [id]);

  // khi tour đổi, chọn ảnh primary nếu có
  useEffect(() => {
    if (tour?.photos?.length) {
      const idx = tour.photos.findIndex((p) => Number(p.is_primary) === 1);
      setActive(idx >= 0 ? idx : 0);
    } else {
      setActive(0);
    }
  }, [tour]);

  // Tính trung bình rating, nếu chưa có thì mặc định 5.0
  const ratingStats = useMemo(() => {
    const ratings = comments
      .map((c) => Number(c.rating) || 0)
      .filter((n) => n > 0);
    if (!ratings.length) return { avg: 5.0, count: 0 }; // Mặc định 5 sao nếu chưa có đánh giá
    const sum = ratings.reduce((a, b) => a + b, 0);
    return { avg: sum / ratings.length, count: ratings.length };
  }, [comments]);

  if (loading) {
    return (
      <div className="container" style={{ padding: "24px 0" }}>
        <div className="text-center py-5">
          <div className="spinner-border text-primary" />
        </div>
      </div>
    );
    }

  if (!tour) {
    return (
      <div className="container" style={{ padding: "24px 0" }}>
        <div className="alert alert-warning">Không tìm thấy tour!</div>
        <Link className="btn btn-outline-primary" to="/tours">
          ← Quay lại danh sách
        </Link>
      </div>
    );
  }

  const days = tour.duration_days ?? diffDays(tour.start_date, tour.end_date);
  const priceLabel = typeof tour.price === "number" ? fmtVND.format(tour.price) : tour.price;

  const photos = tour?.photos || [];
  const heroSrc = photos[active]?.image_url || tour.image_url || "/no-image.png";
  const prev = () => photos.length && setActive((i) => (i - 1 + photos.length) % photos.length);
  const next = () => photos.length && setActive((i) => (i + 1) % photos.length);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("access_token");
    if (!token) {
      alert("Vui lòng đăng nhập để bình luận.");
      return nav("/login?next=" + encodeURIComponent(`/tours/${tour.id}`));
    }
    if (!newContent.trim()) return alert("Nội dung bình luận không được rỗng.");

    setSubmitting(true);
    try {
      // optimistic UI
      const temp = {
        id: "temp-" + Date.now(),
        user_id: null,
        tour_id: tour.id,
        content: newContent.trim(),
        rating: canRate ? newRating : null,
        created_at: new Date().toISOString().slice(0, 19).replace("T", " "),
        user_name: "Bạn",
      };
      setComments((prev) => [temp, ...prev]);

      const payload = { content: newContent.trim() };
      if (canRate) payload.rating = newRating;

      const saved = await commentService.create(tour.id, payload);

      setComments((prev) => [saved, ...prev.filter((c) => c.id !== temp.id)]);
      setNewContent("");
      if (saved?.rating) {
        setCanRate(false); // đã vote thành công → khóa vote tiếp
        setNewRating(5);
      }
    } catch (err) {
      // BE có thể trả 400 "already rated"
      const detail = err?.response?.data?.detail || err?.message || "Gửi bình luận thất bại.";
      alert(detail);
      if (String(detail).toLowerCase().includes("already rated")) {
        setCanRate(false);
      }
      // rollback temp
      setComments((prev) => prev.filter((c) => !String(c.id).startsWith("temp-")));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container" style={{ padding: "24px 0" }}>
      <div className="row g-4">
        <div className="col-md-7">
          {/* Ảnh lớn */}
          <div className="position-relative mb-3">
            <img
              src={heroSrc}
              alt={tour.title}
              className="w-100 rounded-3 shadow-sm"
              style={{ maxHeight: 420, objectFit: "cover" }}
              onError={(e) => {
                e.currentTarget.onerror = null;
                e.currentTarget.src = "/no-image.png";
              }}
            />
            {photos.length > 1 && (
              <>
                <button
                  type="button"
                  className="btn btn-light position-absolute top-50 start-0 translate-middle-y shadow"
                  onClick={prev}
                  aria-label="Previous photo"
                >
                  <i className="bi bi-chevron-left" />
                </button>
                <button
                  type="button"
                  className="btn btn-light position-absolute top-50 end-0 translate-middle-y shadow"
                  onClick={next}
                  aria-label="Next photo"
                >
                  <i className="bi bi-chevron-right" />
                </button>
              </>
            )}
          </div>

          {/* Thumbnails */}
          {photos.length > 0 && (
            <div className="d-flex gap-2 overflow-auto pb-1">
              {photos.map((p, i) => (
                <button
                  key={p.photo_id ?? i}
                  type="button"
                  className="p-0 border-0 bg-transparent"
                  onClick={() => setActive(i)}
                  title={p.caption || `Ảnh ${i + 1}`}
                >
                  <img
                    src={p.image_url}
                    alt={p.caption || `Ảnh ${i + 1}`}
                    style={{
                      width: 96,
                      height: 72,
                      objectFit: "cover",
                      borderRadius: 8,
                      border: i === active ? "2px solid #0d6efd" : "1px solid #e9ecef",
                    }}
                    onError={(e) => {
                      e.currentTarget.onerror = null;
                      e.currentTarget.src = "/no-image.png";
                    }}
                  />
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="col-md-5">
          <h3>{tour.title}</h3>
          <div className="text-muted mb-2">
            <i className="bi bi-geo-alt-fill text-danger"></i> {tour.location}
          </div>
          <div className="mb-2 d-flex align-items-center gap-3">
            <span className="badge bg-primary">{days ? `${days} days` : "TBA"}</span>
            <span className="text-warning d-flex align-items-center gap-2">
              <i className="bi bi-star-fill"></i>
              <Stars value={ratingStats.avg} />
              {ratingStats.count > 0 && (
                <small className="text-muted">({ratingStats.count})</small>
              )}
            </span>
          </div>
          <p className="text-muted">{tour.description || tour.short_desc}</p>

          <div className="d-flex align-items-center gap-3 my-3">
            <h4 className="text-primary mb-0">{priceLabel}</h4>
            <small className="text-muted">/ người</small>
          </div>

          <div className="d-flex gap-2">
            <button
              className="btn btn-primary rounded-pill"
              onClick={() => nav(`/booking/${tour.id}`)}
            >
              Đặt tour
            </button>
            <Link to="/tours" className="btn btn-outline-secondary rounded-pill">
              ← Quay lại
            </Link>
          </div>
        </div>
      </div>

      {/* Itinerary (demo) */}
      <div className="mt-5">
        <h5>Lịch trình nổi bật</h5>
        <ul className="list-group list-group-flush">
          <li className="list-group-item">Ngày 1–2: City tour & ẩm thực địa phương</li>
          <li className="list-group-item">Ngày 3–4: Khám phá thiên nhiên / trekking</li>
          <li className="list-group-item">Ngày 5–6: Tham quan, trải nghiệm văn hoá</li>
        </ul>
      </div>

      {/* ===== Comments ===== */}
      <div className="mt-5">
        <div className="d-flex align-items-center justify-content-between mb-3">
          <h5 className="mb-0">Bình luận ({comments.length})</h5>
          <div className="small text-muted d-flex align-items-center gap-2">
            <Stars value={ratingStats.avg} />
            <span>({ratingStats.count} đánh giá)</span>
          </div>
        </div>

        {/* Form bình luận */}
        <form className="mb-4" onSubmit={handleSubmit}>
          <div className="mb-2">
            <label className="form-label me-2">Đánh giá:</label>
            {canRate ? (
              <StarPicker value={newRating} onChange={setNewRating} />
            ) : (
              <span className="text-muted small">
                Bạn đã đánh giá tour này. Bạn vẫn có thể bình luận thêm.
              </span>
            )}
          </div>
          <div className="mb-2">
            <textarea
              className="form-control"
              rows={3}
              placeholder="Chia sẻ cảm nhận của bạn…"
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
            />
          </div>
          <button className="btn btn-primary rounded-pill" type="submit" disabled={submitting}>
            {submitting ? "Đang gửi..." : "Gửi bình luận"}
          </button>
        </form>

        {/* Danh sách bình luận */}
        {cLoading ? (
          <div className="text-muted">Đang tải bình luận…</div>
        ) : comments.length === 0 ? (
          <div className="text-muted">Chưa có bình luận nào.</div>
        ) : (
          <ul className="list-group">
            {comments.map((c) => (
              <li key={c.id} className="list-group-item">
                <div className="d-flex justify-content-between">
                  <strong>{c.user_name || "Ẩn danh"}</strong>
                  <small className="text-muted">{c.created_at}</small>
                </div>
                {Number(c.rating) > 0 && (
                  <div className="mb-1">
                    <Stars value={c.rating} />
                  </div>
                )}
                <p className="mb-0">{c.content}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
