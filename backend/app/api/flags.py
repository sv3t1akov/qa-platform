"""
API endpoints для флагов
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime
from typing import Optional, Dict
import logging

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.mission import Bug, UserFoundFlag, Mission, UserMissionProgress, MissionStatus
from app.utils.ranks import calculate_rank
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Кэш для проверки наличия колонки active (Phase2)
_bugs_active_column_exists: Optional[bool] = None

async def _check_bugs_active_column(db: AsyncSession) -> bool:
    """Проверяет наличие колонки active в таблице bugs (Phase2)"""
    global _bugs_active_column_exists
    if _bugs_active_column_exists is not None:
        return _bugs_active_column_exists
    
    try:
        result = await db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'bugs' 
            AND column_name = 'active'
        """))
        exists = result.scalar_one_or_none() is not None
        _bugs_active_column_exists = exists
        logger.info(f"Phase2: bugs.active column exists = {exists}")
        return exists
    except Exception as e:
        logger.warning(f"Phase2: Error checking bugs.active column: {e}, assuming False")
        _bugs_active_column_exists = False
        return False

# Маппинг баллов по тирам миссий
POINTS_BY_TIER: Dict[str, int] = {
    "T1": 10,
    "T2": 20,
    "T3": 30,
    "T4": 40,
    "T5": 50,
}


class FlagVerifyRequest(BaseModel):
    flag: str


class RankInfo(BaseModel):
    id: str
    nameRu: str
    nameEn: str
    color: str


class FlagVerifyResponse(BaseModel):
    valid: bool
    newFlag: bool = False
    alreadyFound: bool = False
    points: int = 0
    bugTitle: Optional[str] = None
    missionId: Optional[str] = None
    message: str
    newTotalPoints: Optional[int] = None
    rank: Optional[RankInfo] = None


@router.post("/verify", response_model=FlagVerifyResponse)
async def verify_flag(
    request: FlagVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Проверка и регистрация флага.
    Флаг привязывается ТОЛЬКО к текущему пользователю.
    """
    flag = request.flag.strip().upper()
    
    # Найти баг по флагу (поиск без учёта регистра: в БД может быть a1b2c3, пользователь вводит то же)
    result = await db.execute(
        select(Bug).where(func.upper(Bug.flag) == flag)
    )
    bug = result.scalar_one_or_none()
    
    if not bug:
        return FlagVerifyResponse(
            valid=False,
            points=0,
            message="Флаг не найден в системе"
        )
    
    # Проверить, не найден ли уже этот флаг ЭТИМ пользователем
    existing_result = await db.execute(
        select(UserFoundFlag)
        .where(UserFoundFlag.user_id == current_user.id)
        .where(UserFoundFlag.bug_id == bug.id)
    )
    
    if existing_result.scalar_one_or_none():
        return FlagVerifyResponse(
            valid=True,
            alreadyFound=True,
            points=0,
            message="Флаг уже был зарегистрирован ранее"
        )
    
    # Получить миссию для расчёта баллов по тиру
    mission_result = await db.execute(
        select(Mission).where(Mission.id == bug.mission_id)
    )
    mission = mission_result.scalar_one_or_none()
    
    if not mission:
        return FlagVerifyResponse(
            valid=False,
            points=0,
            message="Миссия не найдена"
        )
    
    # Рассчитать баллы по тиру миссии
    points = POINTS_BY_TIER.get(mission.tier, 10)  # По умолчанию 10, если тир не найден
    
    # Зарегистрировать флаг для текущего пользователя
    found_flag = UserFoundFlag(
        user_id=current_user.id,
        bug_id=bug.id
    )
    db.add(found_flag)
    
    # Обновить прогресс по миссии
    await update_mission_progress(db, current_user.id, bug.mission_id)
    
    await db.commit()
    
    # Пересчитать общие баллы пользователя по тирам миссий
    # Получаем все найденные флаги с их миссиями
    found_flags_result = await db.execute(
        select(Bug, Mission)
        .join(Mission, Mission.id == Bug.mission_id)
        .join(UserFoundFlag, Bug.id == UserFoundFlag.bug_id)
        .where(UserFoundFlag.user_id == current_user.id)
    )
    
    # Пересчитываем total_points по тирам миссий
    new_total_points = 0
    for row in found_flags_result:
        mission_tier = row.Mission.tier
        new_total_points += POINTS_BY_TIER.get(mission_tier, 10)
    
    # Получить информацию о ранге
    rank_info = calculate_rank(new_total_points)
    
    return FlagVerifyResponse(
        valid=True,
        newFlag=True,
        points=points,
        bugTitle=bug.title,
        missionId=bug.mission_id,
        message=f"🎉 Отлично! Флаг принят! +{points} баллов",
        newTotalPoints=new_total_points,
        rank=RankInfo(
            id=rank_info["current"]["id"],
            nameRu=rank_info["current"]["nameRu"],
            nameEn=rank_info["current"]["nameEn"],
            color=rank_info["current"]["color"]
        )
    )


async def update_mission_progress(
    db: AsyncSession, 
    user_id: str, 
    mission_id: str
):
    """Обновляет статус миссии на основе найденных флагов"""
    
    # Получить все активные баги миссии (Phase2: active only)
    has_active = await _check_bugs_active_column(db)
    query = select(func.count(Bug.id)).where(Bug.mission_id == mission_id)
    if has_active:
        query = query.where(Bug.active == True)
    total_bugs_result = await db.execute(query)
    total = total_bugs_result.scalar() or 0
    
    # Получить найденные баги пользователем (только активные — Phase2)
    query = select(func.count(UserFoundFlag.id)).join(Bug, Bug.id == UserFoundFlag.bug_id).where(Bug.mission_id == mission_id).where(UserFoundFlag.user_id == user_id)
    if has_active:
        query = query.where(Bug.active == True)
    found_bugs_result = await db.execute(query)
    found = found_bugs_result.scalar() or 0
    
    # Определить статус
    if found == 0:
        status = MissionStatus.available
    elif found < total:
        status = MissionStatus.in_progress
    else:
        status = MissionStatus.completed
    
    # Upsert прогресса
    progress_result = await db.execute(
        select(UserMissionProgress)
        .where(UserMissionProgress.user_id == user_id)
        .where(UserMissionProgress.mission_id == mission_id)
    )
    existing = progress_result.scalar_one_or_none()
    
    if existing:
        existing.status = status
        if status == MissionStatus.in_progress and not existing.started_at:
            existing.started_at = datetime.utcnow()
        if status == MissionStatus.completed and not existing.completed_at:
            existing.completed_at = datetime.utcnow()
    else:
        new_progress = UserMissionProgress(
            user_id=user_id,
            mission_id=mission_id,
            status=status,
            started_at=datetime.utcnow() if status != MissionStatus.available else None
        )
        db.add(new_progress)
