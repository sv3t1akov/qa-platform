"""
API endpoints для доменов и миссий
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Dict, List, Optional, TYPE_CHECKING
import logging

from app.db.session import get_db
from app.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.mission import Domain, Mission, UserFoundFlag, Bug
from app.schemas.missions import (
    Domain as DomainModel,
    Mission as MissionModel,
    TierInfo,
    DomainMissionsResponse,
    Theory,
    TheoryAccessInfo,
    TheoryAccessResponse
)

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


# Баллы за один флаг по тиру миссии (согласно системе рангов)
POINTS_BY_TIER: Dict[str, int] = {
    "T1": 10,
    "T2": 20,
    "T3": 30,
    "T4": 40,
    "T5": 50,
}


async def _check_tier_unlocked(
    tier: str,
    domain_id: str,
    user_id: str,
    db: AsyncSession,
    user_role: str = None
) -> bool:
    """Проверяет, разблокирован ли тир для пользователя"""
    # Админы имеют доступ ко всем тирам
    if user_role == "admin":
        return True
    
    # T1 всегда разблокирован
    if tier == "T1":
        return True
    
    # Получить номер тира
    tier_num = int(tier[1])
    if tier_num < 2:
        return True
    
    # Получить предыдущий тир
    prev_tier = f"T{tier_num - 1}"
    
    # Получить все активные баги предыдущего тира в этом домене (Phase2: active only)
    has_active = await _check_bugs_active_column(db)
    query = select(Bug.id, Bug.mission_id).join(Mission, Bug.mission_id == Mission.id).where(Mission.domain_id == domain_id).where(Mission.tier == prev_tier)
    if has_active:
        query = query.where(Bug.active == True)
    bugs_result = await db.execute(query)
    prev_tier_bugs = bugs_result.all()
    total_bugs = len(prev_tier_bugs)
    
    if total_bugs == 0:
        # Если нет багов в предыдущем тире, считаем его разблокированным
        return True
    
    # Получить найденные флаги пользователя в предыдущем тире
    bug_ids = [bug.id for bug in prev_tier_bugs]
    found_flags_result = await db.execute(
        select(func.count(UserFoundFlag.id))
        .where(UserFoundFlag.user_id == user_id)
        .where(UserFoundFlag.bug_id.in_(bug_ids))
    )
    found_bugs = found_flags_result.scalar() or 0
    
    # Тир разблокирован, если найдено >= 80% багов в предыдущем тире
    progress = round((found_bugs / total_bugs) * 100)
    return progress >= 80


def _mission_for_student(
    mission_db: Mission,
    found_bugs: int,
    total_bugs: Optional[int] = None,
    theory_title: str = None,
    theory_content: str = None
):
    """Преобразует Mission из БД в модель для API.
    total_bugs: фактическое кол-во активных багов (из bugs). Если None — используется mission_db.bugs.
    Баллы = (баллы за тир) * кол-во активных багов."""
    bugs_count = total_bugs if total_bugs is not None else (mission_db.bugs or 0)
    points_per_flag = POINTS_BY_TIER.get(mission_db.tier, 10)
    points_total = points_per_flag * bugs_count
    return MissionModel(
        id=mission_db.id,
        title=mission_db.title,
        description=mission_db.description or "",
        difficulty=mission_db.difficulty or "Beginner",
        estimatedTime=mission_db.estimated_time or "",
        points=points_total,
        bugs=bugs_count,
        foundBugs=found_bugs,
        status="available",  # TODO: получить из user_mission_progress
        endpoint=mission_db.endpoint or "",
        baseUrl=mission_db.base_url or "",
        theory=Theory(
            title=theory_title or mission_db.theory_title or "",
            content=theory_content or mission_db.theory_content or ""
        ),
        hints=mission_db.hints or [],
        domainId=mission_db.domain_id,
        tier=mission_db.tier,
        taskDescription=mission_db.task_description,
        requestBodyExample=mission_db.request_body_example,
        requirements=mission_db.requirements
    )


@router.get("/domains")
async def get_domains(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка доменов с прогрессом (completedMissions). Без токена — прогресс 0."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("GET /domains: Fetching domains from database...")
    result = await db.execute(select(Domain).order_by(Domain.sort_order))
    domains_db = result.scalars().all()
    logger.info(f"GET /domains: Found {len(domains_db)} domains")
    
    completed_mission_ids = set()
    if current_user:
        has_active = await _check_bugs_active_column(db)
        query = select(Mission.id).join(Bug, Bug.mission_id == Mission.id).join(UserFoundFlag, Bug.id == UserFoundFlag.bug_id).where(UserFoundFlag.user_id == current_user.id)
        if has_active:
            query = query.where(Bug.active == True)
        query = query.group_by(Mission.id).having(func.count(UserFoundFlag.id) >= func.max(Mission.bugs))
        completed_missions_result = await db.execute(query)
        completed_mission_ids = {row[0] for row in completed_missions_result.all()}
        logger.info(f"GET /domains: user={current_user.id} completed_mission_ids={list(completed_mission_ids)}")
    else:
        logger.info("GET /domains: no user (optional auth), completedMissions=0 for all")
    
    domains = []
    for domain_db in domains_db:
        missions_count_result = await db.execute(
            select(Mission.id).where(Mission.domain_id == domain_db.id)
        )
        mission_ids = [row[0] for row in missions_count_result.all()]
        total_missions = len(mission_ids)
        completed_missions = sum(1 for mid in mission_ids if mid in completed_mission_ids)
        
        domains.append(DomainModel(
            id=domain_db.id,
            name=domain_db.name,
            icon=domain_db.icon or "",
            description=domain_db.description or "",
            totalMissions=total_missions,
            completedMissions=completed_missions
        ))
        logger.info(f"GET /domains: domain {domain_db.id} completedMissions={completed_missions} totalMissions={total_missions}")
    
    logger.info(f"GET /domains: Returning {len(domains)} domains")
    return {"domains": domains}


@router.get("/domains/{domain_id}")
async def get_domain(
    domain_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Получение домена по ID с прогрессом. Без токена — completedMissions=0."""
    
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain_db = result.scalar_one_or_none()
    
    if not domain_db:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    missions_count_result = await db.execute(
        select(Mission.id).where(Mission.domain_id == domain_id)
    )
    mission_ids = [row[0] for row in missions_count_result.all()]
    total_missions = len(mission_ids)
    
    completed_missions = 0
    if current_user:
        has_active = await _check_bugs_active_column(db)
        query = select(Mission.id).join(Bug, Bug.mission_id == Mission.id).join(UserFoundFlag, Bug.id == UserFoundFlag.bug_id).where(UserFoundFlag.user_id == current_user.id).where(Mission.domain_id == domain_id)
        if has_active:
            query = query.where(Bug.active == True)
        query = query.group_by(Mission.id).having(func.count(UserFoundFlag.id) >= func.max(Mission.bugs))
        completed_missions_result = await db.execute(query)
        completed_missions = len(completed_missions_result.all())
    
    return DomainModel(
        id=domain_db.id,
        name=domain_db.name,
        icon=domain_db.icon or "",
        description=domain_db.description or "",
        totalMissions=total_missions,
        completedMissions=completed_missions
    )


