"""
Retry and timeout configuration.
"""
from dataclasses import dataclass
from typing import Tuple, Type


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    exceptions: Tuple[Type[Exception], ...] = (Exception,)


@dataclass
class TimeoutConfig:
    """Configuration for timeouts."""
    llm_request_timeout: int = 120  # seconds
    database_query_timeout: int = 30  # seconds
    callback_timeout: int = 10  # seconds
    redis_timeout: int = 5  # seconds


@dataclass
class JobConfig:
    """Configuration for job processing."""
    num_workers: int = 2
    queue_timeout: int = 1  # seconds for blocking dequeue
    result_ttl: int = 86400  # 24 hours in seconds
    status_ttl: int = 86400  # 24 hours in seconds

