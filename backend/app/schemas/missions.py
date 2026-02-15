"""
Pydantic схемы для миссий и доменов
"""
from pydantic import BaseModel
from typing import Optional, Dict, List
from enum import Enum


class MissionStatus(str, Enum):
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    LOCKED = "locked"


class Difficulty(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


class FlagDifficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class Theory(BaseModel):
    title: str
    content: str


class Domain(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    totalMissions: int
    completedMissions: int = 0


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
    taskDescription: Optional[str] = None
    requestBodyExample: Optional[str] = None
    requirements: Optional[str] = None  # Бизнес-правила для T3 миссий


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


class FlagVerifyRequest(BaseModel):
    flag: str


class RankInfo(BaseModel):
    id: str
    nameRu: str
    nameEn: str
    color: str


class NextRankInfo(BaseModel):
    id: str
    nameRu: str
    nameEn: str
    minPoints: int


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
    rank: RankInfo
    nextRank: Optional[NextRankInfo] = None
    rankProgress: int  # 0-100
    pointsToNextRank: int  # 0 если максимальный ранг
    completedMissions: int
    foundBugs: int
    totalBugs: int


class LabStartRequest(BaseModel):
    missionId: str


class TheoryAccessInfo(BaseModel):
    """Информация о доступе к разделу теории"""
    unlocked: bool
    progress: int = 0  # Процент найденных багов в предыдущем тире
    totalBugs: int = 0  # Всего багов в предыдущем тире
    foundBugs: int = 0  # Найдено багов в предыдущем тире
    requiredProgress: int = 80  # Требуемый процент для разблокировки


class TheoryAccessResponse(BaseModel):
    """Ответ с информацией о доступе ко всем разделам теории"""
    tiers: Dict[str, TheoryAccessInfo]  # {"T1": {...}, "T2": {...}, ...}
