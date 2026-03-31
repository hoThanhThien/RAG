export function connectSupportWS(token) {
  // Xác định xem đang ở production (hosting) hay development (local)
  const isProd = import.meta.env.PROD;

  // Quyết định URL máy chủ WebSocket
  const wsHost = isProd
    ? 'wss://52.64.184.203:8000' //  URL khi chạy trên HOSTING
    : 'ws://127.0.0.1:8000';   //  URL khi chạy ở LOCAL

  const url = `${wsHost}/ws/support?token=${token}`;
  
  console.log(`Connecting to WS at: ${url}`); // Thêm log để debug

  const ws = new WebSocket(url);
  ws.onopen = () => console.log("WS support connected");
  ws.onclose = () => console.log("WS support closed");
  ws.onerror = (e) => console.error("WS support error", e);
  return ws;
}
