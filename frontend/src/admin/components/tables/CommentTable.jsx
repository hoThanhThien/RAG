import React, { useEffect, useState } from "react";
import { getAllComments, deleteComment } from "../../services/commentService";

export default function CommentTable() {
  const [comments, setComments] = useState([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchData();
  }, [search]);

  const fetchData = async () => {
    const res = await getAllComments({ q: search });
    setComments(res?.items || []);
  };

  const handleDelete = async (id) => {
    if (window.confirm("Bạn có chắc muốn xoá đánh giá này không?")) {
      await deleteComment(id);
      fetchData();
    }
  };

  return (
    <>
      <div className="d-flex mb-3">
        <input
          className="form-control me-2"
          placeholder="Tìm theo tên người dùng hoặc tour"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button className="btn btn-outline-secondary" onClick={fetchData}>
          Tìm
        </button>
      </div>

      <div className="table-responsive">
        <table className="table table-bordered table-hover">
          <thead className="table-dark text-center">
            <tr>
              <th>STT</th>
              <th>Người dùng</th>
              <th>Tour</th>
              <th>Số sao</th>
              <th>Nội dung</th>
              <th>Ngày tạo</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {comments.map((cmt, idx) => (
              <tr key={cmt.comment_id}>
                <td className="text-center">{idx + 1}</td>
                <td>{cmt.user_name}</td>
                <td>{cmt.tour_title}</td>
                <td className="text-center">{cmt.rating || "-"}</td>
                <td>{cmt.content}</td>
                <td>{cmt.created_at}</td>
                <td className="text-center">
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => handleDelete(cmt.comment_id)}
                  >
                    Xoá
                  </button>
                </td>
              </tr>
            ))}
            {comments.length === 0 && (
              <tr>
                <td colSpan={7} className="text-center text-muted">
                  Không có đánh giá nào.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
