# Tour Booking System – Tổng Hợp Kiến Thức Dự Án

> Tài liệu này tổng hợp kiến trúc, công nghệ và các quyết định thiết kế quan trọng của toàn bộ hệ thống.

---

## Mục Lục

1. [Tổng Quan Hệ Thống](#1-tổng-quan-hệ-thống)
2. [Kiến Trúc & Stack Công Nghệ](#2-kiến-trúc--stack-công-nghệ)
3. [Cấu Trúc Thư Mục](#3-cấu-trúc-thư-mục)
4. [Backend – FastAPI](#4-backend--fastapi)
5. [Frontend – React + Vite](#5-frontend--react--vite)
6. [Cơ Sở Dữ Liệu – MySQL](#6-cơ-sở-dữ-liệu--mysql)
7. [RAG Chatbot](#7-rag-chatbot)
8. [AI/ML – K-Means Clustering](#8-aiml--k-means-clustering)
9. [Thanh Toán – PayPal & MoMo](#9-thanh-toán--paypal--momo)
10. [Real-time – WebSocket](#10-real-time--websocket)
11. [Xác Thực & Phân Quyền](#11-xác-thực--phân-quyền)
12. [Triển Khai – Docker Compose](#12-triển-khai--docker-compose)
13. [Biến Môi Trường Quan Trọng](#13-biến-môi-trường-quan-trọng)
14. [Các Vấn Đề & Giải Pháp Đã Ghi Nhận](#14-các-vấn-đề--giải-pháp-đã-ghi-nhận)

---

## 1. Tổng Quan Hệ Thống

Hệ thống **Tour Booking Management** là một nền tảng đặt tour du lịch trực tuyến bao gồm:

- Quản lý tour, danh mục, lịch trình, hình ảnh
- Hệ thống đặt vé, thanh toán tích hợp (PayPal, MoMo)
- Chat hỗ trợ khách hàng real-time (WebSocket)
- Chatbot AI tư vấn tour sử dụng kỹ thuật RAG (Retrieval-Augmented Generation)
- Phân tích & phân cụm khách hàng / điểm đến với K-Means
- Phân quyền 3 cấp: Admin – Guide – User

---

## 2. Kiến Trúc & Stack Công Nghệ

```
┌─────────────────────────────────────────────────────────┐
│                        Client Browser                    │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP / WebSocket
┌──────────────────▼──────────────────────────────────────┐
│            Frontend  (React 18 + Vite)                   │
│         Port 3000 – phục vụ bởi Nginx trong Docker       │
└──────────────────┬──────────────────────────────────────┘
                   │ REST API / WebSocket
┌──────────────────▼──────────────────────────────────────┐
│             Backend  (FastAPI + Python)                   │
│         Port 8000 – Uvicorn ASGI server                  │
│  ┌─────────────────────────────────────────────────────┐ │
│  │   Controllers → Services → Models (MVC pattern)     │ │
│  │   RAG Engine: FAISS + BM25 + Cross-encoder reranker │ │
│  │   ML Engine:  scikit-learn KMeans                   │ │
│  └─────────────────────────────────────────────────────┘ │
└──────┬───────────────────────┬──────────────────────────┘
       │ SQLAlchemy ORM        │ redis-py
┌──────▼─────────┐    ┌────────▼──────────┐
│  MySQL 8.0     │    │   Redis 7 Alpine  │
│  Port 3306     │    │   Port 6379       │
└────────────────┘    └───────────────────┘
```

| Layer | Công Nghệ |
|---|---|
| Frontend | React 18, Vite, Axios, Socket.io-client |
| Backend | FastAPI, Uvicorn, SQLAlchemy, Alembic |
| Database | MySQL 8.0 |
| Cache | Redis 7 |
| Vector Search | FAISS, NumPy |
| Lexical Search | BM25 (rank_bm25) |
| Embedding | OpenAI `text-embedding-3-small` (hoặc local `paraphrase-multilingual-MiniLM-L12-v2`) |
| Reranker | Cross-encoder `ms-marco-MiniLM-L-6-v2` |
| ML Clustering | scikit-learn KMeans, StandardScaler |
| Auth | JWT (python-jose) |
| Thanh toán | PayPal SDK, MoMo REST API |
| Container | Docker, Docker Compose |

---

## 3. Cấu Trúc Thư Mục

```
RAG/
├── docker-compose.yml          # Định nghĩa toàn bộ services
├── README.md                   # Hướng dẫn tổng quát
├── KMEANS_ALGORITHM.md         # Tài liệu giải thích thuật toán K-Means
├── MOMO_SETUP_GUIDE.md         # Hướng dẫn cấu hình MoMo
├── tourbookingdb.sql            # SQL schema khởi tạo database
│
├── backend/
│   ├── main.py                 # Entrypoint (production WSGI wrapper)
│   ├── build_rag_index.py      # Script xây dựng lại RAG index từ DB
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── alembic/                # Database migration
│   └── app/
│       ├── main.py             # FastAPI app + CORS + router registration
│       ├── database.py         # SQLAlchemy engine & session
│       ├── controllers/        # Route handlers (1 file = 1 domain)
│       ├── models/             # SQLAlchemy ORM models
│       ├── schemas/            # Pydantic request/response schemas
│       ├── services/           # Business logic
│       │   ├── rag/            # RAG engine modules
│       │   ├── rag_service.py
│       │   ├── recommendation_service.py
│       │   ├── customer_segmentation_service.py
│       │   ├── destination_clustering_service.py
│       │   └── tour_clustering_service.py
│       ├── dependencies/
│       │   └── auth_dependencies.py  # JWT dependency injection
│       ├── jobs/
│       │   └── pull_bank_txn_and_reconcile.py  # MoMo bank reconciliation
│       └── archive/
│           ├── train_vietnam_tourism.json  # SQuAD-format knowledge base
│           └── valid_vietnam_tourism.json
│
├── frontend/
│   ├── vite.config.js
│   ├── Dockerfile
│   └── src/
│       ├── App.jsx             # Root, phân nhánh Admin/Client
│       ├── api.js              # Axios instance chung
│       ├── admin/              # Giao diện Admin
│       │   ├── views/          # Các trang (TourList, UserList, ...)
│       │   ├── services/       # API service functions (admin)
│       │   └── components/     # Shared UI components (admin)
│       └── client/             # Giao diện Client
│           ├── pages/          # Các trang (Home, Tours, TourDetail, ...)
│           ├── services/       # API service functions (client)
│           └── context/        # React Context (Auth, Cart, ...)
│
└── rag_store/                  # Artifacts RAG sau khi build index
    ├── tour_index.faiss        # FAISS dense index
    ├── vectors.npy             # Embedding vectors
    ├── chunks.json             # Text chunks + metadata
    └── state.json              # Trạng thái build (built_at, count, ...)
```

---

## 4. Backend – FastAPI

### 4.1 Quy Tắc MVC

| Thành phần | Vai Trò |
|---|---|
| **Controller** | Định nghĩa routes FastAPI, validate đầu vào bằng Pydantic schema |
| **Service** | Business logic, gọi models, tính toán |
| **Model** | SQLAlchemy ORM – ánh xạ bảng database |
| **Schema** | Pydantic – định nghĩa request body và response shape |

### 4.2 Danh Sách Controllers & Chức Năng

| Controller | Prefix | Mô Tả |
|---|---|---|
| `auth_controller` | `/auth` | Đăng ký, đăng nhập, refresh token |
| `user_controller` | `/users` | CRUD user, đổi mật khẩu, profile |
| `tour_controller` | `/tours` | CRUD tour, filter, pagination |
| `booking_controller` | `/bookings` | Đặt tour, hủy, lịch sử |
| `payment_controller` | `/payments` | PayPal integration |
| `momo_controller` | `/momo` | MoMo integration + IPN callback |
| `comment_controller` | `/comments` | Comment + rating tour |
| `category_controller` | `/categories` | Danh mục tour |
| `discount_controller` | `/discounts` | Mã giảm giá |
| `photo_controller` | `/photos` | Upload/quản lý ảnh tour |
| `admin_controller` | `/admin` | Dashboard, thống kê, phân quyền |
| `support_controller` | `/support` | Chat hỗ trợ (threads + messages) |
| `chat_controller` | `/chat` | RAG chatbot |
| `recommendation_controller` | `/recommendations` | Đề xuất tour, `/destinations/featured` |
| `websocket_controller` | `/ws` | WebSocket real-time |
| `upload_controller` | `/upload` | Upload file chung |
| `role_controller` | `/roles` | Quản lý roles |

### 4.3 Database Session

- `app/database.py` tạo `SessionLocal` bằng `create_engine` SQLAlchemy.
- Dependency `get_db()` inject session vào từng request, tự `close()` khi xong.

---

## 5. Frontend – React + Vite

### 5.1 Phân Tách Admin / Client

`App.jsx` kiểm tra role trong JWT stored ở `localStorage` rồi render `AdminApp` hoặc `ClientApp`.

### 5.2 Admin Views

| View | Chức Năng |
|---|---|
| `TourList` | Danh sách tour có phân trang, tìm kiếm, giá hiển thị đơn vị `đ` |
| `UserList` | Quản lý user, đổi role |
| `BookingList` | Xem tất cả bookings + trạng thái thanh toán |
| `PaymentList` | Lịch sử giao dịch thanh toán |
| `CustomerClustering` | Phân cụm khách hàng K-Means, biểu đồ Elbow, Silhouette |
| `TourClustering` | Phân cụm tour theo đặc điểm |
| `ClusteringView` | Tổng hợp clustering dashboard |
| `SupportChat` | Giao diện chat hỗ trợ phía admin |
| `CommentList` | Quản lý comment/review |
| `DiscountList` | CRUD mã giảm giá |
| `PhotoList` | Quản lý ảnh tour |

### 5.3 Client Pages

| Page | Chức Năng |
|---|---|
| `Home` | Landing page, "Choose Your Place" dùng Featured Destinations API |
| `Tours` | Danh sách tour lọc theo category, giá, địa điểm |
| `TourDetail` | Chi tiết tour + nhúng chatbot RAG |
| `Booking` | Chọn số vé, ngày khởi hành |
| `Payment` / `PaymentPage` | Chọn phương thức thanh toán (PayPal / MoMo) |
| `PaymentSuccess` | Xác nhận thanh toán thành công |
| `MoMoCallback` | Redirect sau thanh toán MoMo |
| `BookingHistory` | Lịch sử đặt tour của user |
| `Recommendations` | Tour gợi ý dựa trên lịch sử user |
| `UserProfile` | Cập nhật thông tin cá nhân |
| `Auth` | Login / Register |

### 5.4 API Calls

`src/api.js` tạo một Axios instance duy nhất với:
- `baseURL` = `VITE_API_URL` (env var)
- Request interceptor tự đính kèm `Authorization: Bearer <token>`
- Response interceptor redirect về login khi nhận 401

---

## 6. Cơ Sở Dữ Liệu – MySQL

### 6.1 Các Bảng Chính

| Bảng | Mô Tả |
|---|---|
| `users` | Tài khoản người dùng (id, email, hashed_password, role_id, created_at) |
| `roles` | Bảng role (Admin / Guide / User) |
| `tours` | Thông tin tour (tên, mô tả, giá, capacity, location, ...) |
| `tour_schedules` | Lịch khởi hành của từng tour |
| `bookings` | Đơn đặt tour (user_id, tour_id, schedule_id, status, passenger_count) |
| `payments` | Giao dịch thanh toán (booking_id, method, status, transaction_id, ...) |
| `categories` | Danh mục tour |
| `comments` | Review + rating (user_id, tour_id, content, rating, created_at) |
| `photos` | Ảnh tour (tour_id, url, is_primary) |
| `discounts` | Mã giảm giá (code, type, value, expiry) |
| `support_threads` | Luồng hội thoại hỗ trợ |
| `support_messages` | Tin nhắn trong luồng hỗ trợ |
| `bank_transactions` | Giao dịch ngân hàng MoMo (reconciliation) |

### 6.2 Migration

Dự án dùng **Alembic** để quản lý migration schema. Một số migration thủ công nằm ở file `.sql` và `.py` trong thư mục gốc backend (ví dụ: `add_paypal_columns.py`, `add_transaction_id_column.sql`).

> **Lưu ý**: MySQL version này không hỗ trợ `ADD COLUMN IF NOT EXISTS`, nên các migration script phải kiểm tra tồn tại cột trước khi thêm.

---

## 7. RAG Chatbot

### 7.1 Kiến Trúc Tổng Quát

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────┐
│              Intent Detection                    │
│   (intents.py – focus_tour_id, query_type, ...)  │
└─────────────────┬───────────────────────────────┘
                  │
         ┌────────▼────────┐
         │  Query Embedding │  (OpenAI hoặc local MiniLM)
         └────────┬────────┘
                  │
    ┌─────────────▼──────────────────┐
    │     Hybrid Retrieval           │
    │  ┌──────────┐ ┌─────────────┐  │
    │  │  FAISS   │ │  BM25       │  │
    │  │  Dense   │ │  Lexical    │  │
    │  └────┬─────┘ └──────┬──────┘  │
    │       │   RRF Merge   │         │
    │       └──────┬────────┘        │
    └──────────────┼─────────────────┘
                   │ top-N candidates
         ┌─────────▼──────────┐
         │  Cross-encoder     │
         │  Reranker          │  (ms-marco-MiniLM)
         └─────────┬──────────┘
                   │ top-K final
         ┌─────────▼──────────┐
         │  Prompting + LLM   │  (OpenAI GPT / fallback TF-IDF)
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Response Cache    │  (Redis hoặc in-memory LRU)
         └────────────────────┘
```

### 7.2 Modules RAG (`backend/app/services/rag/`)

| Module | Chức Năng |
|---|---|
| `config.py` | `RAGSettings` dataclass, đọc toàn bộ cấu hình từ env vars |
| `chunking.py` | Chia văn bản thành chunks có overlap |
| `bm25.py` | BM25 lexical search wrapper |
| `cache.py` | In-memory LRU cache + Redis cache cho query embedding & response |
| `intents.py` | Phát hiện intent: tour cụ thể, địa điểm, general, v.v. |
| `knowledge_base.py` | Load SQuAD JSON từ `backend/archive/` làm knowledge chunks bổ sung |
| `prompting.py` | Tạo system prompt & user prompt cho LLM |
| `metrics.py` | Logging latency, candidate count, fallback rate |

### 7.3 Data Flow Xây Dựng Index

```
build_rag_index.py
    │
    ├── Query toàn bộ tours từ MySQL
    ├── Đọc knowledge base (archive/*.json)
    ├── Chunk văn bản
    ├── Embed bằng OpenAI (batch) hoặc local model
    ├── Lưu FAISS index → rag_store/tour_index.faiss
    ├── Lưu vectors     → rag_store/vectors.npy
    ├── Lưu chunks      → rag_store/chunks.json
    └── Cập nhật state  → rag_store/state.json (built_at, count)
```

### 7.4 Cache Key Strategy

- **Query embedding cache**: `RAG_REDIS_KEY_PREFIX + hash(query_text)` – TTL `RAG_QUERY_CACHE_TTL_SECONDS`
- **Response cache**: `RAG_REDIS_KEY_PREFIX + hash(query + focus_tour_id + top_k)` – TTL `RAG_RESPONSE_CACHE_TTL_SECONDS`
- Cache key bao gồm `built_at` để tránh trả về kết quả cũ sau khi rebuild index.

### 7.5 Knowledge Base (Vietnam Tourism)

- Hai file SQuAD-format JSON trong `backend/archive/`:
  - `train_vietnam_tourism.json`
  - `valid_vietnam_tourism.json`
- Cấu trúc: `{"data": [{"title": "...", "paragraphs": [{"context": "..."}]}]}`
- Context passages được chunk và thêm vào FAISS index cùng tour data.
- Mục đích: bổ sung kiến thức về điểm đến (văn hóa, ẩm thực, hoạt động) mà dữ liệu tour không có.

---

## 8. AI/ML – K-Means Clustering

### 8.0 Lý Thuyết K-Means

#### Định Nghĩa

K-Means là thuật toán phân cụm **không giám sát**, chia tập dữ liệu thành K nhóm sao cho các điểm trong cùng nhóm gần nhau nhất có thể.

**Hàm mục tiêu – Inertia (tổng bình phương khoảng cách):**

$$
\text{Inertia} = \sum_{i=1}^{K}\sum_{x\in C_i}\lVert x - \mu_i \rVert^2
$$

Trong đó:
- $C_i$: tập điểm thuộc cụm $i$
- $\mu_i$: centroid (tâm) của cụm $i$
- Inertia càng nhỏ → cụm càng compact

#### Quy Trình Lloyd (phiên bản phổ biến)

```
1. Chọn K, khởi tạo K centroid (ngẫu nhiên hoặc k-means++)
2. Assignment step: gán mỗi điểm vào cụm có centroid gần nhất
3. Update step:   cập nhật centroid = trung bình các điểm trong cụm
4. Lặp lại 2–3 đến khi hội tụ
```

Dự án dùng `sklearn KMeans(n_init=10, random_state=42)` để tăng độ ổn định.

#### Chuẩn Hóa Dữ Liệu – StandardScaler

K-Means dùng khoảng cách Euclidean nên scale của feature ảnh hưởng trực tiếp đến kết quả. Dự án dùng `StandardScaler`:

$$
z = \frac{x - \mu}{\sigma}
$$

Sau chuẩn hóa, mỗi feature có mean ≈ 0 và std ≈ 1, không feature nào "lấn át" hướng phân cụm.

Ngoài ra, với feature lệch cao (skew > 1.0) như `total_spending`, `order_count`, `price` — dự án áp dụng thêm **log transform** trước StandardScaler:

$$
x' = \log(1 + x)
$$

#### Chọn Số Cụm K

**Elbow Method** – vẽ đồ thị Inertia theo K, chọn điểm "khuỷu tay":

$$
\text{Inertia giảm chậm lại ở } K^* \Rightarrow \text{chọn } K^*
$$

**Silhouette Score** – đánh giá chất lượng phân cụm từng điểm:

$$
s(i) = \frac{b(i) - a(i)}{\max(a(i),\, b(i))} \in [-1,\, 1]
$$

Trong đó:
- $a(i)$: khoảng cách trung bình đến điểm **cùng cụm**
- $b(i)$: khoảng cách trung bình đến **cụm gần nhất khác**

| Giá trị | Ý nghĩa |
|---|---|
| Gần **+1** | Phân cụm tốt, điểm nằm sâu trong cụm |
| Gần **0** | Điểm nằm ở ranh giới giữa hai cụm |
| **Âm** | Có khả năng gán nhầm cụm |

Dự án ưu tiên silhouette để chọn K tự động, với tolerance `0.03` (n ≤ 25) hoặc `0.02` (n > 25).

**Heuristic chọn K:**
$$
K_{\text{target}} = \text{round}\!\left(\sqrt{n/2}\right)
$$
rồi chọn giá trị gần nhất trong tập candidate động.

#### Độ Phức Tạp Tính Toán

$$
O(n \cdot K \cdot d \cdot I)
$$

Với $n$ = số điểm, $d$ = số chiều, $K$ = số cụm, $I$ = số vòng lặp.

#### Stability Check (Kiểm Tra Độ Ổn Định)

Chạy lại nhiều seed (42, 52, 62, 72, 82), theo dõi:
- `silhouette_mean`, `silhouette_std`
- `ari_mean` – Adjusted Rand Index trung bình giữa các lần chạy

Nếu `silhouette_std` lớn hoặc `ari_mean` thấp → cảnh báo cụm chưa ổn định.

#### PCA Visualization

Dữ liệu nhiều chiều được chiếu xuống 2D bằng **PCA** để vẽ biểu đồ:
- Trục X = PC1, trục Y = PC2
- Điểm gần nhau → hành vi giống nhau; điểm xa nhau → hành vi khác nhau
- Dấu sao (★) = centroid của cụm

> PCA chỉ dùng để trực quan hóa, **không** thay đổi logic gán nhãn business.

---

### 8.1 Customer Segmentation (`customer_segmentation_service.py`)

**5 features đầu vào:**

| Feature | Ý Nghĩa |
|---|---|
| `total_spending` | Tổng chi tiêu (Monetary) |
| `order_count` | Số lần đặt tour (Frequency) |
| `days_since_last_purchase` | Ngày kể từ lần đặt gần nhất (Recency) |
| `avg_order_value` | Giá trị đơn trung bình |
| `discount_usage_rate` | Tỉ lệ dùng mã giảm giá |

**Tiền xử lý đặc biệt:**
- Tách **cold-start** (user chưa có booking) thành nhóm riêng `Khách mới / Chưa tương tác` trước K-Means để tránh lệch centroid.
- Log transform cho `total_spending`, `order_count`, `avg_order_value` nếu skew > 1.0.

**Rule gán nhãn segment (theo quantile):**

| Nhãn | Điều Kiện |
|---|---|
| `VIP` | spending ≥ p90 **và** orders ≥ p75 |
| `Khách mua nhiều` | spending ≥ p75 **và** orders ≥ p75 |
| `Khách săn sale` | discount_rate cao **và** orders ≥ 1 |
| `Khách ít tương tác` | recency ≥ p60 **hoặc** orders ≤ 0.5 |
| `Khách mới` | orders ≤ 1.5 **và** recency ≤ 90 ngày |
| `Khách trung thành` | fallback còn lại |

Ràng buộc: mỗi nhãn quan trọng chỉ xuất hiện **tối đa 1 lần** (unique label) — nếu nhiều cụm cùng đủ điều kiện, chỉ cụm "mạnh nhất" được gán nhãn đó.

**Output API rebuild:**
```json
{
  "n_clusters": 3,
  "total_groups": 4,
  "clusters": [...],
  "silhouette_data": [...],
  "inertia_data": [...],
  "pca_points": [...],
  "pca_centroids": [...],
  "feature_transforms": { "log1p_applied": ["total_spending", ...] },
  "stability": { "silhouette_mean": 0.42, "silhouette_std": 0.02, "ari_mean": 0.91, "n_runs": 5 }
}
```

---

### 8.2 Tour Clustering (`tour_clustering_service.py`)

**6 features đầu vào:**

| Feature | Ý Nghĩa |
|---|---|
| `booking_count` | Số lượng booking |
| `avg_revenue` | Doanh thu trung bình |
| `fill_rate` | Tỉ lệ lấp đầy capacity |
| `recency_score` | Độ mới (normalized) |
| `price` | Giá tour |
| `vip_rate` | Tỉ lệ khách VIP |

**Tiền xử lý đặc biệt:**
- Tách **dead tours** (hết hạn / quá lâu không booking) thành nhóm riêng.
- `recency_score` được chuẩn hóa robust bằng mốc p95 để giảm ảnh hưởng outlier:

$$
\text{recency\_score} = 1 - \frac{\text{clip}(\text{recency\_days},\, 0,\, p_{95})}{p_{95}}
$$

**Nhãn cluster:** Tour Cao Cấp, Tour Hot, Tour Doanh Thu Cao, Đang Trending, Phổ Biến Giá Rẻ, Tour Ít Khách, Tour Mới Nổi, Tour Ổn Định, v.v.

---

### 8.3 Destination Clustering (`destination_clustering_service.py`)

**Features:** `booking_count`, `tour_count`, `avg_price`, `avg_capacity`, `recency_score`

**Lọc địa điểm trước khi cluster:**
- Loại bỏ địa chỉ cấp thấp: `thôn/khu phố/địa phận/huyện/quận/thị xã/thị trấn`
- Loại bỏ chuỗi quá dài (địa chỉ verbose)

**Endpoint:** `GET /destinations/featured` – TTL cache 180s – dùng cho section "Choose Your Place" ở trang Home.

---

### 8.4 So Sánh Nhanh Customer vs Tour Clustering

| Mục | Customer | Tour |
|---|---|---|
| K candidates | Động theo `sqrt(n/2)` | Động theo `sqrt(n/2)` |
| Số feature | 5 | 6 |
| Tách nhóm đặc thù | Cold-start | Dead tours |
| Chọn K | Heuristic + Silhouette | Heuristic + Silhouette |
| Elbow chart | Có | Có |
| PCA chart | Có | Có |
| Log transform | `total_spending`, `order_count`, `avg_order_value` | `booking_count`, `avg_revenue`, `price` |
| Lưu kết quả DB | `customer_segment` | `tour_cluster` |

---

## 9. Thanh Toán – PayPal & MoMo

### 9.1 PayPal

| Bước | Mô Tả |
|---|---|
| 1 | Frontend gọi `POST /payments/paypal/create-order` |
| 2 | Backend tạo order với PayPal SDK, trả về `approval_url` |
| 3 | User redirect đến PayPal để xác nhận |
| 4 | PayPal redirect về `FRONTEND_BASE_URL/payment-success?token=...` |
| 5 | Frontend gọi `POST /payments/paypal/capture-order` |
| 6 | Backend capture order, cập nhật `payments` table |

**Env vars cần thiết:** `PAYPAL_MODE`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `FRONTEND_BASE_URL`

### 9.2 MoMo

| Bước | Mô Tả |
|---|---|
| 1 | Frontend gọi `POST /momo/create-payment` |
| 2 | Backend ký HMAC-SHA256, gọi MoMo API, trả về `payUrl` |
| 3 | User redirect đến MoMo để xác nhận |
| 4 | MoMo gọi IPN callback về `MOMO_IPN_URL` (backend) |
| 5 | MoMo redirect về `MOMO_REDIRECT_URL` (frontend `MoMoCallback.jsx`) |
| 6 | Backend reconcile qua `pull_bank_txn_and_reconcile.py` |

**Env vars cần thiết:** `MOMO_PARTNER_CODE`, `MOMO_ACCESS_KEY`, `MOMO_SECRET_KEY`, `MOMO_REDIRECT_URL`, `MOMO_IPN_URL`, `MOMO_API_ENDPOINT`, `MOMO_ENVIRONMENT`

### 9.3 Cột Database Thanh Toán

Bảng `payments` yêu cầu các cột sau (cần migrate thủ công nếu schema cũ):
- `PaidAt` (DATETIME)
- `PaypalOrderID` (VARCHAR)
- `PaypalTransactionID` (VARCHAR)
- `UpdatedAt` (DATETIME)

---

## 10. Real-time – WebSocket

**Controller:** `websocket_controller.py` – prefix `/ws`

**Các loại room:**

| Room | Mục Đích |
|---|---|
| `tour:{tour_id}` | Chat real-time giữa passengers trong tour |
| `support:{thread_id}` | Chat hỗ trợ user ↔ admin |
| `admin` | Thông báo global cho admin |

**Lưu ý triển khai:**
- Admin không join room `support:{user_id}` để tránh echo duplicate.
- AI recommendation reply được sinh trong background task để endpoint trả về nhanh.
- Client tự recover khi nhận 401/403 bằng cách reopen valid thread.

---

## 11. Xác Thực & Phân Quyền

### 11.1 JWT Authentication

- **Library:** `python-jose`
- Token gồm: `user_id`, `role_name`, `exp`
- `auth_dependencies.py` cung cấp:
  - `get_current_user()` – verify token, trả về user object
  - `require_admin()` – raise 403 nếu không phải Admin
  - `require_admin_or_guide()` – cho Guide access

### 11.2 Phân Quyền 3 Cấp

| Role | Quyền |
|---|---|
| **Admin** | Toàn quyền; không thể tự xóa bản thân hoặc thay đổi role của chính mình |
| **Guide** | Xem tour được giao, xem booking & thông tin khách của tour mình; không sửa/xóa tour |
| **User** | Đặt tour, hủy booking (chưa confirmed), comment & rate (chỉ tour đã đặt) |

> Admin detection trong support routes dùng cả `RoleID` lẫn `RoleName` để xử lý đúng khi user offline.

---

## 12. Triển Khai – Docker Compose

### 12.1 Services

| Service | Image | Port |
|---|---|---|
| `mysql` | `mysql:8.0` | 3306 |
| `redis` | `redis:7-alpine` | 6379 |
| `backend` | `rag-backend` (build `./backend`) | 8000 |
| `frontend` | `rag-frontend` (build `./frontend`) | 3000 |
| `phpmyadmin` | `phpmyadmin:latest` | 8080 |

### 12.2 Lệnh Triển Khai

```bash
# Build và khởi động toàn bộ
docker compose build
docker compose up

# Chỉ rebuild backend sau khi sửa code Python
docker compose build backend
docker compose up -d backend

# Rebuild RAG index trong container đang chạy
docker exec backend python build_rag_index.py

# Xem log backend
docker compose logs -f backend
```

> **Quan trọng:** Container `nhom09_backend` không mount source code từ host. Mọi thay đổi Python đều cần `docker compose build backend` mới có hiệu lực.

### 12.3 Volumes

| Volume | Mục Đích |
|---|---|
| `mysql_data` | Persistent data MySQL |
| `uploads_data` | File upload (ảnh tour) |

### 12.4 Health Check

MySQL service có healthcheck bằng `mysqladmin ping`. Backend và Frontend chờ MySQL healthy mới start.

---

## 13. Biến Môi Trường Quan Trọng

### Backend

| Biến | Mặc Định | Mô Tả |
|---|---|---|
| `DATABASE_URL` | – | SQLAlchemy connection string |
| `OPENAI_API_KEY` | optional | API key OpenAI (nếu không có, dùng TF-IDF local) |
| `PAYPAL_MODE` | `sandbox` | `sandbox` hoặc `live` |
| `PAYPAL_CLIENT_ID` | – | PayPal client ID |
| `PAYPAL_CLIENT_SECRET` | – | PayPal client secret |
| `FRONTEND_BASE_URL` | `http://localhost:3000` | URL frontend (PayPal redirect) |
| `MOMO_PARTNER_CODE` | – | MoMo partner code |
| `MOMO_ACCESS_KEY` | – | MoMo access key |
| `MOMO_SECRET_KEY` | – | MoMo secret key |
| `MOMO_REDIRECT_URL` | – | URL redirect sau thanh toán MoMo |
| `MOMO_IPN_URL` | – | URL nhận IPN từ MoMo |
| `MOMO_API_ENDPOINT` | `https://test-payment.momo.vn/...` | MoMo API endpoint |
| `RAG_REDIS_ENABLED` | `true` | Bật Redis cho RAG cache |
| `RAG_REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |

### RAG Tuning Vars

| Biến | Mô Tả |
|---|---|
| `RAG_SEARCH_MULTIPLIER` | Số candidate dense theo top_k |
| `RAG_LEXICAL_SEARCH_MULTIPLIER` | Số candidate BM25 theo top_k |
| `RAG_MIN_SEARCH_K` / `RAG_MAX_SEARCH_K` | Giới hạn candidate pool |
| `RAG_HYBRID_DENSE_WEIGHT` / `RAG_HYBRID_LEXICAL_WEIGHT` | Trọng số hybrid retrieval |
| `RAG_QUERY_CACHE_TTL_SECONDS` | TTL query embedding cache |
| `RAG_RESPONSE_CACHE_TTL_SECONDS` | TTL response cache |
| `RAG_EMBEDDING_BATCH_SIZE` | Batch size khi build embedding |
| `RAG_CHUNK_SIZE_WORDS` | Số từ mỗi chunk |
| `RAG_CHUNK_OVERLAP_SENTENCES` | Overlap giữa các chunk |
| `RAG_ANSWER_TEMPERATURE` | Temperature LLM |
| `RAG_ANSWER_MAX_TOKENS` | Max tokens câu trả lời |

### Frontend

| Biến | Mô Tả |
|---|---|
| `VITE_API_URL` | URL backend API (ví dụ: `http://backend:8000`) |

---

## 14. Các Vấn Đề & Giải Pháp Đã Ghi Nhận

| Vấn Đề | Nguyên Nhân | Giải Pháp |
|---|---|---|
| Support chat gửi tin duplicate | Admin join room `support:user` + WebSocket echo trước API response | Xóa redundant join, dùng optimistic UI đúng cách |
| Admin send message lỗi khi user offline | Check RoleID cứng trong support routes | Dùng cả `RoleName` để detect admin |
| Thanh toán PayPal/MoMo lỗi | URL hardcode EC2 trong frontend service | Dùng env var `VITE_API_URL` |
| Payment schema thiếu cột | MySQL không hỗ trợ `ADD COLUMN IF NOT EXISTS` | Check cột tồn tại trước, migrate thủ công |
| Admin add-tour màn trắng | `TourForm` nhận `null` thay vì `{}` | Normalize `null → {}` trước khi truyền vào form |
| RAG không update sau sửa code | Docker image không mount source code | Rebuild image: `docker compose build backend` |
| Chatbot trả lời sai tour | Cache key không có `focus_tour_id` | Thêm `focus_tour_id` vào response cache key |
| User chat 401 do stale token | Thread/token state cũ | Auto-recover bằng cách reopen valid thread trên client |
| "Choose Your Place" hiển thị địa chỉ dài | Không filter trước K-Means | Filter địa chỉ cấp thấp và chuỗi dài trước clustering |
| RAG embedding cache stale sau rebuild | Cache key không bao gồm `built_at` | Thêm `built_at` từ `state.json` vào cache key |

---

*Tài liệu được tổng hợp ngày 05/05/2026 từ toàn bộ source code, README và ghi chú quá trình phát triển.*
