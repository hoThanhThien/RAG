// src/client/components/Destinations.jsx
import React, { useEffect, useState } from "react";
import { Link, useNavigate, createSearchParams } from "react-router-dom";
// 👉 CHỌN 1 TRONG 2 DÒNG SAU cho đúng cấu trúc dự án của bạn:
import { tourService } from "../services/tourService";
// import { tourService } from "../services/tourService";

// (tuỳ chọn) nếu bạn có bookingService.list, import nó; nếu chưa có thì đoạn try/catch sẽ tự bỏ qua
import { bookingService } from "../services/bookingService";
// import { bookingService } from "../services/bookingService";

const toKey = (s) => (s || "").trim().toLowerCase();

const pickImage = (tour) => {
  // tourService trước đó đã map sẵn image_url tuyệt đối
  return tour?.image_url || tour?.photos?.[0]?.image_url || "/no-image.png";
};

export default function Destinations() {
  const [destinations, setDestinations] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        // Lấy nhiều tour để có đủ dữ liệu nhóm theo location
        const { items: tours } = await tourService.getAll({ page: 1, page_size: 200 });

        // ===== Lấy thống kê bookings (nếu có endpoint) =====
                const counts = new Map(); // tourId -> totalBooked (hoặc số booking)
                try {
                  if (bookingService?.list) {
                    // tuỳ backend: page_size lớn để gom đủ, đổi nếu backend của bạn có endpoint aggregate riêng
                    const { items: bookings } = await bookingService.list({ page: 1, page_size: 1000 });
                    for (const b of bookings || []) {
                      const tid = b.tour_id || b.tourId || b.tour?.tour_id || b.tour?.id;
                      if (!tid) continue;
                      const qty = Number(b.number_of_people ?? 1);
                      counts.set(tid, (counts.get(tid) || 0) + (isNaN(qty) ? 1 : qty));
                    }
                  }
                } catch {
                  // Không có API bookings hoặc lỗi → fallback theo ngày start_date
                }

        // Đính kèm _bookings vào tour
        const toursAnno = tours.map((t) => ({
          ...t,
          _bookings: counts.get(t.id) || 0,
          _start: t.start_date || null,
        }));

        // Nhóm theo location
        const groups = new Map();
        for (const t of toursAnno) {
          const key = toKey(t.location);
          if (!key) continue;
          if (!groups.has(key)) {
            groups.set(key, {
              // name/country để hiển thị: nếu bạn có country riêng, map thêm ở đây
              name: t.location,
              country: "", // không có country trong API → để trống
              count: 0,
              latestStart: t._start,
              image: pickImage(t),
              sampleTourId: t.id, // dùng để link tới trang tours với location
            });
          }
          const g = groups.get(key);
          g.count += t._bookings;
          // chọn ảnh + tour đại diện là tour có start_date mới nhất
          if (!g.latestStart || (t._start && t._start > g.latestStart)) {
            g.latestStart = t._start;
            g.image = pickImage(t);
            g.sampleTourId = t.id;
          }
        }

        // Sắp xếp theo rule:
        let arr = [...groups.values()];
        const hasAnyBookings = arr.some((x) => x.count > 0);
        arr.sort((a, b) => {
          if (hasAnyBookings) {
            if (b.count !== a.count) return b.count - a.count; // nhiều đặt trước
            return (b.latestStart || "").localeCompare(a.latestStart || ""); // cùng count thì mới nhất trước
          }
          // Không có booking → sort theo mới nhất
          return (b.latestStart || "").localeCompare(a.latestStart || "");
        });

        // Lấy 5 địa điểm đẹp nhất
        arr = arr.slice(0, 5);
        if (!alive) return;
        setDestinations(arr);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const goToLocation = (loc) => {
    // Link tới trang /tours và truyền query location
    navigate({
      pathname: "/tours",
      search: `?${createSearchParams({ location: loc })}`,
    });
  };

  if (loading) {
    return (
      <section id="destinations" className="section destination py-5 bg-light">
        <div className="container text-center">
          <div className="spinner-border text-primary" role="status" />
          <p className="mt-3 text-muted">Đang chọn điểm đến nổi bật…</p>
        </div>
      </section>
    );
  }

  if (destinations.length === 0) {
    return null; // hoặc render trạng thái rỗng tuỳ bạn
  }

  // 2 cái đầu to, các cái sau nhỏ như UI cũ
  const firstTwo = destinations.slice(0, 2);
  const rest = destinations.slice(2);

  return (
    <section id="destinations" className="section destination py-5 bg-light">
      <div className="container">
        <div className="text-center mb-5">
          <p
            className="section-subtitle text-primary mb-2"
            style={{ fontSize: "1rem", letterSpacing: "2px", textTransform: "uppercase" }}
          >
            Destinations
          </p>
          <h2 className="section-title display-5 fw-bold mb-3">Choose Your Place</h2>
        </div>

        <div className="row g-4">
          {firstTwo.map((d) => (
            <div key={d.name} className="col-md-6">
              <button
                type="button"
                onClick={() => goToLocation(d.name)}
                className="destination-card card border-0 shadow-lg overflow-hidden h-100 text-start text-decoration-none w-100"
                style={{ borderRadius: "20px", transition: "all 0.3s ease" }}
              >
                <figure className="card-banner position-relative overflow-hidden m-0" style={{ height: "400px" }}>
                  <img
                    src={d.image}
                    className="img-cover w-100 h-100"
                    style={{ objectFit: "cover", transition: "transform 0.3s ease" }}
                    loading="lazy"
                    alt={d.name}
                    onMouseOver={(e) => (e.currentTarget.style.transform = "scale(1.05)")}
                    onMouseOut={(e) => (e.currentTarget.style.transform = "scale(1)")}
                    onError={(e) => {
                      e.currentTarget.onerror = null;
                      e.currentTarget.src = "/no-image.png";
                    }}
                  />
                  <div
                    className="position-absolute bottom-0 start-0 w-100 p-4"
                    style={{ background: "linear-gradient(transparent, rgba(0,0,0,0.8))" }}
                  >
                    <div className="card-content text-white">
                      <p className="card-subtitle mb-1 opacity-75 small">{d.name}</p>
                      <h3 className="card-title h4 mb-0 fw-bold">{d.country || d.name}</h3>
                    </div>
                  </div>
                </figure>
              </button>
            </div>
          ))}

          {rest.map((d) => (
            <div key={d.name} className="col-lg-4 col-md-6">
              <button
                type="button"
                onClick={() => goToLocation(d.name)}
                className="destination-card card border-0 shadow-lg overflow-hidden h-100 text-start text-decoration-none w-100"
                style={{ borderRadius: "20px", transition: "all 0.3s ease" }}
              >
                <figure className="card-banner position-relative overflow-hidden m-0" style={{ height: "280px" }}>
                  <img
                    src={d.image}
                    className="img-cover w-100 h-100"
                    style={{ objectFit: "cover", transition: "transform 0.3s ease" }}
                    loading="lazy"
                    alt={d.name}
                    onMouseOver={(e) => (e.currentTarget.style.transform = "scale(1.05)")}
                    onMouseOut={(e) => (e.currentTarget.style.transform = "scale(1)")}
                    onError={(e) => {
                      e.currentTarget.onerror = null;
                      e.currentTarget.src = "/no-image.png";
                    }}
                  />
                  <div
                    className="position-absolute bottom-0 start-0 w-100 p-3"
                    style={{ background: "linear-gradient(transparent, rgba(0,0,0,0.8))" }}
                  >
                    <div className="card-content text-white">
                      <p className="card-subtitle mb-1 opacity-75 small">{d.name}</p>
                      <h3 className="card-title h6 mb-0 fw-bold">{d.country || d.name}</h3>
                    </div>
                  </div>
                </figure>
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
