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

from fastapi import FastAPI, HTTPException, Body, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:5173",
        "*"  # Для MVP разрешаем все
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS & MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class MissionStatus(str, Enum):
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    LOCKED = "locked"


class Difficulty(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class FlagDifficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


# Request Models
class LabStartRequest(BaseModel):
    missionId: str


class FlagVerifyRequest(BaseModel):
    flag: str


# Response Models
class Domain(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    totalMissions: int
    completedMissions: int = 0


class Theory(BaseModel):
    title: str
    content: str


class Mission(BaseModel):
    id: str
    title: str
    description: str
    difficulty: str
    estimatedTime: str
    points: int
    bugs: int
    foundBugs: int = 0
    status: MissionStatus
    endpoint: str
    baseUrl: str
    theory: Theory
    hints: List[str] = []
    domainId: str
    tier: str


class TierInfo(BaseModel):
    unlocked: bool
    progress: int = 0
    requiredProgress: int = 80
    missions: List[Mission] = []


class DomainMissionsResponse(BaseModel):
    domainId: str
    tiers: Dict[str, TierInfo]


class LabSession(BaseModel):
    sessionId: str
    missionId: str
    baseUrl: str
    expiresAt: str
    status: str


class FlagVerifyResponse(BaseModel):
    valid: bool
    newFlag: bool = False
    alreadyFound: bool = False
    points: int = 0
    bugTitle: Optional[str] = None
    missionId: Optional[str] = None
    message: str


class FoundFlag(BaseModel):
    id: str
    oderId: str  # userId - typo в спецификации, сохраняем для совместимости
    missionId: str
    flag: str
    bugTitle: str
    bugDescription: Optional[str] = None
    points: int
    difficulty: FlagDifficulty
    foundAt: str


class UserStats(BaseModel):
    userId: str
    totalPoints: int
    rank: str
    completedMissions: int
    foundBugs: int
    totalBugs: int


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
                description="Интернет-магазины, корзины, заказы, возвраты",
                totalMissions=1,
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
        self.missions = {
            "ecom-return-refund": Mission(
                id="ecom-return-refund",
                title="Return & Refund Pipeline",
                description="Тестирование API возвратов товаров крупного маркетплейса MegaMart. Найдите 12 скрытых багов в сложной бизнес-логике.",
                difficulty="Advanced",
                estimatedTime="4-6 часов",
                points=1750,
                bugs=12,
                foundBugs=0,
                status=MissionStatus.AVAILABLE,
                endpoint="/api/v1/returns",
                baseUrl=os.getenv("ECOM_LAB_URL", "https://qa-lab-ecom-return-refund.fly.dev"),
                theory=Theory(
                    title="Тестирование сложных бизнес-процессов",
                    content="""## Введение

В этой миссии вы будете тестировать систему обработки возвратов товаров маркетплейса MegaMart.

## Ключевые области тестирования

### 1. Бизнес-правила
- Сроки возврата (14 дней стандарт, 7 дней электроника, 30 дней VIP)
- Категории товаров (некоторые не подлежат возврату)
- Расчёт суммы возврата с учётом скидок

### 2. Валидация данных  
- 127 параметров в запросе на возврат
- Взаимозависимости между полями
- Граничные значения

### 3. Безопасность
- Проверка владельца данных
- Антифрод система
- Авторизация операций

### 4. Интеграции
- Логистика (курьеры, ПВЗ)
- Платёжные системы
- Система лояльности

## API Endpoints

- `POST /api/v1/returns` - Создание заявки на возврат
- `GET /api/v1/returns/{id}` - Получение статуса
- `POST /api/v1/returns/{id}/cancel` - Отмена заявки
- `GET /api/v1/hints` - Подсказки

## Формат флагов

При нахождении бага API возвращает флаг:
```
FLAG{SNAKE_CASE_NAME}
```

Введите флаг в поле проверки для получения баллов."""
                ),
                hints=[
                    "Проверьте, когда именно определяется тип клиента — при покупке или при возврате",
                    "Внимательно посмотрите на все поля, содержащие слово 'Food'",
                    "Как рассчитывается скидка за bundle при частичном возврате?"
                ],
                domainId="ecommerce",
                tier="T4-T5"
            )
        }
        
        # Маппинг флагов миссии (для верификации)
        self.mission_flags = {
            "ecom-return-refund": {
                "FLAG{RETURN_WINDOW_BYPASS}": {
                    "title": "Return Window Bypass",
                    "description": "VIP статус после покупки даёт расширенный срок",
                    "points": 150,
                    "difficulty": FlagDifficulty.HARD
                },
                "FLAG{FOOD_CATEGORY_INCONSISTENCY}": {
                    "title": "Food Category Inconsistency",
                    "description": "Subcategory с 'Food' проходит проверку",
                    "points": 100,
                    "difficulty": FlagDifficulty.MEDIUM
                },
                "FLAG{DISCOUNT_DOUBLE_REFUND}": {
                    "title": "Discount Double Refund",
                    "description": "Bundle-скидка не пересчитывается при частичном возврате",
                    "points": 150,
                    "difficulty": FlagDifficulty.HARD
                },
                "FLAG{RESTOCKING_FEE_VIP_CONFLICT}": {
                    "title": "Restocking Fee VIP Conflict",
                    "description": "VIP полностью отменяет fee даже для вскрытых товаров",
                    "points": 150,
                    "difficulty": FlagDifficulty.HARD
                },
                "FLAG{COURIER_WEEKEND_SLIP}": {
                    "title": "Courier Weekend Slip",
                    "description": "Праздничные дни не блокируются",
                    "points": 100,
                    "difficulty": FlagDifficulty.MEDIUM
                },
                "FLAG{CROSSBORDER_COURIER_ALLOWED}": {
                    "title": "CrossBorder Courier Allowed",
                    "description": "Курьер доступен для cross-border вопреки правилам",
                    "points": 150,
                    "difficulty": FlagDifficulty.HARD
                },
                "FLAG{FRAUD_SCORE_BYPASS}": {
                    "title": "Fraud Score Bypass",
                    "description": "Отменённые заявки не учитываются в счётчике",
                    "points": 200,
                    "difficulty": FlagDifficulty.HARD
                },
                "FLAG{IIN_OWNER_MISMATCH}": {
                    "title": "IIN Owner Mismatch",
                    "description": "ИИН получателя не сверяется с покупателем",
                    "points": 200,
                    "difficulty": FlagDifficulty.HARD
                },
                "FLAG{INSPECTION_SKIP_THRESHOLD}": {
                    "title": "Inspection Skip Threshold",
                    "description": "Порог 100K проверяется per item, не по сумме",
                    "points": 150,
                    "difficulty": FlagDifficulty.HARD
                },
                "FLAG{EXCHANGE_DIFFERENT_CATEGORY}": {
                    "title": "Exchange Different Category",
                    "description": "Обмен между разными категориями проходит",
                    "points": 100,
                    "difficulty": FlagDifficulty.MEDIUM
                },
                "FLAG{VIDEO_REQUIREMENT_BYPASS}": {
                    "title": "Video Requirement Bypass",
                    "description": "Невалидные URL видео принимаются",
                    "points": 100,
                    "difficulty": FlagDifficulty.MEDIUM
                },
                "FLAG{LOYALTY_POINTS_OVERFLOW}": {
                    "title": "Loyalty Points Overflow",
                    "description": "Integer overflow при возврате бонусов",
                    "points": 200,
                    "difficulty": FlagDifficulty.HARD
                },
            }
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


# ─────────────────────────────────────────────────────────────────────────────
# DOMAINS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v1/domains")
async def get_domains():
    """Получение списка доменов"""
    return {"domains": list(db.domains.values())}


@app.get("/api/v1/domains/{domain_id}")
async def get_domain(domain_id: str):
    """Получение домена по ID"""
    if domain_id not in db.domains:
        raise HTTPException(status_code=404, detail="Domain not found")
    return db.domains[domain_id]


@app.get("/api/v1/domains/{domain_id}/missions")
async def get_domain_missions(domain_id: str):
    """Получение миссий домена с группировкой по тирам"""
    if domain_id not in db.domains:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    # Получаем миссии домена
    domain_missions = [m for m in db.missions.values() if m.domainId == domain_id]
    
    # Группируем по тирам
    tiers = {
        "T1": TierInfo(unlocked=True, progress=0, missions=[]),
        "T2": TierInfo(unlocked=True, progress=0, missions=[]),
        "T3": TierInfo(unlocked=True, progress=0, missions=[]),
        "T4": TierInfo(unlocked=True, progress=0, missions=[]),
        "T5": TierInfo(unlocked=True, progress=0, missions=[]),
    }
    
    for mission in domain_missions:
        # Определяем тир из mission.tier (может быть "T4-T5")
        tier_key = mission.tier.split("-")[0] if "-" in mission.tier else mission.tier
        if tier_key in tiers:
            tiers[tier_key].missions.append(mission)
    
    return DomainMissionsResponse(domainId=domain_id, tiers=tiers)


# ─────────────────────────────────────────────────────────────────────────────
# MISSIONS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v1/missions")
async def get_all_missions():
    """Получение всех миссий"""
    return {"missions": list(db.missions.values())}


@app.get("/api/v1/missions/{mission_id}")
async def get_mission(mission_id: str):
    """Получение детальной информации о миссии"""
    if mission_id not in db.missions:
        raise HTTPException(status_code=404, detail="Mission not found")
    return db.missions[mission_id]


# ─────────────────────────────────────────────────────────────────────────────
# LABS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v1/labs/start")
async def start_lab(request: LabStartRequest):
    """
    Запуск лабораторной среды
    
    В MVP версии возвращаем URL уже задеплоенной лабы.
    В production здесь будет оркестрация контейнеров через Fly.io Machines API.
    """
    if request.missionId not in db.missions:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    mission = db.missions[request.missionId]
    session_id = str(uuid.uuid4())[:12]
    
    # Проверяем доступность лабы
    lab_url = mission.baseUrl
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


# ─────────────────────────────────────────────────────────────────────────────
# FLAGS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v1/flags/verify")
async def verify_flag(request: FlagVerifyRequest):
    """
    Верификация флага
    
    1. Проверяем формат флага
    2. Ищем в нашей базе флагов
    3. Опционально валидируем через API лабы
    """
    flag = request.flag.strip().upper()
    user_id = db.get_user_id()
    
    # Инициализируем список флагов пользователя
    if user_id not in db.found_flags:
        db.found_flags[user_id] = []
    
    # Проверяем, не найден ли уже этот флаг
    existing_flags = [f.flag for f in db.found_flags[user_id]]
    if flag in existing_flags:
        return FlagVerifyResponse(
            valid=True,
            alreadyFound=True,
            points=0,
            message="Флаг уже был зарегистрирован ранее"
        )
    
    # Ищем флаг в нашей базе
    for mission_id, flags in db.mission_flags.items():
        if flag in flags:
            flag_info = flags[flag]
            
            # Создаём запись о найденном флаге
            found_flag = FoundFlag(
                id=str(uuid.uuid4()),
                oderId=user_id,
                missionId=mission_id,
                flag=flag,
                bugTitle=flag_info["title"],
                bugDescription=flag_info["description"],
                points=flag_info["points"],
                difficulty=flag_info["difficulty"],
                foundAt=datetime.now().isoformat()
            )
            
            db.found_flags[user_id].append(found_flag)
            
            return FlagVerifyResponse(
                valid=True,
                newFlag=True,
                points=flag_info["points"],
                bugTitle=flag_info["title"],
                missionId=mission_id,
                message=f"🎉 Отлично! Флаг принят! +{flag_info['points']} баллов"
            )
    
    # Пробуем валидировать через API лабы (если лаба запущена)
    for mission_id, mission in db.missions.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{mission.baseUrl}/api/v1/flags/verify",
                    json={"flag": flag},
                    headers={"X-Platform-Secret": settings.PLATFORM_SECRET}
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get("valid"):
                        info = result.get("info", {})
                        points = info.get("points", 100)
                        title = info.get("name", "Unknown Bug")
                        
                        found_flag = FoundFlag(
                            id=str(uuid.uuid4()),
                            oderId=user_id,
                            missionId=mission_id,
                            flag=flag,
                            bugTitle=title,
                            bugDescription=info.get("description"),
                            points=points,
                            difficulty=FlagDifficulty.MEDIUM,
                            foundAt=datetime.now().isoformat()
                        )
                        
                        db.found_flags[user_id].append(found_flag)
                        
                        return FlagVerifyResponse(
                            valid=True,
                            newFlag=True,
                            points=points,
                            bugTitle=title,
                            missionId=mission_id,
                            message=f"🎉 Отлично! Флаг принят! +{points} баллов"
                        )
        except:
            continue
    
    return FlagVerifyResponse(
        valid=False,
        points=0,
        message="Флаг не найден в системе"
    )


# ─────────────────────────────────────────────────────────────────────────────
# USER STATS & FLAGS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v1/users/me/stats")
async def get_user_stats():
    """Получение статистики пользователя"""
    user_id = db.get_user_id()
    user_flags = db.found_flags.get(user_id, [])
    
    total_points = sum(f.points for f in user_flags)
    total_bugs = sum(m.bugs for m in db.missions.values())
    
    # Подсчёт завершённых миссий
    completed_missions = 0
    for mission in db.missions.values():
        mission_flags = [f for f in user_flags if f.missionId == mission.id]
        if len(mission_flags) >= mission.bugs:
            completed_missions += 1
    
    return UserStats(
        userId=user_id,
        totalPoints=total_points,
        rank=db.get_rank(total_points),
        completedMissions=completed_missions,
        foundBugs=len(user_flags),
        totalBugs=total_bugs
    )


@app.get("/api/v1/users/me/flags")
async def get_user_flags():
    """Получение найденных флагов пользователя"""
    user_id = db.get_user_id()
    user_flags = db.found_flags.get(user_id, [])
    
    return {
        "flags": [f.dict() for f in user_flags],
        "total": len(user_flags)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=settings.DEBUG
    )
