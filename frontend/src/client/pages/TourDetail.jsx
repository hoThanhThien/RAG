import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { tourService } from "../services/tourService";
import { commentService } from "../services/commentService";
import { chatbotService } from "../services/chatbotService";

function parseJwt(token) {
  if (!token) return null;
  try {
    return JSON.parse(atob(token.split(".")[1]));
  } catch {
    return null;
  }
}

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

function formatDisplayDate(value) {
  if (!value) return "Chưa cập nhật";
  try {
    const raw = String(value).slice(0, 10);
    const d = new Date(`${raw}T00:00:00`);
    if (Number.isNaN(d.getTime())) return raw;
    return d.toLocaleDateString("vi-VN");
  } catch {
    return String(value).slice(0, 10);
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
  const [currentUserId, setCurrentUserId] = useState(null);
  const [editingCommentId, setEditingCommentId] = useState(null);
  const [editContent, setEditContent] = useState("");
  const [editRating, setEditRating] = useState(0);

  const [canRate, setCanRate] = useState(false);
  const [remainingReviews, setRemainingReviews] = useState(0);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");
  const [chatMessages, setChatMessages] = useState([
    {
      id: "intro",
      role: "assistant",
      content: "Mình có thể tư vấn nhanh về tour này, chi phí, lịch trình hoặc gợi ý tour tương tự.",
      sources: [],
    },
  ]);

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

  const refreshReviewQuota = useCallback(async () => {
    try {
      const token = localStorage.getItem("access_token");
      const payload = parseJwt(token);
      setCurrentUserId(payload?.user_id ?? payload?.UserID ?? null);

      if (!token) {
        setCanRate(false);
        setRemainingReviews(0);
        return;
      }

      const quota = await commentService.canRate(id);
      setCanRate(Boolean(quota?.can_rate));
      setRemainingReviews(Number(quota?.remaining_reviews ?? 0));
    } catch {
      setCanRate(false);
      setRemainingReviews(0);
    }
  }, [id]);

  // hỏi BE xem user còn quyền vote không
  useEffect(() => {
    refreshReviewQuota();
  }, [refreshReviewQuota]);










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

  const chatbotSuggestions = useMemo(() => {
    if (!tour) return [];
    return [
      `Tour này phù hợp với ai?`,
      `Chi phí tour ${tour.title} có hợp lý không?`,
      `Có tour nào tương tự ${tour.title} không?`,
    ];
  }, [tour]);

  const buildTourAwareQuery = useCallback(
    (question) => {
      const trimmed = String(question || "").trim();
      if (!trimmed || !tour) return trimmed;
      return [
        `Chỉ trả lời về tour đang xem: ${tour.title}.`,
        `Địa điểm: ${tour.location || "Chưa rõ"}.`,
        `Giá hiện tại: ${typeof tour.price === "number" ? tour.price : tour.price || "Chưa rõ"}.`,
        `Nếu người dùng không hỏi tour tương tự thì không gợi ý tour khác.`,
        `Câu hỏi hiện tại: ${trimmed}`,
      ].join(" ");
    },
    [tour]
  );

  // Use a ref to always read the latest chatInput without adding it to deps,
  // preventing stale closure that caused "send once" behaviour.
  const chatInputRef = useRef(chatInput);
  useEffect(() => { chatInputRef.current = chatInput; }, [chatInput]);

  const chatLoadingRef = useRef(chatLoading);
  useEffect(() => { chatLoadingRef.current = chatLoading; }, [chatLoading]);

  const submitChat = useCallback(
    async (rawQuestion) => {
      const question = String(rawQuestion ?? chatInputRef.current).trim();
      if (!question || !tour || chatLoadingRef.current) return;

      const userMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: question,
        sources: [],
      };

      setChatError("");
      setChatLoading(true);
      setChatMessages((prev) => [...prev, userMessage]);
      setChatInput("");

      try {
        const result = await chatbotService.chat({
          query: buildTourAwareQuery(question),
          userId: currentUserId,
          topK: 3,
          focusTourId: Number(tour.id || id),
        });

        setChatMessages((prev) => [
          ...prev,
          {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content: result?.answer || "Mình chưa có câu trả lời phù hợp lúc này.",
            sources: result?.sources || [],
          },
        ]);
      } catch (error) {
        console.error("Chatbot error:", error);
        setChatError("Không thể kết nối chatbot lúc này. Bạn hãy thử lại sau.");
        setChatMessages((prev) => [
          ...prev,
          {
            id: `assistant-error-${Date.now()}`,
            role: "assistant",
            content: "Mình đang bận xử lý, bạn thử hỏi lại sau ít phút nhé.",
            sources: [],
          },
        ]);
      } finally {
        setChatLoading(false);
      }
    },
    [buildTourAwareQuery, currentUserId, id, tour]
  );

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
  const startDateLabel = formatDisplayDate(tour.start_date);
  const endDateLabel = formatDisplayDate(tour.end_date);

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
      setNewRating(5);
      await refreshReviewQuota();
    } catch (err) {
      // BE có thể trả 400 "already rated"
      const detail = err?.response?.data?.detail || err?.message || "Gửi bình luận thất bại.";
      alert(detail);
      // rollback temp
      setComments((prev) => prev.filter((c) => !String(c.id).startsWith("temp-")));
      await refreshReviewQuota();
    } finally {
      setSubmitting(false);
    }
  };

  const startEdit = (comment) => {
    setEditingCommentId(comment.id);
    setEditContent(comment.content || "");
    setEditRating(Number(comment.rating) || 0);
  };

  const cancelEdit = () => {
    setEditingCommentId(null);
    setEditContent("");
    setEditRating(0);
  };

  const saveEdit = async (commentId) => {
    if (!editContent.trim()) {
      alert("Nội dung bình luận không được rỗng.");
      return;
    }

    try {
      const payload = { content: editContent.trim() };
      if (editRating > 0) payload.rating = editRating;

      await commentService.update(commentId, payload);
      setComments((prev) =>
        prev.map((c) =>
          c.id === commentId
            ? { ...c, content: editContent.trim(), rating: editRating > 0 ? editRating : c.rating }
            : c
        )
      );
      cancelEdit();
      await refreshReviewQuota();
    } catch (err) {
      alert(err?.response?.data?.detail || "Không thể cập nhật đánh giá.");
    }
  };

  const removeComment = async (commentId) => {
    if (!window.confirm("Bạn có chắc muốn xóa đánh giá này không?")) return;
    try {
      await commentService.remove(commentId);
      setComments((prev) => prev.filter((c) => c.id !== commentId));
      await refreshReviewQuota();
    } catch (err) {
      alert(err?.response?.data?.detail || "Không thể xóa đánh giá.");
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

          <div className="row g-2 my-3">
            <div className="col-sm-6">
              <div className="border rounded-3 px-3 py-2 h-100 bg-light">
                <div className="small text-muted">Ngày bắt đầu</div>
                <div className="fw-semibold">
                  <i className="bi bi-calendar-event text-primary me-2"></i>
                  {startDateLabel}
                </div>
              </div>
            </div>
            <div className="col-sm-6">
              <div className="border rounded-3 px-3 py-2 h-100 bg-light">
                <div className="small text-muted">Ngày kết thúc</div>
                <div className="fw-semibold">
                  <i className="bi bi-calendar-check text-success me-2"></i>
                  {endDateLabel}
                </div>
              </div>
            </div>
          </div>

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

      <div className="mt-5">
        <div className="card border-0 shadow-sm rounded-4 overflow-hidden">
          <div className="card-header bg-primary text-white py-3 border-0 d-flex align-items-center justify-content-between">
            <div>
              <div className="fw-semibold d-flex align-items-center gap-2">
                <i className="bi bi-robot"></i>
                Hỏi đáp nhanh về tour này
              </div>
              <div className="small text-white-50">Tư vấn chi phí, độ phù hợp và tour tương tự ngay trên trang chi tiết.</div>
            </div>
            <span className="badge bg-light text-primary">/chat</span>
          </div>

          <div className="card-body bg-white">
            <div className="d-flex flex-wrap gap-2 mb-3">
              {chatbotSuggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className="btn btn-sm btn-outline-primary rounded-pill"
                  onClick={() => submitChat(suggestion)}
                  disabled={chatLoading}
                >
                  {suggestion}
                </button>
              ))}
            </div>

            <div
              className="border rounded-4 bg-light p-3 mb-3"
              style={{ maxHeight: 360, overflowY: "auto" }}
            >
              <div className="d-flex flex-column gap-3">
                {chatMessages.map((message) => (
                  <div
                    key={message.id}
                    className={`d-flex ${message.role === "user" ? "justify-content-end" : "justify-content-start"}`}
                  >
                    <div
                      className={`rounded-4 px-3 py-2 ${message.role === "user" ? "bg-primary text-white" : "bg-white border"}`}
                      style={{ maxWidth: "85%", whiteSpace: "pre-wrap" }}
                    >
                      <div className="small fw-semibold mb-1">
                        {message.role === "user" ? "Bạn" : "Tour Assistant"}
                      </div>
                      <div>{message.content}</div>
                      {message.role === "assistant" && Array.isArray(message.sources) && message.sources.length > 0 && (
                        <div className="mt-2 pt-2 border-top small text-muted">
                          <div className="fw-semibold mb-1">Nguồn gợi ý:</div>
                          <ul className="mb-0 ps-3">
                            {message.sources.slice(0, 3).map((source) => (
                              <li key={`${message.id}-${source.tour_id}-${source.chunk_type}`}>
                                {source.title} - {source.location}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {chatLoading && (
                  <div className="d-flex justify-content-start">
                    <div className="rounded-4 px-3 py-2 bg-white border d-inline-flex align-items-center gap-2">
                      <div className="spinner-border spinner-border-sm text-primary" role="status" />
                      <span>Đang suy nghĩ…</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {chatError && <div className="alert alert-warning py-2">{chatError}</div>}

            <form
              className="d-flex flex-column flex-md-row gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                submitChat();
              }}
            >
              <input
                type="text"
                className="form-control rounded-pill"
                placeholder="Ví dụ: tour này có phù hợp cho gia đình không?"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={chatLoading}
              />
              <button
                type="submit"
                className="btn btn-primary rounded-pill px-4"
                disabled={chatLoading || !chatInput.trim()}
              >
                <i className="bi bi-send-fill me-2"></i>
                Hỏi bot
              </button>
            </form>
          </div>
        </div>
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
              <div className="d-flex align-items-center gap-2 flex-wrap">
                <StarPicker value={newRating} onChange={setNewRating} />
                <span className="text-muted small">Còn {remainingReviews} lượt đánh giá từ các lần đặt tour.</span>
              </div>
            ) : (
              <span className="text-muted small">
                Bạn đã dùng hết lượt đánh giá cho tour này, nhưng vẫn có thể sửa hoặc xóa đánh giá cũ của mình.
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
            {comments.map((c) => {
              const isOwner = Number(c.user_id) === Number(currentUserId);
              const isEditing = editingCommentId === c.id;

              return (
                <li key={c.id} className="list-group-item">
                  <div className="d-flex justify-content-between align-items-start gap-3">
                    <strong>{c.user_name || "Ẩn danh"}</strong>
                    <div className="d-flex align-items-center gap-2">
                      <small className="text-muted">{c.created_at}</small>
                      {isOwner && !isEditing && (
                        <>
                          <button type="button" className="btn btn-sm btn-outline-primary" onClick={() => startEdit(c)}>
                            Sửa
                          </button>
                          <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => removeComment(c.id)}>
                            Xóa
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {isEditing ? (
                    <div className="mt-2">
                      <div className="mb-2">
                        <StarPicker value={editRating} onChange={setEditRating} />
                      </div>
                      <textarea
                        className="form-control mb-2"
                        rows={3}
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                      />
                      <div className="d-flex gap-2">
                        <button type="button" className="btn btn-sm btn-primary" onClick={() => saveEdit(c.id)}>
                          Lưu
                        </button>
                        <button type="button" className="btn btn-sm btn-secondary" onClick={cancelEdit}>
                          Hủy
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      {Number(c.rating) > 0 && (
                        <div className="mb-1">
                          <Stars value={c.rating} />
                        </div>
                      )}
                      <p className="mb-0">{c.content}</p>
                    </>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}