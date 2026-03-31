// 📁 services/supportService.js
import { api } from "../../client/services/api";

export const supportApi = {
  openOrCreateThread: () => api.post("/support/thread"),
  getMessages: (threadId) => api.get(`/support/threads/${threadId}/messages`),
  postMessage: (threadId, content) => api.post(`/support/threads/${threadId}/messages`, { content }),
  getAllThreads: () => api.get("/support/threads"),         // ✅ Lấy tất cả thread (cho admin)
  getThreadInfo: (threadId) => api.get(`/support/threads/${threadId}`),

};
