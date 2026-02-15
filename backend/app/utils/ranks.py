"""
Утилиты для расчета рангов пользователей
"""
from typing import TypedDict, Optional


class RankData(TypedDict):
    id: str
    nameRu: str
    nameEn: str
    minPoints: int
    color: str


class RankInfo(TypedDict):
    current: RankData
    next: Optional[RankData]
    progress: int  # 0-100
    pointsToNext: int


# Константа с данными всех рангов
RANKS: list[RankData] = [
    {"id": "newbie", "nameRu": "Новичок", "nameEn": "Newbie", "minPoints": 0, "color": "#9CA3AF"},
    {"id": "trainee", "nameRu": "Стажёр", "nameEn": "Trainee", "minPoints": 30, "color": "#6B7280"},
    {"id": "seeker", "nameRu": "Искатель", "nameEn": "Seeker", "minPoints": 75, "color": "#22C55E"},
    {"id": "tracker", "nameRu": "Следопыт", "nameEn": "Tracker", "minPoints": 140, "color": "#16A34A"},
    {"id": "tester", "nameRu": "Тестировщик", "nameEn": "Tester", "minPoints": 230, "color": "#3B82F6"},
    {"id": "bug_hunter", "nameRu": "Охотник за багами", "nameEn": "Bug Hunter", "minPoints": 350, "color": "#2563EB"},
    {"id": "explorer", "nameRu": "Исследователь", "nameEn": "Explorer", "minPoints": 500, "color": "#8B5CF6"},
    {"id": "qa_engineer", "nameRu": "QA-инженер", "nameEn": "QA Engineer", "minPoints": 700, "color": "#7C3AED"},
    {"id": "detective", "nameRu": "Детектив", "nameEn": "Detective", "minPoints": 950, "color": "#F59E0B"},
    {"id": "specialist", "nameRu": "Специалист", "nameEn": "Specialist", "minPoints": 1250, "color": "#D97706"},
    {"id": "bug_slayer", "nameRu": "Истребитель багов", "nameEn": "Bug Slayer", "minPoints": 1650, "color": "#EF4444"},
    {"id": "expert", "nameRu": "Эксперт", "nameEn": "Expert", "minPoints": 2150, "color": "#DC2626"},
    {"id": "senior_tester", "nameRu": "Старший тестировщик", "nameEn": "Senior Tester", "minPoints": 2800, "color": "#EC4899"},
    {"id": "test_architect", "nameRu": "Архитектор тестов", "nameEn": "Test Architect", "minPoints": 3650, "color": "#DB2777"},
    {"id": "qa_master", "nameRu": "Мастер QA", "nameEn": "QA Master", "minPoints": 4750, "color": "#F97316"},
    {"id": "legend", "nameRu": "Легенда", "nameEn": "Legend", "minPoints": 6500, "color": "#FBBF24"},
]


def calculate_rank(total_points: int) -> RankInfo:
    """
    Рассчитывает текущий ранг пользователя на основе накопленных баллов.
    
    Args:
        total_points: Общее количество баллов пользователя
        
    Returns:
        RankInfo с информацией о текущем ранге, следующем ранге, прогрессе и баллах до следующего ранга
    """
    # Находим текущий ранг (последний, где minPoints <= total_points)
    current_index = 0
    for i in range(len(RANKS) - 1, -1, -1):
        if total_points >= RANKS[i]["minPoints"]:
            current_index = i
            break
    
    current = RANKS[current_index]
    next_rank = RANKS[current_index + 1] if current_index < len(RANKS) - 1 else None
    
    # Расчёт прогресса до следующего ранга
    progress = 100
    points_to_next = 0
    
    if next_rank:
        points_in_current_rank = total_points - current["minPoints"]
        points_needed_for_next = next_rank["minPoints"] - current["minPoints"]
        progress = int((points_in_current_rank / points_needed_for_next) * 100)
        points_to_next = next_rank["minPoints"] - total_points
    
    return {
        "current": current,
        "next": next_rank,
        "progress": progress,
        "pointsToNext": points_to_next,
    }
