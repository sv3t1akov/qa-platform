// API Service - handles both mock mode and real backend
// When VITE_API_URL is set and VITE_DEMO_MODE is not 'true', calls backend API

import { authService } from './auth';

const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true' || !API_BASE_URL;

class ApiService {
  constructor() {
    this.baseUrl = API_BASE_URL;
    this.demoMode = DEMO_MODE;
    this.refreshing = false;
  }

  // Helper for making authenticated requests
  async request(endpoint, options = {}) {
    if (this.demoMode) {
      console.log('Demo mode: API call skipped', endpoint);
      return { ok: true, status: 200, data: {} };
    }

    const url = `${this.baseUrl}${endpoint}`;
    const token = authService.getAccessToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    };

    try {
      let response = await fetch(url, { ...options, headers });
      const data = await response.json().catch(() => ({}));
      
      // Если получили 401, попробовать обновить токен
      if (response.status === 401 && !options._retry) {
        const refreshed = await this.refreshTokenIfNeeded();
        if (refreshed) {
          // Повторить запрос с новым токеном
          const newToken = authService.getAccessToken();
          const newHeaders = {
            ...headers,
            Authorization: `Bearer ${newToken}`,
          };
          response = await fetch(url, { ...options, headers: newHeaders, _retry: true });
          const newData = await response.json().catch(() => ({}));
          return { ok: response.ok, status: response.status, data: newData };
        } else {
          // Не удалось обновить токен, очистить и редирект
          authService.clearTokens();
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
        }
      }
      
      return { ok: response.ok, status: response.status, data };
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  async refreshTokenIfNeeded() {
    if (this.refreshing) {
      // Уже обновляем токен, подождать
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (!this.refreshing) {
            clearInterval(checkInterval);
            resolve(true);
          }
        }, 100);
      });
    }

    const refreshToken = authService.getRefreshToken();
    if (!refreshToken) {
      return false;
    }

    this.refreshing = true;
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        authService.setTokens(data.access_token, data.refresh_token);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Token refresh error:', error);
      return false;
    } finally {
      this.refreshing = false;
    }
  }

  // === Auth ===
  async login(email, password) {
    return this.request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(email, password, displayName = null) {
    return this.request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, display_name: displayName }),
    });
  }

  async logout() {
    const refreshToken = authService.getRefreshToken();
    if (refreshToken) {
      await this.request('/api/v1/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    }
    authService.clearTokens();
  }

  async refreshToken() {
    const refreshToken = authService.getRefreshToken();
    if (!refreshToken) {
      return { ok: false };
    }
    return this.request('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  async forgotPassword(email) {
    return this.request('/api/v1/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  async resetPassword(token, newPassword) {
    return this.request('/api/v1/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, new_password: newPassword }),
    });
  }

  async getCurrentUser() {
    return this.request('/api/v1/auth/me');
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

  // === Ranks ===
  async getRanks() {
    const res = await this.request('/api/v1/ranks');
    return res.ok ? res.data.ranks ?? [] : [];
  }

  // === Theory ===
  async getTheoryAccess() {
    const res = await this.request('/api/v1/theory/access');
    if (res.ok && res.data?.tiers) {
      return res.data.tiers;
    }
    // Fallback для demo mode или ошибок
    return {
      T1: { unlocked: true, progress: 100, totalBugs: 0, foundBugs: 0, requiredProgress: 80 },
      T2: { unlocked: false, progress: 0, totalBugs: 0, foundBugs: 0, requiredProgress: 80 },
      T3: { unlocked: false, progress: 0, totalBugs: 0, foundBugs: 0, requiredProgress: 80 },
      T4: { unlocked: false, progress: 0, totalBugs: 0, foundBugs: 0, requiredProgress: 80 },
      T5: { unlocked: false, progress: 0, totalBugs: 0, foundBugs: 0, requiredProgress: 80 },
    };
  }

  /**
   * Load domains and missions from API in the shape expected by Dashboard/Lab.
   * Returns { domains, missionsByDomain }. Use when !isDemoMode.
   */
  async loadDomainsAndMissions() {
    try {
      console.log('Loading domains...');
      const rawDomains = await this.getDomains();
      console.log('Domains received:', rawDomains);
      
      if (!rawDomains?.length) {
        console.warn('No domains found in API response');
        return { domains: [], missionsByDomain: {} };
      }

      const defaultStyle = {
        color: 'from-pm-orange to-orange-600',
        bgColor: 'bg-pm-orange/10',
        borderColor: 'border-pm-orange/30',
        textColor: 'text-pm-orange',
      };
      const domains = rawDomains.map((d) => ({
        ...d,
        ...(DOMAIN_STYLES[d.id] ?? defaultStyle),
      }));

      console.log('Loading missions for domains...');
      const missionsByDomain = {};
      for (const domain of rawDomains) {
        try {
          console.log(`Loading missions for domain: ${domain.id}`);
          const res = await this.getDomainMissions(domain.id);
          console.log(`Missions response for ${domain.id}:`, res);
          
          if (!res?.tiers) {
            console.warn(`No tiers in response for domain ${domain.id}`);
            missionsByDomain[domain.id] = {};
            continue;
          }
          missionsByDomain[domain.id] = {};
          for (const [tier, tierInfo] of Object.entries(res.tiers)) {
            const missions = tierInfo.missions ?? [];
            // Сохраняем информацию о разблокировке и прогрессе тира
            missionsByDomain[domain.id][tier] = {
              missions: missions.length > 0 ? missions.map((m) => ({
                ...m,
                foundBugs: m.foundBugs ?? 0,
                theory: m.theory ?? { title: '', content: '' },
                hints: Array.isArray(m.hints) ? m.hints : [],
              })) : [],
              unlocked: tierInfo.unlocked ?? (tier === 'T1'), // T1 всегда разблокирован
              progress: tierInfo.progress ?? 0,
            };
          }
        } catch (domainError) {
          console.error(`Error loading missions for domain ${domain.id}:`, domainError);
          missionsByDomain[domain.id] = {};
        }
      }

      console.log('Final result:', { domains, missionsByDomain });
      return { domains, missionsByDomain };
    } catch (error) {
      console.error('Error in loadDomainsAndMissions:', error);
      throw error;
    }
  }
}

// Стили доменов для UI (совпадают с моками по id)
const DOMAIN_STYLES = {
  ecommerce: {
    color: 'from-blue-500 to-indigo-600',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    textColor: 'text-blue-400',
  },
  fintech: {
    color: 'from-emerald-500 to-teal-600',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30',
    textColor: 'text-emerald-400',
  },
  booking: {
    color: 'from-purple-500 to-violet-600',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
    textColor: 'text-purple-400',
  },
  marketplace: {
    color: 'from-orange-500 to-amber-600',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/30',
    textColor: 'text-orange-400',
  },
  healthcare: {
    color: 'from-red-500 to-rose-600',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    textColor: 'text-red-400',
  },
  social: {
    color: 'from-pink-500 to-fuchsia-600',
    bgColor: 'bg-pink-500/10',
    borderColor: 'border-pink-500/30',
    textColor: 'text-pink-400',
  },
};

export const api = new ApiService();
export const isDemoMode = DEMO_MODE;
export default api;
