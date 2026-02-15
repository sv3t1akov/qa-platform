"""
Pytest configuration and fixtures for mission tests
"""
import os
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.db.session import get_db, AsyncSessionLocal
from app.models.mission import Mission, Bug


# Test configuration from environment
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
TEST_LAB_TIMEOUT = float(os.getenv("TEST_LAB_TIMEOUT", "10.0"))
SKIP_MISSION_TESTS = os.getenv("SKIP_MISSION_TESTS", "false").lower() == "true"


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests"""
    return "asyncio"


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session fixture for tests.
    Uses the same database connection as the main app.
    """
    if not TEST_DATABASE_URL:
        pytest.skip("DATABASE_URL not set, skipping database tests")
    
    if not AsyncSessionLocal:
        pytest.skip("Database not configured, skipping database tests")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture(scope="function")
async def httpx_client() -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP client fixture for making requests to labs.
    """
    async with AsyncClient(timeout=TEST_LAB_TIMEOUT, follow_redirects=True) as client:
        yield client


@pytest.fixture(scope="function")
async def missions_with_labs(db_session: AsyncSession) -> list[Mission]:
    """
    Get all missions that have a base_url (labs).
    """
    if not TEST_DATABASE_URL:
        pytest.skip("DATABASE_URL not set, skipping database-dependent tests")
    
    if not db_session:
        pytest.skip("Database session not available")
    
    try:
        result = await db_session.execute(
            select(Mission).where(Mission.base_url.isnot(None)).where(Mission.base_url != "")
        )
        missions = result.scalars().all()
        return list(missions)
    except Exception as e:
        pytest.skip(f"Failed to fetch missions from database: {str(e)}")


@pytest.fixture(scope="function")
async def all_bugs(db_session: AsyncSession) -> list[Bug]:
    """
    Get all bugs from database.
    """
    if not TEST_DATABASE_URL:
        pytest.skip("DATABASE_URL not set, skipping database-dependent tests")
    
    if not db_session:
        pytest.skip("Database session not available")
    
    try:
        # Phase2: only active bugs (inactive = dropped for credo)
        result = await db_session.execute(select(Bug).where(Bug.active == True))
        bugs = result.scalars().all()
        return list(bugs)
    except Exception as e:
        pytest.skip(f"Failed to fetch bugs from database: {str(e)}")


@pytest.fixture(scope="function")
async def bugs_by_mission(db_session: AsyncSession) -> dict[str, list[Bug]]:
    """
    Get bugs grouped by mission_id (active only — Phase2).
    """
    if not TEST_DATABASE_URL:
        pytest.skip("DATABASE_URL not set, skipping database-dependent tests")
    
    if not db_session:
        pytest.skip("Database session not available")
    
    try:
        result = await db_session.execute(select(Bug).where(Bug.active == True))
        bugs = result.scalars().all()
        
        bugs_dict: dict[str, list[Bug]] = {}
        for bug in bugs:
            if bug.mission_id not in bugs_dict:
                bugs_dict[bug.mission_id] = []
            bugs_dict[bug.mission_id].append(bug)
        
        return bugs_dict
    except Exception as e:
        pytest.skip(f"Failed to fetch bugs from database: {str(e)}")


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "mission_health: Tests for lab availability")
    config.addinivalue_line("markers", "mission_flags: Tests for flag retrieval")
    config.addinivalue_line("markers", "slow: Slow running tests")


def pytest_collection_modifyitems(config, items):
    """Skip mission tests if SKIP_MISSION_TESTS is set"""
    if SKIP_MISSION_TESTS:
        skip_marker = pytest.mark.skip(reason="SKIP_MISSION_TESTS is set")
        for item in items:
            if "mission" in item.name:
                item.add_marker(skip_marker)
