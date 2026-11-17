// src/admin/services/adminService.js
import { api } from '../../client/services/api';

const liveConfig = () => ({
  headers: {
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    Pragma: 'no-cache',
    Expires: '0',
  },
  params: {
    _ts: Date.now(),
  },
});

export const adminService = {
  // Lấy thống kê tổng quan
  getDashboardStats: async () => {
    try {
      const response = await api.get('/admin/dashboard/stats', liveConfig());
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      throw error;
    }
  },

  // Lấy dữ liệu biểu đồ doanh thu
  getRevenueChart: async (period = 'month') => {
    try {
      const response = await api.get('/admin/dashboard/revenue-chart', {
        ...liveConfig(),
        params: {
          period,
          _ts: Date.now(),
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching revenue chart:', error);
      throw error;
    }
  },

  // Lấy top 5 khách hàng
  getTopCustomers: async () => {
    try {
      const response = await api.get('/admin/dashboard/top-customers', liveConfig());
      return response.data;
    } catch (error) {
      console.error('Error fetching top customers:', error);
      throw error;
    }
  },

  // Lấy thống kê booking theo status
  getBookingStatus: async () => {
    try {
      const response = await api.get('/admin/dashboard/booking-status', liveConfig());
      return response.data;
    } catch (error) {
      console.error('Error fetching booking status:', error);
      throw error;
    }
  },

  // Lấy doanh thu theo địa điểm
  getRevenueByLocation: async (locationType = null) => {
    try {
      const response = await api.get('/admin/dashboard/revenue-by-location', {
        ...liveConfig(),
        params: {
          ...(locationType ? { location_type: locationType } : {}),
          _ts: Date.now(),
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching revenue by location:', error);
      throw error;
    }
  },

  // Lấy doanh thu theo danh mục tour
  getRevenueByCategory: async (locationType = null) => {
    try {
      const response = await api.get('/admin/dashboard/revenue-by-category', {
        ...liveConfig(),
        params: {
          ...(locationType ? { location_type: locationType } : {}),
          _ts: Date.now(),
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching revenue by category:', error);
      throw error;
    }
  },

  // Lấy dữ liệu K-Means phân cụm điểm đến để hiển thị biểu đồ admin
  getKmeansDestinations: async (nClusters = 0) => {
    try {
      const response = await api.get('/admin/kmeans/destinations', {
        ...liveConfig(),
        params: {
          n_clusters: nClusters,
          _ts: Date.now(),
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching K-Means destinations:', error);
      throw error;
    }
  },

  rebuildCustomerSegments: async (nClusters = 0) => {
    try {
      const response = await api.post('/segments/rebuild', null, {
        ...liveConfig(),
        params: {
          n_clusters: nClusters,
          _ts: Date.now(),
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error rebuilding customer segments:', error);
      throw error;
    }
  },

  rebuildTourClusters: async (nClusters = 0) => {
    try {
      const response = await api.post('/admin/kmeans/tours/rebuild', null, {
        ...liveConfig(),
        params: {
          n_clusters: nClusters,
          _ts: Date.now(),
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error rebuilding tour clusters:', error);
      throw error;
    }
  },

  getCustomerSegment: async (userId) => {
    try {
      const response = await api.get(`/segments/${userId}`, liveConfig());
      return response.data;
    } catch (error) {
      console.error('Error fetching customer segment:', error);
      throw error;
    }
  },

  getRagConfig: async () => {
    try {
      const response = await api.get('/chat/config', liveConfig());
      return response.data;
    } catch (error) {
      console.error('Error fetching RAG config:', error);
      throw error;
    }
  },

  updateRagConfig: async (payload) => {
    try {
      const response = await api.put('/chat/config', payload);
      return response.data;
    } catch (error) {
      console.error('Error updating RAG config:', error);
      throw error;
    }
  },

  testRagChat: async (payload) => {
    try {
      const response = await api.post('/chat/test', payload);
      return response.data;
    } catch (error) {
      console.error('Error testing RAG chat:', error);
      throw error;
    }
  },

  reindexRag: async (force = true) => {
    try {
      const response = await api.post('/chat/reindex', null, {
        params: { force },
      });
      return response.data;
    } catch (error) {
      console.error('Error reindexing RAG:', error);
      throw error;
    }
  },

  invalidateRagCache: async (reason = 'admin_manual') => {
    try {
      const response = await api.post('/chat/cache/invalidate', null, {
        params: { reason },
      });
      return response.data;
    } catch (error) {
      console.error('Error invalidating RAG cache:', error);
      throw error;
    }
  },

  getRagMetrics: async () => {
    try {
      const response = await api.get('/chat/metrics', liveConfig());
      return response.data;
    } catch (error) {
      console.error('Error fetching RAG metrics:', error);
      throw error;
    }
  },
};
