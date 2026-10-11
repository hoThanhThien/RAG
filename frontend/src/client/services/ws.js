import { getAuthToken } from "./api";

/**
 * Lấy WebSocket URL từ biến môi trường hoặc tự tính từ API URL
 * Tự động đồng bộ giữa 127.0.0.1 và localhost
 */
export function getWsBaseUrl() {
  if (typeof window !== "undefined") {
    const { hostname, protocol } = window.location;
    if (hostname === "127.0.0.1" || hostname === "localhost") {
      const wsProto = protocol === "https:" ? "wss:" : "ws:";
      return `${wsProto}//${hostname}:8000`;
    }
  }

  // Ưu tiên dùng VITE_WS_URL nếu có
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL;
  }
  
  // Fallback: Tự tính từ VITE_API_URL
  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  return apiUrl.replace(/^http/, "ws");
}

/**
 * Kết nối WebSocket cho Support Chat
 */
export function connectSupportWS(token = null) {
  const effectiveToken = token || getAuthToken();
  const wsHost = getWsBaseUrl();
  const url = effectiveToken ? `${wsHost}/ws/support?token=${effectiveToken}` : `${wsHost}/ws/support`;

  console.log("🔌 Connecting to Support WebSocket:", url);

  const ws = new WebSocket(url);
  ws.onopen = () => console.log("✅ WS support connected");
  ws.onclose = () => console.log("❌ WS support closed");
  ws.onerror = (e) => console.error("⚠️ WS support error", e);
  return ws;
}

/**
 * Kết nối WebSocket với auto-reconnect (advanced)
 */
export function connectSupportWSWithRetry(token, options = {}) {
  const {
    onOpen,
    onClose,
    onError,
    onMessage,
    maxRetries = 5,
    retryDelay = 3000
  } = options;

  let ws = null;
  let retryCount = 0;
  let isManualClose = false;

  const connect = () => {
    const wsHost = getWsBaseUrl();
    const url = token ? `${wsHost}/ws/support?token=${token}` : `${wsHost}/ws/support`;

    console.log("🔌 Connecting to Support WebSocket");

    ws = new WebSocket(url);
    
    ws.onopen = () => {
      console.log("✅ WS support connected");
      retryCount = 0;
      onOpen?.();
    };
    
    ws.onclose = (event) => {
      console.log(`❌ WS support closed (code: ${event.code})`);
      onClose?.(event);
      
      if (!isManualClose && retryCount < maxRetries) {
        retryCount++;
        const delay = retryDelay * retryCount;
        console.log(`🔄 Reconnecting in ${delay/1000}s... (attempt ${retryCount}/${maxRetries})`);
        setTimeout(connect, delay);
      }
    };
    
    ws.onerror = (e) => {
      console.error("⚠️ WS support error", e);
      onError?.(e);
    };

    ws.onmessage = (event) => {
      onMessage?.(event);
    };

    return ws;
  };

  ws = connect();

  return {
    get ws() { return ws; },
    send: (data) => ws?.readyState === WebSocket.OPEN && ws.send(typeof data === 'string' ? data : JSON.stringify(data)),
    close: () => {
      isManualClose = true;
      ws?.close();
    }
  };
}

/**
 * Kết nối WebSocket cho Admin Dashboard realtime updates
 */
export function connectAdminDashboardWS(token = null) {
  const effectiveToken = token || getAuthToken();
  const wsHost = getWsBaseUrl();
  const url = effectiveToken ? `${wsHost}/ws/admin/dashboard?token=${effectiveToken}` : `${wsHost}/ws/admin/dashboard`;

  const ws = new WebSocket(url);
  ws.onopen = () => console.log("✅ WS dashboard connected");
  ws.onclose = () => console.log("❌ WS dashboard closed");
  ws.onerror = (e) => console.error("⚠️ WS dashboard error", e);
  return ws;
}

/**
 * Kết nối WebSocket cho Tour realtime updates
 */
export function connectTourWS(tourId) {
  const wsHost = getWsBaseUrl();
  const url = `${wsHost}/ws/tour/${tourId}`;
  
  console.log(`🔌 Connecting to Tour WebSocket: ${url}`);

  const ws = new WebSocket(url);
  ws.onopen = () => console.log(`✅ WS tour ${tourId} connected`);
  ws.onclose = () => console.log(`❌ WS tour ${tourId} closed`);
  ws.onerror = (e) => console.error(`⚠️ WS tour ${tourId} error`, e);
  return ws;
}
