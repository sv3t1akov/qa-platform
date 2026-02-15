"""
Rate limiting middleware для защиты от брутфорса
"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Простой in-memory rate limiter (для production использовать Redis)"""
    
    def __init__(self):
        # Структура: {key: [(timestamp, count), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = timedelta(minutes=5)
        self.last_cleanup = datetime.utcnow()
    
    def _cleanup_old_entries(self):
        """Удалить старые записи"""
        now = datetime.utcnow()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = now - timedelta(hours=1)
        keys_to_delete = []
        
        for key, timestamps in self.requests.items():
            self.requests[key] = [
                ts for ts in timestamps 
                if ts[0] > cutoff_time
            ]
            if not self.requests[key]:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.requests[key]
        
        self.last_cleanup = now
    
    def is_allowed(
        self, 
        key: str, 
        max_requests: int, 
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        Проверить, разрешён ли запрос
        
        Returns:
            (is_allowed, remaining_requests)
        """
        self._cleanup_old_entries()
        
        now = datetime.utcnow()
        cutoff_time = now - timedelta(seconds=window_seconds)
        
        # Удалить старые записи из окна
        self.requests[key] = [
            ts for ts in self.requests[key] 
            if ts[0] > cutoff_time
        ]
        
        # Подсчитать запросы в окне
        current_count = len(self.requests[key])
        
        if current_count >= max_requests:
            return False, 0
        
        # Добавить текущий запрос
        self.requests[key].append((now, 1))
        
        remaining = max_requests - current_count - 1
        return True, remaining


# Глобальный экземпляр rate limiter
rate_limiter = RateLimiter()


def get_client_identifier(request: Request) -> str:
    """Получить идентификатор клиента для rate limiting"""
    # Используем IP адрес или email из body для более точного ограничения
    client_ip = request.client.host if request.client else "unknown"
    
    # Для эндпоинтов регистрации/логина можно использовать email из body
    # Но это требует парсинга body, что сложнее
    # Пока используем IP + путь
    return f"{client_ip}:{request.url.path}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware для rate limiting"""
    
    def __init__(self, app, rate_limit_config: Dict[str, Tuple[int, int]] = None):
        """
        Args:
            app: FastAPI приложение
            rate_limit_config: Словарь {path: (max_requests, window_seconds)}
        """
        super().__init__(app)
        self.rate_limit_config = rate_limit_config or {
            "/api/v1/auth/register": (5, 300),  # 5 запросов за 5 минут
            "/api/v1/auth/login": (10, 300),     # 10 запросов за 5 минут
            "/api/v1/auth/forgot-password": (3, 600),  # 3 запроса за 10 минут
            "/api/v1/auth/reset-password": (5, 300),   # 5 запросов за 5 минут
        }
    
    async def dispatch(self, request: Request, call_next):
        # Пропускаем OPTIONS запросы (preflight для CORS)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Проверяем только указанные пути
        path = request.url.path
        
        if path in self.rate_limit_config:
            max_requests, window_seconds = self.rate_limit_config[path]
            client_id = get_client_identifier(request)
            
            is_allowed, remaining = rate_limiter.is_allowed(
                client_id, 
                max_requests, 
                window_seconds
            )
            
            if not is_allowed:
                logger.warning(
                    f"Rate limit exceeded: {client_id} on {path} "
                    f"(limit: {max_requests}/{window_seconds}s)"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Слишком много запросов. Попробуйте позже. "
                           f"Лимит: {max_requests} запросов за {window_seconds // 60} минут."
                )
            
            # Добавить заголовки с информацией о лимитах
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Window"] = str(window_seconds)
            return response
        
        return await call_next(request)
