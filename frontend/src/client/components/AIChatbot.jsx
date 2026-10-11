// src/client/components/AIChatbot.jsx
import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { chatbotService } from "../services/chatbotService";
import "../../styles/AIChatbot.css";

const QUICK_PROMPTS = [
  "Tour biển hè Đà Nẵng - Nha Trang",
  "Gợi ý tour Đà Lạt dưới 5 triệu",
  "Tour nghỉ dưỡng cho gia đình",
  "Tour văn hóa tâm linh miền Bắc",
];

export default function AIChatbot() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      sender: "bot",
      text: "Xin chào! 👋 Tôi là Trợ lý AI Du Lịch (RAG). Tôi có thể tư vấn các tour hấp dẫn, so sánh mức giá, thời lượng và gợi ý điểm đến phù hợp nhất với bạn. Bạn đang muốn đi du lịch ở đâu?",
      sources: [],
      timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      inputRef.current?.focus();
    }
  }, [isOpen, messages, isLoading]);

  const handleSendMessage = async (queryText) => {
    const textToSend = (queryText || inputText).trim();
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
      const userId = user?.UserID || user?.user_id || null;
      const res = await chatbotService.chat({
        query: textToSend,
        userId: userId,
        topK: 4,
      });

      const botMsg = {
        id: `b_${Date.now()}`,
        sender: "bot",
        text: res.answer || "Dưới đây là một số tour phù hợp với yêu cầu của bạn:",
        sources: Array.isArray(res.sources) ? res.sources : [],
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
    setMessages([
      {
        id: "welcome_reset",
        sender: "bot",
        text: "Cuộc trò chuyện đã được làm mới. Bạn cần hỗ trợ tư vấn tour nào?",
        sources: [],
        timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
  };

  return (
    <div className="ai-chatbot-widget">
      {/* Floating Button */}
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

      {/* Chat Window */}
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
                  Tư vấn RAG thông minh 24/7
                </div>
              </div>
            </div>

            <div className="ai-header-actions">
              <button
                className="ai-btn-action"
                onClick={handleClearChat}
                title="Làm mới cuộc trò chuyện"
              >
                <i className="bi bi-arrow-counterclockwise"></i>
              </button>
              <button
                className="ai-btn-action"
                onClick={() => setIsOpen(false)}
                title="Đóng chat"
              >
                <i className="bi bi-x-lg"></i>
              </button>
            </div>
          </div>

          {/* Messages Body */}
          <div className="ai-chat-body">
            {messages.map((m) => (
              <div key={m.id} className={`ai-message ${m.sender}`}>
                <div className="ai-bubble">
                  {m.text}

                  {/* Render Sources / Gợi ý tour */}
                  {m.sources && m.sources.length > 0 && (
                    <div className="ai-sources-container">
                      <div className="ai-sources-title">
                        <i className="bi bi-geo-alt-fill text-danger"></i> Tour liên quan được gợi ý:
                      </div>
                      {m.sources.map((src, idx) => (
                        <div
                          key={`${src.tour_id}-${idx}`}
                          className="ai-source-card"
                          onClick={() => {
                            navigate(`/tours/${src.tour_id}`);
                            setIsOpen(false);
                          }}
                        >
                          <div className="ai-source-header">
                            <span className="ai-source-name">{src.title}</span>
                            {src.price != null && (
                              <span className="ai-source-price">
                                {Number(src.price).toLocaleString("vi-VN")} đ
                              </span>
                            )}
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
                      ))}
                    </div>
                  )}
                </div>
                <span className="ai-msg-time">{m.timestamp}</span>
              </div>
            ))}

            {/* Quick Prompts (hiển thị khi chỉ có tin nhắn chào) */}
            {messages.length === 1 && !isLoading && (
              <div className="ai-quick-prompts">
                {QUICK_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="ai-chip-prompt"
                    onClick={() => handleSendMessage(prompt)}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}

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

          {/* Footer Input */}
          <div className="ai-chat-footer">
            <input
              ref={inputRef}
              type="text"
              className="ai-chat-input"
              placeholder="Hỏi về tour, giá vé, lịch trình..."
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
        </div>
      )}
    </div>
  );
}
