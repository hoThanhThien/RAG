import { api } from "./api";

export const recommendationService = {
  async recommend({ userId, prompt, topK = 5 }) {
    const res = await api.get("/recommend", {
      params: {
        user_id: userId,
        prompt,
        top_k: topK,
      },
    });
    return res.data;
  },

  async getSegment(userId) {
    const res = await api.get(`/segments/${userId}`);
    return res.data;
  },
};
