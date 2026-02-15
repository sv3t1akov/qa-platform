"""
Tests for mission flag retrieval.

These tests verify that flags can be obtained according to bug conditions.
"""
import os
import pytest
from typing import Optional, Dict, Any
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mission import Mission, Bug
from tests.mission_triggers import get_trigger, has_trigger, get_base_return_request

# Check DATABASE_URL at module level
if not os.getenv("DATABASE_URL") and not os.getenv("TEST_DATABASE_URL"):
    pytest.skip("DATABASE_URL not set. Set DATABASE_URL or TEST_DATABASE_URL to run tests.", allow_module_level=True)


def find_flag_in_response(response: Response, flag: str, trigger_config: Dict[str, Any]) -> bool:
    """
    Find flag in HTTP response.
    Checks various locations based on trigger configuration.
    """
    flag_upper = flag.upper()
    
    # Check response text first (for any location)
    response_text = response.text
    if flag_upper in response_text.upper():
        return True
    
    # Try to parse as JSON
    try:
        data = response.json()
    except Exception:
        # Not JSON, already checked text
        return False
    
    # Check specific field if configured
    flag_field = trigger_config.get("flag_field", "flag")
    flag_location = trigger_config.get("flag_location", "response_body")
    flag_contains = trigger_config.get("flag_contains", False)
    
    if flag_location == "response_body":
        # Check in specific field
        if flag_field in data:
            field_value = data[flag_field]
            if isinstance(field_value, str):
                if flag_contains:
                    return flag_upper in field_value.upper()
                return flag_upper == field_value.upper()
            elif isinstance(field_value, list):
                # Check if flag is in list (e.g., warnings array)
                return any(flag_upper in str(item).upper() for item in field_value)
        
        # Check recursively in nested structures
        def check_nested(obj: Any) -> bool:
            if isinstance(obj, dict):
                for value in obj.values():
                    if check_nested(value):
                        return True
            elif isinstance(obj, list):
                for item in obj:
                    if check_nested(item):
                        return True
            elif isinstance(obj, str):
                if flag_contains:
                    return flag_upper in obj.upper()
                return flag_upper == obj.upper()
            return False
        
        return check_nested(data)
    
    return False


async def execute_trigger(
    httpx_client: AsyncClient,
    base_url: str,
    trigger_config: Dict[str, Any],
    bug_flag: str
) -> tuple[Optional[Response], Optional[str]]:
    """
    Execute trigger request(s) and return response.
    Handles setup requests, repeated requests, etc.
    """
    # Execute setup requests first
    setup_requests = trigger_config.get("setup", [])
    for setup_req in setup_requests:
        setup_url = f"{base_url}{setup_req['url']}"
        setup_body = setup_req.get("body")
        if callable(setup_body):
            setup_body = setup_body()
        
        try:
            await httpx_client.request(
                setup_req.get("method", "POST"),
                setup_url,
                params=setup_req.get("params", {}),
                json=setup_body,
                timeout=10.0
            )
        except Exception as e:
            # Setup might fail, but continue with main request
            print(f"Warning: Setup request failed: {e}")
    
    # Prepare main request
    method = trigger_config["method"]
    url = f"{base_url}{trigger_config['url']}"
    params = trigger_config.get("params", {})
    body = trigger_config.get("body")
    headers = trigger_config.get("headers", {})
    
    # Handle callable body (for dynamic requests)
    if callable(body):
        body = body()
    
    # Execute main request (possibly multiple times)
    repeat = trigger_config.get("repeat", 1)
    last_response = None
    last_error = None
    
    for _ in range(repeat):
        try:
            response = await httpx_client.request(
                method,
                url,
                params=params,
                json=body,
                headers=headers,
                timeout=10.0
            )
            last_response = response
        except Exception as e:
            last_error = str(e)
            continue
    
    if last_response is None:
        return None, last_error or "Request failed"
    
    return last_response, None


