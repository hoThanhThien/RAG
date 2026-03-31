import React from "react";

export default function DiscountTable({ discounts, onEdit, onDelete }) {
  return (
    <table className="table table-bordered table-striped">
      <thead className="table-dark">
        <tr>
          <th>ID</th>
          <th>Code</th>
          <th>Description</th>
          <th>Amount</th>
          <th>Is %</th>
          <th>Start</th>
          <th>End</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {discounts.map((d) => (
          <tr key={d.discount_id}>
            <td>{d.discount_id}</td>
            <td>{d.code}</td>
            <td>{d.description}</td>
            <td>{d.discount_amount}</td>
            <td>{d.is_percent ? "Yes" : "No"}</td>
            <td>{d.start_date}</td>
            <td>{d.end_date}</td>
            <td>
              <button className="btn btn-sm btn-primary me-2" onClick={() => onEdit(d)}>
                Sửa
              </button>
              <button className="btn btn-sm btn-danger" onClick={() => onDelete(d.discount_id)}>
                Xoá
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
