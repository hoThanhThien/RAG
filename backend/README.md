# FastAPI Backend (MVC)

## Cấu trúc thư mục
- app/
  - main.py
  - models/
  - views/
  - controllers/

## Chạy server
```bash
python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```