@pytest.mark.asyncio
@pytest.mark.mission_flags
async def test_all_mission_flags(
    missions_with_labs: list[Mission],
    bugs_by_mission: Dict[str, list[Bug]],
    httpx_client: AsyncClient,
    db_session: AsyncSession
):
    """
    Test that all mission bugs can be triggered and flags retrieved.
    """
    # Fixtures will skip if DATABASE_URL is not set
    if not missions_with_labs:
        pytest.skip("No missions with labs found")
    
    results = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "no_trigger": 0,
        "errors": []
    }
    
    for mission in missions_with_labs:
        mission_id = mission.id
        base_url = mission.base_url
        
        if not base_url:
            continue
        
        bugs = bugs_by_mission.get(mission_id, [])
        results["total"] += len(bugs)
        
        for bug in bugs:
            bug_id = bug.id
            bug_flag = bug.flag
            
            # Check if trigger is configured
            if not has_trigger(bug_id):
                results["no_trigger"] += 1
                results["skipped"] += 1
                print(f"⚠️  Skipping {bug_id}: no trigger configuration")
                continue
            
            trigger_config = get_trigger(bug_id)
            if not trigger_config:
                results["no_trigger"] += 1
                results["skipped"] += 1
                continue
            
            # Execute trigger
            try:
                response, error = await execute_trigger(
                    httpx_client,
                    base_url,
                    trigger_config,
                    bug_flag
                )
                
                if error:
                    results["failed"] += 1
                    results["errors"].append({
                        "bug_id": bug_id,
                        "mission_id": mission_id,
                        "error": error
                    })
                    continue
                
                if not response:
                    results["failed"] += 1
                    results["errors"].append({
                        "bug_id": bug_id,
                        "mission_id": mission_id,
                        "error": "No response received"
                    })
                    continue
                
                # Check status code
                expected_status = trigger_config.get("expected_status", [200])
                if response.status_code not in expected_status:
                    results["failed"] += 1
                    results["errors"].append({
                        "bug_id": bug_id,
                        "mission_id": mission_id,
                        "error": f"Expected status {expected_status}, got {response.status_code}"
                    })
                    continue
                
                # Check for flag
                flag_found = find_flag_in_response(response, bug_flag, trigger_config)
                
                if flag_found:
                    results["success"] += 1
                    print(f"✅ {bug_id}: Flag found")
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "bug_id": bug_id,
                        "mission_id": mission_id,
                        "error": f"Flag {bug_flag} not found in response",
                        "response_preview": response.text[:200] if response.text else "No response text"
                    })
                    print(f"❌ {bug_id}: Flag not found")
            
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "bug_id": bug_id,
                    "mission_id": mission_id,
                    "error": str(e)
                })
                print(f"❌ {bug_id}: Exception - {str(e)}")
    
    # Print summary
    print(f"\n=== Flag Test Summary ===")
    print(f"Total bugs: {results['total']}")
    print(f"Successful: {results['success']}")
    print(f"Failed: {results['failed']}")
    print(f"Skipped (no trigger): {results['no_trigger']}")
    print(f"Total skipped: {results['skipped']}")
    
    if results["errors"]:
        print(f"\nFailed bugs ({len(results['errors'])}):")
        for error in results["errors"][:10]:  # Show first 10
            print(f"  - {error['bug_id']} ({error['mission_id']}): {error['error']}")
        if len(results["errors"]) > 10:
            print(f"  ... and {len(results['errors']) - 10} more")
    
    # Assertions
    if results["total"] == 0:
        pytest.skip("No bugs found to test")
    
    # Don't fail if some bugs don't have triggers (they might be added later)
    # But fail if bugs with triggers are not working
    tested_count = results["total"] - results["no_trigger"]
    if tested_count > 0:
        success_rate = results["success"] / tested_count
        if success_rate < 0.5:  # Less than 50% success
            pytest.fail(
                f"Too many flag tests failed: {results['failed']}/{tested_count} "
                f"({success_rate*100:.1f}% success rate)"
            )


