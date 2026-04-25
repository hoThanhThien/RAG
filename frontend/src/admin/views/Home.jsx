import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { adminService } from "../services/adminService";
import { connectAdminDashboardWS } from "../../client/services/ws";
import { Link } from "react-router-dom";
import { 
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

// Giải mã hex color sang RGB
function hexToRgb(hex) {
  return [
    parseInt(hex.slice(1, 3), 16),
    parseInt(hex.slice(3, 5), 16),
    parseInt(hex.slice(5, 7), 16),
  ];
}

const CLUSTER_COLORS = [
  '#4e79a7', '#f28e2b', '#e15759', '#76b7b2',
  '#59a14f', '#edc948', '#b07aa1', '#ff9da7',
  '#9c755f', '#bab0ac', '#d4a373', '#a2d2ff',
];

// Xóa emoji đứng đầu chuỗi insight
function stripEmoji(s) {
  return (s || '').replace(/^(\p{Emoji_Presentation}|\p{Extended_Pictographic})+\s*/u, '');
}

function formatAxisTick(value) {
  return Number(value || 0).toFixed(2);
}

// Tạo path SVG hình ngôi sao 5 cánh
function starPath(cx, cy, outerR = 9, innerR = 3.6, pts = 5) {
  let d = '';
  for (let i = 0; i < pts * 2; i++) {
    const angle = (i * Math.PI / pts) - Math.PI / 2;
    const r = i % 2 === 0 ? outerR : innerR;
    const x = cx + r * Math.cos(angle);
    const y = cy + r * Math.sin(angle);
    d += (i === 0 ? 'M' : 'L') + `${x.toFixed(2)},${y.toFixed(2)}`;
  }
  return d + 'Z';
}

// Dashboard admin với biểu đồ doanh thu theo địa điểm
const AdminHome = () => {
  const [stats, setStats] = useState({
    users: 0,
    tours: 0,
    categories: 0,
    discounts: 0,
    bookings: 0,
    revenue: 0
  });
  const [topCustomers, setTopCustomers] = useState([]);
  const [bookingStatus, setBookingStatus] = useState([]);
  const [locationRevenue, setLocationRevenue] = useState([]);
  const [kmeansData, setKmeansData] = useState({ locations: [], clusters: [], total: 0, n_clusters: 0 });
  const [topCustomerSegments, setTopCustomerSegments] = useState({});
  const [kmeansLoading, setKmeansLoading] = useState(false);
  const [kmeansHovered, setKmeansHovered] = useState(null);
  const kmeansCanvasRef = useRef(null);

  // Tính bounds PCA space để map sang canvas pixel
  // Dùng inlier để tránh outlier kéo giãn tọa độ làm điểm chính bị dồn góc
  const kmeansBounds = useMemo(() => {
    if (!kmeansData.locations.length) return null;
    const inliers = kmeansData.locations.filter(l => !l.is_outlier);
    const src = inliers.length >= 2 ? inliers : kmeansData.locations;
    const xs = src.map(l => l.pca_x);
    const ys = src.map(l => l.pca_y);
    const pad = 0.18;
    const rX = (Math.max(...xs) - Math.min(...xs)) || 2;
    const rY = (Math.max(...ys) - Math.min(...ys)) || 2;
    return {
      minX: Math.min(...xs) - rX * pad,
      maxX: Math.max(...xs) + rX * pad,
      minY: Math.min(...ys) - rY * pad,
      maxY: Math.max(...ys) + rY * pad,
    };
  }, [kmeansData.locations]);

  // Vẽ Voronoi tessellation lên canvas: mỗi pixel tô màu theo centroid gần nhất
  useEffect(() => {
    const canvas = kmeansCanvasRef.current;
    if (!canvas || !kmeansData.clusters.length || !kmeansBounds) return;
    const W = 300, H = 220;
    const { minX, maxX, minY, maxY } = kmeansBounds;
    const centroids = kmeansData.clusters.map(c => ({
      id: c.cluster_id,
      px: ((c.centroid_x - minX) / (maxX - minX)) * W,
      py: H - ((c.centroid_y - minY) / (maxY - minY)) * H,
    }));
    const ctx = canvas.getContext('2d');
    const imageData = ctx.createImageData(W, H);
    for (let py = 0; py < H; py++) {
      for (let px = 0; px < W; px++) {
        let nearest = 0, minDist = Infinity;
        for (const c of centroids) {
          const dx = px - c.px, dy = py - c.py;
          const d = dx * dx + dy * dy;
          if (d < minDist) { minDist = d; nearest = c.id; }
        }
        const [r, g, b] = hexToRgb(CLUSTER_COLORS[nearest % CLUSTER_COLORS.length]);
        const idx = (py * W + px) * 4;
        imageData.data[idx] = r;
        imageData.data[idx + 1] = g;
        imageData.data[idx + 2] = b;
        imageData.data[idx + 3] = 110;
      }
    }
    ctx.putImageData(imageData, 0, 0);
  }, [kmeansData, kmeansBounds]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [isAdmin, setIsAdmin] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [locationFilter, setLocationFilter] = useState('all'); // 'all', 'domestic', 'international'
  const wsRef = useRef(null);
  const hasLoadedRef = useRef(false);

  // Load dashboard data
  const loadDashboardData = useCallback(async ({ source = 'background' } = {}) => {
    const showFullLoader = source === 'initial' && !hasLoadedRef.current;
    const showManualRefresh = source === 'manual';

    try {
      if (showFullLoader) {
        setLoading(true);
      }
      if (showManualRefresh) {
        setRefreshing(true);
      }
      
      // Thử gọi API admin mới trước
      try {
        const [statsData, locationData, customers, statusData] = await Promise.all([
          adminService.getDashboardStats(),
          adminService.getRevenueByLocation(locationFilter !== 'all' ? locationFilter : null),
          adminService.getTopCustomers(),
          adminService.getBookingStatus()
        ]);

        setIsAdmin(true);
        setErrorMessage('');
        setStats(statsData);
        setLocationRevenue(locationData);
        setTopCustomers(customers);
        setBookingStatus(statusData);
        setLastUpdate(new Date());

        // Load K-Means data không block render chính
        setKmeansLoading(true);
        adminService.getKmeansDestinations(8)
          .then(data => setKmeansData(data || { locations: [], clusters: [], total: 0, n_clusters: 0 }))
          .catch(() => {})
          .finally(() => setKmeansLoading(false));
      } catch (adminError) {
        // Nếu lỗi 403, có thể không phải admin - dùng dữ liệu cơ bản
        console.warn("Cannot load admin dashboard data, user may not be admin:", adminError);
        
        if (adminError.response?.status === 403) {
          setIsAdmin(false);
          setErrorMessage('Bạn không có quyền truy cập dashboard admin. Vui lòng đăng nhập bằng tài khoản admin.');
        }
        
        // Load basic stats from old endpoints
        const { fetchUsers } = await import("../services/userService");
        const { getTours } = await import("../services/tourService");
        const { fetchCategories } = await import("../services/categoryService");
        const { fetchDiscounts } = await import("../services/discountService");
        
        const [users, toursRes, categories, discounts] = await Promise.all([
          fetchUsers(),
          getTours(),
          fetchCategories(),
          fetchDiscounts(),
        ]);

        setStats({
          users: users.length,
          tours: toursRes.data?.items?.length || 0,
          categories: categories.length,
          discounts: discounts.length,
          bookings: 0,
          revenue: 0
        });
        setLastUpdate(new Date());
        
        // Empty arrays for charts since we don't have data
        setLocationRevenue([]);
        setTopCustomers([]);
        setBookingStatus([]);
        setTopCustomerSegments({});
      }
    } catch (error) {
      console.error("❌ Lỗi khi load dữ liệu dashboard:", error);
    } finally {
      hasLoadedRef.current = true;
      setLoading(false);
      setRefreshing(false);
    }
  }, [locationFilter]);

  useEffect(() => {
    let cancelled = false;

    const enrichTopCustomersWithSegments = async () => {
      if (!isAdmin || topCustomers.length === 0) {
        setTopCustomerSegments({});
        return;
      }

      try {
        const entries = await Promise.all(
          topCustomers.slice(0, 5).map(async (customer) => {
            try {
              const segment = await adminService.getCustomerSegment(customer.user_id);
              return [customer.user_id, segment];
            } catch {
              return [customer.user_id, null];
            }
          })
        );

        if (!cancelled) {
          setTopCustomerSegments(
            Object.fromEntries(entries.filter(([, segment]) => Boolean(segment)))
          );
        }
      } catch {
        if (!cancelled) {
          setTopCustomerSegments({});
        }
      }
    };

    enrichTopCustomersWithSegments();

    return () => {
      cancelled = true;
    };
  }, [isAdmin, topCustomers]);

  // Load data on mount and when filter changes
  useEffect(() => {
    loadDashboardData({ source: 'initial' });
  }, [loadDashboardData]);

  // Realtime updates via WebSocket without reloading the page
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const ws = connectAdminDashboardWS(token);
    wsRef.current = ws;

    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg?.type === 'dashboard:refresh') {
          loadDashboardData({ source: 'background' });
        }
      } catch (err) {
        console.warn('Dashboard WS parse error:', err);
      }
    };

    return () => {
      setWsConnected(false);
      try {
        ws.close();
      } catch {
        // ignore close error
      }
    };
  }, [loadDashboardData]);

  // Fallback polling in case WS is temporarily unavailable
  useEffect(() => {
    const interval = setInterval(() => {
      loadDashboardData({ source: 'background' });
    }, 20000);

    return () => clearInterval(interval);
  }, [loadDashboardData]);

  // Refresh again when the tab becomes active
  useEffect(() => {
    const handleVisible = () => {
      if (document.visibilityState === 'visible') {
        loadDashboardData({ source: 'background' });
      }
    };

    window.addEventListener('focus', handleVisible);
    document.addEventListener('visibilitychange', handleVisible);

    return () => {
      window.removeEventListener('focus', handleVisible);
      document.removeEventListener('visibilitychange', handleVisible);
    };
  }, [loadDashboardData]);


  const formatCurrency = (value) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND'
    }).format(value);
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];
  const STATUS_COLORS = {
    'Pending': '#ffc107',
    'Confirmed': '#28a745',
    'Paid': '#007bff',
    'Cancelled': '#dc3545'
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '80vh' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid mt-4 px-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2 className="fw-bold text-primary mb-0">
          <i className="bi bi-speedometer2 me-2"></i>
          Bảng điều khiển Admin
        </h2>
        <div className="d-flex align-items-center gap-3">
          <small className="text-muted d-flex align-items-center gap-2">
            <span>
              <i className="bi bi-clock me-1"></i>
              Cập nhật: {lastUpdate.toLocaleTimeString('vi-VN')}
            </span>
            <span className={`badge ${wsConnected ? 'text-bg-success' : 'text-bg-warning'}`}>
              {wsConnected ? 'Live' : 'Đang đồng bộ'}
            </span>
          </small>
          <button 
            className="btn btn-sm btn-outline-primary"
            onClick={() => loadDashboardData({ source: 'manual' })}
            disabled={loading || refreshing}
          >
            <i className={`bi bi-arrow-clockwise me-1 ${(loading || refreshing) ? 'spin' : ''}`}></i>
            {refreshing ? 'Đang cập nhật...' : 'Làm mới'}
          </button>
        </div>
      </div>

      {/* Hiển thị cảnh báo nếu không phải admin */}
      {!isAdmin && errorMessage && (
        <div className="alert alert-warning alert-dismissible fade show" role="alert">
          <i className="bi bi-exclamation-triangle-fill me-2"></i>
          <strong>Cảnh báo:</strong> {errorMessage}
          <button type="button" className="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
      )}

      {/* Thống kê tổng quan */}
      <div className="row g-4 mb-4">
        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100" style={{ borderLeft: '4px solid #007bff' }}>
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Người dùng
                  </h6>
                  <h3 className="fw-bold mb-0 text-primary">{stats.users}</h3>
                </div>
                <div className="bg-primary bg-opacity-10 rounded-circle p-3">
                  <i className="bi bi-people-fill fs-3 text-primary"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100" style={{ borderLeft: '4px solid #28a745' }}>
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Tour
                  </h6>
                  <h3 className="fw-bold mb-0 text-success">{stats.tours}</h3>
                </div>
                <div className="bg-success bg-opacity-10 rounded-circle p-3">
                  <i className="bi bi-globe fs-3 text-success"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100" style={{ borderLeft: '4px solid #ffc107' }}>
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Danh mục
                  </h6>
                  <h3 className="fw-bold mb-0 text-warning">{stats.categories}</h3>
                </div>
                <div className="bg-warning bg-opacity-10 rounded-circle p-3">
                  <i className="bi bi-tag-fill fs-3 text-warning"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100" style={{ borderLeft: '4px solid #dc3545' }}>
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Giảm giá
                  </h6>
                  <h3 className="fw-bold mb-0 text-danger">{stats.discounts}</h3>
                </div>
                <div className="bg-danger bg-opacity-10 rounded-circle p-3">
                  <i className="bi bi-percent fs-3 text-danger"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100" style={{ borderLeft: '4px solid #17a2b8' }}>
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Đặt tour
                  </h6>
                  <h3 className="fw-bold mb-0 text-info">{stats.bookings}</h3>
                </div>
                <div className="bg-info bg-opacity-10 rounded-circle p-3">
                  <i className="bi bi-calendar-check fs-3 text-info"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-xl-2 col-md-4 col-sm-6">
          <div className="card border-0 shadow-sm h-100" style={{ borderLeft: '4px solid #6f42c1' }}>
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Doanh thu
                  </h6>
                  <h4 className="fw-bold mb-0" style={{ color: '#6f42c1', fontSize: '1.5rem' }}>
                    {formatCurrency(stats.revenue).split('₫')[0]}đ
                  </h4>
                </div>
                <div className="rounded-circle p-3" style={{ backgroundColor: 'rgba(111, 66, 193, 0.1)' }}>
                  <i className="bi bi-cash-stack fs-3" style={{ color: '#6f42c1' }}></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Biểu đồ và thống kê - hiển thị khi là admin */}
      {isAdmin && (
        <div className="row g-4 mb-4">
        {/* Biểu đồ doanh thu theo địa điểm */}
        <div className="col-lg-8">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-header bg-white border-0 py-3">
              <div className="d-flex justify-content-between align-items-center">
                <h5 className="mb-0 fw-bold">
                  <i className="bi bi-geo-alt-fill me-2 text-primary"></i>
                  Doanh thu theo địa điểm
                </h5>
                <div className="btn-group btn-group-sm" role="group">
                  <button 
                    type="button" 
                    className={`btn ${locationFilter === 'all' ? 'btn-primary' : 'btn-outline-primary'}`}
                    onClick={() => setLocationFilter('all')}
                  >
                    <i className="bi bi-globe me-1"></i>
                    Tất cả
                  </button>
                  <button 
                    type="button" 
                    className={`btn ${locationFilter === 'domestic' ? 'btn-primary' : 'btn-outline-primary'}`}
                    onClick={() => setLocationFilter('domestic')}
                  >
                    <i className="bi bi-flag me-1"></i>
                    Trong nước
                  </button>
                  <button 
                    type="button" 
                    className={`btn ${locationFilter === 'international' ? 'btn-primary' : 'btn-outline-primary'}`}
                    onClick={() => setLocationFilter('international')}
                  >
                    <i className="bi bi-airplane me-1"></i>
                    Ngoài nước
                  </button>
                </div>
              </div>
            </div>
            <div className="card-body">
              {locationRevenue.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={locationRevenue} margin={{ top: 5, right: 30, left: 20, bottom: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="location" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                      interval={0}
                    />
                    <YAxis tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`} />
                    <Tooltip 
                      formatter={(value, name) => {
                        if (name === 'revenue') return [formatCurrency(value), 'Doanh thu'];
                        if (name === 'total_bookings') return [value, 'Số lần booking'];
                        return [value, name];
                      }}
                      labelFormatter={(label) => `Địa điểm: ${label}`}
                    />
                    <Legend 
                      formatter={(value) => {
                        if (value === 'revenue') return 'Doanh thu';
                        if (value === 'total_bookings') return 'Số lần booking';
                        return value;
                      }}
                    />
                    <Bar dataKey="revenue" fill="#8884d8" radius={[8, 8, 0, 0]} name="Doanh thu" />
                    <Bar dataKey="total_bookings" fill="#82ca9d" radius={[8, 8, 0, 0]} name="Số lần booking" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-center py-5 text-muted">
                  <i className="bi bi-inbox fs-1 d-block mb-2"></i>
                  <p>Chưa có dữ liệu doanh thu theo địa điểm</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Biểu đồ tròn trạng thái booking */}
        <div className="col-lg-4">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-header bg-white border-0 py-3">
              <h5 className="mb-0 fw-bold">
                <i className="bi bi-pie-chart me-2 text-success"></i>
                Trạng thái đặt tour
              </h5>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={bookingStatus}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                    nameKey="status"
                  >
                    {bookingStatus.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={STATUS_COLORS[entry.status] || COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
      )}

      {/* Biểu đồ K-Means phân cụm điểm đến */}
      {isAdmin && (
        <div className="row g-4 mb-4">
          <div className="col-12">
            <div className="card border-0 shadow-sm">
              <div className="card-header bg-white border-0 py-3">
                <div className="d-flex justify-content-between align-items-center">
                  <h5 className="mb-0 fw-bold">
                    <i className="bi bi-diagram-3-fill me-2 text-info"></i>
                    Phân cụm điểm đến – K-Means
                    {kmeansData.n_clusters > 0 && (
                      <span className="badge bg-info ms-2" style={{ fontSize: '0.7rem' }}>
                        {kmeansData.n_clusters} nhóm / {kmeansData.total} điểm
                      </span>
                    )}
                    {kmeansData.auto_selected && kmeansData.optimal_k > 0 && (
                      <span className="badge bg-success ms-1" style={{ fontSize: '0.65rem' }}>
                        K={kmeansData.optimal_k} tự động
                      </span>
                    )}
                    {kmeansData.silhouette_score > 0 && (
                      <span className="badge bg-secondary ms-1" style={{ fontSize: '0.65rem' }}>
                        Silhouette {kmeansData.silhouette_score.toFixed(3)}
                      </span>
                    )}
                    {kmeansData.outlier_count > 0 && (
                      <span className="badge bg-warning text-dark ms-1" style={{ fontSize: '0.65rem' }}>
                        {kmeansData.outlier_count} ngoại lai
                      </span>
                    )}
                  </h5>
                  <small className="text-muted">
                    <i className="bi bi-info-circle me-1"></i>
                    Mỗi điểm = 1 địa điểm &nbsp;·&nbsp; Màu/vùng = Nhóm cluster &nbsp;·&nbsp; ★ = đại diện nhóm
                  </small>
                </div>
                <div className="mt-3 d-flex justify-content-end">
                  <Link to="/admin/clustering" className="btn btn-sm btn-outline-primary">
                    <i className="bi bi-box-arrow-up-right me-1"></i>
                    Xem trang phân cụm khách hàng / tour
                  </Link>
                </div>
              </div>
              <div className="card-body">
                {kmeansLoading ? (
                  <div className="text-center py-5 text-muted">
                    <div className="spinner-border spinner-border-sm me-2" role="status" />
                    Đang phân tích K-Means...
                  </div>
                ) : kmeansData.locations.length === 0 ? (
                  <div className="text-center py-5 text-muted">
                    <i className="bi bi-inbox fs-1 d-block mb-2"></i>
                    <p>Chưa có dữ liệu điểm đến để phân cụm</p>
                  </div>
                ) : (
                  <div className="row g-3">
                    {/* Scatter plot K-Means – style như reference image */}
                    <div className="col-lg-8">
                      <div style={{ position: 'relative' }}>
                        <svg
                          viewBox="0 0 560 340"
                          style={{ width: '100%', height: 'auto', background: '#fafafa', borderRadius: 8, display: 'block' }}
                        >
                          {kmeansBounds && (() => {
                            const { minX, maxX, minY, maxY } = kmeansBounds;
                            const ML = 52, MT = 38, MB = 36, plotRight = 390;
                            const W = plotRight - ML;
                            const H = 340 - MT - MB;
                            const legendX = 402;
                            const inlierLocations = kmeansData.locations.filter(loc => !loc.is_outlier);
                            const outlierLocations = kmeansData.locations.filter(loc => loc.is_outlier);
                            const toX = v => ML + ((v - minX) / (maxX - minX)) * W;
                            const toY = v => MT + H - ((v - minY) / (maxY - minY)) * H;
                            const nTicks = 5;
                            const xTicks = Array.from({ length: nTicks }, (_, i) => minX + (maxX - minX) * i / (nTicks - 1));
                            const yTicks = Array.from({ length: nTicks }, (_, i) => minY + (maxY - minY) * i / (nTicks - 1));
                            return (
                              <>
                                {/* Title */}
                                <text x={ML + W / 2} y={22} textAnchor="middle" fontSize={13} fontWeight="bold" fill="#333" fontFamily="sans-serif">
                                  Phân cụm K-Means – Điểm đến
                                </text>

                                {/* Plot background */}
                                <rect x={ML} y={MT} width={W} height={H} fill="white" />

                                {/* Vertical grid lines + X axis labels */}
                                {xTicks.map((v, i) => {
                                  const x = toX(v);
                                  return (
                                    <g key={`xt-${i}`}>
                                      <line x1={x} y1={MT} x2={x} y2={MT + H} stroke="#e4e4e4" strokeWidth={1} />
                                      <text x={x} y={MT + H + 16} textAnchor="middle" fontSize={10} fill="#888" fontFamily="sans-serif">
                                        {formatAxisTick(v)}
                                      </text>
                                    </g>
                                  );
                                })}

                                {/* Horizontal grid lines + Y axis labels */}
                                {yTicks.map((v, i) => {
                                  const y = toY(v);
                                  return (
                                    <g key={`yt-${i}`}>
                                      <line x1={ML} y1={y} x2={plotRight} y2={y} stroke="#e4e4e4" strokeWidth={1} />
                                      <text x={ML - 7} y={y + 4} textAnchor="end" fontSize={10} fill="#888" fontFamily="sans-serif">
                                        {formatAxisTick(v)}
                                      </text>
                                    </g>
                                  );
                                })}

                                {/* Plot border */}
                                <rect x={ML} y={MT} width={W} height={H} fill="none" stroke="#ccc" strokeWidth={1} />

                                {/* Axis titles */}
                                <text
                                  x={ML + W / 2}
                                  y={MT + H + 32}
                                  textAnchor="middle"
                                  fontSize={11}
                                  fontWeight="600"
                                  fill="#5b6470"
                                  fontFamily="sans-serif"
                                >
                                  Trục X (PCA 1)
                                </text>
                                <text
                                  x={14}
                                  y={MT + H / 2}
                                  textAnchor="middle"
                                  fontSize={11}
                                  fontWeight="600"
                                  fill="#5b6470"
                                  fontFamily="sans-serif"
                                  transform={`rotate(-90 14 ${MT + H / 2})`}
                                >
                                  Trục Y (PCA 2)
                                </text>
                                <text
                                  x={ML + W / 2}
                                  y={MT - 10}
                                  textAnchor="middle"
                                  fontSize={10}
                                  fill="#7b8794"
                                  fontFamily="sans-serif"
                                >
                                  PCA 1: {formatAxisTick(minX)} → {formatAxisTick(maxX)} · PCA 2: {formatAxisTick(minY)} → {formatAxisTick(maxY)}
                                </text>

                                {/* Data points (chỉ inlier trên scatter chính) */}
                                {inlierLocations.map((loc, i) => {
                                  const cx = toX(loc.pca_x);
                                  const cy = toY(loc.pca_y);
                                  const color = CLUSTER_COLORS[loc.cluster_id % CLUSTER_COLORS.length];
                                  return (
                                    <circle
                                      key={i}
                                      cx={cx} cy={cy} r={5}
                                      fill={color}
                                      fillOpacity={0.82}
                                      stroke="none"
                                      strokeWidth={0}
                                      style={{ cursor: 'pointer' }}
                                      onMouseEnter={() => setKmeansHovered(loc)}
                                      onMouseLeave={() => setKmeansHovered(null)}
                                    />
                                  );
                                })}

                                {/* Outlier mini panel */}
                                {outlierLocations.length > 0 && (() => {
                                  const boxX = ML + W - 108;
                                  const boxY = MT + H - 92;
                                  const boxW = 96;
                                  const boxH = 78;
                                  const xs = outlierLocations.map(o => o.pca_x);
                                  const ys = outlierLocations.map(o => o.pca_y);
                                  const minOx = Math.min(...xs), maxOx = Math.max(...xs);
                                  const minOy = Math.min(...ys), maxOy = Math.max(...ys);
                                  const rx = (maxOx - minOx) || 1;
                                  const ry = (maxOy - minOy) || 1;
                                  const toOx = v => boxX + 10 + ((v - minOx) / rx) * (boxW - 20);
                                  const toOy = v => boxY + boxH - 10 - ((v - minOy) / ry) * (boxH - 20);

                                  return (
                                    <g>
                                      <rect x={boxX} y={boxY} width={boxW} height={boxH} rx={6} fill="#fffdf5" stroke="#f59e0b" strokeWidth={1.2} />
                                      <text x={boxX + 8} y={boxY + 12} fontSize={9.5} fill="#9a6700" fontWeight="700" fontFamily="sans-serif">
                                        Ngoại lai
                                      </text>
                                      {outlierLocations.map((loc, i) => {
                                        const color = CLUSTER_COLORS[loc.cluster_id % CLUSTER_COLORS.length];
                                        return (
                                          <circle
                                            key={`out-${i}`}
                                            cx={toOx(loc.pca_x)}
                                            cy={toOy(loc.pca_y)}
                                            r={4.2}
                                            fill={color}
                                            fillOpacity={0.7}
                                            stroke="#f59e0b"
                                            strokeWidth={1.1}
                                            style={{ cursor: 'pointer' }}
                                            onMouseEnter={() => setKmeansHovered(loc)}
                                            onMouseLeave={() => setKmeansHovered(null)}
                                          />
                                        );
                                      })}
                                    </g>
                                  );
                                })()}

                                {/* Centroid red stars */}
                                {kmeansData.clusters.map(c => (
                                  <path
                                    key={`star-${c.cluster_id}`}
                                    d={starPath(toX(c.centroid_x), toY(c.centroid_y), 9, 3.6)}
                                    fill="#e53e3e"
                                    stroke="white"
                                    strokeWidth={1.2}
                                  />
                                ))}

                                {/* Legend box */}
                                <rect
                                  x={legendX - 6} y={MT - 2}
                                  width={152}
                                  height={18 + (kmeansData.clusters.length + 1) * 22}
                                  rx={6} fill="white" stroke="#ddd" strokeWidth={1}
                                />
                                {kmeansData.clusters.map((c, i) => {
                                  const ly = MT + 12 + i * 22;
                                  const color = CLUSTER_COLORS[c.cluster_id % CLUSTER_COLORS.length];
                                  return (
                                    <g key={`leg-${c.cluster_id}`}>
                                      <circle cx={legendX + 7} cy={ly} r={6} fill={color} fillOpacity={0.85} />
                                      <text x={legendX + 18} y={ly + 4} fontSize={11} fill="#444" fontFamily="sans-serif">
                                        {c.label}
                                      </text>
                                    </g>
                                  );
                                })}
                                {(() => {
                                  const ly = MT + 12 + kmeansData.clusters.length * 22;
                                  return (
                                    <g>
                                      <path d={starPath(legendX + 7, ly, 7, 2.8)} fill="#e53e3e" />
                                      <text x={legendX + 18} y={ly + 4} fontSize={11} fill="#444" fontFamily="sans-serif">centroids</text>
                                    </g>
                                  );
                                })()}
                              </>
                            );
                          })()}
                        </svg>

                        {/* Tooltip */}
                        {kmeansHovered && (() => {
                          const cluster = kmeansData.clusters.find(c => c.cluster_id === kmeansHovered.cluster_id);
                          const color = CLUSTER_COLORS[kmeansHovered.cluster_id % CLUSTER_COLORS.length];
                          return (
                            <div style={{
                              position: 'absolute', top: 8, left: 8,
                              background: 'white', borderLeft: `4px solid ${color}`,
                              borderRadius: 6, padding: '8px 12px', fontSize: '0.78rem',
                              pointerEvents: 'none', boxShadow: '0 3px 10px rgba(0,0,0,0.18)', zIndex: 10,
                              maxWidth: 220,
                            }}>
                              <div className="fw-bold mb-1" style={{ fontSize: '0.85rem' }}>
                                {kmeansHovered.name}
                              </div>
                              <div className="mb-1">
                                <span className="badge me-1" style={{ backgroundColor: color }}>Nhóm {kmeansHovered.cluster_id + 1}</span>
                                <span style={{ fontSize: '0.75rem' }}>{stripEmoji(cluster?.insight)}</span>
                              </div>
                              <div style={{ color: '#555', lineHeight: 1.7 }}>
                                <span>Toạ độ X/Y: <b style={{ color: '#333' }}>{Number(kmeansHovered.pca_x || 0).toFixed(2)} / {Number(kmeansHovered.pca_y || 0).toFixed(2)}</b></span><br />
                                <span>Lượt đặt (khách): <b style={{ color: '#333' }}>{kmeansHovered.count}</b></span><br />
                                <span>Số đơn (BookingID): <b style={{ color: '#333' }}>{kmeansHovered.booking_count ?? 0}</b></span><br />
                                <span>Tần suất: <b style={{ color: '#333' }}>{kmeansHovered.frequency?.toFixed(1)}/tour</b></span><br />
                                <span>Lấp đầy: <b style={{ color: '#333' }}>{((kmeansHovered.fill_rate || 0) * 100).toFixed(0)}%</b></span><br />
                                <span>Giá TB: <b style={{ color: '#333' }}>{new Intl.NumberFormat('vi-VN').format(kmeansHovered.avg_price)}đ</b></span>
                                {kmeansHovered.is_outlier && <><br /><span style={{ color: '#f59e0b', fontSize: '0.72rem' }}>⚠ Ngoại lai</span></>}
                              </div>
                            </div>
                          );
                        })()}
                      </div>
                    </div>

                    {/* Bảng thông tin từng nhóm */}
                    <div className="col-lg-4">
                      <div className="table-responsive" style={{ maxHeight: 520, overflowY: 'auto' }}>
                        <table className="table table-sm table-hover mb-0">
                          <thead className="table-light sticky-top">
                            <tr>
                              <th>Nhóm</th>
                              <th>Đặc điểm</th>
                              <th>Đại diện</th>
                              <th className="text-center">SL</th>
                            </tr>
                          </thead>
                          <tbody>
                            {kmeansData.clusters.map(c => (
                              <tr key={c.cluster_id}>
                                <td style={{ whiteSpace: 'nowrap' }}>
                                  <span
                                    className="badge rounded-pill"
                                    style={{ backgroundColor: CLUSTER_COLORS[c.cluster_id % CLUSTER_COLORS.length] }}
                                  >
                                    {c.label}
                                  </span>
                                </td>
                                <td style={{ fontSize: '0.78rem', whiteSpace: 'nowrap' }}>{stripEmoji(c.insight)}</td>
                                <td style={{ fontSize: '0.78rem', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={c.representative}>
                                  <i className="bi bi-star-fill text-warning me-1" style={{ fontSize: '0.65rem' }} />
                                  {c.representative}
                                </td>
                                <td className="text-center">
                                  {c.size}
                                  {c.avg_fill_rate > 0 && (
                                    <div style={{ fontSize: '0.65rem', color: '#6c757d' }}>
                                      {(c.avg_fill_rate * 100).toFixed(0)}% lấp đầy
                                    </div>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top 5 khách hàng chi tiêu nhiều nhất */}
      {isAdmin && (
        <div className="row g-4">
        <div className="col-12">
          <div className="card border-0 shadow-sm">
            <div className="card-header bg-white border-0 py-3">
              <h5 className="mb-0 fw-bold">
                <i className="bi bi-trophy-fill me-2 text-warning"></i>
                Top 5 khách hàng chi tiêu nhiều nhất
              </h5>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-hover mb-0">
                  <thead className="table-light">
                    <tr>
                      <th className="border-0 py-3" style={{ width: '50px' }}>
                        <i className="bi bi-hash"></i>
                      </th>
                      <th className="border-0 py-3">Tên khách hàng</th>
                      <th className="border-0 py-3">Email</th>
                      <th className="border-0 py-3">Số điện thoại</th>
                      <th className="border-0 py-3 text-end">Số lượng đặt</th>
                      <th className="border-0 py-3 text-end">Tổng chi tiêu</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topCustomers.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="text-center py-4 text-muted">
                          <i className="bi bi-inbox fs-1 d-block mb-2"></i>
                          Chưa có dữ liệu khách hàng
                        </td>
                      </tr>
                    ) : (
                      topCustomers.map((customer, index) => (
                        <tr key={customer.user_id}>
                          <td className="align-middle">
                            <div 
                              className="d-flex align-items-center justify-content-center rounded-circle fw-bold text-white"
                              style={{
                                width: '35px',
                                height: '35px',
                                background: index === 0 ? 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)' :
                                          index === 1 ? 'linear-gradient(135deg, #C0C0C0 0%, #808080 100%)' :
                                          index === 2 ? 'linear-gradient(135deg, #CD7F32 0%, #8B4513 100%)' :
                                          'linear-gradient(135deg, #6c757d 0%, #495057 100%)'
                              }}
                            >
                              {index + 1}
                            </div>
                          </td>
                          <td className="align-middle">
                            <div className="d-flex align-items-center">
                              <div 
                                className="rounded-circle bg-primary bg-opacity-10 d-flex align-items-center justify-content-center me-2"
                                style={{ width: '40px', height: '40px' }}
                              >
                                <i className="bi bi-person-fill text-primary"></i>
                              </div>
                              <div>
                                <div className="fw-semibold">{customer.name}</div>
                                {topCustomerSegments[customer.user_id]?.segment_name && (
                                  <span
                                    className="badge rounded-pill mt-1"
                                    style={{
                                      backgroundColor: CLUSTER_COLORS[(topCustomerSegments[customer.user_id]?.cluster_id || 0) % CLUSTER_COLORS.length],
                                      fontSize: '0.7rem'
                                    }}
                                  >
                                    {topCustomerSegments[customer.user_id].segment_name}
                                  </span>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="align-middle text-muted">
                            <i className="bi bi-envelope me-1"></i>
                            {customer.email}
                          </td>
                          <td className="align-middle text-muted">
                            <i className="bi bi-telephone me-1"></i>
                            {customer.phone}
                          </td>
                          <td className="align-middle text-end">
                            <span className="badge bg-info">
                              {customer.total_bookings} tour
                            </span>
                          </td>
                          <td className="align-middle text-end">
                            <span className="fw-bold text-success fs-6">
                              {formatCurrency(customer.total_spent)}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
      )}
    </div>
  );
};

export default AdminHome;
