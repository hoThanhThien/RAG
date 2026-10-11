from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
from datetime import datetime

router = APIRouter(prefix="/upload", tags=["Upload"])

# Thư mục lưu file tuyệt đối (đồng bộ với mount trong main.py)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.dirname(APP_DIR)
UPLOAD_FOLDER = os.path.join(BACKEND_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@router.post("")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Tạo thư mục nếu chưa có
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # Tạo tên file duy nhất
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        _, ext = os.path.splitext(file.filename)
        safe_filename = f"{timestamp}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)

        # Lưu file ảnh
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Trả lại đường dẫn truy cập ảnh cho frontend
        return {"image_url": f"/uploads/{safe_filename}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
