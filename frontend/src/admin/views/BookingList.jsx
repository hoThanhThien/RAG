// src/components/BookingList.jsx
import React, { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
function authHeader() {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// helpers format
function fmtDate(d) {
  if (!d) return "—";
  const dt = new Date(d);
  return isNaN(dt.getTime()) ? String(d) : dt.toLocaleDateString();
}
function fmtMoney(n) {
  const x = Number(n);
  return isNaN(x) ? "0" : x.toLocaleString();
}
const StatusBadge = ({ status }) => {
  const cls =
    status === "Confirmed"
      ? "badge bg-success"
      : status === "Cancelled"
      ? "badge bg-danger"
      : "badge bg-secondary";
  return <span className={cls}>{status || "—"}</span>;
};

// Chuẩn hoá mọi response về { items, meta }
function normalizePaging(json, fallbackMeta) {
  if (!json) return { items: [], meta: fallbackMeta };
  if (json.meta) {
    const m = json.meta || {};
    return {
      items: Array.isArray(json.items) ? json.items : [],
      meta: {
        page: m.page ?? fallbackMeta.page,
        page_size: m.page_size ?? fallbackMeta.page_size,
        total: m.total ?? 0,
        total_pages: m.total_pages ?? 1,
        has_next: !!m.has_next,
        has_prev: !!m.has_prev,
      },
    };
  }
  return {
    items: Array.isArray(json.items) ? json.items : [],
    meta: {
      page: json.page ?? fallbackMeta.page,
      page_size: json.page_size ?? fallbackMeta.page_size,
      total: json.total ?? 0,
      total_pages: json.total_pages ?? 1,
      has_next: !!json.has_next,
      has_prev: !!json.has_prev,
    },
  };
}

export default function BookingList() {
  const [items, setItems] = useState([]);
  const [meta, setMeta] = useState({
    page: 1,
    page_size: 10,
    total: 0,
    total_pages: 1,
    has_next: false,
    has_prev: false,
  });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const [statusFilter, setStatusFilter] = useState(""); // "", "Pending", "Confirmed", "Cancelled"
  const [sort, setSort] = useState("booking_date:desc");

  // đang update những booking nào (Set<booking_id>)
  const [updating, setUpdating] = useState(new Set());

  const allowedStatuses = ["", "Pending", "Confirmed", "Cancelled"];

  async function fetchBookings({
    page = meta.page,
    pageSize = meta.page_size,
    status = statusFilter,
    srt = sort,
  } = {}) {
    const params = new URLSearchParams();
    params.set("page", page);
    params.set("page_size", pageSize);
    if (status) params.set("status_filter", status);
    if (srt) params.set("sort", srt);

    const res = await fetch(`${API_BASE}/bookings?${params.toString()}`, {
      headers: { "Content-Type": "application/json", ...authHeader() },
      credentials: "include",
    });
    if (!res.ok) {
      const t = await res.text().catch(() => "");
      throw new Error(`HTTP ${res.status} - ${t || res.statusText}`);
    }
    const json = await res.json();
    return normalizePaging(json, {
      page,
      page_size: pageSize,
      total: 0,
      total_pages: 1,
      has_next: false,
      has_prev: page > 1,
    });
  }

  // gọi API đổi trạng thái (admin)
  async function updateStatus(bookingId, newStatus) {
    // optimistic: đánh dấu đang update
    setUpdating((prev) => new Set(prev).add(bookingId));
    setErr("");
    try {
      const res = await fetch(
        `${API_BASE}/bookings/${bookingId}/status?new_status=${encodeURIComponent(
          newStatus
        )}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json", ...authHeader() },
          credentials: "include",
        }
      );
      if (!res.ok) {
        const t = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status} - ${t || res.statusText}`);
      }
      // cập nhật tại chỗ
      setItems((old) =>
        old.map((it) =>
          it.booking_id === bookingId ? { ...it, status: newStatus } : it
        )
      );
    } catch (e) {
      setErr(e.message || "Cập nhật trạng thái thất bại");
    } finally {
      setUpdating((prev) => {
        const n = new Set(prev);
        n.delete(bookingId);
        return n;
      });
    }
  }

  // load lần đầu & khi filter/sort đổi -> về page 1
  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setErr("");
        const { items: _items, meta: _meta } = await fetchBookings({
          page: 1,
          pageSize: meta.page_size,
          status: statusFilter,
          srt: sort,
        });
        setItems(_items);
        setMeta(_meta);
      } catch (e) {
        setErr(e.message || "Load bookings failed");
        setItems([]);
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, sort]);

  async function goToPage(nextPage) {
    try {
      setLoading(true);
      setErr("");
      const { items: _items, meta: _meta } = await fetchBookings({
        page: nextPage,
        pageSize: meta.page_size,
        status: statusFilter,
        srt: sort,
      });
      setItems(_items);
      setMeta(_meta);
    } catch (e) {
      setErr(e.message || "Load bookings failed");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  const distinctStatuses = useMemo(
    () => Array.from(new Set(items.map((b) => b?.status).filter(Boolean))),
    [items]
  );

  return (
    <div className="container py-3">
      <h2 className="mb-3">Booking List</h2>

      {/* Controls */}
      <div className="d-flex gap-2 align-items-end flex-wrap mb-3">
        <div>
          <label className="form-label">Trạng thái</label>
          <select
            className="form-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            {allowedStatuses.map((st) => (
              <option key={st || "ALL"} value={st}>
                {st ? st : "Tất cả"}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="form-label">Sắp xếp</label>
          <select
            className="form-select"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="booking_date:desc">Ngày đặt ↓</option>
            <option value="booking_date:asc">Ngày đặt ↑</option>
            <option value="total_amount:desc">Tổng tiền ↓</option>
            <option value="total_amount:asc">Tổng tiền ↑</option>
            <option value="status:asc">Trạng thái A→Z</option>
            <option value="status:desc">Trạng thái Z→A</option>
            <option value="tour_title:asc">Tên tour A→Z</option>
            <option value="tour_title:desc">Tên tour Z→A</option>
            <option value="people:desc">Số người ↓</option>
            <option value="people:asc">Số người ↑</option>
          </select>
        </div>

        <div className="ms-auto">
          <div className="small text-muted">
            Đang hiển thị trang {meta.page}/{meta.total_pages} • Tổng {meta.total} đơn
          </div>
          <div className="d-flex gap-2 mt-1">
            <button
              className="btn btn-outline-secondary btn-sm"
              disabled={!meta.has_prev || loading}
              onClick={() => goToPage(Math.max(1, meta.page - 1))}
            >
              ← Trước
            </button>
            <button
              className="btn btn-outline-secondary btn-sm"
              disabled={!meta.has_next || loading}
              onClick={() => goToPage(Math.min(meta.total_pages, meta.page + 1))}
            >
              Sau →
            </button>
          </div>
        </div>
      </div>

      {/* Error/Loading */}
      {err && <div className="alert alert-danger">{err}</div>}
      {loading && <div className="alert alert-info">Đang tải...</div>}

      {distinctStatuses.length > 0 && (
        <p className="text-muted small">
          Trạng thái đang xuất hiện: {distinctStatuses.join(", ")}
        </p>
      )}

      {/* List */}
      <ul className="list-group">
        {items.map((b) => {
          const title = b?.tour_title || "(Không có tên tour)";
          const loc = b?.tour_location ? ` (${b.tour_location})` : "";
          const isUpdating = updating.has(b.booking_id);

          return (
            <li
              key={b.booking_id}
              className="list-group-item d-flex justify-content-between align-items-center"
            >
              <div className="me-3">
                <div className="fw-semibold">
                  #{b.booking_id} • {title}
                  {loc}
                </div>
                <div className="small text-muted">
                  Ngày đặt: {fmtDate(b.booking_date)} • Số người: {b.number_of_people} • Tổng tiền:{" "}
                  {fmtMoney(b.total_amount)} • <StatusBadge status={b.status} />
                </div>
              </div>

              {/* Actions: đổi trạng thái */}
              <div className="d-flex align-items-center gap-2">
                <select
                  className="form-select form-select-sm"
                  style={{ width: 160 }}
                  defaultValue={b.status || "Pending"}
                  disabled={isUpdating}
                  onChange={(e) => {
                    const next = e.target.value;
                    if (next === b.status) return;
                    if (
                      window.confirm(
                        `Đổi trạng thái booking #${b.booking_id} từ "${b.status}" → "${next}"?`
                      )
                    ) {
                      updateStatus(b.booking_id, next);
                    } else {
                      // khôi phục lại dropdown nếu hủy
                      e.target.value = b.status || "Pending";
                    }
                  }}
                >
                  <option value="Pending">Pending</option>
                  <option value="Confirmed">Confirmed</option>
                  <option value="Cancelled">Cancelled</option>
                </select>

                {isUpdating && (
                  <span className="spinner-border spinner-border-sm" role="status" />
                )}
              </div>
            </li>
          );
        })}
        {!loading && items.length === 0 && (
          <li className="list-group-item">Không có booking nào.</li>
        )}
      </ul>
    </div>
  );
}
