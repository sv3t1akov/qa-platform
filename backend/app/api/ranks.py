"""
API endpoints для рангов
"""
from fastapi import APIRouter
from app.utils.ranks import RANKS

router = APIRouter()


@router.get("")
async def get_ranks():
    """
    Получить список всех рангов в системе
    """
    return {
        "ranks": RANKS
    }
