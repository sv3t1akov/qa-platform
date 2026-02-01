// API Service - handles both mock mode and real backend
// When VITE_API_URL is set and VITE_DEMO_MODE is not 'true', calls backend API

const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
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
      console.log('Demo mode: API call skipped', endpoint);
      return { ok: true, status: 200, data: {} };
    }

    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
      ...options.headers,
    };

    try {
      const response = await fetch(url, { ...options, headers });
      const data = await response.json().catch(() => ({}));
      return { ok: response.ok, status: response.status, data };
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // === Domains ===
  async getDomains() {
    const res = await this.request('/api/v1/domains');
    return res.ok ? res.data.domains : [];
  }

  async getDomain(domainId) {
    const res = await this.request(`/api/v1/domains/${domainId}`);
    return res.ok ? res.data : null;
  }

  async getDomainMissions(domainId) {
    const res = await this.request(`/api/v1/domains/${domainId}/missions`);
    return res.ok ? res.data : null;
  }

  // === Missions ===
  async getMissions() {
    const res = await this.request('/api/v1/missions');
    return res.ok ? res.data.missions : [];
  }

  async getMission(missionId) {
    const res = await this.request(`/api/v1/missions/${missionId}`);
    return res.ok ? res.data : null;
  }

  // === Labs ===
  async startLab(missionId) {
    return this.request('/api/v1/labs/start', {
      method: 'POST',
      body: JSON.stringify({ missionId }),
    });
  }

  async getLabSession(sessionId) {
    return this.request(`/api/v1/labs/${sessionId}`);
  }

  async stopLab(sessionId) {
    return this.request(`/api/v1/labs/${sessionId}/stop`, {
      method: 'POST',
    });
  }

  // === Flags ===
  async verifyFlag(flag) {
    const res = await this.request('/api/v1/flags/verify', {
      method: 'POST',
      body: JSON.stringify({ flag }),
    });
    if (!res.ok) return { valid: false, message: res.data?.detail || 'Ошибка проверки' };
    // Normalize to frontend shape: bugTitle -> bug, newFlag -> isNew
    const d = res.data;
    return {
      valid: d.valid,
      isNew: d.newFlag,
      alreadyFound: d.alreadyFound,
      points: d.points ?? 0,
      bug: d.bugTitle,
      missionId: d.missionId,
      message: d.message ?? '',
    };
  }

  // === User Stats & Flags ===
  async getUserStats() {
    const res = await this.request('/api/v1/users/me/stats');
    return res.ok ? res.data : null;
  }

  async getUserFlags() {
    const res = await this.request('/api/v1/users/me/flags');
    return res.ok ? res.data.flags ?? [] : [];
  }
}

export const api = new ApiService();
export const isDemoMode = DEMO_MODE;
export default api;