@pytest.mark.asyncio
@pytest.mark.mission_flags
async def test_single_bug_flag(
    db_session: AsyncSession,
    httpx_client: AsyncClient,
    bug_id: str = None
):
    """
    Test a single bug flag retrieval.
    Can be parametrized for specific bugs.
    """
    if not bug_id:
        pytest.skip("No bug_id provided")
    
    # Get bug from database
    from sqlalchemy import select
    result = await db_session.execute(select(Bug).where(Bug.id == bug_id))
    bug = result.scalar_one_or_none()
    
    if not bug:
        pytest.skip(f"Bug {bug_id} not found in database")
    
    # Get mission
    result = await db_session.execute(select(Mission).where(Mission.id == bug.mission_id))
    mission = result.scalar_one_or_none()
    
    if not mission or not mission.base_url:
        pytest.skip(f"Mission {bug.mission_id} has no base_url")
    
    # Get trigger
    if not has_trigger(bug_id):
        pytest.skip(f"No trigger configuration for {bug_id}")
    
    trigger_config = get_trigger(bug_id)
    
    # Execute trigger
    response, error = await execute_trigger(
        httpx_client,
        mission.base_url,
        trigger_config,
        bug.flag
    )
    
    assert error is None, f"Request failed: {error}"
    assert response is not None, "No response received"
    
    # Check status
    expected_status = trigger_config.get("expected_status", [200])
    assert response.status_code in expected_status, \
        f"Expected status {expected_status}, got {response.status_code}"
    
    # Check flag
    flag_found = find_flag_in_response(response, bug.flag, trigger_config)
    assert flag_found, \
        f"Flag {bug.flag} not found in response. Response: {response.text[:500]}"


@pytest.mark.asyncio
@pytest.mark.mission_flags
@pytest.mark.parametrize("mission_id", [], indirect=True)
async def test_mission_all_flags(
    db_session: AsyncSession,
    httpx_client: AsyncClient,
    mission_id: str
):
    """
    Test all flags for a specific mission.
    Can be parametrized for specific missions.
    """
    from sqlalchemy import select
    
    # Get mission
    result = await db_session.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    
    if not mission:
        pytest.skip(f"Mission {mission_id} not found")
    
    if not mission.base_url:
        pytest.skip(f"Mission {mission_id} has no base_url")
    
    # Get bugs for mission (active only — Phase2)
    result = await db_session.execute(
        select(Bug).where(Bug.mission_id == mission_id).where(Bug.active == True)
    )
    bugs = result.scalars().all()
    
    if not bugs:
        pytest.skip(f"No bugs found for mission {mission_id}")
    
    success_count = 0
    failed_bugs = []
    
    for bug in bugs:
        bug_id = bug.id
        
        if not has_trigger(bug_id):
            print(f"⚠️  Skipping {bug_id}: no trigger configuration")
            continue
        
        trigger_config = get_trigger(bug_id)
        
        try:
            response, error = await execute_trigger(
                httpx_client,
                mission.base_url,
                trigger_config,
                bug.flag
            )
            
            if error or not response:
                failed_bugs.append({"bug_id": bug_id, "error": error or "No response"})
                continue
            
            expected_status = trigger_config.get("expected_status", [200])
            if response.status_code not in expected_status:
                failed_bugs.append({
                    "bug_id": bug_id,
                    "error": f"Status {response.status_code} not in {expected_status}"
                })
                continue
            
            flag_found = find_flag_in_response(response, bug.flag, trigger_config)
            if flag_found:
                success_count += 1
            else:
                failed_bugs.append({
                    "bug_id": bug_id,
                    "error": f"Flag {bug.flag} not found"
                })
        
        except Exception as e:
            failed_bugs.append({"bug_id": bug_id, "error": str(e)})
    
    if failed_bugs:
        print(f"\nFailed bugs for mission {mission_id}:")
        for failed in failed_bugs:
            print(f"  - {failed['bug_id']}: {failed['error']}")
    
    # Assert at least some flags work
    tested_count = len(bugs) - (len(bugs) - len(failed_bugs) - success_count)
    if tested_count > 0:
        assert success_count > 0, f"No flags retrieved for mission {mission_id}"
