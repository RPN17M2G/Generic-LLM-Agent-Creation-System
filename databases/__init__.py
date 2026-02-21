"""
Database adapters for multi-database support.
"""

from .base import IDatabaseAdapter
from .factory import DatabaseFactory
from .clickhouse_adapter import ClickHouseAdapter
from .mitre_adapter import MITREAdapter

__all__ = [
    'IDatabaseAdapter',
    'DatabaseFactory',
    'ClickHouseAdapter',
    'MITREAdapter',
]

