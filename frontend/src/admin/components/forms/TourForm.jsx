import React, { useEffect, useState } from "react";
import { api, toAbsoluteUrl } from "../../../client/services/api";
import {
  addTourPhoto,
  deleteTourPhoto,
  getTourPhotos,
  updateTourPhoto,
} from "../../services/photoService";

const todayString = () => new Date().toISOString().split("T")[0];
const formatDate = (value) => (value ? String(value).slice(0, 10) : "");
const buildEmptyPhoto = (isPrimary = false) => ({
  key: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
  caption: "",
  image_url: "",
  upload_date: todayString(),
  is_primary: isPrimary,
  image: null,
});

const buildInitialForm = (data = {}) => {
  const safeData = data || {};

  return {
    title: safeData.title || "",
    location: safeData.location || "",
    description: safeData.description || "",
    capacity: safeData.capacity ?? "",
    price: safeData.price ?? "",
    start_date: formatDate(safeData.start_date),
    end_date: formatDate(safeData.end_date),
    status: safeData.status || "Available",
    category_id: safeData.category_id ? String(safeData.category_id) : "",
  };
};

export default function TourForm({ onSubmit = () => {}, initialData = {}, onCancel }) {
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState(buildInitialForm(initialData));
  const [showPhotoForm, setShowPhotoForm] = useState(false);
  const [existingPhotos, setExistingPhotos] = useState([]);
  const [newPhotos, setNewPhotos] = useState([]);
  const [removedPhotoIds, setRemovedPhotoIds] = useState([]);
  const [saving, setSaving] = useState(false);
  const [loadingPhotos, setLoadingPhotos] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const res = await api.get("/categories");
        setCategories(Array.isArray(res.data?.items) ? res.data.items : Array.isArray(res.data) ? res.data : []);
      } catch (err) {
        console.error("❌ Lỗi tải danh mục:", err);
      }
    };
    fetchCategories();
  }, []);

  useEffect(() => {
    setForm(buildInitialForm(initialData));
    setRemovedPhotoIds([]);
    setNewPhotos([]);

    const loadPhotos = async () => {
      if (!initialData?.tour_id) {
        setExistingPhotos([]);
        setShowPhotoForm(false);
        return;
      }

      try {
        setLoadingPhotos(true);
        setShowPhotoForm(true);
        const res = await getTourPhotos(initialData.tour_id);
        setExistingPhotos(
          (res.data || []).map((photo) => ({
            photo_id: photo.photo_id,
            caption: photo.caption || "",
            image_url: photo.image_url || "",
            upload_date: formatDate(photo.upload_date) || todayString(),
            is_primary: !!photo.is_primary,
            image: null,
          }))
        );
      } catch (err) {
        console.error("❌ Lỗi tải ảnh tour:", err);
        setExistingPhotos([]);
      } finally {
        setLoadingPhotos(false);
      }
    };

    loadPhotos();
  }, [initialData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const setPrimaryPhoto = (type, id) => {
    setExistingPhotos((prev) =>
      prev.map((photo) => ({
        ...photo,
        is_primary: type === "existing" ? photo.photo_id === id : false,
      }))
    );
    setNewPhotos((prev) =>
      prev.map((photo) => ({
        ...photo,
        is_primary: type === "new" ? photo.key === id : false,
      }))
    );
  };

  const handleExistingPhotoChange = (photoId, field, value) => {
    if (field === "is_primary" && value) {
      setPrimaryPhoto("existing", photoId);
      return;
    }

    setExistingPhotos((prev) =>
      prev.map((photo) =>
        photo.photo_id === photoId ? { ...photo, [field]: value } : photo
      )
    );
  };

  const handleNewPhotoChange = (key, field, value) => {
    if (field === "is_primary" && value) {
      setPrimaryPhoto("new", key);
      return;
    }

    setNewPhotos((prev) =>
      prev.map((photo) => (photo.key === key ? { ...photo, [field]: value } : photo))
    );
  };

  const addPhotoRow = () => {
    setShowPhotoForm(true);
    setNewPhotos((prev) => [
      ...prev,
      buildEmptyPhoto(existingPhotos.length === 0 && prev.length === 0),
    ]);
  };

  const removeExistingPhoto = (photoId) => {
    setRemovedPhotoIds((prev) => [...prev, photoId]);
    setExistingPhotos((prev) => prev.filter((photo) => photo.photo_id !== photoId));
  };

  const removeNewPhoto = (key) => {
    setNewPhotos((prev) => prev.filter((photo) => photo.key !== key));
  };

  const uploadImage = async (file) => {
    if (!file) return "";
    const formData = new FormData();
    formData.append("file", file);
    const uploadRes = await api.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return uploadRes.data.image_url;
  };

  const getPreviewUrl = (photo) => {
    if (photo?.image) return URL.createObjectURL(photo.image);
    if (photo?.image_url) return toAbsoluteUrl(photo.image_url);
    return "";
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setErrorMessage("");

    try {
      let tour_id = initialData?.tour_id;
      const payload = {
        title: form.title,
        location: form.location,
        description: form.description,
        capacity: parseInt(form.capacity, 10),
        price: parseFloat(form.price),
        start_date: form.start_date,
        end_date: form.end_date,
        status: form.status,
        category_id: parseInt(form.category_id, 10),
      };

      if (tour_id) {
        await api.put(`/tours/${tour_id}`, payload);
      } else {
        const res = await api.post("/tours/", payload);
        tour_id = res.data.tour_id;
      }

      let normalizedExisting = [...existingPhotos];
      let normalizedNew = newPhotos.filter((photo) => photo.image || photo.image_url);
      const hasPrimary = [...normalizedExisting, ...normalizedNew].some((photo) => photo.is_primary);

      if (!hasPrimary) {
        if (normalizedExisting.length > 0) {
          normalizedExisting[0] = { ...normalizedExisting[0], is_primary: true };
        } else if (normalizedNew.length > 0) {
          normalizedNew[0] = { ...normalizedNew[0], is_primary: true };
        }
      }

      for (const photoId of removedPhotoIds) {
        await deleteTourPhoto(photoId);
      }

      for (const photo of normalizedExisting) {
        const uploadedUrl = photo.image ? await uploadImage(photo.image) : "";
        await updateTourPhoto(photo.photo_id, {
          caption: photo.caption || form.title,
          image_url: uploadedUrl || photo.image_url,
          upload_date: photo.upload_date || todayString(),
          is_primary: !!photo.is_primary,
        });
      }

      for (const photo of normalizedNew) {
        const uploadedUrl = photo.image ? await uploadImage(photo.image) : "";
        const imageUrl = uploadedUrl || photo.image_url;
        if (!imageUrl) continue;

        await addTourPhoto(tour_id, {
          caption: photo.caption || form.title,
          image_url: imageUrl,
          upload_date: photo.upload_date || todayString(),
          is_primary: !!photo.is_primary,
        });
      }

      await onSubmit();
    } catch (err) {
      console.error("❌ Lỗi gửi form:", err);
      setErrorMessage(err.response?.data?.detail || "Không thể lưu tour. Vui lòng thử lại.");
    } finally {
      setSaving(false);
    }
  };

  const renderPhotoCard = (photo, type) => {
    const photoId = type === "existing" ? photo.photo_id : photo.key;
    const previewUrl = getPreviewUrl(photo);

    return (
      <div key={photoId} className="border rounded p-3 bg-white mb-3">
        <div className="d-flex justify-content-between align-items-center mb-2 flex-wrap gap-2">
          <span className={`badge ${photo.is_primary ? "bg-success" : "bg-secondary"}`}>
            {photo.is_primary ? "Ảnh chính" : "Ảnh phụ"}
          </span>
          <div className="d-flex gap-2">
            <button
              type="button"
              className="btn btn-outline-primary btn-sm"
              onClick={() => (type === "existing" ? handleExistingPhotoChange(photoId, "is_primary", true) : handleNewPhotoChange(photoId, "is_primary", true))}
            >
              Đặt làm ảnh chính
            </button>
            <button
              type="button"
              className="btn btn-outline-danger btn-sm"
              onClick={() => (type === "existing" ? removeExistingPhoto(photoId) : removeNewPhoto(photoId))}
            >
              Xóa ảnh
            </button>
          </div>
        </div>

        <div className="row g-3 align-items-start">
          <div className="col-md-4">
            <div className="border rounded d-flex align-items-center justify-content-center bg-light" style={{ minHeight: 180 }}>
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt="Tour preview"
                  style={{ width: "100%", maxHeight: 180, objectFit: "cover", borderRadius: 6 }}
                />
              ) : (
                <span className="text-muted">Chưa có ảnh</span>
              )}
            </div>
          </div>

          <div className="col-md-8">
            <div className="mb-2">
              <label className="form-label">Mô tả ảnh</label>
              <input
                type="text"
                className="form-control"
                value={photo.caption}
                onChange={(e) => (type === "existing" ? handleExistingPhotoChange(photoId, "caption", e.target.value) : handleNewPhotoChange(photoId, "caption", e.target.value))}
              />
            </div>

            <div className="mb-2">
              <label className="form-label">Đường dẫn ảnh</label>
              <input
                type="text"
                className="form-control"
                placeholder="Dán link ảnh nếu có"
                value={photo.image_url}
                onChange={(e) => (type === "existing" ? handleExistingPhotoChange(photoId, "image_url", e.target.value) : handleNewPhotoChange(photoId, "image_url", e.target.value))}
              />
            </div>

            <div className="mb-2">
              <label className="form-label">Hoặc tải ảnh từ máy</label>
              <input
                type="file"
                className="form-control"
                accept="image/*"
                onChange={(e) => {
                  const file = e.target.files?.[0] || null;
                  if (type === "existing") {
                    handleExistingPhotoChange(photoId, "image", file);
                  } else {
                    handleNewPhotoChange(photoId, "image", file);
                  }
                }}
              />
            </div>

            <div>
              <label className="form-label">Ngày upload</label>
              <input
                type="date"
                className="form-control"
                value={photo.upload_date || todayString()}
                onChange={(e) => (type === "existing" ? handleExistingPhotoChange(photoId, "upload_date", e.target.value) : handleNewPhotoChange(photoId, "upload_date", e.target.value))}
              />
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>{initialData?.tour_id ? "Cập nhật Tour" : "Thêm Tour mới"}</h2>

      {errorMessage && <div className="alert alert-danger">{errorMessage}</div>}

      <div className="row">
        <div className="col">
          <label>Tiêu đề</label>
          <input type="text" name="title" value={form.title} onChange={handleChange} className="form-control" required />
        </div>
        <div className="col">
          <label>Địa điểm</label>
          <input type="text" name="location" value={form.location} onChange={handleChange} className="form-control" required />
        </div>
      </div>

      <div className="mt-2">
        <label>Mô tả</label>
        <textarea name="description" value={form.description} onChange={handleChange} className="form-control" />
      </div>

      <div className="row mt-2">
        <div className="col">
          <label>Số chỗ</label>
          <input type="number" name="capacity" value={form.capacity} onChange={handleChange} className="form-control" required />
        </div>
        <div className="col">
          <label>Giá</label>
          <input type="number" name="price" value={form.price} onChange={handleChange} className="form-control" required />
        </div>
      </div>

      <div className="row mt-2">
        <div className="col">
          <label>Ngày bắt đầu</label>
          <input type="date" name="start_date" value={form.start_date} onChange={handleChange} className="form-control" required />
        </div>
        <div className="col">
          <label>Ngày kết thúc</label>
          <input type="date" name="end_date" value={form.end_date} onChange={handleChange} className="form-control" required />
        </div>
      </div>

      <div className="row mt-2">
        <div className="col">
          <label>Trạng thái</label>
          <select name="status" value={form.status} onChange={handleChange} className="form-control">
            <option value="Available">Available</option>
            <option value="Full">Full</option>
            <option value="Closed">Closed</option>
          </select>
        </div>
        <div className="col">
          <label>Danh mục</label>
          <select name="category_id" value={form.category_id} onChange={handleChange} className="form-control" required>
            <option value="">-- Chọn danh mục --</option>
            {categories.filter(Boolean).map((cat) => (
              <option key={cat.category_id} value={cat.category_id}>{cat.name || `Danh mục ${cat.category_id}`}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-4 border rounded p-3 bg-light">
        <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
          <div>
            <h5 className="mb-1">Quản lý ảnh tour</h5>
            <small className="text-muted">Bạn có thể chỉnh ảnh chính, ảnh phụ, thêm mới hoặc xoá ảnh ngay tại đây.</small>
          </div>
          <div className="d-flex gap-2">
            <button type="button" className="btn btn-outline-primary" onClick={() => setShowPhotoForm((prev) => !prev)}>
              {showPhotoForm ? "Ẩn phần ảnh" : "Hiện phần ảnh"}
            </button>
            <button type="button" className="btn btn-primary" onClick={addPhotoRow}>
              + Thêm ảnh
            </button>
          </div>
        </div>

        {showPhotoForm && (
          <>
            {loadingPhotos && <div className="alert alert-info">Đang tải ảnh tour...</div>}

            {!loadingPhotos && existingPhotos.length === 0 && newPhotos.length === 0 && (
              <div className="text-muted">Chưa có ảnh nào cho tour này.</div>
            )}

            {existingPhotos.map((photo) => renderPhotoCard(photo, "existing"))}
            {newPhotos.map((photo) => renderPhotoCard(photo, "new"))}
          </>
        )}
      </div>

      <div className="mt-4">
        <button type="submit" className="btn btn-success me-2" disabled={saving}>
          {saving ? "Đang lưu..." : "Lưu"}
        </button>
        <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={saving}>
          Huỷ
        </button>
      </div>
    </form>
  );
}
