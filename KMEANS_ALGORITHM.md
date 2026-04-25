# K-Means Toan Tap Va Cach Ap Dung Trong He Thong

## 1. K-Means La Gi?

K-Means la thuat toan phan cum khong giam sat, chia tap du lieu thanh K nhom sao cho cac diem trong cung nhom gan nhau nhat co the.

Muc tieu toi uu la giam tong binh phuong khoang cach tu diem den tam cum (centroid):

$$
\text{Inertia} = \sum_{i=1}^{K}\sum_{x\in C_i}\lVert x - \mu_i \rVert^2
$$

Trong do:
- $C_i$: tap diem thuoc cum $i$
- $\mu_i$: centroid cua cum $i$

Gia tri inertia cang nho thi cum cang compact.

---

## 2. Quy Trinh Lloyd (Phien Ban Pho Bien Cua K-Means)

1. Chon so cum K.
2. Khoi tao K centroid ban dau (ngau nhien hoac k-means++).
3. Assignment step:
   Moi diem du lieu duoc gan vao cum co centroid gan nhat.
4. Update step:
   Cap nhat centroid bang trung binh cac diem trong cum.
5. Lap lai buoc 3-4 den khi hoi tu (gan nhu khong doi nhan, hoac inertia giam rat nho).

Du an dang dung `sklearn KMeans(n_init=10, random_state=42)` de tang do on dinh ket qua.

---

## 3. Vi Sao Can Chuan Hoa Du Lieu?

K-Means dung khoang cach Euclidean, nen scale cua feature anh huong truc tiep den ket qua.

Vi du:
- Feature A trong khoang 0-1
- Feature B trong khoang 0-1000000

Neu khong chuan hoa, feature B se "de" toan bo huong phan cum.

Do do he thong dung `StandardScaler`:

$$
z = \frac{x - \mu}{\sigma}
$$

sau chuan hoa, moi feature co mean gan 0 va std gan 1.

---

## 4. Chon So Cum K Nhu The Nao?

### 4.1 Elbow Method

Ve do thi Inertia theo K:
- K tang -> Inertia giam.
- Chon diem "khuyu tay" (muc giam bat dau cham lai).

Elbow mang tinh goc nhin truc quan, rat huu ich cho admin dashboard.

### 4.2 Silhouette Score

Silhouette cua mot diem:

$$
s(i)=\frac{b(i)-a(i)}{\max(a(i), b(i))} \in [-1,1]
$$

Trong do:
- $a(i)$: khoang cach trung binh den diem cung cum
- $b(i)$: khoang cach trung binh den cum gan nhat khac

Dien giai:
- Gan 1: phan cum tot
- Gan 0: nam o ranh gioi cum
- Am: co kha nang gan nham cum

He thong uu tien silhouette de chon K tu dong.

---

## 5. Do Phuc Tap Tinh Toan

Voi:
- $n$: so diem
- $d$: so chieu
- $K$: so cum
- $I$: so vong lap

Do phuc tap xap xi:

$$
O(n \cdot K \cdot d \cdot I)
$$

Do do khi du lieu lon:
- can gioi han K hop ly
- can toi uu feature
- can can nhac MiniBatchKMeans neu scale rat lon

---

## 6. Cac Van De Thuong Gap Cua K-Means

1. Nhay cam voi outlier.
2. Gia dinh cum dang "tron" trong khong gian Euclidean.
3. Can xac dinh truoc K.
4. Nhay cam voi khoi tao ban dau.

Cach giam thieu trong he thong:
- Tien xu ly tach nhom dac thu (cold-start, dead tours)
- Chuan hoa feature
- Dung `n_init=10`
- So sanh silhouette giua cac K candidate

---

## 7. Ap Dung Trong Du An: Customer Segmentation

### 7.1 File lien quan
- `backend/app/services/customer_segmentation_service.py`

### 7.2 Feature dau vao (5 chieu)
- `total_spending` (Monetary)
- `order_count` (Frequency)
- `days_since_last_purchase` (Recency)
- `avg_order_value`
- `discount_usage_rate`

### 7.3 Tien xu ly
- Tach cold-start: nguoi dung chua co booking duoc dua vao nhom rieng `Khach moi / Chua tuong tac`.
- Khong dua nhom nay vao K-Means chinh de tranh lam lech centroid.
- Chuan hoa bang `StandardScaler`.

### 7.4 Chon K
- Candidate: `{3, 5}`
- Heuristic: `target_k = sqrt(n/2)` roi chon gia tri gan nhat trong `{3, 5}`
- Chay thu silhouette cho tung K candidate
- Dung tolerance:
  - `0.03` neu n <= 25
  - `0.02` neu n > 25
- Neu silhouette cua K khac vuot qua tolerance thi doi K.

