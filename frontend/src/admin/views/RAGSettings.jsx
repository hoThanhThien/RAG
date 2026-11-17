import React, { useCallback, useEffect, useState } from "react";
import { adminService } from "../services/adminService";

const IN_SCOPE_SAMPLES = [
  "Tour Đà Nẵng giá bao nhiêu?",
  "Tìm tour đi biển giá rẻ",
  "Hội An có gì nổi bật?",
];

const OUT_OF_SCOPE_SAMPLES = [
  "Tour đi Ai Cập ngắm Kim Tự Tháp",
  "Kinh nghiệm xin visa du học Mỹ cần những gì?",
  "100 USD bằng bao nhiêu Yên Nhật?",
  "Tour đi Nam Cực ngắm chim cánh cụt",
];

const SUGGESTED_OOS_MODELS = [
  { label: "Dùng chung Model chính", value: "" },
  { label: "gpt-4o-mini (OpenAI)", value: "gpt-4o-mini" },
  { label: "gpt-4o (OpenAI)", value: "gpt-4o" },
  { label: "llama-3.3-70b-versatile (Groq)", value: "llama-3.3-70b-versatile" },
  { label: "gemini-2.0-flash (Gemini)", value: "gemini-2.0-flash" },
  { label: "openai/gpt-4o-mini (OpenRouter)", value: "openai/gpt-4o-mini" },
];

