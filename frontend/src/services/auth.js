// Auth service - управление токенами и авторизацией
const TOKEN_KEY = 'qa_access_token';
const REFRESH_KEY = 'qa_refresh_token';

export const authService = {
  setTokens(access, refresh) {
    localStorage.setItem(TOKEN_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  
  getAccessToken() {
    return localStorage.getItem(TOKEN_KEY);
  },
  
  getRefreshToken() {
    return localStorage.getItem(REFRESH_KEY);
  },
  
  clearTokens() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
  
  isAuthenticated() {
    const token = this.getAccessToken();
    if (!token) return false;
    
    // Проверить срок действия
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 > Date.now();
    } catch {
      return false;
    }
  }
};
