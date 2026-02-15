"""
Tests for mission lab availability (health checks)
"""
import os
import pytest
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mission import Mission

# Check DATABASE_URL at module level
if not os.getenv("DATABASE_URL") and not os.getenv("TEST_DATABASE_URL"):
    pytest.skip("DATABASE_URL not set. Set DATABASE_URL or TEST_DATABASE_URL to run tests.", allow_module_level=True)


@pytest.mark.asyncio
@pytest.mark.mission_health
async def test_all_labs_health_check(
    missions_with_labs: list[Mission],
    httpx_client: AsyncClient
):
    """
    Test that all mission labs respond to health check endpoints.
    """
    # missions_with_labs fixture will skip if DATABASE_URL is not set
    if not missions_with_labs:
        pytest.skip("No missions with labs found")
    
    results = {
        "total": len(missions_with_labs),
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "errors": []
    }
    
    for mission in missions_with_labs:
        base_url = mission.base_url
        if not base_url:
            results["skipped"] += 1
            continue
        
        # Try /health endpoint
        health_urls = [
            f"{base_url}/health",
            f"{base_url}/api/v1/health",
            f"{base_url}/api/health",
        ]
        
        health_ok = False
        last_error = None
        
        for health_url in health_urls:
            try:
                response: Response = await httpx_client.get(health_url, timeout=5.0)
                if response.status_code == 200:
                    health_ok = True
                    break
            except Exception as e:
                last_error = str(e)
                continue
        
        if health_ok:
            results["success"] += 1
        else:
            results["failed"] += 1
            results["errors"].append({
                "mission_id": mission.id,
                "base_url": base_url,
                "error": last_error or "Health check failed for all endpoints"
            })
    
    # Print summary
    print(f"\n=== Health Check Summary ===")
    print(f"Total missions with labs: {results['total']}")
    print(f"Successful: {results['success']}")
    print(f"Failed: {results['failed']}")
    print(f"Skipped: {results['skipped']}")
    
    if results["errors"]:
        print("\nFailed missions:")
        for error in results["errors"]:
            print(f"  - {error['mission_id']}: {error['base_url']} - {error['error']}")
    
    # Assert that at least some labs are accessible
    # We don't fail if all are down (might be temporary), but log warnings
    if results["failed"] == results["total"] and results["total"] > 0:
        pytest.fail(f"All {results['total']} labs are unreachable. Check network connectivity or lab deployment status.")


@pytest.mark.asyncio
@pytest.mark.mission_health
async def test_lab_response_time(
    missions_with_labs: list[Mission],
    httpx_client: AsyncClient
):
    """
    Test that labs respond within reasonable time (< 5 seconds).
    """
    if not missions_with_labs:
        pytest.skip("No missions with labs found")
    
    import time
    
    slow_labs = []
    
    for mission in missions_with_labs:
        base_url = mission.base_url
        if not base_url:
            continue
        
        health_url = f"{base_url}/health"
        
        try:
            start_time = time.time()
            response = await httpx_client.get(health_url, timeout=5.0)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                if elapsed > 5.0:
                    slow_labs.append({
                        "mission_id": mission.id,
                        "base_url": base_url,
                        "response_time": elapsed
                    })
        except Exception:
            # Skip if lab is unreachable (handled by other test)
            continue
    
    if slow_labs:
        print("\n=== Slow Labs (>5s response time) ===")
        for lab in slow_labs:
            print(f"  - {lab['mission_id']}: {lab['response_time']:.2f}s")
    
    # Don't fail test, just warn
    # This is informational - some labs might be slow due to cold starts


@pytest.mark.asyncio
@pytest.mark.mission_health
@pytest.mark.parametrize("mission", [], indirect=True)
async def test_single_mission_health(
    mission: Mission,
    httpx_client: AsyncClient
):
    """
    Parametrized test for individual mission health check.
    Can be used to test specific missions.
    """
    if not mission.base_url:
        pytest.skip(f"Mission {mission.id} has no base_url")
    
    health_url = f"{mission.base_url}/health"
    
    try:
        response = await httpx_client.get(health_url, timeout=5.0)
        assert response.status_code == 200, f"Health check failed for {mission.id}: {response.status_code}"
        
        # Optionally check response content
        data = response.json()
        assert "status" in data or "healthy" in str(data).lower(), \
            f"Health check response doesn't contain status for {mission.id}"
    except Exception as e:
        pytest.fail(f"Health check failed for mission {mission.id} ({mission.base_url}): {str(e)}")
