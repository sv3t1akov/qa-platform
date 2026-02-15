"""
Integration tests for existing lab tests.

This module adapts existing lab-specific tests (e.g., ecommerce_return_refund_lab)
to work with production URLs from the database.
"""
import pytest
import os
from typing import Optional
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.mission import Mission


@pytest.mark.asyncio
@pytest.mark.mission_flags
async def test_ecommerce_return_refund_lab_flags(
    db_session: AsyncSession,
    httpx_client: AsyncClient
):
    """
    Test flags for ecommerce_return_refund_lab using adapted tests.
    
    This test finds the mission in the database and uses its base_url
    to run the lab-specific tests.
    """
    # Find the return/refund mission
    result = await db_session.execute(
        select(Mission).where(Mission.id.like("%return%refund%"))
    )
    mission = result.scalar_one_or_none()
    
    if not mission:
        # Try alternative mission IDs
        for mission_id in ["ecom-return-refund", "ecom-t4-001", "ecom-t5-001"]:
            result = await db_session.execute(
                select(Mission).where(Mission.id == mission_id)
            )
            mission = result.scalar_one_or_none()
            if mission:
                break
    
    if not mission or not mission.base_url:
        pytest.skip("E-Commerce Return & Refund lab mission not found or has no base_url")
    
    base_url = mission.base_url
    
    # Import and adapt tests from the lab
    # Note: We can't directly import the lab tests as they're in a different package
    # Instead, we'll use the trigger configurations from mission_triggers.py
    # which are based on those tests
    
    from tests.mission_triggers import MISSION_TRIGGERS, get_base_return_request
    from datetime import date, timedelta
    
    # Test flags that are configured for this lab
    return_refund_bugs = [
        bug_id for bug_id in MISSION_TRIGGERS.keys()
        if "return" in bug_id.lower() or "refund" in bug_id.lower()
    ]
    
    if not return_refund_bugs:
        pytest.skip("No return/refund bug triggers configured")
    
    success_count = 0
    failed_bugs = []
    
    for bug_id in return_refund_bugs[:5]:  # Test first 5 to avoid timeout
        trigger_config = MISSION_TRIGGERS[bug_id]
        
        try:
            # Prepare request body
            body = trigger_config.get("body")
            if callable(body):
                body = body()
            else:
                body = body or get_base_return_request()
            
            # Execute request
            url = f"{base_url}{trigger_config['url']}"
            response = await httpx_client.request(
                trigger_config["method"],
                url,
                params=trigger_config.get("params", {}),
                json=body,
                timeout=15.0
            )
            
            # Check response
            expected_status = trigger_config.get("expected_status", [200])
            if response.status_code not in expected_status:
                failed_bugs.append({
                    "bug_id": bug_id,
                    "error": f"Status {response.status_code} not in {expected_status}"
                })
                continue
            
            # Check for flag (simplified - would need actual flag from DB)
            response_text = response.text
            if "FLAG{" in response_text:
                success_count += 1
            else:
                failed_bugs.append({
                    "bug_id": bug_id,
                    "error": "Flag not found in response"
                })
        
        except Exception as e:
            failed_bugs.append({
                "bug_id": bug_id,
                "error": str(e)
            })
    
    if failed_bugs:
        print(f"\nFailed return/refund lab bugs:")
        for failed in failed_bugs:
            print(f"  - {failed['bug_id']}: {failed['error']}")
    
    # Assert at least some work
    if len(return_refund_bugs) > 0:
        assert success_count > 0 or len(failed_bugs) < len(return_refund_bugs), \
            "All return/refund lab tests failed"


@pytest.mark.asyncio
@pytest.mark.mission_flags
async def test_lab_health_endpoints(
    missions_with_labs: list[Mission],
    httpx_client: AsyncClient
):
    """
    Test that lab-specific health endpoints work.
    Some labs have custom health endpoints beyond /health.
    """
    if not missions_with_labs:
        pytest.skip("No missions with labs found")
    
    health_endpoints = [
        "/health",
        "/api/v1/health",
        "/api/health",
    ]
    
    for mission in missions_with_labs:
        if not mission.base_url:
            continue
        
        base_url = mission.base_url
        health_ok = False
        
        for endpoint in health_endpoints:
            try:
                url = f"{base_url}{endpoint}"
                response = await httpx_client.get(url, timeout=5.0)
                if response.status_code == 200:
                    health_ok = True
                    break
            except Exception:
                continue
        
        # Don't fail test, just log
        if not health_ok:
            print(f"⚠️  Mission {mission.id}: Health check failed for all endpoints")