### 7.5 Rule gan nhan segment
Rule theo quantile:
- VIP: spending >= p90 va orders >= p75
- Khach mua nhieu: spending >= p75 va orders >= p75
- Khach san sale: discount_rate cao va orders >= 1
- Khach it tuong tac: recency >= p60 hoac orders <= 0.5
- Khach moi: orders <= 1.5 va recency <= 90 ngay
- Khach trung thanh: fallback

### 7.6 Rang buoc unique label
He thong da bo sung rang buoc: cac nhan quan trong chi xuat hien toi da 1 lan (VIP, Khach mua nhieu, Khach san sale, Khach it tuong tac, Khach moi). Cac cum con lai fallback ve `Khach trung thanh`.

### 7.7 Output chinh
API rebuild tra ve:
- `n_clusters`: so cum K-Means thuc
- `total_groups`: tong nhom hien thi (co the bao gom cold-start)
- `clusters`: thong ke tung nhom
- `silhouette_data`, `inertia_data`
- `pca_points`, `pca_centroids` (de ve chart)

---

## 8. Ap Dung Trong Du An: Tour Clustering

### 8.1 File lien quan
- `backend/app/services/tour_clustering_service.py`

### 8.2 Feature dau vao (6 chieu)
- `booking_count`
- `avg_revenue`
- `fill_rate`
- `recency_score`
- `price`
- `vip_rate`

### 8.3 Tien xu ly
- Tach dead tours (het han / khong mo ban / qua lau khong booking) thanh nhom rieng de khong lam nhiu K-Means chinh.
- Chuan hoa du lieu truoc khi fit.

### 8.4 Chon K
- Candidate: `{3, 5, 7}`
- Heuristic: K gan `sqrt(n/2)`
- Danh gia bang silhouette + inertia

### 8.5 Rule gan nhan tour cluster
Theo global mean:
- Tour Cao Cap
- Tour Hot
- Tour Doanh Thu Cao
- Dang Trending
- Cao Cap It Khach
- Pho Bien Gia Re
- Tour It Khach
- Tour Moi Noi
- Tour On Dinh (fallback)
- Dead tours gan nhan rieng

### 8.6 Output chinh
- `clusters`, `tours`
- `n_clusters`, `total_groups`
- `silhouette_score`, `silhouette_data`, `inertia_data`
- `pca_x`, `pca_y`, `centroid_x`, `centroid_y`

---

## 9. PCA Trong Dashboard Nghia La Gi?

PCA (Principal Component Analysis) duoc dung de chieu du lieu nhieu chieu xuong 2D de ve.

- Truc X la PCA 1
- Truc Y la PCA 2

Cac gia tri nhu `-3.92, -1.66, 0.60, 2.86, 5.12` la toa do tren truc PCA, khong phai don vi nghiep vu (khong phai VND, khong phai so don).

Y nghia:
- Diem gan nhau -> hanh vi giong nhau
- Diem xa nhau -> hanh vi khac nhau
- Sao do (centroid) la tam cua cum

PCA dung de truc quan hoa, khong thay doi logic gan nhan business.

---

## 10. Huong Dan Van Hanh Nhanh

1. Vao trang admin clustering.
2. Chon mode Auto hoac K co dinh.
3. Bam Rebuild.
4. Kiem tra:
   - K dang dung
   - Silhouette
   - Elbow
   - Bang nhan cum
   - Vi tri cum tren chart PCA

Neu ket qua "nhin giong cu":
- Kha nang cao do du lieu dau vao chua thay doi nhieu.
- K-Means dung `random_state=42` nen ket qua on dinh qua cac lan chay.

---

## 11. Checklist Chat Luong Ket Qua

- Silhouette khong qua thap
- Cum co y nghia nghiep vu ro rang
- Nhom cold-start / dead tours da tach rieng
- Khong co nhan quan trong bi trung (voi customer)
- K trong API thong nhat voi K hien thi UI

---

## 12. Tham So Nhanh

| Muc | Customer | Tour |
|---|---|---|
| K candidates | {3, 5} | {3, 5, 7} |
| So feature | 5 | 6 |
| Tach nhom dac thu | Cold-start | Dead tours |
| Chon K | Heuristic + Silhouette | Heuristic + Silhouette |
| Elbow | Co (quan sat) | Co (quan sat) |
| PCA chart | Co | Co |
| Luu ket qua DB | customer_segment | tour_cluster |

---

## 13. Ghi Chu Trien Khai

- K-Means phu hop cho segmentation nhanh, de giai thich.
- Neu du lieu lon va thay doi lien tuc, can xem xet:
  - lich rebuild dinh ky
  - canh bao drift
  - mini-batch hoac online clustering
- Tieu chi nghiep vu cuoi cung van quan trong hon metric thuan ML.
