"""
Pytest configuration for E-Commerce Return & Refund Lab tests
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