@router.get("/domains/{domain_id}/missions")
async def get_domain_missions(
    domain_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение миссий домена с группировкой по тирам"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Fetching missions for domain: {domain_id}, user: {current_user.id}")
    
    # Проверить существование домена
    domain_result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain_db = domain_result.scalar_one_or_none()
    if not domain_db:
        logger.warning(f"Domain {domain_id} not found")
        raise HTTPException(status_code=404, detail="Domain not found")
    
    logger.info(f"Domain {domain_id} found: {domain_db.name}")
    
    # Получить миссии домена
    missions_result = await db.execute(
        select(Mission).where(Mission.domain_id == domain_id).order_by(Mission.sort_order)
    )
    missions_db = missions_result.scalars().all()
    logger.info(f"Found {len(missions_db)} missions for domain {domain_id}")
    
    # Получить найденные флаги пользователя (только по активным багам — Phase2)
    has_active = await _check_bugs_active_column(db)
    query = select(UserFoundFlag.bug_id, Bug.mission_id).join(Bug, Bug.id == UserFoundFlag.bug_id).where(UserFoundFlag.user_id == current_user.id)
    if has_active:
        query = query.where(Bug.active == True)
    flags_result = await db.execute(query)
    user_flags_by_mission: Dict[str, int] = {}
    for row in flags_result:
        mission_id = row.mission_id
        user_flags_by_mission[mission_id] = user_flags_by_mission.get(mission_id, 0) + 1
    
    # Получить все активные баги для подсчета по тирам (Phase2: active only)
    has_active = await _check_bugs_active_column(db)
    query = select(Bug.mission_id, Bug.id).join(Mission, Bug.mission_id == Mission.id).where(Mission.domain_id == domain_id)
    if has_active:
        query = query.where(Bug.active == True)
    bugs_result = await db.execute(query)
    bugs_by_mission: Dict[str, List[str]] = {}
    for row in bugs_result:
        mission_id = row.mission_id
        bug_id = row.id
        if mission_id not in bugs_by_mission:
            bugs_by_mission[mission_id] = []
        bugs_by_mission[mission_id].append(bug_id)
    
    # Преобразовать миссии (total_bugs = фактическое кол-во активных багов из bugs)
    mission_list = []
    for m in missions_db:
        found_bugs = user_flags_by_mission.get(m.id, 0)
        total_bugs = len(bugs_by_mission.get(m.id, []))
        mission_list.append(_mission_for_student(m, found_bugs, total_bugs=total_bugs))
    
    # Группировать по тирам и вычислять прогресс
    tiers_data: Dict[str, Dict] = {
        "T1": {"missions": [], "total_bugs": 0, "found_bugs": 0},
        "T2": {"missions": [], "total_bugs": 0, "found_bugs": 0},
        "T3": {"missions": [], "total_bugs": 0, "found_bugs": 0},
        "T4": {"missions": [], "total_bugs": 0, "found_bugs": 0},
        "T5": {"missions": [], "total_bugs": 0, "found_bugs": 0},
    }
    
    for mission in mission_list:
        tier_key = mission.tier
        if tier_key in tiers_data:
            tiers_data[tier_key]["missions"].append(mission)
            # Подсчитать общее количество багов для этой миссии
            mission_bugs = bugs_by_mission.get(mission.id, [])
            tiers_data[tier_key]["total_bugs"] += len(mission_bugs)
            tiers_data[tier_key]["found_bugs"] += user_flags_by_mission.get(mission.id, 0)
    
    # Вычислить разблокировку тиров (T1 всегда разблокирован, остальные требуют 80% в предыдущем)
    # Админы имеют доступ ко всем тирам
    is_admin = current_user.role.value == "admin"
    
    tiers = {}
    for tier_num in range(1, 6):
        tier_key = f"T{tier_num}"
        tier_data = tiers_data[tier_key]
        
        # Вычислить прогресс в процентах
        progress = 0
        if tier_data["total_bugs"] > 0:
            progress = round((tier_data["found_bugs"] / tier_data["total_bugs"]) * 100)
        
        # T1 всегда разблокирован, остальные требуют 80% в предыдущем тире
        # Админы имеют доступ ко всем тирам
        unlocked = False
        if is_admin:
            unlocked = True  # Админы имеют доступ ко всем тирам
        elif tier_num == 1:
            unlocked = True  # T1 всегда доступен
        else:
            prev_tier_key = f"T{tier_num - 1}"
            prev_tier_data = tiers_data[prev_tier_key]
            prev_progress = 0
            if prev_tier_data["total_bugs"] > 0:
                prev_progress = round((prev_tier_data["found_bugs"] / prev_tier_data["total_bugs"]) * 100)
            unlocked = prev_progress >= 80
        
        tiers[tier_key] = TierInfo(
            unlocked=unlocked,
            progress=progress,
            missions=tier_data["missions"]
        )
        logger.info(f"Tier {tier_key}: unlocked={unlocked}, progress={progress}%, missions={len(tier_data['missions'])}")
    
    logger.info(f"Returning missions response for domain {domain_id} with {len(tiers)} tiers")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content=DomainMissionsResponse(domainId=domain_id, tiers=tiers).model_dump(mode="json"),
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@router.get("/missions")
async def get_all_missions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех миссий"""
    missions_result = await db.execute(select(Mission).order_by(Mission.sort_order))
    missions_db = missions_result.scalars().all()
    
    # Получить найденные флаги пользователя (только по активным багам — Phase2)
    has_active = await _check_bugs_active_column(db)
    query = select(UserFoundFlag.bug_id, Bug.mission_id).join(Bug, Bug.id == UserFoundFlag.bug_id).where(UserFoundFlag.user_id == current_user.id)
    if has_active:
        query = query.where(Bug.active == True)
    flags_result = await db.execute(query)
    user_flags_by_mission: Dict[str, int] = {}
    for row in flags_result:
        mission_id = row.mission_id
        user_flags_by_mission[mission_id] = user_flags_by_mission.get(mission_id, 0) + 1
    
    # Фактическое кол-во активных багов по миссиям
    has_active = await _check_bugs_active_column(db)
    query = select(Bug.mission_id, Bug.id)
    if has_active:
        query = query.where(Bug.active == True)
    bugs_result = await db.execute(query)
    bugs_by_mission: Dict[str, List[str]] = {}
    for row in bugs_result:
        mission_id = row.mission_id
        if mission_id not in bugs_by_mission:
            bugs_by_mission[mission_id] = []
        bugs_by_mission[mission_id].append(row.id)
    
    missions = []
    for m in missions_db:
        found_bugs = user_flags_by_mission.get(m.id, 0)
        total_bugs = len(bugs_by_mission.get(m.id, []))
        missions.append(_mission_for_student(m, found_bugs, total_bugs=total_bugs))
    
    return {"missions": missions}


@router.get("/missions/{mission_id}")
async def get_mission(
    mission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение детальной информации о миссии"""
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission_db = result.scalar_one_or_none()
    
    if not mission_db:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    # Проверить, разблокирован ли тир для пользователя
    tier_unlocked = await _check_tier_unlocked(
        mission_db.tier,
        mission_db.domain_id,
        current_user.id,
        db,
        user_role=current_user.role.value
    )
    
    # Админы имеют доступ ко всем миссиям
    if not tier_unlocked and current_user.role.value != "admin":
        raise HTTPException(
            status_code=403,
            detail=f"Tier {mission_db.tier} is locked. Complete 80% of {mission_db.tier[0]}{int(mission_db.tier[1]) - 1} missions first."
        )
    
    # Подсчитать найденные флаги для этой миссии (только активные баги — Phase2)
    has_active = await _check_bugs_active_column(db)
    query = select(func.count(UserFoundFlag.id)).join(Bug, Bug.id == UserFoundFlag.bug_id).where(Bug.mission_id == mission_id).where(UserFoundFlag.user_id == current_user.id)
    if has_active:
        query = query.where(Bug.active == True)
    flags_result = await db.execute(query)
    found_bugs = flags_result.scalar() or 0
    
    # Фактическое кол-во активных багов в миссии
    query = select(func.count(Bug.id)).where(Bug.mission_id == mission_id)
    if has_active:
        query = query.where(Bug.active == True)
    total_bugs_result = await db.execute(query)
    total_bugs = total_bugs_result.scalar() or 0
    
    return _mission_for_student(mission_db, found_bugs, total_bugs=total_bugs)


