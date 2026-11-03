"""
Pytest Global Configuration and Fixtures.
"""
import os
import sys
import pytest

# Add workspace root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.lake_storage import LakeStorage
from warehouse.warehouse_manager import WarehouseManager


@pytest.fixture(scope="session")
def lake_storage():
    return LakeStorage()


@pytest.fixture(scope="session")
def warehouse():
    return WarehouseManager()