export default function RAGSettings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [clearingCache, setClearingCache] = useState(false);
  const [testing, setTesting] = useState(false);

  const [alert, setAlert] = useState(null); // { type: 'success' | 'danger' | 'info', text }
  const [showApiKey, setShowApiKey] = useState(false);

  const [metrics, setMetrics] = useState({});
  const [indexState, setIndexState] = useState({});
  const [providerPresets, setProviderPresets] = useState({});
  const [oosModes, setOosModes] = useState([]);
  const [hasApiKey, setHasApiKey] = useState(false);

  const [form, setForm] = useState({
    llm_provider: "openai",
    openai_base_url: "https://api.openai.com/v1",
    openai_api_key: "",
    chat_model: "gpt-4o-mini",
    embedding_model: "text-embedding-3-small",
    temperature: 0.15,
    max_tokens: 320,
    top_k_default: 4,
    hybrid_dense_weight: 0.68,
    hybrid_lexical_weight: 0.32,
    reranker_enabled: false,
    reranker_model: "BAAI/bge-reranker-base",
    knowledge_base_enabled: true,
    custom_system_prompt_addon: "",
    out_of_scope_mode: "general_travel",
    out_of_scope_model: "",
    out_of_scope_temperature: 0.5,
    out_of_scope_max_tokens: 400,
    similarity_threshold: 0.22,
    suggest_popular_tours_on_oos: true,
    out_of_scope_system_prompt: "",
    out_of_scope_fallback_message: "",
  });

  // Playground state
  const [testQuery, setTestQuery] = useState("Tour đi Ai Cập ngắm Kim Tự Tháp");
  const [testFocusTourId, setTestFocusTourId] = useState("");
  const [useFormOverride, setUseFormOverride] = useState(true);
  const [testResult, setTestResult] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const data = await adminService.getRagConfig();
      const cfg = data?.config || {};
      setMetrics(data?.metrics || {});
      setIndexState(data?.index_state || {});
      setProviderPresets(cfg.provider_presets || {});
      setOosModes(cfg.out_of_scope_modes || []);
      setHasApiKey(Boolean(cfg.has_api_key));

      setForm({
        llm_provider: cfg.llm_provider || "openai",
        openai_base_url: cfg.openai_base_url || "https://api.openai.com/v1",
        openai_api_key: cfg.openai_api_key || "",
        chat_model: cfg.chat_model || "gpt-4o-mini",
        embedding_model: cfg.embedding_model || "text-embedding-3-small",
        temperature: cfg.temperature ?? 0.15,
        max_tokens: cfg.max_tokens ?? 320,
        top_k_default: cfg.top_k_default ?? 4,
        hybrid_dense_weight: cfg.hybrid_dense_weight ?? 0.68,
        hybrid_lexical_weight: cfg.hybrid_lexical_weight ?? 0.32,
        reranker_enabled: Boolean(cfg.reranker_enabled),
        reranker_model: cfg.reranker_model || "BAAI/bge-reranker-base",
        knowledge_base_enabled: cfg.knowledge_base_enabled !== false,
        custom_system_prompt_addon: cfg.custom_system_prompt_addon || "",
        out_of_scope_mode: cfg.out_of_scope_mode || "general_travel",
        out_of_scope_model: cfg.out_of_scope_model || "",
        out_of_scope_temperature: cfg.out_of_scope_temperature ?? 0.5,
        out_of_scope_max_tokens: cfg.out_of_scope_max_tokens ?? 400,
        similarity_threshold: cfg.similarity_threshold ?? 0.22,
        suggest_popular_tours_on_oos: cfg.suggest_popular_tours_on_oos !== false,
        out_of_scope_system_prompt: cfg.out_of_scope_system_prompt || "",
        out_of_scope_fallback_message: cfg.out_of_scope_fallback_message || "",
      });
    } catch (err) {
      setAlert({
        type: "danger",
        text: err?.response?.data?.detail || "Không thể tải cấu hình RAG.",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFieldChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleProviderChange = (providerKey) => {
    const preset = providerPresets[providerKey];
    setForm((prev) => {
      const next = { ...prev, llm_provider: providerKey };
      if (preset?.base_url) {
        next.openai_base_url = preset.base_url;
      }
      if (preset?.models?.length && !preset.models.includes(prev.chat_model)) {
        next.chat_model = preset.models[0];
      }
      return next;
    });
  };

  const handleDenseWeightChange = (val) => {
    const dense = Math.max(0, Math.min(1, Number(val) || 0));
    const lexical = Number((1 - dense).toFixed(2));
    setForm((prev) => ({
      ...prev,
      hybrid_dense_weight: Number(dense.toFixed(2)),
      hybrid_lexical_weight: lexical,
    }));
  };

  const buildUpdatePayload = () => {
    const payload = {
      ...form,
      temperature: Number(form.temperature),
      max_tokens: Number(form.max_tokens),
      top_k_default: Number(form.top_k_default),
      hybrid_dense_weight: Number(form.hybrid_dense_weight),
      hybrid_lexical_weight: Number(form.hybrid_lexical_weight),
      out_of_scope_temperature: Number(form.out_of_scope_temperature),
      out_of_scope_max_tokens: Number(form.out_of_scope_max_tokens),
      similarity_threshold: Number(form.similarity_threshold),
    };
    if (!payload.openai_api_key || payload.openai_api_key.includes("****")) {
      delete payload.openai_api_key;
    }
    return payload;
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setAlert(null);
    try {
      const res = await adminService.updateRagConfig(buildUpdatePayload());
      const cfg = res?.config || {};
      setHasApiKey(Boolean(cfg.has_api_key));
      if (cfg.openai_api_key !== undefined) {
        setForm((prev) => ({ ...prev, openai_api_key: cfg.openai_api_key }));
      }
      setAlert({
        type: "success",
        text: "Đã lưu cấu hình RAG và tự động làm mới bộ nhớ đệm phản hồi!",
      });
    } catch (err) {
      setAlert({
        type: "danger",
        text: err?.response?.data?.detail || "Lưu cấu hình RAG thất bại.",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleClearApiKey = async () => {
    if (!window.confirm("Bạn muốn xóa API Key đã lưu và chuyển về chế độ dự phòng?")) return;
    setSaving(true);
    setAlert(null);
    try {
      const res = await adminService.updateRagConfig({ clear_api_key: true });
      const cfg = res?.config || {};
      setHasApiKey(Boolean(cfg.has_api_key));
      setForm((prev) => ({ ...prev, openai_api_key: cfg.openai_api_key || "" }));
      setAlert({ type: "info", text: "Đã xóa API Key khỏi cấu hình runtime." });
    } catch (err) {
      setAlert({
        type: "danger",
        text: err?.response?.data?.detail || "Không thể xóa API Key.",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleReindex = async () => {
    setReindexing(true);
    setAlert(null);
    try {
      const res = await adminService.reindexRag(true);
      setAlert({
        type: "success",
        text: `Rebuild thành công ${res.documents} chunks từ ${res.tour_count} tours (Embedding: ${res.embedding_provider}).`,
      });
      await loadData();
    } catch (err) {
      setAlert({
        type: "danger",
        text: err?.response?.data?.detail || "Rebuild RAG index thất bại.",
      });
    } finally {
      setReindexing(false);
    }
  };

  const handleInvalidateCache = async () => {
    setClearingCache(true);
    setAlert(null);
    try {
      const res = await adminService.invalidateRagCache("admin_ui");
      setAlert({
        type: "success",
        text: `Đã xóa cache phản hồi RAG (epoch ${res.epoch}).`,
      });
      await loadData();
    } catch (err) {
      setAlert({
        type: "danger",
        text: err?.response?.data?.detail || "Không thể xóa cache RAG.",
      });
    } finally {
      setClearingCache(false);
    }
  };

  const handleRunTest = async (customQuery) => {
    const queryText = (typeof customQuery === "string" ? customQuery : testQuery).trim();
    if (!queryText) return;
    if (typeof customQuery === "string") {
      setTestQuery(customQuery);
    }

    setTesting(true);
    setTestResult(null);
    try {
      const payload = {
        query: queryText,
        top_k: Number(form.top_k_default) || 4,
        focus_tour_id: testFocusTourId ? Number(testFocusTourId) : null,
      };
      if (useFormOverride) {
        payload.config_override = buildUpdatePayload();
      }
      const res = await adminService.testRagChat(payload);
      setTestResult(res);
    } catch (err) {
      setAlert({
        type: "danger",
        text: err?.response?.data?.detail || "Lỗi khi test RAG chatbot.",
      });
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: "70vh" }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  const currentPreset = providerPresets[form.llm_provider] || {};
  const cacheHits =
    Number(metrics.response_cache_hits_memory || 0) + Number(metrics.response_cache_hits_redis || 0);

  return (
    <div className="container-fluid mt-4 px-4 pb-5">
      {/* Header */}
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
        <div>
          <h2 className="fw-bold text-primary mb-1">
            <i className="bi bi-robot me-2"></i>
            Quản trị & Tùy chỉnh Model RAG AI
          </h2>
          <p className="text-muted mb-0 small">
            Điều chỉnh Model chính, ngưỡng lọc ngữ nghĩa và Model/chế độ xử lý các câu hỏi nằm ngoài danh mục tour.
          </p>
        </div>
        <div className="d-flex flex-wrap gap-2">
          <button
            type="button"
            className="btn btn-outline-secondary"
            onClick={handleInvalidateCache}
            disabled={clearingCache}
          >
            <i className="bi bi-trash3 me-1"></i>
            {clearingCache ? "Đang xóa..." : "Xóa Cache"}
          </button>
          <button
            type="button"
            className="btn btn-outline-primary"
            onClick={handleReindex}
            disabled={reindexing}
          >
            <i className={`bi bi-arrow-repeat me-1 ${reindexing ? "spin" : ""}`}></i>
            {reindexing ? "Đang Rebuild..." : "Rebuild Vector Index"}
          </button>
        </div>
      </div>

      {alert && (
        <div className={`alert alert-${alert.type} alert-dismissible fade show`} role="alert">
          {alert.text}
          <button
            type="button"
            className="btn-close"
            aria-label="Close"
            onClick={() => setAlert(null)}
          ></button>
        </div>
      )}

      {/* 1. Metrics & Index Status */}
      <div className="row g-3 mb-4">
        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-body">
              <div className="text-muted small text-uppercase">Tổng Chunks</div>
              <div className="fs-4 fw-bold text-primary">{indexState.document_count ?? 0}</div>
              <small className="text-muted">{indexState.tour_count ?? 0} tours đã index</small>
            </div>
          </div>
        </div>
        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-body">
              <div className="text-muted small text-uppercase">Embedding</div>
              <div className="fs-6 fw-bold text-dark text-truncate" title={indexState.embedding_model}>
                {indexState.embedding_provider || "unknown"}
              </div>
              <small className="text-muted">{indexState.retriever || "hybrid-faiss-bm25"}</small>
            </div>
          </div>
        </div>
        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-body">
              <div className="text-muted small text-uppercase">Tổng lượt hỏi</div>
              <div className="fs-4 fw-bold text-success">{metrics.requests_total ?? 0}</div>
              <small className="text-muted">Cache hits: {cacheHits}</small>
            </div>
          </div>
        </div>
        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-body">
              <div className="text-muted small text-uppercase">Ngoài danh mục</div>
              <div className="fs-4 fw-bold text-warning">{metrics.out_of_scope_total ?? 0}</div>
              <small className="text-muted">Fallback LLM: {metrics.openai_answer_fallback_total ?? 0}</small>
            </div>
          </div>
        </div>
        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-body">
              <div className="text-muted small text-uppercase">Độ trễ TB</div>
              <div className="fs-4 fw-bold text-info">{metrics.answer_latency_ms_avg ?? 0} ms</div>
              <small className="text-muted">Retrieve: {metrics.retrieve_latency_ms_avg ?? 0} ms</small>
            </div>
          </div>
        </div>
        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-body">
              <div className="text-muted small text-uppercase">Trạng thái LLM</div>
              <div className="mt-1">
                {hasApiKey && form.llm_provider !== "local_fallback" ? (
                  <span className="badge text-bg-success">API Key Sẵn Sàng</span>
                ) : (
                  <span className="badge text-bg-warning">Local Fallback</span>
                )}
              </div>
              <small className="text-muted d-block mt-1 text-truncate">
                OOS Model: {form.out_of_scope_model || form.chat_model}
              </small>
            </div>
          </div>
        </div>
      </div>

      <form onSubmit={handleSave}>
        <div className="row g-4">
          {/* 2. Out-of-Scope Configuration */}
          <div className="col-lg-6">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-header bg-white border-0 py-3">
                <h5 className="mb-0 fw-bold text-dark">
                  <i className="bi bi-signpost-split me-2 text-warning"></i>
                  Xử lý câu hỏi NGOÀI DANH MỤC (Out-of-Scope)
                </h5>
                <small className="text-muted">
                  Tùy chỉnh cách RAG phản hồi và Model sử dụng khi khách hỏi nội dung không nằm trong mục tour/dữ liệu.
                </small>
              </div>
              <div className="card-body">
                {/* Mode selector */}
                <label className="form-label fw-semibold">Chế độ xử lý câu hỏi ngoài mục</label>
                <div className="d-flex flex-column gap-2 mb-3">
                  {(oosModes.length
                    ? oosModes
                    : [
                        {
                          value: "strict",
                          label: "Strict — Chỉ trả lời dữ liệu trong danh mục",
                          description: "Từ chối lịch sự theo mẫu câu cài đặt khi câu hỏi không nằm trong dữ liệu.",
                        },
                        {
                          value: "general_travel",
                          label: "General Travel — Dùng Model riêng tư vấn du lịch mở rộng",
                          description: "Gọi Model Out-of-Scope giải đáp hữu ích, báo chưa có tour khớp và gợi ý tour nổi bật.",
                        },
                        {
                          value: "open_ai",
                          label: "Open AI — Dùng Model riêng trả lời linh hoạt mọi chủ đề",
                          description: "Cho phép Model Out-of-Scope trả lời tự nhiên theo System Prompt tùy chỉnh.",
                        },
                      ]
                  ).map((mode) => (
                    <label
                      key={mode.value}
                      className={`border rounded-3 p-2 px-3 d-flex align-items-start gap-2 cursor-pointer ${
                        form.out_of_scope_mode === mode.value
                          ? "border-primary bg-primary bg-opacity-10"
                          : "bg-light"
                      }`}
                      style={{ cursor: "pointer" }}
                    >
                      <input
                        type="radio"
                        className="form-check-input mt-1"
                        name="out_of_scope_mode"
                        checked={form.out_of_scope_mode === mode.value}
                        onChange={() => handleFieldChange("out_of_scope_mode", mode.value)}
                      />
                      <div>
                        <div className="fw-semibold small">{mode.label}</div>
                        <div className="text-muted" style={{ fontSize: "0.78rem" }}>
                          {mode.description}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>

                {/* OOS Model */}
                <div className="mb-3">
                  <label className="form-label fw-semibold">
                    Model riêng cho câu hỏi ngoài mục (<code>out_of_scope_model</code>)
                  </label>
                  <div className="input-group">
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Để trống để dùng chung Model chính..."
                      value={form.out_of_scope_model}
                      onChange={(e) => handleFieldChange("out_of_scope_model", e.target.value)}
                      disabled={form.out_of_scope_mode === "strict"}
                    />
                    <select
                      className="form-select"
                      style={{ maxWidth: "220px" }}
                      value={
                        SUGGESTED_OOS_MODELS.some((m) => m.value === form.out_of_scope_model)
                          ? form.out_of_scope_model
                          : "__custom__"
                      }
                      onChange={(e) => {
                        if (e.target.value !== "__custom__") {
                          handleFieldChange("out_of_scope_model", e.target.value);
                        }
                      }}
                      disabled={form.out_of_scope_mode === "strict"}
                    >
                      {SUGGESTED_OOS_MODELS.map((m) => (
                        <option key={m.label} value={m.value}>
                          {m.label}
                        </option>
                      ))}
                      {!SUGGESTED_OOS_MODELS.some((m) => m.value === form.out_of_scope_model) && (
                        <option value="__custom__">Model tùy chỉnh</option>
                      )}
                    </select>
                  </div>
                  <div className="form-text">
                    Ví dụ: dùng <code>gpt-4o-mini</code> cho truy xuất nhanh trong mục, và{" "}
                    <code>gpt-4o</code> cho câu hỏi tư vấn mở rộng ngoài mục.
                  </div>
                </div>

                {/* Similarity Threshold */}
                <div className="mb-3">
                  <div className="d-flex justify-content-between align-items-center">
                    <label className="form-label fw-semibold mb-1">
                      Ngưỡng nhận diện ngoài mục (<code>similarity_threshold</code>)
                    </label>
                    <span className="badge text-bg-primary">{form.similarity_threshold}</span>
                  </div>
                  <input
                    type="range"
                    className="form-range"
                    min="0.05"
                    max="0.80"
                    step="0.01"
                    value={form.similarity_threshold}
                    onChange={(e) => handleFieldChange("similarity_threshold", Number(e.target.value))}
                  />
                  <div className="form-text">
                    Điểm khớp tối đa thấp hơn ngưỡng này (hoặc không khớp từ khóa chủ đề) sẽ kích hoạt luồng xử lý ngoài danh mục.
                  </div>
                </div>

                <div className="row g-3 mb-3">
                  <div className="col-sm-6">
                    <label className="form-label fw-semibold small">
                      Temperature ngoài mục ({form.out_of_scope_temperature})
                    </label>
                    <input
                      type="range"
                      className="form-range"
                      min="0"
                      max="1.5"
                      step="0.05"
                      value={form.out_of_scope_temperature}
                      onChange={(e) =>
                        handleFieldChange("out_of_scope_temperature", Number(e.target.value))
                      }
                    />
                  </div>
                  <div className="col-sm-6">
                    <label className="form-label fw-semibold small">Max Tokens ngoài mục</label>
                    <input
                      type="number"
                      className="form-control"
                      min="50"
                      max="4096"
                      value={form.out_of_scope_max_tokens}
                      onChange={(e) =>
                        handleFieldChange("out_of_scope_max_tokens", Number(e.target.value))
                      }
                    />
                  </div>
                </div>

                <div className="form-check form-switch mb-3">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    id="suggestPopularSwitch"
                    checked={form.suggest_popular_tours_on_oos}
                    onChange={(e) =>
                      handleFieldChange("suggest_popular_tours_on_oos", e.target.checked)
                    }
                  />
                  <label className="form-check-label fw-semibold" htmlFor="suggestPopularSwitch">
                    Gợi ý kèm 3 tour nổi bật khi câu hỏi nằm ngoài danh mục
                  </label>
                </div>

                <div className="mb-3">
                  <label className="form-label fw-semibold small">
                    System Prompt cho câu hỏi ngoài mục
                  </label>
                  <textarea
                    className="form-control"
                    rows={3}
                    value={form.out_of_scope_system_prompt}
                    onChange={(e) =>
                      handleFieldChange("out_of_scope_system_prompt", e.target.value)
                    }
                  />
                </div>

                <div className="mb-0">
                  <label className="form-label fw-semibold small">
                    Câu trả lời mặc định (chế độ Strict / khi thiếu API Key)
                  </label>
                  <textarea
                    className="form-control"
                    rows={2}
                    value={form.out_of_scope_fallback_message}
                    onChange={(e) =>
                      handleFieldChange("out_of_scope_fallback_message", e.target.value)
                    }
                  />
                </div>
              </div>
            </div>
          </div>

          {/* 3. In-Scope Model & Retrieval Config */}
          <div className="col-lg-6">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-header bg-white border-0 py-3">
                <h5 className="mb-0 fw-bold text-dark">
                  <i className="bi bi-sliders me-2 text-primary"></i>
                  Model RAG Chính & Cấu hình Truy xuất (Retrieval)
                </h5>
                <small className="text-muted">
                  Thiết lập nhà cung cấp AI, Model trả lời trong danh mục và trọng số Hybrid Search (FAISS + BM25).
                </small>
              </div>
              <div className="card-body">
                <div className="row g-3 mb-3">
                  <div className="col-sm-5">
                    <label className="form-label fw-semibold small">Nhà cung cấp LLM</label>
                    <select
                      className="form-select"
                      value={form.llm_provider}
                      onChange={(e) => handleProviderChange(e.target.value)}
                    >
                      {Object.entries(providerPresets).length > 0 ? (
                        Object.entries(providerPresets).map(([key, item]) => (
                          <option key={key} value={key}>
                            {item.label}
                          </option>
                        ))
                      ) : (
                        <>
                          <option value="openai">OpenAI</option>
                          <option value="groq">Groq</option>
                          <option value="gemini">Google Gemini</option>
                          <option value="openrouter">OpenRouter</option>
                          <option value="custom">Custom Endpoint</option>
                          <option value="local_fallback">Local Fallback</option>
                        </>
                      )}
                    </select>
                  </div>

                  <div className="col-sm-7">
                    <label className="form-label fw-semibold small">
                      Model RAG Chính (<code>chat_model</code>)
                    </label>
                    <input
                      type="text"
                      list="in-scope-model-suggestions"
                      className="form-control"
                      value={form.chat_model}
                      onChange={(e) => handleFieldChange("chat_model", e.target.value)}
                      disabled={form.llm_provider === "local_fallback"}
                    />
                    <datalist id="in-scope-model-suggestions">
                      {(currentPreset.models || []).map((m) => (
                        <option key={m} value={m} />
                      ))}
                    </datalist>
                  </div>
                </div>

                <div className="mb-3">
                  <label className="form-label fw-semibold small">API Base URL</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="https://api.openai.com/v1"
                    value={form.openai_base_url}
                    onChange={(e) => handleFieldChange("openai_base_url", e.target.value)}
                    disabled={form.llm_provider === "local_fallback"}
                  />
                </div>

                <div className="mb-3">
                  <div className="d-flex justify-content-between align-items-center mb-1">
                    <label className="form-label fw-semibold small mb-0">
                      API Key{" "}
                      <span className={`badge ms-1 ${hasApiKey ? "text-bg-success" : "text-bg-secondary"}`}>
                        {hasApiKey ? "Đã lưu" : "Chưa có"}
                      </span>
                    </label>
                    {hasApiKey && (
                      <button
                        type="button"
                        className="btn btn-link btn-sm text-danger p-0 text-decoration-none"
                        onClick={handleClearApiKey}
                      >
                        Xóa Key
                      </button>
                    )}
                  </div>
                  <div className="input-group">
                    <input
                      type={showApiKey ? "text" : "password"}
                      className="form-control"
                      placeholder="Nhập API Key mới (để nguyên nếu không thay đổi)..."
                      value={form.openai_api_key}
                      onChange={(e) => handleFieldChange("openai_api_key", e.target.value)}
                      disabled={form.llm_provider === "local_fallback"}
                    />
                    <button
                      type="button"
                      className="btn btn-outline-secondary"
                      onClick={() => setShowApiKey((v) => !v)}
                    >
                      <i className={`bi ${showApiKey ? "bi-eye-slash" : "bi-eye"}`}></i>
                    </button>
                  </div>
                </div>

                <div className="row g-3 mb-3">
                  <div className="col-sm-4">
                    <label className="form-label fw-semibold small">
                      Temperature ({form.temperature})
                    </label>
                    <input
                      type="range"
                      className="form-range"
                      min="0"
                      max="1.5"
                      step="0.05"
                      value={form.temperature}
                      onChange={(e) => handleFieldChange("temperature", Number(e.target.value))}
                    />
                  </div>
                  <div className="col-sm-4">
                    <label className="form-label fw-semibold small">Max Tokens</label>
                    <input
                      type="number"
                      className="form-control"
                      min="50"
                      max="4096"
                      value={form.max_tokens}
                      onChange={(e) => handleFieldChange("max_tokens", Number(e.target.value))}
                    />
                  </div>
                  <div className="col-sm-4">
                    <label className="form-label fw-semibold small">Top-K mặc định</label>
                    <input
                      type="number"
                      className="form-control"
                      min="1"
                      max="8"
                      value={form.top_k_default}
                      onChange={(e) => handleFieldChange("top_k_default", Number(e.target.value))}
                    />
                  </div>
                </div>

                <div className="mb-3">
                  <div className="d-flex justify-content-between align-items-center">
                    <label className="form-label fw-semibold small mb-1">
                      Trọng số Hybrid Search: Dense ({form.hybrid_dense_weight}) / BM25 ({form.hybrid_lexical_weight})
                    </label>
                  </div>
                  <input
                    type="range"
                    className="form-range"
                    min="0"
                    max="1"
                    step="0.02"
                    value={form.hybrid_dense_weight}
                    onChange={(e) => handleDenseWeightChange(e.target.value)}
                  />
                </div>

                <div className="row g-3 mb-3">
                  <div className="col-sm-6">
                    <label className="form-label fw-semibold small">Embedding Model (OpenAI)</label>
                    <input
                      type="text"
                      className="form-control"
                      value={form.embedding_model}
                      onChange={(e) => handleFieldChange("embedding_model", e.target.value)}
                    />
                  </div>
                  <div className="col-sm-6">
                    <label className="form-label fw-semibold small">Cross-Encoder Reranker Model</label>
                    <input
                      type="text"
                      className="form-control"
                      value={form.reranker_model}
                      onChange={(e) => handleFieldChange("reranker_model", e.target.value)}
                      disabled={!form.reranker_enabled}
                    />
                  </div>
                </div>

                <div className="d-flex flex-wrap gap-4 mb-3">
                  <div className="form-check form-switch">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="kbEnabledSwitch"
                      checked={form.knowledge_base_enabled}
                      onChange={(e) =>
                        handleFieldChange("knowledge_base_enabled", e.target.checked)
                      }
                    />
                    <label className="form-check-label small fw-semibold" htmlFor="kbEnabledSwitch">
                      Bật Knowledge Base Du lịch VN (cần Rebuild Index)
                    </label>
                  </div>
                  <div className="form-check form-switch">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="rerankerSwitch"
                      checked={form.reranker_enabled}
                      onChange={(e) => handleFieldChange("reranker_enabled", e.target.checked)}
                    />
                    <label className="form-check-label small fw-semibold" htmlFor="rerankerSwitch">
                      Bật Cross-Encoder Reranker
                    </label>
                  </div>
                </div>

                <div className="mb-3">
                  <label className="form-label fw-semibold small">
                    Hướng dẫn bổ sung cho System Prompt chính (tùy chọn)
                  </label>
                  <textarea
                    className="form-control"
                    rows={2}
                    placeholder="VD: Luôn nhắc khách kiểm tra lịch khởi hành trước khi đặt vé..."
                    value={form.custom_system_prompt_addon}
                    onChange={(e) =>
                      handleFieldChange("custom_system_prompt_addon", e.target.value)
                    }
                  />
                </div>

                <div className="d-flex justify-content-end">
                  <button type="submit" className="btn btn-primary px-4" disabled={saving}>
                    <i className="bi bi-save me-2"></i>
                    {saving ? "Đang lưu..." : "Lưu toàn bộ cấu hình"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </form>

      {/* 4. Live RAG Playground */}
      <div className="card border-0 shadow-sm mt-4">
        <div className="card-header bg-white border-0 py-3 d-flex flex-wrap justify-content-between align-items-center gap-2">
          <div>
            <h5 className="mb-0 fw-bold text-dark">
              <i className="bi bi-terminal me-2 text-success"></i>
              Phòng thử nghiệm RAG (Live Test Playground)
            </h5>
            <small className="text-muted">
              Kiểm tra trực tiếp khả năng phân loại Trong mục / Ngoài mục và Model phản hồi.
            </small>
          </div>
          <div className="form-check form-switch mb-0">
            <input
              className="form-check-input"
              type="checkbox"
              id="overrideTestSwitch"
              checked={useFormOverride}
              onChange={(e) => setUseFormOverride(e.target.checked)}
            />
            <label className="form-check-label small fw-semibold" htmlFor="overrideTestSwitch">
              Thử bằng cấu hình đang nhập trên form (chưa cần Lưu)
            </label>
          </div>
        </div>

        <div className="card-body">
          <div className="row g-2 mb-3">
            <div className="col-md-7">
              <input
                type="text"
                className="form-control"
                placeholder="Nhập câu hỏi thử nghiệm..."
                value={testQuery}
                onChange={(e) => setTestQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleRunTest();
                  }
                }}
              />
            </div>
            <div className="col-md-3">
              <input
                type="number"
                className="form-control"
                placeholder="Focus Tour ID (tuỳ chọn)"
                value={testFocusTourId}
                onChange={(e) => setTestFocusTourId(e.target.value)}
              />
            </div>
            <div className="col-md-2 d-grid">
              <button
                type="button"
                className="btn btn-success"
                onClick={() => handleRunTest()}
                disabled={testing || !testQuery.trim()}
              >
                <i className="bi bi-play-fill me-1"></i>
                {testing ? "Đang chạy..." : "Test ngay"}
              </button>
            </div>
          </div>

          {/* Sample buttons */}
          <div className="d-flex flex-wrap gap-2 mb-3 align-items-center">
            <span className="small fw-semibold text-success me-1">Mẫu Trong mục:</span>
            {IN_SCOPE_SAMPLES.map((q) => (
              <button
                key={q}
                type="button"
                className="btn btn-sm btn-outline-success rounded-pill"
                onClick={() => handleRunTest(q)}
                disabled={testing}
              >
                {q}
              </button>
            ))}
          </div>
          <div className="d-flex flex-wrap gap-2 mb-4 align-items-center">
            <span className="small fw-semibold text-warning me-1">Mẫu Ngoài mục:</span>
            {OUT_OF_SCOPE_SAMPLES.map((q) => (
              <button
                key={q}
                type="button"
                className="btn btn-sm btn-outline-warning text-dark rounded-pill"
                onClick={() => handleRunTest(q)}
                disabled={testing}
              >
                {q}
              </button>
            ))}
          </div>

          {testResult && (
            <div className="border rounded-3 p-3 bg-light">
              <div className="d-flex flex-wrap gap-2 mb-3">
                <span
                  className={`badge ${
                    testResult.is_out_of_scope ? "text-bg-warning" : "text-bg-success"
                  }`}
                >
                  {testResult.is_out_of_scope
                    ? "NGOÀI DANH MỤC (Out-of-Scope)"
                    : "TRONG DANH MỤC (In-Scope)"}
                </span>
                {testResult.out_of_scope_reason && (
                  <span className="badge text-bg-secondary">
                    Lý do: {testResult.out_of_scope_reason}
                  </span>
                )}
                {testResult.out_of_scope_mode && (
                  <span className="badge text-bg-info">
                    Chế độ OOS: {testResult.out_of_scope_mode}
                  </span>
                )}
                <span className="badge text-bg-primary">
                  Model: {testResult.model_used || "N/A"}
                </span>
                <span className="badge text-bg-dark">
                  Max Score: {testResult.max_score ?? 0}
                </span>
                {testResult.latency_ms != null && (
                  <span className="badge text-bg-light border text-dark">
                    {testResult.latency_ms} ms
                  </span>
                )}
              </div>

              <div className="bg-white border rounded-3 p-3 mb-3" style={{ whiteSpace: "pre-wrap" }}>
                {testResult.answer}
              </div>

              <div>
                <div className="small fw-semibold text-muted mb-2">
                  Sources trả về ({(testResult.sources || []).length}):
                </div>
                {(testResult.sources || []).length === 0 ? (
                  <div className="text-muted small">Không có source nào được đính kèm.</div>
                ) : (
                  <div className="row g-2">
                    {testResult.sources.map((src, idx) => (
                      <div key={`${src.tour_id}-${src.chunk_type}-${idx}`} className="col-md-6">
                        <div className="bg-white border rounded-2 p-2 h-100 small">
                          <div className="d-flex justify-content-between align-items-start gap-2">
                            <strong>
                              [{src.tour_id > 0 ? `Tour #${src.tour_id}` : "Knowledge"}] {src.title}
                            </strong>
                            <span className="badge text-bg-light border text-dark">
                              score: {src.score}
                            </span>
                          </div>
                          <div className="text-muted" style={{ fontSize: "0.75rem" }}>
                            chunk: {src.chunk_type} · {src.location || src.category_name}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
