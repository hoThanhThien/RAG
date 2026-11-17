# Tour Booking Management & Hybrid RAG AI System

Hệ thống đặt tour du lịch trực tuyến tích hợp **Chatbot AI tư vấn theo kiến trúc Hybrid RAG** (FAISS + BM25 + Cross-Encoder Reranker + Out-of-Scope Routing), **Phân cụm khách hàng & điểm đến bằng K-Means**, thanh toán trực tuyến (**PayPal / MoMo / SePay**) và **CSKH Real-time qua WebSocket**.

---

## Mục Lục

1. [Tính Năng Chính](#1-tính-năng-chính)
2. [Kiến Trúc Hệ Thống & Công Nghệ](#2-kiến-trúc-hệ-thống--công-nghệ)
3. [Cấu Trúc Thư Mục](#3-cấu-trúc-thư-mục)
4. [Hệ Thống RAG AI & Trang Admin Tùy Chỉnh Model](#4-hệ-thống-rag-ai--trang-admin-tùy-chỉnh-model)
5. [Hướng Dẫn Cài Đặt & Khởi Chạy](#5-hướng-dẫn-cài-đặt--khởi-chạy)
   - [Cách 1: Chạy bằng Docker Compose (Khuyên dùng)](#cách-1-chạy-bằng-docker-compose-khuyên-dùng)
   - [Cách 2: Chạy thủ công trên máy Local (Dev)](#cách-2-chạy-thủ-công-trên-máy-local-dev)
6. [Biến Môi Trường Quan Trọng (`.env`)](#6-biến-môi-trường-quan-trọng-env)
7. [Địa Chỉ Truy Cập & Tài Liệu API](#7-địa-chỉ-truy-cập--tài-liệu-api)
8. [Hướng Dẫn Sử Dụng Nhanh Theo Vai Trò](#8-hướng-dẫn-sử-dụng-nhanh-theo-vai-trò)

---

## 1. Tính Năng Chính

### Dành cho Khách hàng (Client)
- **Tìm kiếm & Đặt tour:** Lọc tour theo danh mục, địa điểm, giá cả; kiểm tra sức chứa tự động khi đặt chỗ; áp dụng mã giảm giá.
- **Trợ lý AI Du Lịch (`AIChatbot`):**
  - Tư vấn tìm tour theo ý định (biển, núi, giá rẻ, cao cấp, gia đình, trong nước / nước ngoài).
  - Hỗ trợ **hội thoại nhiều lượt (Multi-turn History)** và tự động nhận diện ngữ cảnh tour khách đang xem (`focus_tour_id` trên trang `/tours/:id`).
  - Xử lý thông minh cả câu hỏi trong danh mục lẫn câu hỏi kiến thức/ngoài danh mục.
- **Thanh toán đa cổng:** PayPal, MoMo (IPN + Callback) và chuyển khoản ngân hàng / SePay Webhook.
- **Đánh giá & Hỗ trợ trực tuyến:** Bình luận, chấm điểm 1–5 sao (cho tour đã đặt) và chat trực tiếp với nhân viên CSKH qua WebSocket.

### Dành cho Quản trị viên (Admin) & Hướng dẫn viên (Guide)
- **Dashboard thống kê Live:** Doanh thu theo tour/danh mục/khu vực, trạng thái đơn đặt, top khách hàng, cập nhật real-time qua WebSocket.
- **Phân tích AI/ML (K-Means Clustering):**
  - Phân cụm khách hàng (`VIP`, `Khách mua nhiều`, `Khách săn sale`, `Khách trung thành`, `Khách mới`...) kèm biểu đồ Elbow, Silhouette & PCA.
  - Phân cụm tour & phân cụm điểm đến nổi bật (`/admin/clustering/customers`, `/admin/clustering/tours`).
- **Quản trị & Tùy chỉnh Model RAG AI (`/admin/rag-settings`):**
  - Đổi nhà cung cấp & Model AI ngay trên giao diện mà không cần sửa code hay restart server.
  - Cấu hình **Model & chế độ riêng cho câu hỏi ngoài danh mục** (`strict` / `general_travel` / `open_ai`), ngưỡng lọc ngữ nghĩa (`similarity_threshold`), Rebuild Vector Index, xóa Cache và **Live Test Playground**.
- **Phân quyền 3 cấp (RBAC):**
  - `Admin`: Toàn quyền quản trị (không thể tự xóa hoặc đổi role của chính mình).
  - `Guide`: Xem danh sách tour được phân công và thông tin booking của tour đó.
  - `User`: Đặt tour, hủy booking (chưa xác nhận), bình luận/đánh giá và chat hỗ trợ.

---

## 2. Kiến Trúc Hệ Thống & Công Nghệ

```text
┌──────────────────────────────────────────────────────────┐
│                 Client / Admin Browser                   │
└───────────────────────────┬──────────────────────────────┘
                            │ HTTP / WebSocket
┌───────────────────────────▼──────────────────────────────┐
│           Frontend (React 18 + Vite + Bootstrap 5)       │
│                        Port 3000                         │
└───────────────────────────┬──────────────────────────────┘
                            │ REST API / WS
┌───────────────────────────▼──────────────────────────────┐
│             Backend (FastAPI + Uvicorn ASGI)             │
│                        Port 8000                         │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Controllers -> Services -> Models                  │  │
│  │ Hybrid RAG: FAISS + BM25 + Cross-Encoder + OOS LLM │  │
│  │ ML Engine:  scikit-learn KMeans + PCA              │  │
│  └────────────────────────────────────────────────────┘  │
└──────────┬─────────────────────────────────┬─────────────┘
           │ PyMySQL / SQLAlchemy            │ redis-py
┌──────────▼──────────┐           ┌──────────▼──────────┐
│   MySQL 8.0 (3306)  │           │   Redis 7 (6379)    │
│ phpMyAdmin (8080)   │           │ Embedding/Resp Cache│
└─────────────────────┘           └─────────────────────┘
```

| Thành phần | Công nghệ sử dụng |
|---|---|
| **Frontend** | React 18, Vite 7, React Router 7, Axios, Bootstrap 5, Recharts |
| **Backend** | FastAPI 0.119, Uvicorn, Pydantic v2, SQLAlchemy 2, PyMySQL, Alembic |
| **Database & Cache** | MySQL 8.0, Redis 7 Alpine, phpMyAdmin |
| **RAG & Vector Search** | FAISS (`faiss-cpu`), NumPy, BM25 (`BM25Index`), TF-IDF / SBERT / OpenAI Embeddings, Cross-Encoder |
| **Machine Learning** | scikit-learn (K-Means, StandardScaler, PCA, Silhouette Score) |
| **Auth & Realtime** | JWT (`python-jose`), bcrypt (`passlib`), WebSocket / `python-socketio` |
| **Thanh toán** | PayPal SDK, MoMo API (HMAC-SHA256), SePay Bank Webhook |

---

## 3. Cấu Trúc Thư Mục

```text
RAG/
├── docker-compose.yml              # Khởi chạy toàn bộ 5 services (mysql, redis, backend, frontend, phpmyadmin)
├── .env.example                    # File mẫu biến môi trường dùng chung
├── tourbookingdb.sql               # SQL schema & dữ liệu mẫu khởi tạo MySQL
├── README.md                       # Tài liệu hướng dẫn tổng quan (file này)
├── PROJECT_KNOWLEDGE.md            # Tài liệu tổng hợp kiến thức & quyết định kỹ thuật
├── KMEANS_ALGORITHM.md             # Chi tiết thuật toán phân cụm K-Means
├── MOMO_SETUP_GUIDE.md             # Hướng dẫn cấu hình cổng thanh toán MoMo
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── build_rag_index.py          # Script build lại FAISS/BM25 index từ MySQL & Knowledge Base
│   ├── main.py / passenger_wsgi.py
│   ├── alembic/                    # Quản lý migration database
│   ├── archive/                    # Knowledge Base du lịch VN (SQuAD JSON)
│   │   ├── train_vietnam_tourism.json
│   │   └── valid_vietnam_tourism.json
│   ├── rag_store/                  # Artifacts RAG sau khi build index
│   │   ├── tour_index.faiss        # FAISS vector index
│   │   ├── vectors.npy             # Embedding vectors chuẩn hóa L2
│   │   ├── chunks.json             # Text chunks + metadata tour & knowledge base
│   │   ├── state.json              # Trạng thái index (built_at, document_count, provider)
│   │   ├── tfidf_vectorizer.pkl    # TF-IDF vectorizer (khi dùng local-tfidf)
│   │   └── runtime_config.json     # Cấu hình động do Admin chỉnh từ UI
│   └── app/
│       ├── main.py                 # Khởi tạo FastAPI, CORS, đăng ký routers
│       ├── database.py             # Kết nối MySQL
│       ├── dependencies/           # JWT auth & phân quyền (require_admin, require_guide)
│       ├── controllers/            # REST endpoints (chat, tour, booking, admin, payment...)
│       ├── schemas/                # Pydantic schemas
│       ├── models/                 # SQLAlchemy ORM models
│       ├── utils/                  # Tiện ích auth, payment, location, pagination
│       └── services/
│           ├── rag_service.py      # Pipeline Hybrid RAG chính
│           ├── rag/                # Các module con của RAG
│           │   ├── config.py       # Đọc RAG env settings
│           │   ├── runtime_config.py # Quản lý cấu hình động cho Admin UI
│           │   ├── intents.py      # Chuẩn hóa tiếng Việt (đ/Đ), intent, stopwords, follow-up
│           │   ├── chunking.py     # Semantic chunking có overlap
│           │   ├── bm25.py         # BM25 lexical search
│           │   ├── knowledge_base.py # Nạp dữ liệu kiến thức du lịch VN
│           │   ├── prompting.py    # System/User prompt (In-Scope & Out-of-Scope)
│           │   ├── cache.py        # Cache 2 tầng Redis + In-Memory TTL LRU
│           │   └── metrics.py      # Đo đạc latency, cache hits, OOS count
│           ├── customer_segmentation_service.py
│           ├── tour_clustering_service.py
│           ├── destination_clustering_service.py
│           └── recommendation_service.py
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx                 # Phân luồng Client / Admin
        ├── admin/
        │   ├── routes.jsx          # Routes trang Admin (gồm /admin/rag-settings)
        │   ├── components/layout/  # Sidebar, Navbar, AdminLayout
        │   ├── services/           # adminService.js (Dashboard, Clustering, RAG Config...)
        │   └── views/              # Home, RAGSettings, TourList, CustomerClustering...
        └── client/
            ├── routes.jsx          # Routes trang Client
            ├── components/         # AIChatbot.jsx, TourCard.jsx, SupportChat.jsx...
            ├── pages/              # Home, Tours, TourDetail, Booking, Payment...
            └── services/           # chatbotService.js, tourService.js, api.js...
```

---

## 4. Hệ Thống RAG AI & Trang Admin Tùy Chỉnh Model

### Luồng xử lý một câu hỏi trên `/chat`
1. **Nhận ngữ cảnh:** Nhận `query`, `user_id` (lấy phân khúc khách hàng K-Means), `focus_tour_id` (tự động gắn khi khách đang ở trang chi tiết tour `/tours/:id`) và `history` (6 lượt hội thoại gần nhất).
2. **Mở rộng & Ngữ cảnh hóa:** Nếu là câu hỏi nối tiếp (*"Giá bao nhiêu?"*, *"Tour đầu mấy ngày?"*), hệ thống tự ghép ngữ cảnh câu trước từ `history`.
3. **Hybrid Retrieval:** Tìm kiếm song song bằng **FAISS Dense Vector** và **BM25 Lexical Search**, chuẩn hóa điểm theo độ tin cậy thực tế (`raw_dense_score`, `raw_lexical_score`), lọc theo intent & khử trùng theo `tour_id` (và chạy Cross-Encoder Reranker nếu bật).
4. **Phân loại Trong mục (In-Scope) vs Ngoài danh mục (Out-of-Scope):**
   - Nếu không có source phù hợp, điểm khớp dưới `similarity_threshold`, hoặc từ khóa chủ đề/địa danh không nằm trong dữ liệu tour & knowledge base → chuyển sang **luồng Out-of-Scope**.
5. **Sinh câu trả lời theo cấu hình của Admin:**
   - **Trong danh mục:** Dùng `chat_model` kết hợp `temperature`, `max_tokens` và `custom_system_prompt_addon`. (Nếu chưa cấu hình API key, dùng bộ trả lời mẫu thông minh tại local).
   - **Ngoài danh mục (`out_of_scope_mode`):**
     - `strict`: Từ chối lịch sự theo `out_of_scope_fallback_message` (không gọi LLM mở rộng).
     - `general_travel`: Dùng **`out_of_scope_model`** (Admin có thể chọn model riêng mạnh hơn như `gpt-4o`, `llama-3.3-70b-versatile`, `gemini-2.0-flash`...) để tư vấn kiến thức du lịch mở rộng, báo rõ chưa có tour khớp trực tiếp và gợi ý kèm 3 tour nổi bật nếu bật `suggest_popular_tours_on_oos`.
     - `open_ai`: Dùng **`out_of_scope_model`** trả lời tự do theo `out_of_scope_system_prompt` do Admin cài đặt.

### Các API quản trị RAG (yêu cầu JWT Admin)
- `GET /chat/config` — Xem cấu hình RAG hiện tại (API Key được che bảo mật), trạng thái index và metrics.
- `PUT /chat/config` — Cập nhật Model chính, Model ngoài danh mục, API Key, trọng số Hybrid, ngưỡng `similarity_threshold` (có hiệu lực ngay và tự xóa cache phản hồi).
- `POST /chat/test` — Chạy thử nghiệm câu hỏi (hỗ trợ `config_override` để test trước khi lưu).
- `POST /chat/reindex` — Rebuild lại toàn bộ FAISS & BM25 index từ Database.
- `POST /chat/cache/invalidate` — Xóa cache phản hồi RAG.
- `GET /chat/metrics` — Xem thống kê số lượt hỏi, số lượt ngoài danh mục, cache hit và độ trễ trung bình.

---

## 5. Hướng Dẫn Cài Đặt & Khởi Chạy

### Bước chuẩn bị chung: Tạo file `.env`
Sao chép file mẫu cấu hình ở thư mục gốc:
```bash
# Windows (PowerShell / CMD)
copy .env.example .env

# Linux / macOS
cp .env.example .env
```
Mở `.env` và điền `OPENAI_API_KEY` (hoặc giữ trống nếu muốn chạy chế độ local fallback / cấu hình sau trên giao diện Admin).

---

### Cách 1: Chạy bằng Docker Compose (Khuyên dùng)

**Yêu cầu:** Đã cài đặt **Docker** và **Docker Compose** (trên Windows bật **Docker Desktop**).

1. **Build và khởi động toàn bộ 5 container (`mysql`, `redis`, `backend`, `frontend`, `phpmyadmin`):**
   ```bash
   docker compose build
   docker compose up -d
   ```

2. **Kiểm tra trạng thái các container & nạp dữ liệu MySQL (nếu DB trống):**
   - Kiểm tra container đang chạy:
     ```bash
     docker compose ps
     ```
   - Import file `tourbookingdb.sql` vào MySQL (nếu cần khởi tạo lại dữ liệu mẫu):
     ```bash
     # PowerShell
     Get-Content tourbookingdb.sql | docker exec -i mysql mysql -uroot -proot123 tourbookingdb

     # Linux / macOS / Git Bash
     docker exec -i mysql mysql -uroot -proot123 tourbookingdb < tourbookingdb.sql
     ```

3. **Build RAG Vector Index lần đầu (hoặc sau khi đổi API Key / Embedding):**
   ```bash
   docker exec backend python build_rag_index.py
   ```

4. **Xem log khi cần debug:**
   ```bash
   docker compose logs -f backend
   ```

> **Lưu ý khi sửa code Python/React với Docker:** Container `backend` và `frontend` đóng gói mã nguồn vào image, nên sau khi sửa code cần chạy lại `docker compose build backend frontend && docker compose up -d`.

---

### Cách 2: Chạy thủ công trên máy Local (Dev)

**Yêu cầu:** Python `3.12+`, Node.js `20+`, MySQL `8.0` (và Redis `7` nếu muốn bật cache Redis).

1. **Khởi tạo Database MySQL:**
   - Tạo database `tourbookingdb` trên MySQL local (`localhost:3306`) và import file `tourbookingdb.sql`.
   - Cập nhật `backend/.env` cho khớp `DATABASE_URL=mysql+pymysql://tour_user:tour_pass123@localhost:3306/tourbookingdb` (và đặt `RAG_REDIS_ENABLED=false` nếu không chạy Redis).

2. **Chạy Backend (FastAPI):**
   ```bash
   cd backend
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   # source .venv/bin/activate

   pip install -r requirements.txt
   python build_rag_index.py
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Chạy Frontend (React + Vite):**
   Mở một terminal mới tại thư mục gốc:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   *(Khi chạy `npm run dev`, Vite thường mở tại `http://localhost:5173`; khi build Nginx trong Docker là `http://localhost:3000`.)*

---

## 6. Biến Môi Trường Quan Trọng (`.env`)

| Biến | Mặc định | Mô tả |
|---|---|---|
| `FRONTEND_PORT` / `BACKEND_PORT` | `3000` / `8000` | Cổng chạy Frontend và Backend |
| `DATABASE_URL` | `mysql+pymysql://tour_user:tour_pass123@mysql:3306/tourbookingdb` | Chuỗi kết nối MySQL (đổi `mysql` thành `localhost` nếu chạy ngoài Docker) |
| `SECRET_KEY` | dev key | Khóa ký JWT (nên đổi chuỗi ngẫu nhiên dài khi deploy production) |
| `VITE_API_URL` / `VITE_WS_URL` | `http://localhost:8000` / `ws://localhost:8000` | URL Backend và WebSocket cho Frontend |
| `FRONTEND_BASE_URL` | `http://localhost:3000` | URL Frontend dùng cho CORS & redirect thanh toán |
| `RAG_REDIS_ENABLED` / `RAG_REDIS_URL` | `true` / `redis://redis:6379/0` | Bật/tắt Redis Cache cho embedding và câu trả lời RAG |
| `OPENAI_API_KEY` | *(trống)* | API Key OpenAI / Groq / OpenRouter / Gemini (có thể nhập trực tiếp trên trang Admin) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Endpoint API chuẩn OpenAI |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model chat mặc định |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Model embedding mặc định (nếu không có key OpenAI sẽ dùng local embedding) |
| `RAG_ANSWER_MAX_TOKENS` | `320` | Giới hạn token câu trả lời |
| `PAYPAL_*` / `MOMO_*` / `SEPAY_*` | sandbox | Cấu hình các cổng thanh toán |

---

## 7. Địa Chỉ Truy Cập & Tài Liệu API

| Dịch vụ | URL (Docker mặc định) |
|---|---|
| **Trang chủ Khách hàng & Admin** | `http://localhost:3000` |
| **Trang Quản trị RAG AI** | `http://localhost:3000/admin/rag-settings` |
| **Backend API** | `http://localhost:8000` |
| **Swagger API Docs (Interactive)** | `http://localhost:8000/docs` |
| **phpMyAdmin (Quản lý MySQL)** | `http://localhost:8080` |

Tài liệu chi tiết thêm trong repo:
- Kiến thức kiến trúc toàn dự án: [PROJECT_KNOWLEDGE.md](PROJECT_KNOWLEDGE.md)
- Thuật toán K-Means: [KMEANS_ALGORITHM.md](KMEANS_ALGORITHM.md)
- Hướng dẫn MoMo: [MOMO_SETUP_GUIDE.md](MOMO_SETUP_GUIDE.md)
- Tài liệu API Backend: [backend/API_Documentation.md](backend/API_Documentation.md)

---

## 8. Hướng Dẫn Sử Dụng Nhanh Theo Vai Trò

### 1. Người dùng (Khách đặt tour)
1. Truy cập `http://localhost:3000`, xem các tour nổi bật hoặc lọc tour ở mục **Tours**.
2. Nhấn nút **AI Tour** ở góc dưới bên phải để mở Chatbot RAG:
   - Hỏi tìm tour (*"Tìm tour đi biển giá rẻ"*, *"Tour Đà Nẵng giá bao nhiêu?"*), hỏi tiếp nối nhiều lượt (*"Mấy ngày?"*, *"Còn chỗ không?"*).
   - Khi đang xem trang chi tiết một tour (`/tours/:id`), chatbot tự gắn ngữ cảnh tour đó để trả lời lịch trình, giá, số chỗ còn lại hoặc gợi ý tour tương tự.
3. Đăng nhập / Đăng ký để đặt tour, thanh toán (PayPal / MoMo / QR ngân hàng), đánh giá tour và nhắn tin với nhân viên CSKH.

### 2. Quản trị viên (Admin) — Tùy chỉnh Model RAG
1. Đăng nhập tài khoản Admin, vào mục **Cấu hình RAG AI** (`/admin/rag-settings`) trên thanh menu bên trái.
2. Tại khối **Model RAG Chính & Cấu hình Truy xuất**:
   - Chọn **Nhà cung cấp LLM** (`OpenAI`, `Groq`, `Google Gemini`, `OpenRouter`, `Custom` hoặc `Local Fallback`), nhập **API Key** và chọn `chat_model`.
   - Điều chỉnh `temperature`, `max_tokens` và tỷ trọng Hybrid Search (`Dense` / `BM25`).
3. Tại khối **Xử lý câu hỏi NGOÀI DANH MỤC (Out-of-Scope)**:
   - Chọn chế độ: `strict`, `general_travel` hoặc `open_ai`.
   - Chọn **Model riêng cho câu hỏi ngoài mục (`out_of_scope_model`)** (hoặc để trống để dùng chung model chính).
   - Kéo thanh `similarity_threshold` (mặc định `0.22`), tùy chỉnh System Prompt và bật/tắt gợi ý kèm 3 tour nổi bật.
4. Bấm **Lưu toàn bộ cấu hình**.
5. Dùng ngay **Phòng thử nghiệm RAG (Live Test Playground)** bên dưới để bấm test các mẫu câu *Trong mục* và *Ngoài mục*, kiểm tra nhãn phân loại, điểm `max_score`, `model_used` và `sources` trả về.
6. Nếu mới cập nhật nhiều dữ liệu tour hoặc đổi mô hình embedding, nhấn nút **Rebuild Vector Index** ở góc trên bên phải để đồng bộ lại chỉ mục FAISS & BM25.