@router.get("/theory/access", response_model=TheoryAccessResponse)
async def get_theory_access(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение информации о доступе ко всем разделам теории.
    Доступ к разделу открывается при достижении 80% багов в предыдущем тире
    хотя бы в одном домене. T1 всегда доступен.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    is_admin = current_user.role.value == "admin"
    
    # Получить все активные баги по доменам и тирам (Phase2: active only)
    # Следующий тир теории открывается, когда хотя бы в одном домене пройдено 80% заданий
    has_active = await _check_bugs_active_column(db)
    query = select(Bug.id, Bug.mission_id, Mission.tier, Mission.domain_id).join(Mission, Bug.mission_id == Mission.id)
    if has_active:
        query = query.where(Bug.active == True)
    bugs_result = await db.execute(query)
    
    # bugs_by_domain_tier[domain_id][tier] = list of bug_ids
    bugs_by_domain_tier: Dict[str, Dict[str, List[str]]] = {}
    
    for row in bugs_result:
        domain_id = row.domain_id
        tier = row.tier
        bug_id = row.id
        if domain_id not in bugs_by_domain_tier:
            bugs_by_domain_tier[domain_id] = {"T1": [], "T2": [], "T3": [], "T4": [], "T5": []}
        if tier in bugs_by_domain_tier[domain_id]:
            bugs_by_domain_tier[domain_id][tier].append(bug_id)
    
    # Получить найденные флаги пользователя по доменам и тирам (только активные баги — Phase2)
    has_active = await _check_bugs_active_column(db)
    query = select(UserFoundFlag.bug_id, Bug.mission_id, Mission.tier, Mission.domain_id).join(Bug, Bug.id == UserFoundFlag.bug_id).join(Mission, Bug.mission_id == Mission.id).where(UserFoundFlag.user_id == current_user.id)
    if has_active:
        query = query.where(Bug.active == True)
    flags_result = await db.execute(query)
    
    # found_bugs_by_domain_tier[domain_id][tier] = count
    found_bugs_by_domain_tier: Dict[str, Dict[str, int]] = {}
    
    for row in flags_result:
        domain_id = row.domain_id
        tier = row.tier
        if domain_id not in found_bugs_by_domain_tier:
            found_bugs_by_domain_tier[domain_id] = {"T1": 0, "T2": 0, "T3": 0, "T4": 0, "T5": 0}
        if tier in found_bugs_by_domain_tier[domain_id]:
            found_bugs_by_domain_tier[domain_id][tier] += 1
    
    def _best_progress_for_prev_tier(prev_tier_key: str) -> tuple:
        """Возвращает (unlocked, progress, total_bugs, found_bugs) для предыдущего тира.
        unlocked = True если хотя бы в одном домене >= 80%.
        progress/total/found — из домена с лучшим прогрессом."""
        best_progress = 0
        best_total = 0
        best_found = 0
        any_unlocked = False
        for domain_id, tier_data in bugs_by_domain_tier.items():
            total = len(tier_data.get(prev_tier_key, []))
            if total == 0:
                continue
            found = found_bugs_by_domain_tier.get(domain_id, {}).get(prev_tier_key, 0)
            pct = round((found / total) * 100)
            if pct >= 80:
                any_unlocked = True
            if pct > best_progress:
                best_progress = pct
                best_total = total
                best_found = found
        return (any_unlocked, best_progress, best_total, best_found)
    
    # Вычислить доступ для каждого тира
    tiers_access = {}
    
    for tier_num in range(1, 6):
        tier_key = f"T{tier_num}"
        prev_tier_key = f"T{tier_num - 1}"
        
        # T1 всегда разблокирован, админы имеют доступ ко всем тирам
        if tier_num == 1 or is_admin:
            total_all = sum(len(d.get(tier_key, [])) for d in bugs_by_domain_tier.values())
            unlocked = True
            progress = 100 if total_all > 0 else 0
            total_bugs = total_all
            found_bugs = sum(found_bugs_by_domain_tier.get(did, {}).get(tier_key, 0) for did in bugs_by_domain_tier)
        else:
            unlocked, progress, total_bugs, found_bugs = _best_progress_for_prev_tier(prev_tier_key)
            if total_bugs == 0:
                unlocked = True
                progress = 100
        
        tiers_access[tier_key] = TheoryAccessInfo(
            unlocked=unlocked,
            progress=progress,
            totalBugs=total_bugs,
            foundBugs=found_bugs,
            requiredProgress=80
        )
    
    logger.info(f"Theory access for user {current_user.id}: {[(k, v.unlocked) for k, v in tiers_access.items()]}")
    
    return TheoryAccessResponse(tiers=tiers_access)
