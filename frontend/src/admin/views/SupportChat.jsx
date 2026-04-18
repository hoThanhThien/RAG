import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { supportApi } from "../services/supportService";
import { connectSupportWS } from "../../client/services/ws.js";

function parseJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch {
    return null;
  }
}

export default function SupportChat() {
  const { thread_id } = useParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [adminName, setAdminName] = useState("Admin");
  const bottomRef = useRef(null);
  const wsRef = useRef(null);
  const textareaRef = useRef(null);

  // Get admin name from token
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const payload = parseJwt(token);
    if (payload?.full_name) {
      setAdminName(payload.full_name);
    }
  }, []);

  // Load tin nhắn ban đầu
  useEffect(() => {
    const fetchMessages = async () => {
      try {
        setIsLoading(true);
        const res = await supportApi.getMessages(thread_id);
        setMessages(res.data || []);
        
        // Get user info
        try {
          const threadInfo = await supportApi.getThreadInfo(thread_id);
          setUserInfo(threadInfo.data);
        } catch (err) {
          console.error("Không thể lấy thông tin thread:", err);
        }
      } catch (error) {
        console.error("Lỗi khi load tin nhắn:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchMessages();
  }, [thread_id]);

  // Kết nối WebSocket
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const ws = connectSupportWS(token);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("✅ WebSocket connected (Admin)");
      setIsConnected(true);
    };

    ws.onclose = () => {
      console.log("WebSocket closed (Admin)");
      setIsConnected(false);
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
      setIsConnected(false);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log("📨 Admin received WebSocket message:", msg);
        
        if (
          msg.type === "support:new_message" &&
          msg.message?.thread_id == thread_id
        ) {
          setMessages((prev) => {
            const existsById = prev.some(
              (m) => String(m.id) === String(msg.message.id)
            );
            if (existsById) return prev;

            const optimisticIndex = prev.findIndex(
              (m) =>
                m.pending &&
                m.is_admin &&
                m.content === msg.message.content &&
                Number(m.thread_id) === Number(msg.message.thread_id)
            );

            if (optimisticIndex !== -1) {
              const next = [...prev];
              next[optimisticIndex] = { ...msg.message, pending: false };
              return next;
            }

            return [...prev, { ...msg.message, pending: false }];
          });
        }
      } catch (e) {
        console.error("WS message parse error", e);
      }
    };

    return () => {
      ws.close();
    };
  }, [thread_id]);

  // Gửi tin nhắn
  const send = async () => {
    if (!text.trim() || isLoading || isSending) return;

    const content = text.trim();
    const tempId = `temp_${Date.now()}`;

    const optimisticMessage = {
      id: tempId,
      content,
      is_admin: true,
      full_name: adminName,
      thread_id: Number(thread_id),
      created_at: new Date().toISOString(),
      pending: true,
    };

    setIsSending(true);
    setMessages((prev) => [...prev, optimisticMessage]);
    setText("");

    try {
      const response = await supportApi.postMessage(thread_id, content);
      setMessages((prev) => {
        const existingIndex = prev.findIndex(
          (m) => String(m.id) === String(response.data.id)
        );

        if (existingIndex !== -1) {
          const next = [...prev];
          next[existingIndex] = {
            ...next[existingIndex],
            ...response.data,
            pending: false,
          };
          return next;
        }

        const tempIndex = prev.findIndex((m) => m.id === tempId);
        if (tempIndex !== -1) {
          const next = [...prev];
          next[tempIndex] = { ...response.data, pending: false };
          return next;
        }

        return [...prev, { ...response.data, pending: false }];
      });
    } catch (error) {
      console.error("Lỗi khi gửi tin nhắn:", error);
      setMessages((prev) => prev.filter((m) => m.id !== tempId));
      setText(content);
      alert("Không thể gửi tin nhắn. Vui lòng thử lại!");
    } finally {
      setIsSending(false);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [text]);

  // Tự động cuộn xuống khi có tin nhắn mới
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Format time
  const formatTime = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: '2-digit'
      });
    } catch {
      return "";
    }
  };

  return (
    <div className="container-fluid h-100 d-flex flex-column" style={{ maxHeight: '100vh', padding: 0 }}>
      {/* Header */}
      <div className="bg-white border-bottom shadow-sm" style={{ padding: '16px 24px' }}>
        <div className="d-flex align-items-center justify-content-between">
          <div className="d-flex align-items-center gap-3">
            <button
              className="btn btn-outline-primary rounded-circle d-flex align-items-center justify-content-center"
              onClick={() => navigate("/admin/support")}
              style={{ width: '40px', height: '40px', padding: 0 }}
              title="Quay lại"
            >
              <i className="bi bi-arrow-left"></i>
            </button>
            
            <div>
              <h5 className="mb-0 fw-bold">
                <i className="bi bi-chat-dots me-2 text-primary"></i>
                Hỗ trợ khách hàng
              </h5>
              <small className="text-muted">
                {userInfo ? (
                  <>
                    <i className="bi bi-person me-1"></i>
                    {userInfo.user_name || 'Người dùng'}
                    {userInfo.user_email && <span className="ms-2">({userInfo.user_email})</span>}
                  </>
                ) : (
                  `Thread #${thread_id}`
                )}
              </small>
            </div>
          </div>
          
          <div className="d-flex align-items-center gap-3">
            <span className={`badge ${isConnected ? 'bg-success' : 'bg-danger'}`}>
              <i className={`bi ${isConnected ? 'bi-wifi' : 'bi-wifi-off'} me-1`}></i>
              {isConnected ? 'Đang kết nối' : 'Mất kết nối'}
            </span>
          </div>
        </div>
      </div>

      {/* Chat body */}
      <div 
        className="flex-grow-1 overflow-auto px-4 py-3" 
        style={{ 
          background: 'linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%)',
          minHeight: 0
        }}
      >
        {isLoading ? (
          <div className="d-flex justify-content-center align-items-center h-100">
            <div className="text-center">
              <div className="spinner-border text-primary mb-3" role="status">
                <span className="visually-hidden">Đang tải...</span>
              </div>
              <p className="text-muted">Đang tải tin nhắn...</p>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="d-flex justify-content-center align-items-center h-100">
            <div className="text-center text-muted">
              <i className="bi bi-chat-square-text" style={{ fontSize: '64px', opacity: 0.3 }}></i>
              <p className="mt-3 fw-bold">Chưa có tin nhắn</p>
              <small>Bắt đầu trò chuyện với khách hàng</small>
            </div>
          </div>
        ) : (
          <div className="d-flex flex-column gap-3">
            {messages.map((m, i) => {
              const showAvatar = i === 0 || messages[i - 1]?.is_admin !== m.is_admin;
              const isAdmin = m.is_admin;
              
              return (
                <div 
                  key={m.id || i} 
                  className={`d-flex ${isAdmin ? 'justify-content-end' : 'justify-content-start'} align-items-end gap-2`}
                  style={{ opacity: m.pending ? 0.6 : 1 }}
                >
                  {!isAdmin && showAvatar && (
                    <div 
                      className="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                      style={{
                        width: '36px',
                        height: '36px',
                        background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                        color: 'white',
                        fontSize: '18px'
                      }}
                    >
                      <i className="bi bi-person-fill"></i>
                    </div>
                  )}
                  
                  <div style={{ maxWidth: '70%' }}>
                    {showAvatar && (
                      <div className={`small fw-bold mb-1 ${isAdmin ? 'text-end' : ''}`} style={{ opacity: 0.7 }}>
                        {m.full_name || (isAdmin ? adminName : "Khách hàng")}
                      </div>
                    )}
                    
                    <div
                      className={`p-3 rounded-3 ${
                        isAdmin 
                          ? 'text-white' 
                          : 'bg-white border'
                      }`}
                      style={{
                        background: isAdmin 
                          ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                          : 'white',
                        boxShadow: isAdmin 
                          ? '0 4px 12px rgba(102, 126, 234, 0.3)'
                          : '0 2px 8px rgba(0, 0, 0, 0.08)',
                        borderBottomRightRadius: isAdmin ? '4px' : undefined,
                        borderBottomLeftRadius: !isAdmin ? '4px' : undefined,
                        wordWrap: 'break-word'
                      }}
                    >
                      <div style={{ whiteSpace: 'pre-wrap' }}>{m.content}</div>
                      <div 
                        className={`small mt-2 d-flex align-items-center gap-1 ${isAdmin ? 'justify-content-end' : ''}`}
                        style={{ opacity: 0.7, fontSize: '11px' }}
                      >
                        {formatTime(m.created_at)}
                        {m.pending && <i className="bi bi-clock-history ms-1"></i>}
                      </div>
                    </div>
                  </div>
                  
                  {isAdmin && showAvatar && (
                    <div 
                      className="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
                      style={{
                        width: '36px',
                        height: '36px',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: 'white',
                        fontSize: '18px'
                      }}
                    >
                      <i className="bi bi-person-badge-fill"></i>
                    </div>
                  )}
                </div>
              );
            })}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-white border-top shadow-sm" style={{ padding: '16px 24px' }}>
        <div className="d-flex gap-2 align-items-end">
          <textarea
            ref={textareaRef}
            className="form-control"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder="Nhập tin nhắn... (Shift + Enter để xuống dòng)"
            disabled={isLoading || isSending}
            rows="1"
            style={{
              resize: 'none',
              minHeight: '44px',
              maxHeight: '120px',
              overflow: 'auto'
            }}
          />
          <button 
            className="btn btn-primary rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
            onClick={send}
            disabled={!text.trim() || isLoading || isSending}
            title="Gửi tin nhắn"
            style={{
              width: '44px',
              height: '44px',
              padding: 0
            }}
          >
            <i className="bi bi-send-fill"></i>
          </button>
        </div>
        
        {!isConnected && (
          <div className="alert alert-warning mt-2 mb-0 py-2 px-3 small d-flex align-items-center gap-2">
            <i className="bi bi-exclamation-triangle-fill"></i>
            <span>Realtime đang gián đoạn, nhưng bạn vẫn có thể gửi tin nhắn. Hệ thống sẽ lưu lại.</span>
          </div>
        )}
      </div>
    </div>
  );
}
