"""
QA Training Platform - Backend API
Реализует контракты для существующего фронтенда на Fly.io
"""

import os
import uuid
import hashlib
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum

from fastapi import FastAPI, HTTPException, Body, Query, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn
import json
import time
from app.middleware.rate_limit import RateLimitMiddleware

from app.theory_blocks import get_theory
from app.api import auth, users, flags, ranks
from app.config import settings as app_settings
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.missions import (
    MissionStatus, Difficulty, FlagDifficulty,
    Theory, Domain, Mission, TierInfo, DomainMissionsResponse,
    LabSession, FlagVerifyRequest, FlagVerifyResponse,
    FoundFlag, UserStats, LabStartRequest
)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class Settings:
    # URL фронтенда для CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://qa-platform-frontend.fly.dev")
    
    # Базовый URL для лабораторий
    LAB_BASE_URL: str = os.getenv("LAB_BASE_URL", "https://qa-lab-{mission_id}.fly.dev")
    
    # Секрет для верификации флагов через лабы
    PLATFORM_SECRET: str = os.getenv("PLATFORM_SECRET", "platform-secret-key")
    
    # Режим отладки
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="QA Training Platform API",
    description="Backend API для платформы обучения QA-инженеров",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS для фронтенда
# #region agent log
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"CORS config: frontendUrl={app_settings.FRONTEND_URL}")
# #endregion
# CORS configuration - нельзя использовать "*" с allow_credentials=True
cors_origins = [
    app_settings.FRONTEND_URL,
    "http://localhost:3000",
    "http://localhost:5173",
]
# #region agent log
logger.info(f"CORS origins configured: {cors_origins}")
# #endregion
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware для защиты от брутфорса
app.add_middleware(RateLimitMiddleware)

# Exception handler для установки CORS заголовков при ошибках
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # #region agent log
    logger.exception(f"Global exception handler: {request.method} {request.url.path}: {type(exc).__name__}: {exc}")
    # #endregion
    origin = request.headers.get('origin', '')
    # Проверяем, что origin в списке разрешенных
    allowed_origins = [
        app_settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    headers = {}
    if origin in allowed_origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Methods"] = "*"
        headers["Access-Control-Allow-Headers"] = "*"
    
    # #region agent log
    logger.info(f"Exception handler: Setting CORS headers: {headers}")
    # #endregion
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=headers
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers=headers
        )

