import React, { useCallback, useEffect, useMemo, useState } from "react";
import { adminService } from "../services/adminService";

const CLUSTER_COLORS = [
  '#4e79a7', '#f28e2b', '#e15759', '#76b7b2',
  '#59a14f', '#edc948', '#b07aa1', '#ff9da7',
  '#9c755f', '#bab0ac', '#d4a373', '#a2d2ff',
];

const DEFAULT_CUSTOMER_SEGMENT_DATA = {
  clusters: [],
  pca_points: [],
  pca_centroids: [],
  total_users: 0,
  n_clusters: 0,
  modeled_group_count: 0,
  special_group_count: 0,
  total_groups: 0,
  optimal_k: 0,
  formula_suggested_k: 0,
  auto_selected: true,
  allowed_k_values: [],
  zero_group_users: 0,
  modeled_users: 0,
  recency_cap_days: 0,
  elbow_data: [],
  inertia_data: [],
  silhouette_data: [],
};

const DEFAULT_TOUR_CLUSTER_DATA = {
  clusters: [],
  tours: [],
  total_tours: 0,
  n_clusters: 0,
  modeled_group_count: 0,
  special_group_count: 0,
  total_groups: 0,
  optimal_k: 0,
  auto_selected: true,
  silhouette_score: 0,
  k_candidates: [],
  elbow_data: [],
  inertia_data: [],
  silhouette_data: [],
};

const formatCompactMoney = (value) => `${new Intl.NumberFormat('vi-VN').format(Math.round(value || 0))}đ`;
const formatPercent = (value, digits = 0) => `${((value || 0) * 100).toFixed(digits)}%`;
const formatAxisTick = (value) => Number(value || 0).toFixed(2);

const starPath = (cx, cy, outerR = 8, innerR = 3.2) => {
  let path = '';
  for (let i = 0; i < 10; i += 1) {
    const angle = (-90 + i * 36) * (Math.PI / 180);
    const r = i % 2 === 0 ? outerR : innerR;
    const x = cx + Math.cos(angle) * r;
    const y = cy + Math.sin(angle) * r;
    path += `${i === 0 ? 'M' : 'L'} ${x} ${y} `;
  }
  return `${path}Z`;
};

function getCustomerClusterInsight(cluster) {
  const meanSpending = Number(cluster?.mean_spending || 0);
  const meanOrders = Number(cluster?.mean_orders || 0);
  const meanRecency = Number(cluster?.mean_recency_days || 0);
  const meanDiscountRate = Number(cluster?.mean_discount_rate || 0);

  if ((cluster?.segment_name || '').includes('VIP')) {
    return 'Chi tiêu và tần suất đều rất cao, đây là nhóm giá trị nhất.';
  }
  if (meanRecency >= 120 || (cluster?.segment_name || '').includes('ít tương tác')) {
    return 'Đã lâu chưa quay lại hoặc mua rất thưa, có dấu hiệu rời bỏ.';
  }
  if (meanDiscountRate >= 0.35 || (cluster?.segment_name || '').includes('săn sale')) {
    return 'Nhạy với khuyến mãi, dễ phản hồi khi có ưu đãi rõ ràng.';
  }
  if (meanSpending >= 5000000 && meanOrders >= 2) {
    return 'Mua đều và chi tiêu khá, có tiềm năng nâng lên nhóm trung thành cao.';
  }
  if (meanOrders <= 1.5 && meanRecency <= 90) {
    return 'Nhóm mới hình thành hành vi, cần đẩy đơn thứ hai càng sớm càng tốt.';
  }
  return 'Hành vi tương đối ổn định, nên giữ nhịp chăm sóc và theo dõi dịch chuyển.';
}

function getCustomerClusterAction(cluster) {
  const meanOrders = Number(cluster?.mean_orders || 0);
  const meanRecency = Number(cluster?.mean_recency_days || 0);
  const meanDiscountRate = Number(cluster?.mean_discount_rate || 0);

  if ((cluster?.segment_name || '').includes('VIP')) {
    return 'Giữ chân bằng ưu đãi riêng, early access và CSKH ưu tiên.';
  }
  if (meanRecency >= 120 || (cluster?.segment_name || '').includes('ít tương tác')) {
    return 'Chạy win-back campaign với tour gần, giá tốt và thời hạn ngắn.';
  }
  if (meanDiscountRate >= 0.35 || (cluster?.segment_name || '').includes('săn sale')) {
    return 'Đẩy combo, flash sale và thông điệp tiết kiệm thay vì upsell giá cao.';
  }
  if (meanOrders <= 1.5 && meanRecency <= 90) {
    return 'Tập trung kéo đơn thứ hai bằng gợi ý cá nhân hóa sau chuyến đầu.';
  }
  return 'Nuôi dưỡng bằng remarketing nhẹ và nội dung theo danh mục yêu thích.';
}

function buildModeledClusterOrdinalMap(clusters) {
  const modeledIds = (clusters || [])
    .filter((cluster) => !cluster?.is_special_group)
    .map((cluster) => Number(cluster.cluster_id))
    .filter((clusterId) => Number.isInteger(clusterId))
    .sort((a, b) => a - b);

  return modeledIds.reduce((accumulator, clusterId, index) => {
    accumulator[clusterId] = index + 1;
    return accumulator;
  }, {});
}

