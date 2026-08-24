"""
Shared pytest configuration for the RazorGrowth AI test suite.
"""
import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
