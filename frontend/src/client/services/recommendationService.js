import { api, toAbsoluteUrl } from "./api";

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

  async getFeaturedDestinations({
    limit = 5,
    activeOnly = false,
    minPrice,
    categoryId,
    maxLocationLength,
  } = {}) {
    const res = await api.get("/destinations/featured", {
      params: {
        limit,
        active_only: activeOnly,
        min_price: minPrice,
        category_id: categoryId,
        max_location_length: maxLocationLength,
      },
    });

    return {
      ...res.data,
      items: (res.data?.items || []).map((item) => ({
        ...item,
        image: item?.image ? toAbsoluteUrl(item.image) : "/no-image.png",
      })),
    };
  },
};
