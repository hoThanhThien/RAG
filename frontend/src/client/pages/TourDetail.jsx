import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { tourService } from "../services/tourService";
import { commentService } from "../services/commentService";

const fmtVND = new Intl.NumberFormat("vi-VN", {
  style: "currency",
  currency: "VND",
});

const parseJwt = (token) => {
  try {
    return token ? JSON.parse(atob(token.split(".")[1])) : null;
  } catch {
    return null;
  }
};

const formatDate = (value) => {
  if (!value) return "Chưa cập nhật";
  const d = new Date(value);
  return isNaN(d) ? value : d.toLocaleDateString("vi-VN");
};

const Stars = React.memo(({ value = 0 }) => {
  const v = Math.round(value);
  return (
    <span className="d-inline-flex align-items-center gap-1">
      {Array.from({ length: 5 }, (_, i) => (
        <i key={i} className={`bi ${i < v ? "bi-star-fill" : "bi-star"} text-warning`} />
      ))}
      <small className="text-muted">{value.toFixed(1)}</small>
    </span>
  );
});

export default function TourDetail() {
  const { id } = useParams();
  const nav = useNavigate();

  const [tour, setTour] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cLoading, setCLoading] = useState(true);
  const [active, setActive] = useState(0);

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        setLoading(true);
        setCLoading(true);

        const [tourData, commentData] = await Promise.all([
          tourService.getById(id),
          commentService.listByTour(id, { page: 1, page_size: 50 }),
        ]);

        if (!mounted) return;

        setTour(tourData);

        const sorted = commentData.items.sort(
          (a, b) => new Date(b.created_at) - new Date(a.created_at)
        );
        setComments(sorted);
      } catch (err) {
        console.error(err);
      } finally {
        if (mounted) {
          setLoading(false);
          setCLoading(false);
        }
      }
    })();

    return () => (mounted = false);
  }, [id]);

  const ratingStats = useMemo(() => {
    if (!comments.length) return { avg: 5, count: 0 };
    const sum = comments.reduce((a, c) => a + (c.rating || 0), 0);
    return {
      avg: sum / comments.length,
      count: comments.length,
    };
  }, [comments]);

  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" />
      </div>
    );
  }

  if (!tour) return <div className="alert alert-warning">Không có tour</div>;

  const photos = tour.photos || [];
  const hero = photos[active]?.image_url || tour.image_url;

  return (
    <div className="container py-4">
      <div className="row g-4">
        {/* ===== IMAGE (LAZY LOAD) ===== */}
        <div className="col-md-7">
          <img
            src={hero}
            alt={tour.title}
            loading="lazy"
            className="w-100 rounded"
            style={{ maxHeight: 400, objectFit: "cover" }}
          />

          <div className="d-flex gap-2 mt-2 overflow-auto">
            {photos.map((p, i) => (
              <img
                key={i}
                src={p.image_url}
                loading="lazy"
                alt=""
                onClick={() => setActive(i)}
                style={{
                  width: 80,
                  height: 60,
                  cursor: "pointer",
                  border: i === active ? "2px solid blue" : "1px solid #ddd",
                }}
              />
            ))}
          </div>
        </div>

        {/* ===== INFO ===== */}
        <div className="col-md-5">
          <h3>{tour.title}</h3>
          <p className="text-muted">{tour.location}</p>

          <Stars value={ratingStats.avg} />

          <h4 className="text-primary mt-3">{fmtVND.format(tour.price)}</h4>

          <p>{tour.description}</p>

          <button
            className="btn btn-primary"
            onClick={() => nav(`/booking/${tour.id}`)}
          >
            Đặt tour
          </button>
        </div>
      </div>

      {/* ===== COMMENTS ===== */}
      <div className="mt-5">
        <h5>Bình luận ({comments.length})</h5>

        {cLoading ? (
          <p>Đang tải...</p>
        ) : comments.length === 0 ? (
          <p>Chưa có bình luận</p>
        ) : (
          <ul className="list-group">
            {comments.map((c) => (
              <li key={c.id} className="list-group-item">
                <strong>{c.user_name}</strong>
                <div>
                  <Stars value={c.rating || 0} />
                </div>
                <p>{c.content}</p>
                <small>{formatDate(c.created_at)}</small>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}