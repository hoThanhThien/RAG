import { api } from "./api";

export const supportApi = {
  openOrCreateThread: () => api.post("/support/threads/open-or-create"),
  getMessages: (threadId) => api.get(`/support/threads/${threadId}/messages`),
  postMessage: (threadId, content) =>
    api.post(`/support/threads/${threadId}/messages`, { content }),
  // 🆕 Thread management
  getMyThreads: () => api.get("/support/threads/my/all"),
  createNewThread: () => api.post("/support/threads/new"),
  deleteThread: (threadId) => api.delete(`/support/threads/${threadId}`),
};