# Middleware для логирования запросов и проверки CORS
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # #region agent log
    origin = request.headers.get('origin', 'N/A')
    access_control_request_method = request.headers.get('access-control-request-method', 'N/A')
    access_control_request_headers = request.headers.get('access-control-request-headers', 'N/A')
    logger.info(f"Incoming request: {request.method} {request.url.path}, origin={origin}, acrm={access_control_request_method}, acrh={access_control_request_headers}")
    
    # Проверяем, что origin в списке разрешенных
    allowed_origins = [
        app_settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    logger.info(f"CORS check: origin={origin}, in_allowed={origin in allowed_origins}, allowed_origins={allowed_origins}")
    # #endregion
    try:
        response = await call_next(request)
        # #region agent log
        acao = response.headers.get('access-control-allow-origin', 'NOT SET')
        acam = response.headers.get('access-control-allow-methods', 'NOT SET')
        acac = response.headers.get('access-control-allow-credentials', 'NOT SET')
        logger.info(f"Request processed: {request.method} {request.url.path} -> {response.status_code}, acao={acao}, acam={acam}, acac={acac}")
        
        # Если CORS заголовки не установлены и это не health check, добавляем их вручную
        if acao == 'NOT SET' and request.url.path != '/health' and origin != 'N/A':
            if origin in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "*"
                response.headers["Access-Control-Allow-Headers"] = "*"
                logger.info(f"Manually added CORS headers for origin={origin}")
        # #endregion
        return response
    except Exception as e:
        # #region agent log
        logger.exception(f"Request error: {request.method} {request.url.path}: {type(e).__name__}: {e}")
        # #endregion
        # Пробрасываем исключение дальше - оно будет обработано exception_handler
        raise

# Подключение роутеров
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(flags.router, prefix="/api/v1/flags", tags=["flags"])
app.include_router(ranks.router, prefix="/api/v1/ranks", tags=["ranks"])

# Импорт роутера миссий (модели теперь в schemas/missions.py)
from app.api import missions as missions_router
app.include_router(missions_router.router, prefix="/api/v1", tags=["missions"])


# Startup event для логирования и миграций
@app.on_event("startup")
async def startup_event():
    # #region agent log
    logger.info("Application startup: Starting initialization...")
    logger.info(f"Database URL configured: {bool(os.getenv('DATABASE_URL'))}")
    logger.info(f"JWT Secret configured: {bool(os.getenv('JWT_SECRET_KEY'))}")
    
    # Проверка версии AuthService
    try:
        from app.services.auth_service import AUTH_SERVICE_VERSION
        logger.info(f"AuthService version: {AUTH_SERVICE_VERSION}")
    except ImportError:
        logger.warning("Could not import AUTH_SERVICE_VERSION - using old version")
    # #endregion
    
    # Автоматически применяем миграции при старте
    if os.getenv("DATABASE_URL"):
        try:
            # #region agent log
            logger.info("Running database migrations...")
            # #endregion
            from app.db.migrate import run_migration
            await run_migration()
            # #region agent log
            logger.info("Database migrations completed successfully")
            # #endregion
        except Exception as e:
            # #region agent log
            logger.exception(f"Error running migrations: {type(e).__name__}: {e}")
            logger.warning("Continuing startup despite migration error - tables may already exist")
            # #endregion
    
    # #region agent log
    logger.info("Application startup completed successfully")
    # #endregion


# ═══════════════════════════════════════════════════════════════════════════════
# IN-MEMORY DATABASE (для MVP, в production использовать PostgreSQL)
# ═══════════════════════════════════════════════════════════════════════════════

class Database:
    def __init__(self):
        self.found_flags: Dict[str, List[FoundFlag]] = {}  # userId -> flags
        self.lab_sessions: Dict[str, dict] = {}  # sessionId -> session info
        self.user_progress: Dict[str, Dict[str, int]] = {}  # userId -> {missionId: foundBugs}
        
        # Статические данные
        self._init_domains()
        self._init_missions()
    
    def _init_domains(self):
        self.domains = {
            "ecommerce": Domain(
                id="ecommerce",
                name="E-Commerce",
                icon="🛒",
                description="Интернет-магазины: Products, Cart, Orders, Checkout (по документу ECOMMERCE_TRAINING_MISSIONS_T1_T5)",
                totalMissions=10,
                completedMissions=0
            ),
            "fintech": Domain(
                id="fintech",
                name="Fintech",
                icon="💳",
                description="Банковские API, платежи, кошельки",
                totalMissions=0,
                completedMissions=0
            ),
            "booking": Domain(
                id="booking",
                name="Booking",
                icon="🏨",
                description="Бронирование отелей, билетов, услуг",
                totalMissions=0,
                completedMissions=0
            ),
            "marketplace": Domain(
                id="marketplace",
                name="Marketplace",
                icon="🏪",
                description="Маркетплейсы, продавцы, товары",
                totalMissions=0,
                completedMissions=0
            ),
            "healthcare": Domain(
                id="healthcare",
                name="Healthcare",
                icon="🏥",
                description="Медицинские системы, записи, рецепты",
                totalMissions=0,
                completedMissions=0
            ),
            "social": Domain(
                id="social",
                name="Social Media",
                icon="📱",
                description="Социальные сети, посты, профили",
                totalMissions=0,
                completedMissions=0
            ),
        }
    
    def _init_missions(self):
        # baseUrl лабы E-Commerce (Products, Cart, Orders, Checkout — см. ECOMMERCE_TRAINING_MISSIONS_T1_T5.md)
        ecom_lab_url = os.getenv("ECOM_LAB_URL", "https://qa-lab-ecom-return-refund.fly.dev")
        self.missions = {
            # === E-Commerce по документу ECOMMERCE_TRAINING_MISSIONS_T1_T5 ===
            # T1: Mission 1.1 "Призрачный товар" (Ghost Product)
            "ecom-t1-001": Mission(
                id="ecom-t1-001",
                title="Призрачный товар (Ghost Product)",
                description="Проверка корректных HTTP status codes для отсутствующих ресурсов.",
                difficulty="Beginner",
                estimatedTime="15 мин",
                points=50,
                bugs=2,
                foundBugs=0,
                status=MissionStatus.AVAILABLE,
                endpoint="/products/{id}",
                baseUrl=ecom_lab_url,
                theory=Theory(**get_theory("ecom-t1-001")),
                hints=["Вспомни, какой статус-код должен возвращаться для несуществующего ресурса", "Подумай о граничных и нестандартных значениях идентификатора (вне ожидаемого диапазона)", "Скрытые баги: система может некорректно обрабатывать граничные случаи для id — найдите флаги и зарегистрируйте на странице Flags."],
                domainId="ecommerce",
                tier="T1",
                taskDescription="Интернет-магазин электроники запустил новый каталог товаров. Клиенты жалуются, что при попытке открыть несуществующий товар система ведёт себя странно. Проверьте корректность обработки запросов к несуществующим ресурсам.\n\nОжидаемое поведение: несуществующий товар → 404 Not Found. Для id от 1 до 1000 API возвращает соответствующий товар из каталога. Для id вне допустимого диапазона — корректная ошибка без раскрытия внутренних данных.\n\nСкрытые баги: система может некорректно обрабатывать граничные или нестандартные значения id.",
                requestBodyExample=None  # GET — тело не требуется
            ),
            # T1: Mission 1.2 "Метод не тот" (Wrong Method)
            "ecom-t1-002": Mission(
                id="ecom-t1-002",
                title="Метод не тот (Wrong Method)",
                description="Проверка допустимых HTTP методов для endpoints.",
                difficulty="Beginner",
                estimatedTime="15 мин",
                points=50,
                bugs=1,
                foundBugs=0,
                status=MissionStatus.AVAILABLE,
                endpoint="/products/{id}",
                baseUrl=ecom_lab_url,
                theory=Theory(**get_theory("ecom-t1-002")),
                hints=["Вспомни, какие HTTP-методы допустимы для read-only ресурсов и как сервер сообщает о недопустимом методе", "Подумай, как API должен реагировать на «не тот» метод к тому же пути", "Скрытый баг: API может принять неожиданный метод и вернуть 200 с флагом — найдите и зарегистрируйте флаг на странице Flags."],
                domainId="ecommerce",
                tier="T1",
                taskDescription="Разработчики утверждают, что API строго следует REST-конвенциям. Проверьте, правильно ли обрабатываются некорректные HTTP-методы.\n\nОжидаемое поведение: POST к read-only endpoint → 405 Method Not Allowed.",
                requestBodyExample='{"any": "data"}'
            ),
            # T1: Mission 1.3 "Пустая корзина" (Empty Cart)
            "ecom-t1-003": Mission(
                id="ecom-t1-003",
                title="Пустая корзина (Empty Cart)",
                description="Проверка обязательных полей (required fields validation).",
                difficulty="Beginner",
                estimatedTime="15 мин",
                points=50,
                bugs=1,
                foundBugs=0,
                status=MissionStatus.AVAILABLE,
                endpoint="/cart/items",
                baseUrl=ecom_lab_url,
                theory=Theory(**get_theory("ecom-t1-003")),
                hints=["Вспомни, как проверяются обязательные поля и минимальные значения в API", "Подумай о разнице между отсутствующим полем и нулевым значением", "Скрытый баг: API может принять невалидное или отсутствующее значение и вернуть 201 с флагом — найдите и зарегистрируйте на странице Flags."],
                domainId="ecommerce",
                tier="T1",
                taskDescription="Функция добавления товара в корзину должна валидировать все обязательные поля. Проверьте, что система корректно отклоняет запросы с отсутствующими или недопустимыми данными.\n\nОжидаемое поведение: запрос с отсутствующими обязательными полями или недопустимыми значениями → 400 Bad Request.",
                requestBodyExample='{"productId": "123", "quantity": 1}'
            ),
            # T1: Mission 1.4 "Типы данных" (Data Types)
            "ecom-t1-004": Mission(
                id="ecom-t1-004",
                title="Типы данных (Data Types)",
                description="Type coercion и строгая валидация типов.",
                difficulty="Beginner",
                estimatedTime="15 мин",
                points=50,
                bugs=1,
                foundBugs=0,
                status=MissionStatus.AVAILABLE,
                endpoint="/cart/items",
                baseUrl=ecom_lab_url,
                theory=Theory(**get_theory("ecom-t1-004")),
                hints=["Вспомни, как контракт API задаёт типы полей (integer, string) и что происходит при несоответствии", "Подумай о неявном преобразовании типов в разных языках и фреймворках", "Скрытый баг: API может принять значение неверного типа и вернуть успешный ответ — найдите и зарегистрируйте на странице Flags."],
                domainId="ecommerce",
                tier="T1",
                taskDescription="В endpoint добавления в корзину (POST /cart/items) поле quantity по контракту должно быть целым числом (integer). Партнёры иногда отправляют данные в неверном формате. Ожидается строгая валидация типов.\n\nОжидаемое поведение: запрос с некорректным типом для обязательных полей → 400 Bad Request. Корректный запрос с ожидаемыми типами → 201 Created.",
                requestBodyExample='{"productId": "123", "quantity": 5}'
            ),
            # T1: Mission 1.5 "Content-Type игнорируется" (Content-Type Bypass)
            "ecom-t1-005": Mission(
                id="ecom-t1-005",
                title="Content-Type игнорируется (Content-Type Bypass)",
                description="Валидация Content-Type заголовка.",
                difficulty="Beginner",
                estimatedTime="15 мин",
                points=50,
                bugs=1,
                foundBugs=0,
                status=MissionStatus.AVAILABLE,
                endpoint="/cart/items",
                baseUrl=ecom_lab_url,
                theory=Theory(**get_theory("ecom-t1-005")),
                hints=["Вспомни, зачем клиент отправляет заголовок Content-Type и как сервер должен на него реагировать", "Подумай, что происходит, если заголовок не совпадает с форматом тела", "Скрытый баг: API может игнорировать Content-Type и вернуть 200 с флагом — найдите и зарегистрируйте на странице Flags."],
                domainId="ecommerce",
                tier="T1",
                taskDescription="REST API должен проверять заголовок Content-Type и отклонять запросы с неподдерживаемыми форматами.\n\nОжидаемое поведение: JSON с Content-Type: text/plain → 415 Unsupported Media Type.",
                requestBodyExample='{"productId": "123", "quantity": 1}'
            ),
            # T1: Mission 1.6 "Дублирование заказа" (Duplicate Order)
            "ecom-t1-006": Mission(
                id="ecom-t1-006",
                title="Дублирование заказа (Duplicate Order)",
                description="Идемпотентность операций.",
                difficulty="Beginner",
                estimatedTime="20 мин",
                points=50,
                bugs=1,
                foundBugs=0,
                status=MissionStatus.AVAILABLE,
                endpoint="/orders",
                baseUrl=ecom_lab_url,
                theory=Theory(**get_theory("ecom-t1-006")),
                hints=["Вспомни, зачем нужна идемпотентность при создании заказов и как её обычно реализуют", "Подумай, что должно происходить при повторной отправке того же запроса", "Скрытый баг: API может игнорировать ключ идемпотентности и создавать дубликаты — найдите флаг и зарегистрируйте на странице Flags."],
                domainId="ecommerce",
                tier="T1",
                taskDescription="При создании заказа API должен корректно обрабатывать повторную отправку идентичного запроса.\n\nОжидаемое поведение: повторный POST с тем же X-Idempotency-Key → 200 OK с существующим заказом (тот же orderId).",
                requestBodyExample='{"cartId": "cart-001"}'
            ),
            # T2: Mission 2.1 "Граница количества" (Quantity Boundary)
            "ecom-t2-001": Mission(
                id="ecom-t2-001",
                title="Граница количества (Quantity Boundary)",
                description="Граничные значения: quantity от 1 до 99. Off-by-one в валидации.",
                difficulty="Intermediate",
                estimatedTime="20 мин",
                points=60,
                bugs=1,
                foundBugs=0,
                status=MissionStatus.AVAILABLE,
                endpoint="/cart/items",
                baseUrl=ecom_lab_url,
                theory=Theory(**get_theory("ecom-t2-001")),
                hints=["Вспомни про тестирование граничных значений: что проверять на границах объявленного диапазона", "Подумай об ошибках off-by-one в условиях валидации", "Скрытый баг: API может принять значение за границей диапазона и вернуть 201 с флагом — найдите и зарегистрируйте на странице Flags."],
                domainId="ecommerce",
                tier="T2",
                taskDescription="В корзине действует правило: в одной позиции можно заказать от 1 до 99 единиц товара. Запросы с quantity вне этого диапазона должны отклоняться.\n\nОжидаемое поведение: значения в допустимом диапазоне принимаются (201 Created). Значения вне диапазона → 400 Bad Request.",
                requestBodyExample='{"productId": "123", "quantity": 5}'
            ),
            # T3: Mission 3.1 "Машина состояний заказа" (Order State Machine)
            "ecom-t3-001": Mission(
                id="ecom-t3-001",
                title="Машина состояний заказа (Order State Machine)",
                description="Заказ в статусе DELIVERED нельзя отменить. Проверка допустимых переходов.",
                difficulty="Intermediate",
                estimatedTime="30 мин",
                points=80,
                bugs=1,
                foundBugs=0,
                status=MissionStatus.AVAILABLE,
                endpoint="/orders/{id}/cancel",
                baseUrl=ecom_lab_url,
                theory=Theory(**get_theory("ecom-t3-001")),
                hints=["Вспомни про машины состояний: какие переходы допустимы после доставки заказа", "Подумай, как API должен реагировать на попытку изменить состояние уже доставленного заказа", "Скрытый баг: API может разрешить недопустимый переход и вернуть флаг — найдите и зарегистрируйте на странице Flags."],
                domainId="ecommerce",
                tier="T3",
                taskDescription="Заказ проходит через состояния: CREATED → PAID → PROCESSING → SHIPPED → DELIVERED. Проверьте корректность переходов между состояниями.\n\nОжидаемое поведение: доставленный заказ (DELIVERED) нельзя отменить.",
                requestBodyExample=None  # POST без тела или пустое тело
            ),
            # T4: Mission 4.1 "Чужой заказ" (IDOR)
            "ecom-t4-001": Mission(
                id="ecom-t4-001",
                title="Чужой заказ (Other's Order — IDOR)",
                description="Пользователь должен видеть только свои заказы. Проверка изоляции данных.",
                difficulty="Hard",
                estimatedTime="35 мин",
                points=100,
                bugs=1,
                foundBugs=0,
                status=MissionStatus.AVAILABLE,
                endpoint="/orders/{id}",
                baseUrl=ecom_lab_url,
                theory=Theory(**get_theory("ecom-t4-001")),
                hints=["Вспомни про проверку владельца ресурса: кто должен видеть данные заказа", "Подумай, как API различает «свой» и «чужой» ресурс при доступе по id", "Скрытый баг: API может вернуть данные чужого ресурса — найдите флаг и зарегистрируйте на странице Flags."],
                domainId="ecommerce",
                tier="T4",
                taskDescription="Пользователь должен видеть только свои заказы. Проверьте изоляцию данных между пользователями.\n\nОжидаемое поведение: пользователь видит только свои заказы.",
                requestBodyExample=None  # GET — тело не требуется
            ),
            # T5: Mission 5.1 "Промокод-брутфорс" (Promo Bruteforce)
            "ecom-t5-001": Mission(
                id="ecom-t5-001",
                title="Промокод-брутфорс (Promo Bruteforce)",
                description="Промокоды формата XXXX-XXXX. Проверка защиты от перебора.",
                difficulty="Expert",
                estimatedTime="45 мин",
                points=120,
                bugs=1,
                foundBugs=0,
                status=MissionStatus.AVAILABLE,
                endpoint="/checkout/promo",
                baseUrl=ecom_lab_url,
                theory=Theory(**get_theory("ecom-t5-001")),
                hints=["Вспомни про защиту от перебора: что должно ограничивать количество попыток проверки кода", "Подумай, как сервер реагирует на массовые запросы к одному endpoint", "Скрытый баг: отсутствие ограничения позволяет перебирать коды — найдите флаг и зарегистрируйте на странице Flags."],
                domainId="ecommerce",
                tier="T5",
                taskDescription="Промокоды имеют формат XXXX-XXXX. Проверьте защиту от перебора.\n\nОжидаемое поведение: защита от brute-force атак на промокоды.",
                requestBodyExample='{\n  "code": "TEST-0001"\n}'
            ),
        }
        # Маппинг флагов (по документу ECOMMERCE_TRAINING_MISSIONS_T1_T5)
        # ВАЖНО: Все флаги должны быть в ВЕРХНЕМ регистре для соответствия системе валидации
        self.mission_flags = {
            "ecom-t1-001": {
                "FLAG{IDOR_NEGATIVE_ID_A1B2C3}": {"title": "IDOR Negative ID", "description": "Отрицательный ID возвращает внутренние данные", "points": 50, "difficulty": FlagDifficulty.EASY},
                "FLAG{INTEGER_OVERFLOW_D4E5F6}": {"title": "Integer Overflow", "description": "ID > MAX_INT вызывает переполнение", "points": 50, "difficulty": FlagDifficulty.EASY},
            },
            "ecom-t1-002": {
                "FLAG{METHOD_CONFUSION_ALLOWED}": {"title": "Wrong Method Allowed", "description": "POST к read-only endpoint возвращает 200", "points": 50, "difficulty": FlagDifficulty.EASY},
            },
            "ecom-t1-003": {
                "FLAG{QUANTITY_ZERO_ACCEPTED}": {"title": "Quantity Zero Accepted", "description": "quantity=0 или отсутствует принимается", "points": 50, "difficulty": FlagDifficulty.EASY},
            },
            "ecom-t1-004": {
                "FLAG{STRING_QUANTITY_PARSED}": {"title": "String Quantity Parsed", "description": "Строка типа \"5шт\" парсится как число", "points": 50, "difficulty": FlagDifficulty.EASY},
            },
            "ecom-t1-005": {
                "FLAG{CONTENT_TYPE_BYPASS}": {"title": "Content-Type Bypass", "description": "JSON с Content-Type: text/plain принимается", "points": 50, "difficulty": FlagDifficulty.EASY},
            },
            "ecom-t1-006": {
                "FLAG{IDEMPOTENCY_IGNORED}": {"title": "Idempotency Ignored", "description": "Повторный POST с тем же ключом создаёт новый заказ", "points": 50, "difficulty": FlagDifficulty.EASY},
            },
            "ecom-t2-001": {
                "FLAG{BOUNDARY_OFF_BY_ONE}": {"title": "Boundary Off By One", "description": "quantity=100 проходит", "points": 60, "difficulty": FlagDifficulty.MEDIUM},
            },
            "ecom-t3-001": {
                "FLAG{DELIVERED_ORDER_CANCELLED}": {"title": "Delivered Order Cancelled", "description": "Отмена доставленного заказа", "points": 80, "difficulty": FlagDifficulty.MEDIUM},
            },
            "ecom-t4-001": {
                "FLAG{ORDER_IDOR_EXPOSED}": {"title": "Order IDOR Exposed", "description": "Доступ к чужому заказу", "points": 100, "difficulty": FlagDifficulty.HARD},
            },
            "ecom-t5-001": {
                "FLAG{PROMO_BRUTEFORCE_ALLOWED}": {"title": "Promo Bruteforce Allowed", "description": "Нет rate limit на промокоды", "points": 120, "difficulty": FlagDifficulty.HARD},
            },
        }
    
    def get_user_id(self) -> str:
        """Для MVP используем анонимного пользователя"""
        return "anonymous-user"
    
    def get_rank(self, points: int) -> str:
        if points >= 2000:
            return "QA Master"
        elif points >= 1000:
            return "Senior Tester"
        elif points >= 500:
            return "Middle Tester"
        elif points >= 200:
            return "Junior Tester"
        return "Newbie"


db = Database()


# ═══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "qa-platform-backend", "timestamp": datetime.now().isoformat()}


# Endpoints для доменов и миссий теперь в роутерах:
# - /api/v1/domains -> missions_router
# - /api/v1/domains/{domain_id} -> missions_router
# - /api/v1/domains/{domain_id}/missions -> missions_router
# - /api/v1/missions -> missions_router
# - /api/v1/missions/{mission_id} -> missions_router


# ─────────────────────────────────────────────────────────────────────────────
# LABS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v1/labs/start")
async def start_lab(
    request: LabStartRequest,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """
    Запуск лабораторной среды
    
    В MVP версии возвращаем URL уже задеплоенной лабы.
    В production здесь будет оркестрация контейнеров через Fly.io Machines API.
    """
    # Получить миссию из БД
    from app.models.mission import Mission as MissionDB, Bug, UserFoundFlag
    from sqlalchemy import select
    from sqlalchemy import func
    
    result = await db_session.execute(select(MissionDB).where(MissionDB.id == request.missionId))
    mission_db = result.scalar_one_or_none()
    
    if not mission_db:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    # Проверить, разблокирован ли тир для пользователя
    tier = mission_db.tier
    domain_id = mission_db.domain_id
    
    # T1 всегда разблокирован
    if tier != "T1":
        tier_num = int(tier[1])
        if tier_num >= 2:
            prev_tier = f"T{tier_num - 1}"
            
            # Получить все активные баги предыдущего тира в этом домене (Phase2: active only)
            bugs_query = (
                select(Bug.id, Bug.mission_id)
                .join(MissionDB, Bug.mission_id == MissionDB.id)
                .where(MissionDB.domain_id == domain_id)
                .where(MissionDB.tier == prev_tier)
            )
            if hasattr(Bug, 'active'):
                bugs_query = bugs_query.where(Bug.active == True)
            bugs_result = await db_session.execute(bugs_query)
            prev_tier_bugs = bugs_result.all()
            total_bugs = len(prev_tier_bugs)
            
            if total_bugs > 0:
                bug_ids = [bug.id for bug in prev_tier_bugs]
                found_flags_result = await db_session.execute(
                    select(func.count(UserFoundFlag.id))
                    .where(UserFoundFlag.user_id == current_user.id)
                    .where(UserFoundFlag.bug_id.in_(bug_ids))
                )
                found_bugs = found_flags_result.scalar() or 0
                
                progress = round((found_bugs / total_bugs) * 100)
                if progress < 80:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Tier {tier} is locked. Complete 80% of {prev_tier} missions first."
                    )
    
    mission_base_url = mission_db.base_url
    session_id = str(uuid.uuid4())[:12]
    
    # Проверяем доступность лабы
    lab_url = mission_base_url
    lab_status = "pending"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{lab_url}/health")
            if response.status_code == 200:
                lab_status = "running"
    except:
        pass
    
    session = LabSession(
        sessionId=session_id,
        missionId=request.missionId,
        baseUrl=lab_url,
        expiresAt=(datetime.now() + timedelta(hours=4)).isoformat(),
        status=lab_status
    )
    
    db.lab_sessions[session_id] = session.dict()
    
    return session


@app.get("/api/v1/labs/{session_id}")
async def get_lab_session(session_id: str):
    """Получение информации о сессии лабы"""
    if session_id not in db.lab_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return db.lab_sessions[session_id]


@app.post("/api/v1/labs/{session_id}/stop")
async def stop_lab(session_id: str):
    """Остановка лабораторной сессии"""
    if session_id in db.lab_sessions:
        db.lab_sessions[session_id]["status"] = "stopped"
    return {"message": "Lab session stopped", "sessionId": session_id}


# Endpoints для флагов и пользователей теперь в роутерах:
# - /api/v1/flags/verify -> flags.router
# - /api/v1/users/me/stats -> users.router
# - /api/v1/users/me/flags -> users.router


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # #region agent log
    logger.info(f"App starting: port={int(os.getenv('PORT', 8080))}, debug={settings.DEBUG}, frontendUrl={app_settings.FRONTEND_URL}, hasDatabaseUrl={bool(os.getenv('DATABASE_URL'))}")
    # #endregion
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=settings.DEBUG
    )
