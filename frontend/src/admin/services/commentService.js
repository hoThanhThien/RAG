import { api } from "../../client/services/api"; // nếu bạn đã có instance axios ở đây

export const getAllComments = async ({ page = 1, page_size = 50, q = "" }) => {
  const res = await api.get("/comments", {
    params: { page, page_size, q },
  });
  return res.data;
};

export const deleteComment = async (id) => {
  const res = await api.delete(`/comments/${id}`);
  return res.data;
};
