"""
API endpoints для пользователей
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import List, Dict, Optional

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.mission import UserFoundFlag, Bug, Mission
from app.utils.ranks import calculate_rank

router = APIRouter()

# Маппинг баллов по тирам миссий (должен совпадать с flags.py)
POINTS_BY_TIER: Dict[str, int] = {
    "T1": 10,
    "T2": 20,
    "T3": 30,
    "T4": 40,
    "T5": 50,
}

_bugs_active_column_exists: Optional[bool] = None


async def _check_bugs_active_column(db: AsyncSession) -> bool:
    """Проверяет наличие колонки active в таблице bugs (Phase2)"""
    global _bugs_active_column_exists
    if _bugs_active_column_exists is not None:
        return _bugs_active_column_exists
    try:
        result = await db.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'bugs' AND column_name = 'active'
        """))
        _bugs_active_column_exists = result.scalar_one_or_none() is not None
        return _bugs_active_column_exists
    except Exception:
        _bugs_active_column_exists = False
        return False


@router.get("/me/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Статистика текущего пользователя.
    Использует фактическое кол-во активных багов (Phase2: bugs.active), не mission.bugs."""
    
    has_active = await _check_bugs_active_column(db)
    
    # Активные баги по миссиям (Phase2: только active=True)
    bugs_query = select(Bug.mission_id, func.count(Bug.id).label("cnt")).group_by(Bug.mission_id)
    if has_active:
        bugs_query = bugs_query.where(Bug.active == True)
    bugs_result = await db.execute(bugs_query)
    active_bugs_by_mission = {row.mission_id: row.cnt for row in bugs_result}
    
    # Найденные флаги пользователя по миссиям (только активные баги)
    flags_query = (
        select(Bug.mission_id, func.count(UserFoundFlag.id).label("cnt"))
        .join(UserFoundFlag, Bug.id == UserFoundFlag.bug_id)
        .where(UserFoundFlag.user_id == current_user.id)
        .group_by(Bug.mission_id)
    )
    if has_active:
        flags_query = flags_query.where(Bug.active == True)
    flags_result = await db.execute(flags_query)
    found_by_mission = {row.mission_id: row.cnt for row in flags_result}
    
    found_count = sum(found_by_mission.values())
    total_bugs = sum(active_bugs_by_mission.values())
    completed_missions = sum(
        1 for mid, total in active_bugs_by_mission.items()
        if found_by_mission.get(mid, 0) >= total
    )
    
    # Подсчёт баллов по тирам миссий (только активные баги)
    points_query = (
        select(Mission.tier)
        .join(Bug, Bug.mission_id == Mission.id)
        .join(UserFoundFlag, Bug.id == UserFoundFlag.bug_id)
        .where(UserFoundFlag.user_id == current_user.id)
    )
    if has_active:
        points_query = points_query.where(Bug.active == True)
    points_result = await db.execute(points_query)
    points = sum(POINTS_BY_TIER.get(row.tier, 10) for row in points_result)
    
    # Расчет ранга с использованием новой системы
    rank_info = calculate_rank(points)
    
    # Формируем ответ с новой структурой ранга
    response = {
        "userId": str(current_user.id),
        "totalPoints": points,
        "rank": {
            "id": rank_info["current"]["id"],
            "nameRu": rank_info["current"]["nameRu"],
            "nameEn": rank_info["current"]["nameEn"],
            "color": rank_info["current"]["color"]
        },
        "nextRank": None,
        "rankProgress": rank_info["progress"],
        "pointsToNextRank": rank_info["pointsToNext"],
        "foundBugs": found_count,
        "totalBugs": total_bugs,
        "completedMissions": completed_missions
    }
    
    # Добавляем информацию о следующем ранге, если он есть
    if rank_info["next"]:
        response["nextRank"] = {
            "id": rank_info["next"]["id"],
            "nameRu": rank_info["next"]["nameRu"],
            "nameEn": rank_info["next"]["nameEn"],
            "minPoints": rank_info["next"]["minPoints"]
        }
    
    return response


@router.get("/me/flags")
async def get_user_flags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Список найденных флагов текущего пользователя"""
    
    result = await db.execute(
        select(UserFoundFlag, Bug, Mission)
        .join(Bug, Bug.id == UserFoundFlag.bug_id)
        .join(Mission, Mission.id == Bug.mission_id)
        .where(UserFoundFlag.user_id == current_user.id)
        .order_by(UserFoundFlag.found_at.desc())
    )
    
    flags = []
    for row in result:
        # Используем баллы по тиру миссии, а не из bugs.points
        # Это соответствует системе расчета рангов
        mission_tier = row.Mission.tier
        points = POINTS_BY_TIER.get(mission_tier, 10)
        
        flags.append({
            "id": str(row.UserFoundFlag.id),
            "flag": row.Bug.flag,
            "bugTitle": row.Bug.title,
            "missionId": row.Mission.id,
            "missionTitle": row.Mission.title,
            "points": points,  # Баллы по тиру миссии, а не из bugs.points
            "difficulty": row.Bug.difficulty,
            "foundAt": row.UserFoundFlag.found_at.isoformat()
        })
    
    return {"flags": flags}
