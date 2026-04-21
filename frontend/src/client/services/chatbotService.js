import { api } from "./api";

export const chatbotService = {
  async chat({ query, userId = null, topK = 4, focusTourId = null }) {
    const response = await api.post("/chat", {
      query,
      user_id: userId,
      top_k: topK,
      focus_tour_id: focusTourId,
    });
    return response.data;
  },
};

export async function askTourChatbot(query, userId) {
  const result = await chatbotService.chat({ query, userId, topK: 4 });
  return result.answer;
}

// Example usage:
// const result = await chatbotService.chat({
//   query: "Tôi muốn tour biển giá tốt cho gia đình",
//   userId: 12,
//   topK: 4,
// });
// console.log(result.answer, result.sources);