function getCustomerClusterDisplayName(cluster, modeledClusterOrder) {
  if (cluster?.is_special_group) {
    return 'Nhóm cold-start';
  }

  const clusterId = Number(cluster?.cluster_id);
  const ordinal = modeledClusterOrder?.[clusterId];
  return ordinal ? `Cụm K${ordinal}` : `Cụm ${clusterId}`;
}

function getTourClusterDisplayName(cluster, modeledClusterOrder) {
  if (cluster?.is_special_group) {
    return 'Nhóm ngủ đông';
  }

  const clusterId = Number(cluster?.cluster_id);
  const ordinal = modeledClusterOrder?.[clusterId];
  return ordinal ? `Cụm K${ordinal}` : `Cụm ${clusterId}`;
}

function formatGroupSummary(modeledGroupCount, specialGroupCount, entityCount, entityLabel) {
  const parts = [];

  if (modeledGroupCount > 0) {
    parts.push(`K-Means ${modeledGroupCount} cụm`);
  }
  if (specialGroupCount > 0) {
    parts.push(`+ ${specialGroupCount} nhóm đặc biệt`);
  }
  if (entityCount > 0) {
    parts.push(`${entityCount} ${entityLabel}`);
  }

  return parts.join(' · ');
}

export default function ClusteringView({ mode = 'both', breadcrumb = '' }) {
  const showCustomerSection = mode !== 'tours';
  const showTourSection = mode !== 'customers';

  const [customerSegmentData, setCustomerSegmentData] = useState(DEFAULT_CUSTOMER_SEGMENT_DATA);
  const [customerSegmentLoading, setCustomerSegmentLoading] = useState(true);
  const [customerSegmentError, setCustomerSegmentError] = useState('');
  const [customerSegmentK, setCustomerSegmentK] = useState(0);

  const [tourClusterData, setTourClusterData] = useState(DEFAULT_TOUR_CLUSTER_DATA);
  const [tourClusterLoading, setTourClusterLoading] = useState(true);
  const [tourClusterError, setTourClusterError] = useState('');
  const [tourClusterK, setTourClusterK] = useState(0);
  const [hoveredCustomer, setHoveredCustomer] = useState(null);
  const [hoveredTour, setHoveredTour] = useState(null);

  const loadCustomerSegments = useCallback(async ({ nClusters = 0, source = 'initial' } = {}) => {
    try {
      if (source !== 'background') {
        setCustomerSegmentLoading(true);
      }

      const data = await adminService.rebuildCustomerSegments(nClusters);
      setCustomerSegmentData({
        ...DEFAULT_CUSTOMER_SEGMENT_DATA,
        ...(data || {}),
      });
      setCustomerSegmentError('');
    } catch (error) {
      console.error('Cannot load customer segmentation summary:', error);
      setCustomerSegmentError(error?.response?.data?.detail || 'Không thể tải phân cụm khách hàng lúc này.');
    } finally {
      setCustomerSegmentLoading(false);
    }
  }, []);

  const loadTourClusters = useCallback(async ({ nClusters = 0, source = 'initial' } = {}) => {
    try {
      if (source !== 'background') {
        setTourClusterLoading(true);
      }

      const data = await adminService.rebuildTourClusters(nClusters);
      setTourClusterData({
        ...DEFAULT_TOUR_CLUSTER_DATA,
        ...(data || {}),
      });
      setTourClusterError('');
    } catch (error) {
      console.error('Cannot load tour clustering summary:', error);
      setTourClusterError(error?.response?.data?.detail || 'Không thể tải phân cụm tour lúc này.');
    } finally {
      setTourClusterLoading(false);
    }
  }, []);

  useEffect(() => {
    if (showCustomerSection) {
      loadCustomerSegments({ nClusters: 0, source: 'initial' });
    }
    if (showTourSection) {
      loadTourClusters({ nClusters: 0, source: 'initial' });
    }
  }, [loadCustomerSegments, loadTourClusters, showCustomerSection, showTourSection]);

  const filteredTours = useMemo(() => {
    return tourClusterData.tours || [];
  }, [tourClusterData.tours]);

  const filteredClusterIds = useMemo(() => {
    return new Set(filteredTours.map((tour) => tour.cluster_id));
  }, [filteredTours]);

  const visibleClusters = useMemo(() => {
    return (tourClusterData.clusters || []).filter((cluster) => filteredClusterIds.has(cluster.cluster_id));
  }, [filteredClusterIds, tourClusterData.clusters]);

  const customerModeledClusterOrder = useMemo(
    () => buildModeledClusterOrdinalMap(customerSegmentData.clusters),
    [customerSegmentData.clusters]
  );

  const customerModeledClusters = useMemo(
    () => (customerSegmentData.clusters || []).filter((cluster) => !cluster?.is_special_group),
    [customerSegmentData.clusters]
  );

  const customerSpecialClusters = useMemo(
    () => (customerSegmentData.clusters || []).filter((cluster) => cluster?.is_special_group),
    [customerSegmentData.clusters]
  );

  const tourModeledClusterOrder = useMemo(
    () => buildModeledClusterOrdinalMap(tourClusterData.clusters),
    [tourClusterData.clusters]
  );

  const customerElbowData = useMemo(() => {
    const raw = customerSegmentData.inertia_data?.length
      ? customerSegmentData.inertia_data
      : (customerSegmentData.elbow_data || []);
    return raw.filter((item) => Number.isFinite(Number(item?.inertia)));
  }, [customerSegmentData.elbow_data, customerSegmentData.inertia_data]);

  const customerChartPoints = useMemo(() => {
    return (customerSegmentData.pca_points || []).filter(
      (point) => Number.isFinite(Number(point?.pca_x)) && Number.isFinite(Number(point?.pca_y))
    );
  }, [customerSegmentData.pca_points]);

  const customerChartCentroids = useMemo(() => {
    return (customerSegmentData.pca_centroids || []).filter(
      (centroid) => Number.isFinite(Number(centroid?.centroid_x)) && Number.isFinite(Number(centroid?.centroid_y))
    );
  }, [customerSegmentData.pca_centroids]);

  const customerChartBounds = useMemo(() => {
    if (!customerChartPoints.length) return null;

    const xs = customerChartPoints.map((point) => Number(point.pca_x || 0));
    const ys = customerChartPoints.map((point) => Number(point.pca_y || 0));
    const xRange = (Math.max(...xs) - Math.min(...xs)) || 2;
    const yRange = (Math.max(...ys) - Math.min(...ys)) || 2;
    const padding = 0.18;

    return {
      minX: Math.min(...xs) - xRange * padding,
      maxX: Math.max(...xs) + xRange * padding,
      minY: Math.min(...ys) - yRange * padding,
      maxY: Math.max(...ys) + yRange * padding,
    };
  }, [customerChartPoints]);

  const tourChartBounds = useMemo(() => {
    if (!filteredTours.length) return null;

    const xs = filteredTours.map((tour) => Number(tour.pca_x || 0));
    const ys = filteredTours.map((tour) => Number(tour.pca_y || 0));
    const xRange = (Math.max(...xs) - Math.min(...xs)) || 2;
    const yRange = (Math.max(...ys) - Math.min(...ys)) || 2;
    const padding = 0.18;

    return {
      minX: Math.min(...xs) - xRange * padding,
      maxX: Math.max(...xs) + xRange * padding,
      minY: Math.min(...ys) - yRange * padding,
      maxY: Math.max(...ys) + yRange * padding,
    };
  }, [filteredTours]);

  const customerClusterOptions = useMemo(() => {
    const ks = [...new Set([2, 5, 7, ...(customerSegmentData.allowed_k_values || [])])]
      .map((k) => Number(k))
      .filter((k) => Number.isInteger(k) && k >= 2)
      .sort((a, b) => a - b);
    return [{ label: 'Auto', value: 0 }, ...ks.map((k) => ({ label: `K = ${k}`, value: k }))];
  }, [customerSegmentData.allowed_k_values]);

  const tourClusterOptions = useMemo(() => {
    const ks = [...new Set([2, 3, 4, ...(tourClusterData.k_candidates || [])])]
      .map((k) => Number(k))
      .filter((k) => Number.isInteger(k) && k >= 2)
      .sort((a, b) => a - b);
    return [{ label: 'Auto', value: 0 }, ...ks.map((k) => ({ label: `K = ${k}`, value: k }))];
  }, [tourClusterData.k_candidates]);

  return (
    <div className="container-fluid mt-4 px-4">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
        <div>
          {breadcrumb && <div className="small text-muted mb-1">{breadcrumb}</div>}
          <h2 className="fw-bold text-primary mb-1">
            <i className="bi bi-diagram-3-fill me-2"></i>
            {showCustomerSection && showTourSection && 'Phân cụm khách hàng và tour'}
            {showCustomerSection && !showTourSection && 'Phân cụm khách hàng'}
            {!showCustomerSection && showTourSection && 'Phân cụm tour'}
          </h2>
          <p className="text-muted mb-0">
            {showCustomerSection && showTourSection && 'Tách riêng khỏi dashboard để quản trị rebuild, so sánh K và đọc insight nhanh hơn.'}
            {showCustomerSection && !showTourSection && 'Nhóm khách theo hành vi để phục vụ phân khúc, chăm sóc và win-back chính xác hơn.'}
            {!showCustomerSection && showTourSection && 'Nhóm tour theo hiệu suất để tối ưu vận hành, giá và kế hoạch truyền thông.'}
          </p>
        </div>
      </div>

      <div className="row g-4 mb-4">
        {showCustomerSection && (
        <div className={showTourSection ? 'col-lg-6' : 'col-12'}>
          <div className="card border-0 shadow-sm h-100">
            <div className="card-header bg-white border-0 py-3">
              <div className="d-flex flex-wrap justify-content-between align-items-center gap-3">
                <div>
                  <h5 className="mb-1 fw-bold">
                    <i className="bi bi-people-fill me-2 text-primary"></i>
                    Phân cụm khách hàng
                    {customerSegmentData.n_clusters > 0 && (
                      <span className="badge bg-primary ms-2" style={{ fontSize: '0.7rem' }}>
                        {formatGroupSummary(
                          customerSegmentData.modeled_group_count || customerSegmentData.n_clusters,
                          0,
                          customerSegmentData.total_users,
                          'khách'
                        )}
                      </span>
                    )}
                  </h5>
                  <small className="text-muted">Auto chọn K theo heuristic + silhouette. Nhóm cold-start không tính vào K.</small>
                </div>

                <div className="d-flex flex-wrap align-items-center gap-2">
                  <div className="btn-group btn-group-sm" role="group">
                    {customerClusterOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        className={`btn ${customerSegmentK === option.value ? 'btn-primary' : 'btn-outline-primary'}`}
                        disabled={customerSegmentLoading}
                        onClick={() => {
                          setCustomerSegmentK(option.value);
                          loadCustomerSegments({ nClusters: option.value, source: 'manual' });
                        }}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => loadCustomerSegments({ nClusters: customerSegmentK, source: 'manual' })}
                    disabled={customerSegmentLoading}
                  >
                    <i className={`bi bi-arrow-repeat me-1 ${customerSegmentLoading ? 'spin' : ''}`}></i>
                    {customerSegmentLoading ? 'Đang rebuild...' : 'Rebuild'}
                  </button>
                </div>
              </div>
            </div>

            <div className="card-body">
              {customerSegmentError && (
                <div className="alert alert-warning py-2" role="alert">
                  <i className="bi bi-exclamation-triangle me-2"></i>
                  {customerSegmentError}
                </div>
              )}

              {customerSegmentLoading && customerSegmentData.clusters.length === 0 ? (
                <div className="text-center py-5 text-muted">
                  <div className="spinner-border spinner-border-sm me-2" role="status" />
                  Đang rebuild phân cụm khách hàng...
                </div>
              ) : (
                <>
                  <div className="row g-3 mb-3">
                    <div className="col-md-4">
                      <div className="rounded-3 border bg-light h-100 p-3">
                        <div className="text-muted small mb-1">K đang dùng</div>
                        <div className="fw-bold fs-4">{customerSegmentData.n_clusters || '—'}</div>
                        <div className="small text-muted">
                          {customerSegmentData.auto_selected
                            ? `Auto chọn, heuristic gợi ý ${customerSegmentData.formula_suggested_k || '—'}`
                            : `Đang dùng K thủ công, optimal auto = ${customerSegmentData.optimal_k || '—'}`}
                        </div>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="rounded-3 border bg-light h-100 p-3">
                        <div className="text-muted small mb-1">Khách phân tích</div>
                        <div className="fw-bold fs-4">{customerSegmentData.modeled_users}</div>
                        <div className="small text-muted">Có booking để đưa vào K-Means</div>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="rounded-3 border bg-light h-100 p-3">
                        <div className="text-muted small mb-1">Cold-start</div>
                        <div className="fw-bold fs-4">{customerSegmentData.zero_group_users}</div>
                        <div className="small text-muted">Tách khỏi cụm chính</div>
                      </div>
                    </div>
                  </div>



                  {customerChartBounds && customerChartPoints.length > 0 && (
                    <div className="row g-3 mb-3">
                      <div className="col-lg-8">
                        <div className="rounded-3 border bg-light p-3 position-relative">
                          <div className="d-flex justify-content-end small text-muted mb-2">
                            Biểu đồ chỉ gồm khách đã vào K-Means · Mỗi điểm = 1 khách · ★ = tâm cụm
                          </div>
                          <svg
                            viewBox="0 0 560 340"
                            style={{ width: '100%', height: 'auto', display: 'block', background: '#fafafa', borderRadius: 8 }}
                          >
                            {(() => {
                              const ML = 52;
                              const MT = 38;
                              const MB = 36;
                              const plotRight = 390;
                              const W = plotRight - ML;
                              const H = 340 - MT - MB;
                              const legendX = 402;
                              const { minX, maxX, minY, maxY } = customerChartBounds;
                              const toX = (value) => ML + ((value - minX) / (maxX - minX)) * W;
                              const toY = (value) => MT + H - ((value - minY) / (maxY - minY)) * H;
                              const xTicks = Array.from({ length: 5 }, (_, index) => minX + ((maxX - minX) * index) / 4);
                              const yTicks = Array.from({ length: 5 }, (_, index) => minY + ((maxY - minY) * index) / 4);
                              const legendClusters = customerModeledClusters;

                              return (
                                <>
                                  <text x={ML + W / 2} y={22} textAnchor="middle" fontSize={13} fontWeight="bold" fill="#333" fontFamily="sans-serif">
                                    Phân cụm K-Means – Khách hàng
                                  </text>

                                  <rect x={ML} y={MT} width={W} height={H} fill="white" />

                                  {xTicks.map((tick, index) => {
                                    const x = toX(tick);
                                    return (
                                      <g key={`cx-${index}`}>
                                        <line x1={x} y1={MT} x2={x} y2={MT + H} stroke="#e4e4e4" strokeWidth={1} />
                                        <text x={x} y={MT + H + 16} textAnchor="middle" fontSize={10} fill="#888">{formatAxisTick(tick)}</text>
                                      </g>
                                    );
                                  })}
                                  {yTicks.map((tick, index) => {
                                    const y = toY(tick);
                                    return (
                                      <g key={`cy-${index}`}>
                                        <line x1={ML} y1={y} x2={plotRight} y2={y} stroke="#e4e4e4" strokeWidth={1} />
                                        <text x={ML - 8} y={y + 4} textAnchor="end" fontSize={10} fill="#888">{formatAxisTick(tick)}</text>
                                      </g>
                                    );
                                  })}

                                  <rect x={ML} y={MT} width={W} height={H} fill="none" stroke="#ccc" strokeWidth={1} />

                                  <text x={ML + W / 2} y={MT + H + 32} textAnchor="middle" fontSize={11} fontWeight="600" fill="#5b6470">
                                    Trục X (PCA 1)
                                  </text>
                                  <text
                                    x={14}
                                    y={MT + H / 2}
                                    textAnchor="middle"
                                    fontSize={11}
                                    fontWeight="600"
                                    fill="#5b6470"
                                    transform={`rotate(-90 14 ${MT + H / 2})`}
                                  >
                                    Trục Y (PCA 2)
                                  </text>
                                  <text x={ML + W / 2} y={MT - 10} textAnchor="middle" fontSize={10} fill="#7b8794">
                                    PCA 1: {formatAxisTick(minX)} → {formatAxisTick(maxX)} · PCA 2: {formatAxisTick(minY)} → {formatAxisTick(maxY)}
                                  </text>

                                  {customerChartPoints.map((point) => {
                                    const cx = toX(Number(point.pca_x || 0));
                                    const cy = toY(Number(point.pca_y || 0));
                                    const fill = CLUSTER_COLORS[point.cluster_id % CLUSTER_COLORS.length];
                                    return (
                                      <circle
                                        key={point.user_id}
                                        cx={cx}
                                        cy={cy}
                                        r={5}
                                        fill={fill}
                                        fillOpacity={0.82}
                                        stroke="none"
                                        style={{ cursor: 'pointer' }}
                                        onMouseEnter={() => setHoveredCustomer(point)}
                                        onMouseLeave={() => setHoveredCustomer(null)}
                                      />
                                    );
                                  })}

                                  {customerChartCentroids.map((centroid) => (
                                    <path
                                      key={`customer-centroid-${centroid.cluster_id}`}
                                      d={starPath(toX(Number(centroid.centroid_x)), toY(Number(centroid.centroid_y)), 9, 3.6)}
                                      fill="#e53e3e"
                                      stroke="white"
                                      strokeWidth={1.2}
                                    />
                                  ))}

                                  <rect
                                    x={legendX - 6}
                                    y={MT - 2}
                                    width={152}
                                    height={18 + (legendClusters.length + 1) * 22}
                                    rx={6}
                                    fill="white"
                                    stroke="#ddd"
                                    strokeWidth={1}
                                  />
                                  {legendClusters.map((cluster, index) => {
                                    const ly = MT + 12 + index * 22;
                                    const color = CLUSTER_COLORS[cluster.cluster_id % CLUSTER_COLORS.length];
                                    return (
                                      <g key={`customer-legend-${cluster.cluster_id}`}>
                                        <circle cx={legendX + 7} cy={ly} r={6} fill={color} fillOpacity={0.85} />
                                        <text x={legendX + 18} y={ly + 4} fontSize={11} fill="#444">{getCustomerClusterDisplayName(cluster, customerModeledClusterOrder)}</text>
                                      </g>
                                    );
                                  })}
                                  {(() => {
                                    const ly = MT + 12 + legendClusters.length * 22;
                                    return (
                                      <g>
                                        <path d={starPath(legendX + 7, ly, 7, 2.8)} fill="#e53e3e" />
                                        <text x={legendX + 18} y={ly + 4} fontSize={11} fill="#444">Tâm cụm (centroid)</text>
                                      </g>
                                    );
                                  })()}
                                </>
                              );
                            })()}
                          </svg>

                          {hoveredCustomer && (
                            <div
                              style={{
                                position: 'absolute',
                                top: 56,
                                right: 16,
                                width: 220,
                                background: '#ffffff',
                                borderRadius: 12,
                                boxShadow: '0 10px 30px rgba(15, 23, 42, 0.15)',
                                padding: '12px 14px',
                                borderLeft: `4px solid ${CLUSTER_COLORS[hoveredCustomer.cluster_id % CLUSTER_COLORS.length]}`,
                                pointerEvents: 'none',
                              }}
                            >
                              <div className="fw-semibold mb-1">{hoveredCustomer.user_name}</div>
                              <div className="small text-muted mb-2">{hoveredCustomer.segment_name}</div>
                              <div className="small">
                                <div>Toạ độ X/Y: <span className="fw-semibold">{Number(hoveredCustomer.pca_x || 0).toFixed(2)} / {Number(hoveredCustomer.pca_y || 0).toFixed(2)}</span></div>
                                <div>Nhóm: <span className="fw-semibold">{getCustomerClusterDisplayName(hoveredCustomer, customerModeledClusterOrder)}</span></div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="col-lg-4">
                        <div className="rounded-3 border bg-white p-3 mb-3">
                          <div className="small text-muted mb-2">Các cụm K-Means đang hiển thị</div>
                          <div className="table-responsive" style={{ maxHeight: 220, overflowY: 'auto' }}>
                            <table className="table table-sm table-hover mb-0">
                              <thead className="table-light sticky-top">
                                <tr>
                                  <th>Cụm</th>
                                  <th>Phân khúc</th>
                                  <th className="text-center">SL</th>
                                </tr>
                              </thead>
                              <tbody>
                                {customerModeledClusters.map((cluster) => (
                                  <tr key={`customer-cluster-${cluster.cluster_id}`}>
                                    <td style={{ whiteSpace: 'nowrap' }}>
                                      <span
                                        className="badge rounded-pill"
                                        style={{ backgroundColor: CLUSTER_COLORS[cluster.cluster_id % CLUSTER_COLORS.length] }}
                                      >
                                        {getCustomerClusterDisplayName(cluster, customerModeledClusterOrder)}
                                      </span>
                                    </td>
                                    <td style={{ fontSize: '0.78rem', whiteSpace: 'nowrap' }}>{cluster.segment_name}</td>
                                    <td className="text-center">{cluster.users}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>


                      </div>
                    </div>
                  )}

                  <div className="table-responsive">
                    <table className="table table-hover align-middle mb-0">
                      <thead className="table-light">
                        <tr>
                          <th>Nhóm</th>
                          <th>Phân khúc</th>
                          <th>Insight / Action</th>
                          <th className="text-end">SL khách</th>
                          <th className="text-end">Chi tiêu TB</th>
                          <th className="text-end">Đơn TB</th>
                          <th className="text-end">Recency</th>
                          <th className="text-end">Giảm giá</th>
                        </tr>
                      </thead>
                      <tbody>
                        {customerModeledClusters.map((cluster) => (
                          <tr key={cluster.cluster_id}>
                            <td>
                              <span
                                className="badge rounded-pill"
                                style={{ backgroundColor: CLUSTER_COLORS[cluster.cluster_id % CLUSTER_COLORS.length] }}
                              >
                                {getCustomerClusterDisplayName(cluster, customerModeledClusterOrder)}
                              </span>
                            </td>
                            <td>
                              <div className="fw-semibold">{cluster.segment_name}</div>
                              <div className="small text-muted">RFM + avg order value + discount usage</div>
                            </td>
                            <td>
                              <div className="small fw-semibold text-dark">{getCustomerClusterInsight(cluster)}</div>
                              <div className="small text-muted mt-1">{getCustomerClusterAction(cluster)}</div>
                            </td>
                            <td className="text-end fw-semibold">{cluster.users}</td>
                            <td className="text-end">{formatCompactMoney(cluster.mean_spending)}</td>
                            <td className="text-end">{cluster.mean_orders?.toFixed?.(1) ?? cluster.mean_orders}</td>
                            <td className="text-end">{Math.round(cluster.mean_recency_days || 0)} ngày</td>
                            <td className="text-end">{formatPercent(cluster.mean_discount_rate, 1)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>



                  {customerSegmentData.silhouette_data?.length > 0 && (
                    <div className="mt-3 rounded-3 border p-3 bg-light">
                      <div className="small text-muted mb-2">So sánh silhouette</div>
                      <div className="d-flex flex-wrap gap-3">
                        {customerSegmentData.silhouette_data.map((item) => (
                          <div key={item.k} className="small">
                            <span className={`badge ${item.k === customerSegmentData.optimal_k ? 'text-bg-primary' : 'text-bg-light'} me-2`}>
                              K={item.k}
                            </span>
                            {Number(item.score || 0).toFixed(3)}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {customerElbowData.length > 0 && (
                    <div className="mt-3 rounded-3 border p-3 bg-light">
                      <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">
                        <div className="small text-muted">The Elbow Method (Inertia theo K)</div>
                        <span className="badge text-bg-primary">K chọn: {customerSegmentData.optimal_k || '—'}</span>
                      </div>
                      <div className="d-flex flex-wrap gap-3">
                        {customerElbowData.map((item, index) => {
                          const prev = customerElbowData[index - 1];
                          const drop = prev ? Number(prev.inertia || 0) - Number(item.inertia || 0) : 0;
                          return (
                            <div key={item.k} className="small">
                              <span className={`badge ${item.k === customerSegmentData.optimal_k ? 'text-bg-primary' : 'text-bg-light'} me-2`}>
                                K={item.k}
                              </span>
                              {Number(item.inertia || 0).toFixed(2)}
                              {index > 0 && (
                                <span className="text-muted ms-2">(↓ {drop.toFixed(2)})</span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                      <div className="small text-muted mt-2">Điểm khuỷu tay thường nằm ở K mà mức giảm inertia bắt đầu chậm lại.</div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
        )}

        {showTourSection && (
        <div className={showCustomerSection ? 'col-lg-6' : 'col-12'}>
          <div className="card border-0 shadow-sm h-100">
            <div className="card-header bg-white border-0 py-3">
              <div className="d-flex flex-wrap justify-content-between align-items-center gap-3">
                <div>
                  <h5 className="mb-1 fw-bold">
                    <i className="bi bi-globe2 me-2 text-success"></i>
                    Phân cụm tour
                    {tourClusterData.n_clusters > 0 && (
                      <span className="badge bg-success ms-2" style={{ fontSize: '0.7rem' }}>
                        {formatGroupSummary(
                          tourClusterData.modeled_group_count || tourClusterData.n_clusters,
                          0,
                          tourClusterData.total_tours,
                          'tour'
                        )}
                      </span>
                    )}
                    {tourClusterData.silhouette_score > 0 && (
                      <span className="badge bg-secondary ms-1" style={{ fontSize: '0.65rem' }}>
                        Silhouette {tourClusterData.silhouette_score.toFixed(3)}
                      </span>
                    )}
                  </h5>
                  <small className="text-muted">Phân cụm theo booking, revenue, fill rate, VIP rate và recency. Tất cả tour đều được đưa vào K-Means.</small>
                </div>

                <div className="d-flex flex-wrap align-items-center gap-2">
                  <div className="btn-group btn-group-sm" role="group">
                    {tourClusterOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        className={`btn ${tourClusterK === option.value ? 'btn-success' : 'btn-outline-success'}`}
                        disabled={tourClusterLoading}
                        onClick={() => {
                          setTourClusterK(option.value);
                          loadTourClusters({ nClusters: option.value, source: 'manual' });
                        }}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => loadTourClusters({ nClusters: tourClusterK, source: 'manual' })}
                    disabled={tourClusterLoading}
                  >
                    <i className={`bi bi-arrow-repeat me-1 ${tourClusterLoading ? 'spin' : ''}`}></i>
                    {tourClusterLoading ? 'Đang rebuild...' : 'Rebuild'}
                  </button>
                </div>
              </div>
            </div>

            <div className="card-body">
              {tourClusterError && (
                <div className="alert alert-warning py-2" role="alert">
                  <i className="bi bi-exclamation-triangle me-2"></i>
                  {tourClusterError}
                </div>
              )}

              {tourClusterLoading && tourClusterData.clusters.length === 0 ? (
                <div className="text-center py-5 text-muted">
                  <div className="spinner-border spinner-border-sm me-2" role="status" />
                  Đang rebuild phân cụm tour...
                </div>
              ) : (
                <>

                  <div className="d-flex justify-content-end small text-muted mb-3">
                    <i className="bi bi-info-circle me-1"></i>
                    Mỗi điểm = 1 tour · Màu/vùng = nhóm cluster · ★ = tâm cụm
                  </div>

                  {tourChartBounds && filteredTours.length > 0 && (
                    <div className="row g-3 mb-3">
                      <div className="col-lg-8">
                        <div className="rounded-3 border bg-light p-3 position-relative">
                          <svg
                            viewBox="0 0 560 340"
                            style={{ width: '100%', height: 'auto', display: 'block', background: '#fafafa', borderRadius: 8 }}
                          >
                            {(() => {
                              const ML = 52;
                              const MT = 38;
                              const MB = 36;
                              const plotRight = 390;
                              const W = plotRight - ML;
                              const H = 340 - MT - MB;
                              const legendX = 402;
                              const { minX, maxX, minY, maxY } = tourChartBounds;
                              const clustersForLegend = visibleClusters.length ? visibleClusters : (tourClusterData.clusters || []);
                              const toX = (value) => ML + ((value - minX) / (maxX - minX)) * W;
                              const toY = (value) => MT + H - ((value - minY) / (maxY - minY)) * H;
                              const xTicks = Array.from({ length: 5 }, (_, index) => minX + ((maxX - minX) * index) / 4);
                              const yTicks = Array.from({ length: 5 }, (_, index) => minY + ((maxY - minY) * index) / 4);

                              return (
                                <>
                                  <text x={ML + W / 2} y={22} textAnchor="middle" fontSize={13} fontWeight="bold" fill="#333" fontFamily="sans-serif">
                                    Phân cụm K-Means – Tour
                                  </text>

                                  <rect x={ML} y={MT} width={W} height={H} fill="white" />

                                  {xTicks.map((tick, index) => {
                                    const x = toX(tick);
                                    return (
                                      <g key={`x-${index}`}>
                                        <line x1={x} y1={MT} x2={x} y2={MT + H} stroke="#e4e4e4" strokeWidth={1} />
                                        <text x={x} y={MT + H + 16} textAnchor="middle" fontSize={10} fill="#888">{formatAxisTick(tick)}</text>
                                      </g>
                                    );
                                  })}
                                  {yTicks.map((tick, index) => {
                                    const y = toY(tick);
                                    return (
                                      <g key={`y-${index}`}>
                                        <line x1={ML} y1={y} x2={plotRight} y2={y} stroke="#e4e4e4" strokeWidth={1} />
                                        <text x={ML - 8} y={y + 4} textAnchor="end" fontSize={10} fill="#888">{formatAxisTick(tick)}</text>
                                      </g>
                                    );
                                  })}

                                  <rect x={ML} y={MT} width={W} height={H} fill="none" stroke="#ccc" strokeWidth={1} />

                                  <text x={ML + W / 2} y={MT + H + 32} textAnchor="middle" fontSize={11} fontWeight="600" fill="#5b6470">
                                    Trục X (PCA 1)
                                  </text>
                                  <text
                                    x={14}
                                    y={MT + H / 2}
                                    textAnchor="middle"
                                    fontSize={11}
                                    fontWeight="600"
                                    fill="#5b6470"
                                    transform={`rotate(-90 14 ${MT + H / 2})`}
                                  >
                                    Trục Y (PCA 2)
                                  </text>
                                  <text x={ML + W / 2} y={MT - 10} textAnchor="middle" fontSize={10} fill="#7b8794">
                                    PCA 1: {formatAxisTick(minX)} → {formatAxisTick(maxX)} · PCA 2: {formatAxisTick(minY)} → {formatAxisTick(maxY)}
                                  </text>

                                  {filteredTours.map((tour) => {
                                    const cx = toX(Number(tour.pca_x || 0));
                                    const cy = toY(Number(tour.pca_y || 0));
                                    const fill = CLUSTER_COLORS[tour.cluster_id % CLUSTER_COLORS.length];
                                    return (
                                      <circle
                                        key={tour.tour_id}
                                        cx={cx}
                                        cy={cy}
                                        r={5}
                                        fill={fill}
                                        fillOpacity={0.82}
                                        stroke="none"
                                        strokeWidth={0}
                                        style={{ cursor: 'pointer' }}
                                        onMouseEnter={() => setHoveredTour(tour)}
                                        onMouseLeave={() => setHoveredTour(null)}
                                      />
                                    );
                                  })}

                                  {(tourClusterData.clusters || []).filter((cluster) => Number.isFinite(Number(cluster.centroid_x)) && Number.isFinite(Number(cluster.centroid_y))).map((cluster) => (
                                    <path
                                      key={`centroid-${cluster.cluster_id}`}
                                      d={starPath(toX(Number(cluster.centroid_x)), toY(Number(cluster.centroid_y)), 9, 3.6)}
                                      fill="#e53e3e"
                                      stroke="white"
                                      strokeWidth={1.2}
                                    />
                                  ))}

                                  <rect
                                    x={legendX - 6}
                                    y={MT - 2}
                                    width={152}
                                    height={18 + (clustersForLegend.length + 1) * 22}
                                    rx={6}
                                    fill="white"
                                    stroke="#ddd"
                                    strokeWidth={1}
                                  />
                                  {clustersForLegend.map((cluster, index) => {
                                    const ly = MT + 12 + index * 22;
                                    const color = CLUSTER_COLORS[cluster.cluster_id % CLUSTER_COLORS.length];
                                    return (
                                      <g key={`legend-${cluster.cluster_id}`}>
                                        <circle cx={legendX + 7} cy={ly} r={6} fill={color} fillOpacity={0.85} />
                                        <text x={legendX + 18} y={ly + 4} fontSize={11} fill="#444">{getTourClusterDisplayName(cluster, tourModeledClusterOrder)}</text>
                                      </g>
                                    );
                                  })}
                                  {(() => {
                                    const ly = MT + 12 + clustersForLegend.length * 22;
                                    return (
                                      <g>
                                        <path d={starPath(legendX + 7, ly, 7, 2.8)} fill="#e53e3e" />
                                        <text x={legendX + 18} y={ly + 4} fontSize={11} fill="#444">Tâm cụm (centroid)</text>
                                      </g>
                                    );
                                  })()}
                                </>
                              );
                            })()}
                          </svg>

                          {hoveredTour && (
                            <div
                              style={{
                                position: 'absolute',
                                top: 56,
                                right: 16,
                                width: 220,
                                background: '#ffffff',
                                borderRadius: 12,
                                boxShadow: '0 10px 30px rgba(15, 23, 42, 0.15)',
                                padding: '12px 14px',
                                borderLeft: `4px solid ${CLUSTER_COLORS[hoveredTour.cluster_id % CLUSTER_COLORS.length]}`,
                                pointerEvents: 'none',
                              }}
                            >
                              <div className="fw-semibold mb-1">{hoveredTour.title}</div>
                              <div className="small text-muted mb-2">{hoveredTour.location || 'Chưa có địa điểm'}</div>
                              <div className="small">
                                <div>Toạ độ X/Y: <span className="fw-semibold">{Number(hoveredTour.pca_x || 0).toFixed(2)} / {Number(hoveredTour.pca_y || 0).toFixed(2)}</span></div>
                                <div>Nhóm: <span className="fw-semibold">{hoveredTour.cluster_label}</span></div>
                                <div>Booking: <span className="fw-semibold">{hoveredTour.booking_count}</span></div>
                                <div>Lấp đầy: <span className="fw-semibold">{formatPercent(hoveredTour.fill_rate, 0)}</span></div>
                                {hoveredTour.is_dead_tour && (
                                  <div>Dead reason: <span className="fw-semibold">{hoveredTour.dead_reason}</span></div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

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
                              {visibleClusters.map((cluster) => (
                                <tr key={cluster.cluster_id}>
                                  <td style={{ whiteSpace: 'nowrap' }}>
                                    <span
                                      className="badge rounded-pill"
                                      style={{ backgroundColor: CLUSTER_COLORS[cluster.cluster_id % CLUSTER_COLORS.length] }}
                                    >
                                      {getTourClusterDisplayName(cluster, tourModeledClusterOrder)}
                                    </span>
                                  </td>
                                  <td style={{ fontSize: '0.78rem', whiteSpace: 'nowrap' }}>{cluster.label}</td>
                                  <td
                                    style={{ fontSize: '0.78rem', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                                    title={cluster.representative_title}
                                  >
                                    <i className="bi bi-pin-angle-fill text-secondary me-1" style={{ fontSize: '0.65rem' }} />
                                    {cluster.representative_title}
                                  </td>
                                  <td className="text-center">
                                    {cluster.size}
                                    {cluster.avg_fill_rate > 0 && (
                                      <div style={{ fontSize: '0.65rem', color: '#6c757d' }}>
                                        {(Number(cluster.avg_fill_rate || 0) * 100).toFixed(0)}% lấp đầy
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

                  {filteredTours.length === 0 && (
                    <div className="text-center py-4 text-muted border rounded-3 bg-light mb-3">
                      <i className="bi bi-funnel fs-3 d-block mb-2"></i>
                      Không có tour để hiển thị phân cụm.
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
        )}
      </div>
    </div>
  );
}