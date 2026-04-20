import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { recommendationService } from "../services/recommendationService";

const fmtVND = new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" });

function readUserIdFromToken() {
  const token = localStorage.getItem("access_token");
  if (!token) return "";
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return String(payload?.user_id ?? payload?.UserID ?? "");
  } catch {
    return "";
  }
}

export default function Recommendations() {
  const [userId, setUserId] = useState(readUserIdFromToken());
  const [prompt, setPrompt] = useState("recommend a family beach tour");
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const recommendations = useMemo(() => result?.recommendations || [], [result]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userId) {
      setError("Vui lòng nhập user ID để lấy gợi ý.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      const data = await recommendationService.recommend({
        userId: Number(userId),
        prompt: prompt.trim() || "recommend a tour",
        topK: Number(topK) || 5,
      });
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err?.response?.data?.detail || "Không thể lấy gợi ý lúc này.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ padding: "24px 0" }}>
      <div className="mb-4">
        <h2 className="fw-bold mb-2">Gợi ý tour thông minh</h2>
        <p className="text-muted mb-0">
          Hệ thống dùng phân khúc khách hàng và RAG để đề xuất tour phù hợp.
        </p>
      </div>

      <div className="row g-4">
        <div className="col-lg-4">
          <div className="card border-0 shadow-sm">
            <div className="card-body">
              <h5 className="card-title mb-3">Nhập yêu cầu</h5>
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label className="form-label">User ID</label>
                  <input
                    className="form-control"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    placeholder="Ví dụ: 1"
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">Nhu cầu</label>
                  <textarea
                    className="form-control"
                    rows={4}
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="Ví dụ: recommend a luxury mountain tour"
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">Số kết quả</label>
                  <select className="form-select" value={topK} onChange={(e) => setTopK(e.target.value)}>
                    <option value={3}>3</option>
                    <option value={5}>5</option>
                    <option value={7}>7</option>
                  </select>
                </div>

                <button className="btn btn-primary w-100 rounded-pill" disabled={loading}>
                  {loading ? "Đang phân tích..." : "Lấy gợi ý"}
                </button>
              </form>

              {error && <div className="alert alert-danger mt-3 mb-0">{error}</div>}
            </div>
          </div>
        </div>

        <div className="col-lg-8">
          {!result ? (
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body d-flex align-items-center justify-content-center text-center text-muted">
                Nhập yêu cầu để xem gợi ý cá nhân hóa.
              </div>
            </div>
          ) : (
            <div className="d-flex flex-column gap-3">
              <div className="card border-0 shadow-sm">
                <div className="card-body">
                  <div className="d-flex flex-wrap gap-2 align-items-center mb-2">
                    <span className="badge bg-primary">{result?.segment?.segment_name || "Unknown segment"}</span>
                    <span className="badge bg-light text-dark">Retriever: {result?.retriever || "RAG"}</span>
                    <span className="badge bg-light text-dark">Category: {result?.segment?.favorite_category || "General"}</span>
                  </div>
                  <p className="mb-0">{result?.answer}</p>
                </div>
              </div>

              <div className="row g-3">
                {recommendations.map((item) => (
                  <div className="col-md-6" key={item.tour_id}>
                    <div className="card h-100 border-0 shadow-sm">
                      <div className="card-body d-flex flex-column">
                        <h5 className="card-title">{item.title}</h5>
                        <div className="text-muted small mb-2">{item.location} • {item.category_name}</div>
                        <p className="small text-muted flex-grow-1">{item.description || "Không có mô tả"}</p>
                        <div className="d-flex justify-content-between align-items-center mb-3">
                          <strong className="text-primary">{fmtVND.format(Number(item.price || 0))}</strong>
                          <span className="small text-warning">⭐ {Number(item.rating || 0).toFixed(1)}</span>
                        </div>
                        <Link to={`/tours/${item.tour_id}`} className="btn btn-outline-primary btn-sm rounded-pill">
                          Xem tour
                        </Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
