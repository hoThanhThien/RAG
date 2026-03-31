import { useEffect, useState, useRef } from "react";
import { supportApi } from "../services/supportService";
import { Link } from "react-router-dom";
import { connectSupportWS } from "../../client/services/ws";

export default function SupportList() {
  const [threads, setThreads] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const wsRef = useRef(null);

  useEffect(() => {
    const fetchThreads = async () => {
      try {
        const res = await supportApi.getAllThreads();
        setThreads(res.data || []);
      } catch (err) {
        console.error("Lỗi khi tải danh sách thread:", err);
      }
    };
    fetchThreads();

    // 🌐 Kết nối WebSocket để nhận tin nhắn mới realtime
    const token = localStorage.getItem("access_token");
    const ws = connectSupportWS(token);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("✅ SupportList WebSocket connected");
      // Admin tự động join room "support:admin" khi connect
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log("📨 SupportList received:", msg);
        
        if (msg.type === "support:new_message") {
          // Update thread list khi có tin nhắn mới
          fetchThreads(); // Reload để có last_content mới
        }
      } catch (error) {
        console.error("Lỗi xử lý WebSocket message:", error);
      }
    };

    ws.onclose = () => {
      console.log("❌ SupportList WebSocket disconnected");
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // ✅ Lọc theo nội dung gần nhất, user_id, thread_id
  const filteredThreads = threads.filter((t) =>
    `${t.thread_id} ${t.user_id} ${t.last_content}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mt-4">
      {/* Tiêu đề + tìm kiếm */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3 className="fw-bold text-primary mb-0">
          <i className="bi bi-chat-dots me-2"></i>
          Hỗ trợ khách hàng
        </h3>
        <div className="input-group w-25">
          <span className="input-group-text bg-white">
            <i className="bi bi-search text-secondary"></i>
          </span>
          <input
            type="text"
            className="form-control"
            placeholder="Tìm theo user ID, nội dung..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Bảng hiển thị */}
      <div className="table-responsive shadow-sm rounded border">
        <table className="table table-bordered table-hover align-middle mb-0">
          <thead className="bg-dark text-white text-center">
            <tr>
              <th style={{ width: "10%" }}>Thread ID</th>
              <th style={{ width: "10%" }}>User ID</th>
              <th style={{ width: "35%" }}>Nội dung gần nhất</th>
              <th style={{ width: "25%" }}>Thời gian</th>
              <th style={{ width: "20%" }}>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {filteredThreads.map((t) => (
              <tr key={t.thread_id}>
                <td className="text-center fw-semibold">{t.thread_id}</td>
                <td className="text-center">{t.user_id}</td>
                <td className="text-center text-muted">
                  {t.last_content || "--"}
                </td>
                <td className="text-center text-nowrap">
                  {t.last_time
                    ? new Date(t.last_time).toLocaleString()
                    : "--"}
                </td>
                <td className="text-center">
                  <Link
                    to={`/admin/support/${t.thread_id}`}
                    className="btn btn-outline-primary btn-sm d-inline-flex align-items-center gap-1 px-3"
                  >
                    <i className="bi bi-reply-fill"></i> Trả lời
                  </Link>
                </td>
              </tr>
            ))}
            {filteredThreads.length === 0 && (
              <tr>
                <td colSpan="5" className="text-center py-4 text-muted">
                  Không có yêu cầu hỗ trợ nào.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
