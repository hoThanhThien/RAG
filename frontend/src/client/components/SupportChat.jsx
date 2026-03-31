import { useEffect, useRef, useState } from "react";
import { supportApi } from "../services/supportService";
import { connectSupportWS } from "../services/ws";
import "../../styles/SupportChat.css";

export default function SupportChat() {
  const [open, setOpen] = useState(false);
  const [threadId, setThreadId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [userId, setUserId] = useState(null);
  const [userFullName, setUserFullName] = useState("Bạn");
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [typing, setTyping] = useState(false);
  const [showThreadList, setShowThreadList] = useState(false);
  const [threads, setThreads] = useState([]);
  const wsRef = useRef(null);
  const bottomRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  // 🔐 Giải mã token để lấy userId và tên
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        setUserId(parseInt(payload.sub));
        setUserFullName(payload.full_name || "Bạn");
      } catch (error) {
        console.error("Lỗi giải mã token:", error);
      }
    }
  }, []);

  // 🚀 Lấy thread và lịch sử
  useEffect(() => {
    const boot = async () => {
      // Check if user is logged in
      const token = localStorage.getItem("access_token");
      if (!token) {
        console.warn("⚠️ User not logged in, chat disabled");
        return;
      }
      
      try {
        setIsLoading(true);
        const { data } = await supportApi.openOrCreateThread();
        console.log("✅ Thread opened/created:", data.thread_id);
        setThreadId(data.thread_id);
        const hist = await supportApi.getMessages(data.thread_id);
        setMessages(hist.data || []);
        // Load all threads
        await loadThreads();
      } catch (error) {
        console.error("❌ Lỗi khi khởi tạo chat:", error);
        console.error("Error details:", error.response?.data);
      } finally {
        setIsLoading(false);
      }
    };
    boot();
  }, []);

  // 📋 Load danh sách threads
  const loadThreads = async () => {
    try {
      const { data } = await supportApi.getMyThreads();
      setThreads(data || []);
    } catch (error) {
      console.error("Lỗi khi tải danh sách threads:", error);
    }
  };

  // 🆕 Tạo thread mới
  const createNewThread = async () => {
    try {
      console.log("🔄 Creating new thread...");
      const response = await supportApi.createNewThread();
      console.log("✅ New thread created:", response.data);
      
      setThreadId(response.data.thread_id);
      setMessages([]);
      await loadThreads();
      setShowThreadList(false);
      alert("Đã tạo cuộc trò chuyện mới!");
    } catch (error) {
      console.error("❌ Lỗi khi tạo thread mới:", error);
      console.error("Error response:", error.response?.data);
      console.error("Error status:", error.response?.status);
      
      // Check if user is logged in
      const token = localStorage.getItem("access_token");
      if (!token) {
        alert("Bạn cần đăng nhập để tạo cuộc trò chuyện mới!");
        return;
      }
      
      alert(`Không thể tạo cuộc trò chuyện mới: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 🗑️ Xóa thread
  const deleteThread = async (threadIdToDelete) => {
    if (!confirm("Bạn có chắc muốn xóa cuộc trò chuyện này?")) return;
    
    try {
      await supportApi.deleteThread(threadIdToDelete);
      await loadThreads();
      
      // Nếu xóa thread đang mở, chuyển sang thread khác hoặc tạo mới
      if (threadIdToDelete === threadId) {
        const { data } = await supportApi.openOrCreateThread();
        setThreadId(data.thread_id);
        const hist = await supportApi.getMessages(data.thread_id);
        setMessages(hist.data || []);
      }
      
      alert("Đã xóa cuộc trò chuyện!");
    } catch (error) {
      console.error("Lỗi khi xóa thread:", error);
      alert("Không thể xóa cuộc trò chuyện");
    }
  };

  // 🔄 Chuyển sang thread khác
  const switchThread = async (newThreadId) => {
    try {
      setIsLoading(true);
      setThreadId(newThreadId);
      const hist = await supportApi.getMessages(newThreadId);
      setMessages(hist.data || []);
      setShowThreadList(false);
    } catch (error) {
      console.error("Lỗi khi chuyển thread:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // 🌐 Kết nối WebSocket khi có threadId
  useEffect(() => {
    if (!threadId) return;

    const token = localStorage.getItem("access_token");
    const ws = connectSupportWS(token);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      console.log("✅ WebSocket connected");
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log("❌ WebSocket disconnected");
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setIsConnected(false);
    };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        
        if (msg.type === "support:new_message" && msg.thread_id === threadId) {
          // Bỏ qua tin nhắn của chính mình (đã xử lý qua optimistic update + API)
          if (msg.message.sender_id === userId && !msg.message.is_admin) {
            console.log("⏭️ Skipping own message from WebSocket");
            return;
          }
          
          setMessages((prev) => {
            // Tránh duplicate message - check cả id và content
            const exists = prev.some(m => {
              // Check by ID (từ DB)
              if (m.id === msg.message.id) return true;
              // Check by content + sender (cho optimistic messages)
              if (m.content === msg.message.content && 
                  m.sender_id === msg.message.sender_id &&
                  Math.abs(new Date(m.created_at) - new Date(msg.message.created_at)) < 5000) {
                return true;
              }
              return false;
            });
            
            if (exists) {
              console.log("⏭️ Duplicate message detected, skipping");
              return prev;
            }
            
            console.log("✅ Adding new message from WebSocket:", msg.message.id);
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
          
          // Nếu là tin nhắn từ admin, ẩn typing indicator
          if (msg.message.is_admin) {
            setTyping(false);
          }
        }
        
        // Typing indicator
        if (msg.type === "support:typing" && msg.thread_id === threadId && msg.is_admin) {
          setTyping(true);
          clearTimeout(typingTimeoutRef.current);
          typingTimeoutRef.current = setTimeout(() => setTyping(false), 3000);
        }
      } catch (error) {
        console.error("Lỗi xử lý message:", error);
      }
    };

    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      ws.close();
    };
  }, [threadId]);

  // 📤 Gửi tin nhắn
  const send = async () => {
    if (!text.trim() || !threadId || isLoading) return;
    
    const content = text.trim();
    const tempId = `temp_${Date.now()}`;
    
    // Optimistic update
    const optimisticMessage = {
      id: tempId,
      sender_id: userId,
      is_admin: false,
      full_name: userFullName,
      content,
      created_at: new Date().toISOString(),
      pending: true,
    };
    
    setMessages(prev => [...prev, optimisticMessage]);
    setText("");
    
    try {
      const response = await supportApi.postMessage(threadId, content);
      // Replace optimistic message with real message from API
      setMessages(prev => 
        prev.map(m => m.id === tempId ? { ...response.data, pending: false } : m)
      );
    } catch (error) {
      console.error("Lỗi khi gửi tin nhắn:", error);
      // Remove failed message
      setMessages(prev => prev.filter(m => m.id !== tempId));
      setText(content); // Restore text
      alert("Không thể gửi tin nhắn. Vui lòng thử lại!");
    }
  };

  // 🔽 Scroll xuống khi có tin nhắn mới
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Format time
  const formatTime = (dateString) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diff = now - date;
      const minutes = Math.floor(diff / 60000);
      
      if (minutes < 1) return "Vừa xong";
      if (minutes < 60) return `${minutes} phút trước`;
      if (minutes < 1440) return `${Math.floor(minutes / 60)} giờ trước`;
      
      return date.toLocaleDateString('vi-VN', { 
        day: '2-digit', 
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return "";
    }
  };

  return (
    <div className="chat-widget">
      {!open && userId && (
        <div className="chat-toggle" onClick={() => setOpen(true)} title="Hỗ trợ trực tuyến">
          <i className="bi bi-chat-dots-fill"></i>
          {!isConnected && (
            <span className="connection-status offline"></span>
          )}
        </div>
      )}
      
      {open && userId && (
        <div className="chat-box">
          <div className="chat-header">
            <div className="d-flex align-items-center justify-content-between w-100">
              <div className="d-flex align-items-center gap-2">
                <button 
                  className="btn btn-sm btn-link p-0 text-white"
                  onClick={() => setShowThreadList(!showThreadList)}
                  title="Danh sách cuộc trò chuyện"
                >
                  <i className="bi bi-list" style={{ fontSize: '24px' }}></i>
                </button>
                <i className="bi bi-headset"></i>
                <div>
                  <div className="fw-bold">Hỗ trợ khách hàng</div>
                  <small className="status-text">
                    {isConnected ? (
                      <>
                        <span className="status-dot online"></span>
                        Đang hoạt động
                      </>
                    ) : (
                      <>
                        <span className="status-dot offline"></span>
                        Đang kết nối...
                      </>
                    )}
                  </small>
                </div>
              </div>
              <button 
                className="btn-close-chat" 
                onClick={() => setOpen(false)}
                title="Đóng"
              >
                <i className="bi bi-x-lg"></i>
              </button>
            </div>
          </div>
          
          {/* Thread List Sidebar */}
          {showThreadList && (
            <div className="thread-list-sidebar">
              <div className="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom">
                <h6 className="m-0">Cuộc trò chuyện</h6>
                <button 
                  className="btn btn-sm btn-primary"
                  onClick={createNewThread}
                  title="Tạo cuộc trò chuyện mới"
                >
                  <i className="bi bi-plus-lg"></i> Tạo mới
                </button>
              </div>
              
              <div className="thread-list">
                {threads.length === 0 ? (
                  <p className="text-muted small text-center">Chưa có cuộc trò chuyện nào</p>
                ) : (
                  threads.map(thread => (
                    <div 
                      key={thread.thread_id}
                      className={`thread-item ${thread.thread_id === threadId ? 'active' : ''}`}
                      onClick={() => switchThread(thread.thread_id)}
                    >
                      <div className="d-flex justify-content-between align-items-start">
                        <div className="flex-grow-1" style={{ minWidth: 0 }}>
                          <div className="thread-preview text-truncate">
                            {thread.last_content || "Chưa có tin nhắn"}
                          </div>
                          <small className="text-muted">
                            {thread.message_count} tin nhắn • {formatTime(thread.last_time || thread.created_at)}
                          </small>
                        </div>
                        <button
                          className="btn btn-sm btn-link text-danger p-0 ms-2"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteThread(thread.thread_id);
                          }}
                          title="Xóa cuộc trò chuyện"
                        >
                          <i className="bi bi-trash"></i>
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
          
          <div className="chat-body">
            {isLoading ? (
              <div className="text-center py-4">
                <div className="spinner-border spinner-border-sm text-primary" role="status">
                  <span className="visually-hidden">Đang tải...</span>
                </div>
                <p className="text-muted small mt-2">Đang tải tin nhắn...</p>
              </div>
            ) : messages.length === 0 ? (
              <div className="empty-state">
                <i className="bi bi-chat-square-text"></i>
                <p>Chưa có tin nhắn</p>
                <small>Gửi tin nhắn để bắt đầu trò chuyện với chúng tôi</small>
              </div>
            ) : (
              <>
                {messages.map((m, i) => {
                  const isUser = m.sender_id === userId || !m.is_admin;
                  const showAvatar = i === 0 || messages[i - 1]?.is_admin !== m.is_admin;
                  
                  return (
                    <div 
                      key={m.id || i} 
                      className={`msg ${isUser ? "user" : "support"} ${m.pending ? "pending" : ""}`}
                    >
                      {showAvatar && (
                        <div className="avatar">
                          {isUser ? (
                            <i className="bi bi-person-circle"></i>
                          ) : (
                            <i className="bi bi-headset"></i>
                          )}
                        </div>
                      )}
                      <div className="bubble">
                        {showAvatar && (
                          <div className="msg-sender">{m.full_name || (isUser ? userFullName : "Hỗ trợ")}</div>
                        )}
                        <div className="msg-content">{m.content}</div>
                        <div className="msg-time">
                          {formatTime(m.created_at)}
                          {m.pending && <i className="bi bi-clock-history ms-1"></i>}
                        </div>
                      </div>
                    </div>
                  );
                })}
                {typing && (
                  <div className="msg support">
                    <div className="avatar">
                      <i className="bi bi-headset"></i>
                    </div>
                    <div className="bubble typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={bottomRef} />
          </div>
          
          <div className="chat-footer">
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder="Nhập tin nhắn... (Enter để gửi)"
              disabled={isLoading || !isConnected}
            />
            <button 
              onClick={send} 
              disabled={!text.trim() || isLoading || !isConnected}
              title="Gửi tin nhắn"
            >
              <i className="bi bi-send-fill"></i>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
