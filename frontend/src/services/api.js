// API Service - handles both mock mode and real backend
// Currently in demo mode - all data comes from mocks/data.js

const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true' || !API_BASE_URL;

class ApiService {
  constructor() {
    this.baseUrl = API_BASE_URL;
    this.demoMode = DEMO_MODE;
    this.token = localStorage.getItem('auth_token');
  }

  // Helper for making authenticated requests
  async request(endpoint, options = {}) {
    if (this.demoMode) {
      // In demo mode, all data is handled by components using mock data
      console.log('Demo mode: API call skipped', endpoint);
      return { ok: true, status: 200, data: {} };
    }

    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });
      
      const data = await response.json();
      return { ok: response.ok, status: response.status, data };
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // === Labs ===
  async startLab(missionId) {
    return this.request('/api/v1/labs/start', {
      method: 'POST',
      body: JSON.stringify({ mission_id: missionId }),
    });
  }

  async stopLab(sessionId) {
    return this.request(`/api/v1/labs/${sessionId}`, {
      method: 'DELETE',
    });
  }

  // === Flags ===
  async verifyFlag(flag) {
    return this.request('/api/v1/flags/verify', {
      method: 'POST',
      body: JSON.stringify({ flag }),
    });
  }

  // === User Stats ===
  async getUserStats() {
    return this.request('/api/v1/stats');
  }
}

export const api = new ApiService();
export default api;
