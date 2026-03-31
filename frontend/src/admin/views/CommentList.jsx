import React from "react";
import CommentTable from "../components/tables/CommentTable";

export default function CommentList() {
  return (
    <div className="container mt-4">
      <h3 className="mb-4 text-primary">
        <i className="bi bi-chat-left-text me-2"></i> Quản lý đánh giá
      </h3>
      <CommentTable />
    </div>
  );
}
