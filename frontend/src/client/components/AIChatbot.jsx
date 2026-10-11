import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toAbsoluteUrl } from "../services/api";
import { chatbotService } from "../services/chatbotService";
import { supportApi } from "../services/supportService";
import { connectSupportWS } from "../services/ws";
import { useAuth } from "../context/AuthContext";
import "../../styles/AIChatbot.css";

const QUICK_PROMPTS = [
  "🌸 Tour Đà Lạt ngàn hoa",
  "🏖️ Tour Nha Trang biển đảo",
  "🌉 Tour Đà Nẵng - Hội An",
  "🏔️ Tour Sa Pa săn mây",
];

const INITIAL_AI_MESSAGE = {
  id: "welcome_init",
  sender: "bot",
  text: "Xin chào quý khách! 👋 Em là Trợ lý AI Du Lịch. Em có thể hỗ trợ bạn tìm kiếm tour du lịch, gợi ý lịch trình, giá vé và tư vấn hành trình phù hợp nhất.\n\nBạn muốn khám phá địa điểm nào hôm nay?",
  sources: [],
  timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
};

export default function AIChatbot() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("ai"); // 'ai' hoặc 'support'

  // ==========================================
  // STATE CHO AI CHATBOT (RAG)
  // ==========================================
  const [messages, setMessages] = useState([INITIAL_AI_MESSAGE]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // ==========================================
  // STATE CHO HỖ TRỢ TRỰC TUYẾN (WEBSOCKET / CSKH)
  // ==========================================
  const [supportThreadId, setSupportThreadId] = useState(null);
  const [supportMessages, setSupportMessages] = useState([]);
  const [supportInput, setSupportInput] = useState("");
  const [isSupportConnected, setIsSupportConnected] = useState(false);
  const [isSupportLoading, setIsSupportLoading] = useState(false);
  const [isSupportSending, setIsSupportSending] = useState(false);
  const [supportTyping, setSupportTyping] = useState(false);
  const [supportThreads, setSupportThreads] = useState([]);
  const [showThreadDrawer, setShowThreadDrawer] = useState(false);

  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const userIdRef = useRef(null);

  const userId = user?.UserID || user?.user_id || null;
  const userFullName = user?.FullName || user?.full_name || "Bạn";

  useEffect(() => {
    userIdRef.current = userId;
  }, [userId]);

  // Cuộn xuống tin nhắn mới nhất
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [isOpen, messages, supportMessages, isLoading, supportTyping, activeTab]);

  // ==========================================
  // KHỞI TẠO VÀ QUẢN LÝ CSKH KHI ĐÃ ĐĂNG NHẬP
  // ==========================================
  useEffect(() => {
    if (!userId) {
      setSupportThreadId(null);
      setSupportMessages([]);
      setIsSupportConnected(false);
      return;
    }

    const initSupportThread = async () => {
      try {
        setIsSupportLoading(true);
        const { data } = await supportApi.openOrCreateThread();
        setSupportThreadId(data.thread_id);
        const hist = await supportApi.getMessages(data.thread_id);
        setSupportMessages(hist.data || []);
        const threadsRes = await supportApi.getMyThreads();
        setSupportThreads(threadsRes.data || []);
      } catch (err) {
        console.error("Lỗi khởi tạo CSKH thread:", err);
      } finally {
        setIsSupportLoading(false);
      }
    };

    initSupportThread();
  }, [userId]);

  // WebSocket cho CSKH
  useEffect(() => {
    if (!userId || !supportThreadId) return;

    const token = localStorage.getItem("access_token");
    const ws = connectSupportWS(token);
    wsRef.current = ws;

    ws.onopen = () => setIsSupportConnected(true);
    ws.onclose = () => setIsSupportConnected(false);
    ws.onerror = () => setIsSupportConnected(false);

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === "support:new_message" && msg.thread_id === supportThreadId) {
          const currentUid = userIdRef.current;
          if (
            msg.message.sender_id != null &&
            currentUid != null &&
            Number(msg.message.sender_id) === Number(currentUid) &&
            !msg.message.is_admin
          ) {
            return;
          }

          setSupportMessages((prev) => {
            const exists = prev.some(
              (m) =>
                m.id === msg.message.id ||
                (m.content === msg.message.content &&
                  m.sender_id === msg.message.sender_id &&
                  Math.abs(new Date(m.created_at) - new Date(msg.message.created_at)) < 5000)
            );
            if (exists) return prev;
            return [
              ...prev,
              {
                id: msg.message.id,
                sender_id: msg.message.sender_id,
                is_admin: msg.message.is_admin,
                full_name: msg.message.full_name,
                content: msg.message.content,
                created_at: msg.message.created_at || new Date().toISOString(),
              },
            ];
          });

          if (msg.message.is_admin) setSupportTyping(false);
        }

        if (msg.type === "support:typing" && msg.thread_id === supportThreadId && msg.is_admin) {
          setSupportTyping(true);
          clearTimeout(typingTimeoutRef.current);
          typingTimeoutRef.current = setTimeout(() => setSupportTyping(false), 3000);
        }
      } catch (err) {
        console.error("Lỗi WS CSKH:", err);
      }
    };

    return () => {
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
      ws.close();
    };
  }, [supportThreadId, userId]);

  // ==========================================
  // XỬ LÝ GỬI TIN NHẮN AI (RAG)
  // ==========================================
  const handleSendMessage = async (queryText) => {
    const textToSend = (typeof queryText === "string" ? queryText : inputText).trim();
    if (!textToSend || isLoading) return;

    const userMsg = {
      id: `u_${Date.now()}`,
      sender: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText("");
    setIsLoading(true);

    try {
      const res = await chatbotService.chat({
        query: textToSend,
        userId: userId,
        topK: 4,
      });

      // Lọc tour trùng lặp theo tour_id
      const seenIds = new Set();
      const uniqueSources = [];
      (res.sources || []).forEach((src) => {
        if (src.tour_id && !seenIds.has(src.tour_id)) {
          seenIds.add(src.tour_id);
          uniqueSources.push(src);
        }
      });

      const botMsg = {
        id: `b_${Date.now()}`,
        sender: "bot",
        text: res.answer || "Dưới đây là một số tour phù hợp với yêu cầu của bạn:",
        sources: uniqueSources,
        timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error("Lỗi khi kết nối Chatbot RAG:", err);
      const errorMsg = {
        id: `err_${Date.now()}`,
        sender: "bot",
        text: "Rất tiếc, hệ thống tư vấn AI đang bận hoặc có lỗi kết nối. Bạn vui lòng thử lại sau giây lát!",
        sources: [],
        timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    if (confirm("Làm mới lại cuộc trò chuyện với Trợ lý AI?")) {
      setMessages([INITIAL_AI_MESSAGE]);
    }
  };

  // ==========================================
  // XỬ LÝ GỬI TIN NHẮN CSKH (LIVE SUPPORT)
  // ==========================================
  const handleSendSupportMessage = async () => {
    if (!supportInput.trim() || !supportThreadId || isSupportSending) return;

    const content = supportInput.trim();
    const tempId = `temp_${Date.now()}`;
    const optimisticMessage = {
      id: tempId,
      sender_id: userId,
      is_admin: false,
      full_name: userFullName,
      content,
      created_at: new Date().toISOString(),
      pending: true,
    };

    setIsSupportSending(true);
    setSupportMessages((prev) => [...prev, optimisticMessage]);
    setSupportInput("");

    try {
      const response = await supportApi.postMessage(supportThreadId, content);
      setSupportMessages((prev) => {
        const withoutTemp = prev.filter((m) => m.id !== tempId);
        const realId = String(response.data.id);
        const existingIndex = withoutTemp.findIndex((m) => String(m.id) === realId);
        if (existingIndex !== -1) {
          const next = [...withoutTemp];
          next[existingIndex] = { ...next[existingIndex], ...response.data, pending: false };
          return next;
        }
        return [...withoutTemp, { ...response.data, pending: false }];
      });
    } catch (error) {
      console.error("Lỗi gửi tin nhắn CSKH:", error);
      setSupportMessages((prev) => prev.filter((m) => m.id !== tempId));
      setSupportInput(content);
      alert("Không thể gửi tin nhắn hỗ trợ. Vui lòng thử lại!");
    } finally {
      setIsSupportSending(false);
    }
  };

  return (
    <div className="ai-chatbot-widget">
      {/* Nút tròn nổi chính diện - Giữ nguyên 100% vẻ ngoài từ thiết kế người dùng */}
      {!isOpen && (
        <button
          className="ai-chatbot-toggle"
          onClick={() => setIsOpen(true)}
          title="Tư vấn tour cùng AI Assistant"
          aria-label="Mở Trợ lý AI Du Lịch"
        >
          <i className="bi bi-robot"></i>
          <span className="ai-badge">AI Tour</span>
        </button>
      )}

      {/* Cửa sổ hội thoại hiện đại */}
      {isOpen && (
        <div className="ai-chatbot-window">
          {/* Header */}
          <div className="ai-chat-header">
            <div className="ai-header-info">
              <div className="ai-header-icon">
                <i className="bi bi-stars"></i>
              </div>
              <div>
                <div className="ai-header-title">Trợ Lý AI Du Lịch</div>
                <div className="ai-header-subtitle">
                  <span className="ai-online-dot"></span>
                  {activeTab === "ai"
                    ? "Tư vấn RAG thông minh 24/7"
                    : isSupportConnected
                    ? "Nhân viên trực tuyến"
                    : "Đang kết nối..."}
                </div>
              </div>
            </div>

            <div className="ai-header-actions">
              {activeTab === "ai" && (
                <button
                  className="ai-btn-action"
                  onClick={handleClearChat}
                  title="Làm mới cuộc trò chuyện"
                >
                  <i className="bi bi-arrow-counterclockwise"></i>
                </button>
              )}
              <button
                className="ai-btn-action"
                onClick={() => setIsOpen(false)}
                title="Đóng chat"
              >
                <i className="bi bi-x-lg"></i>
              </button>
            </div>
          </div>

          {/* Thanh chuyển đổi tab thông minh (khi người dùng đã đăng nhập) */}
          {userId ? (
            <div className="ai-chat-tabs">
              <button
                type="button"
                className={`ai-tab-btn ${activeTab === "ai" ? "active" : ""}`}
                onClick={() => setActiveTab("ai")}
              >
                <i className="bi bi-robot"></i> Trợ lý AI Tour
              </button>
              <button
                type="button"
                className={`ai-tab-btn ${activeTab === "support" ? "active" : ""}`}
                onClick={() => setActiveTab("support")}
              >
                <i className="bi bi-headset"></i> Hỗ trợ nhân viên
              </button>
            </div>
          ) : (
            <div className="ai-guest-banner">
              <span>💡 Chat với AI miễn phí. Đăng nhập để gặp nhân viên hỗ trợ.</span>
              <button
                type="button"
                onClick={() => {
                  navigate("/auth");
                  setIsOpen(false);
                }}
              >
                Đăng nhập
              </button>
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB 1: TRỢ LÝ AI RAG                                     */}
          {/* ========================================================= */}
          {activeTab === "ai" && (
            <>
              <div className="ai-chat-body">
                {messages.map((m) => (
                  <div key={m.id} className={`ai-message ${m.sender}`}>
                    <div className="ai-bubble">
                      <div style={{ whiteSpace: "pre-wrap" }}>{m.text}</div>

                      {/* Danh sách thẻ Tour được gợi ý bởi RAG */}
                      {m.sources && m.sources.length > 0 && (
                        <div className="ai-sources-container">
                          <div className="ai-sources-title">
                            <i className="bi bi-geo-alt-fill text-danger"></i> Gợi ý tour phù hợp:
                          </div>
                          {m.sources.map((src, idx) => {
                            const imageUrl = src.image_url
                              ? toAbsoluteUrl(src.image_url)
                              : "https://placehold.co/600x400?text=Tour";

                            return (
                              <div
                                key={`${src.tour_id}-${idx}`}
                                className="ai-source-card"
                                onClick={() => {
                                  navigate(`/tour-detail/${src.tour_id}`);
                                  setIsOpen(false);
                                }}
                                title={`Xem chi tiết ${src.title}`}
                              >
                                <img
                                  src={imageUrl}
                                  alt={src.title}
                                  className="ai-source-card-img"
                                  onError={(e) => {
                                    e.currentTarget.onerror = null;
                                    e.currentTarget.src =
                                      "https://placehold.co/600x400?text=Tour";
                                  }}
                                />
                                <div className="ai-source-card-content">
                                  <div className="ai-source-name">{src.title}</div>
                                  <div className="ai-source-price">
                                    {src.price != null && Number(src.price) > 0
                                      ? `${Number(src.price).toLocaleString("vi-VN")} đ`
                                      : "Liên hệ"}
                                  </div>
                                  <div className="ai-source-meta">
                                    {src.location && (
                                      <span>
                                        <i className="bi bi-geo-alt"></i> {src.location}
                                      </span>
                                    )}
                                    {src.category_name && (
                                      <span>
                                        <i className="bi bi-tag"></i> {src.category_name}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                    <span className="ai-msg-time">{m.timestamp}</span>
                  </div>
                ))}

                {/* Typing Indicator */}
                {isLoading && (
                  <div className="ai-message bot">
                    <div className="ai-typing-indicator">
                      <span className="ai-typing-dot"></span>
                      <span className="ai-typing-dot"></span>
                      <span className="ai-typing-dot"></span>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Gợi ý câu hỏi nhanh (Quick Prompts) */}
              <div className="ai-quick-prompts">
                {QUICK_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="ai-chip-prompt"
                    onClick={() => handleSendMessage(prompt)}
                    disabled={isLoading}
                  >
                    {prompt}
                  </button>
                ))}
              </div>

              {/* Ô nhập tin nhắn AI */}
              <div className="ai-chat-footer">
                <input
                  ref={inputRef}
                  type="text"
                  className="ai-chat-input"
                  placeholder="Hỏi về tour, giá vé, lịch trình (VD: Tour Đà Lạt)..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  disabled={isLoading}
                />
                <button
                  className="ai-btn-send"
                  onClick={() => handleSendMessage()}
                  disabled={!inputText.trim() || isLoading}
                  title="Gửi"
                >
                  <i className="bi bi-send-fill"></i>
                </button>
              </div>
            </>
          )}

          {/* ========================================================= */}
          {/* TAB 2: HỖ TRỢ TRỰC TIẾP CSKH (CHO NGƯỜI ĐÃ ĐĂNG NHẬP)     */}
          {/* ========================================================= */}
          {activeTab === "support" && (
            <>
              <div className="ai-chat-body">
                {isSupportLoading ? (
                  <div className="text-center py-4">
                    <div className="spinner-border spinner-border-sm text-primary" role="status">
                      <span className="visually-hidden">Đang tải...</span>
                    </div>
                    <p className="text-muted small mt-2">Đang tải lịch sử hỗ trợ...</p>
                  </div>
                ) : supportMessages.length === 0 ? (
                  <div className="text-center py-5 text-muted small">
                    <i className="bi bi-chat-heart" style={{ fontSize: "32px", opacity: 0.5 }}></i>
                    <p className="mt-2 mb-0">Chưa có tin nhắn hỗ trợ.</p>
                    <small>Gửi câu hỏi để kết nối với tư vấn viên thật.</small>
                  </div>
                ) : (
                  supportMessages.map((m, idx) => {
                    const isUser = m.sender_id === userId || !m.is_admin;
                    return (
                      <div
                        key={m.id || idx}
                        className={`ai-message ${isUser ? "user" : "support"}`}
                      >
                        <div className="ai-msg-sender">
                          {m.full_name || (isUser ? userFullName : "Tư vấn viên")}
                        </div>
                        <div className="ai-bubble" style={{ whiteSpace: "pre-wrap" }}>
                          {m.content}
                        </div>
                        <span className="ai-msg-time">
                          {m.created_at
                            ? new Date(m.created_at).toLocaleTimeString("vi-VN", {
                                hour: "2-digit",
                                minute: "2-digit",
                              })
                            : ""}
                        </span>
                      </div>
                    );
                  })
                )}

                {supportTyping && (
                  <div className="ai-message support">
                    <div className="ai-typing-indicator">
                      <span className="ai-typing-dot"></span>
                      <span className="ai-typing-dot"></span>
                      <span className="ai-typing-dot"></span>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Ô nhập tin nhắn hỗ trợ CSKH */}
              <div className="ai-chat-footer">
                <input
                  type="text"
                  className="ai-chat-input"
                  placeholder="Nhắn tin cho tư vấn viên hỗ trợ..."
                  value={supportInput}
                  onChange={(e) => setSupportInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendSupportMessage();
                    }
                  }}
                  disabled={isSupportSending}
                />
                <button
                  className="ai-btn-send"
                  onClick={handleSendSupportMessage}
                  disabled={!supportInput.trim() || isSupportSending}
                  title="Gửi"
                >
                  <i className="bi bi-send-fill"></i>
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
