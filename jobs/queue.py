"""
Redis-based job queue implementation.
"""
import json
import redis
from datetime import datetime
from typing import Optional, Dict, Any
from utils.logger import get_logger
from utils.exceptions import ConfigurationError
from jobs.models import JobRequest, JobResult, JobStatus

logger = get_logger(__name__)


class JobQueue:
    """
    Redis-based job queue for async processing.
    """
    
    QUEUE_KEY = "agent_jobs:queue"
    STATUS_PREFIX = "agent_jobs:status:"
    RESULT_PREFIX = "agent_jobs:result:"
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None
    ):
        """
        Initialize Redis connection.
        
        Args:
            redis_host: Redis host
            redis_port: Redis port
            redis_db: Redis database number
            redis_password: Redis password (optional)
        """
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("redis_connected", host=redis_host, port=redis_port)
        except redis.ConnectionError as e:
            logger.error("redis_connection_failed", error=str(e))
            raise ConfigurationError(f"Failed to connect to Redis: {e}") from e
        except Exception as e:
            logger.error("redis_init_error", error=str(e), exc_info=True)
            raise ConfigurationError(f"Redis initialization failed: {e}") from e
    
    def enqueue(self, job_request: JobRequest) -> str:
        """
        Add a job to the queue.
        
        Args:
            job_request: Job request to enqueue
            
        Returns:
            Job ID
        """
        try:
            job_data = {
                "job_id": job_request.job_id,
                "agent_name": job_request.agent_name,
                "query": job_request.query,
                "context": job_request.context or {},
                "callback_url": job_request.callback_url
            }
            
            # Add to queue
            self.redis_client.lpush(self.QUEUE_KEY, json.dumps(job_data))
            
            # Set initial status
            self.set_status(job_request.job_id, JobStatus.QUEUED)
            
            logger.info("job_enqueued", job_id=job_request.job_id, agent_name=job_request.agent_name)
            return job_request.job_id
        except Exception as e:
            logger.error("job_enqueue_failed", job_id=job_request.job_id, error=str(e), exc_info=True)
            raise
    
    def dequeue(self, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """
        Get next job from queue (blocking).
        
        Args:
            timeout: Timeout in seconds (0 = block indefinitely)
            
        Returns:
            Job data or None if timeout
        """
        try:
            result = self.redis_client.brpop(self.QUEUE_KEY, timeout=timeout)
            if result is None:
                return None
            
            _, job_data_str = result
            job_data = json.loads(job_data_str)
            logger.debug("job_dequeued", job_id=job_data.get("job_id"))
            return job_data
        except redis.TimeoutError:
            return None
        except Exception as e:
            logger.error("job_dequeue_failed", error=str(e), exc_info=True)
            raise
    
    def set_status(self, job_id: str, status: JobStatus, metadata: Optional[Dict[str, Any]] = None):
        """
        Update job status.
        
        Args:
            job_id: Job ID
            status: New status
            metadata: Optional metadata
        """
        try:
            status_data = {
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat()
            }
            if metadata:
                status_data["metadata"] = json.dumps(metadata)
            
            key = f"{self.STATUS_PREFIX}{job_id}"
            self.redis_client.hset(key, mapping=status_data)
            self.redis_client.expire(key, 86400)  # 24 hours TTL
            
            logger.debug("job_status_updated", job_id=job_id, status=status.value)
        except Exception as e:
            logger.error("job_status_update_failed", job_id=job_id, error=str(e), exc_info=True)
            raise
    
    def get_status(self, job_id: str) -> Optional[JobStatus]:
        """
        Get current job status.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status or None if not found
        """
        try:
            key = f"{self.STATUS_PREFIX}{job_id}"
            status_data = self.redis_client.hgetall(key)
            if not status_data:
                return None
            
            status_str = status_data.get("status")
            if status_str:
                return JobStatus(status_str)
            return None
        except Exception as e:
            logger.error("job_status_get_failed", job_id=job_id, error=str(e), exc_info=True)
            return None
    
    def save_result(self, job_result: JobResult):
        """
        Save job result.
        
        Args:
            job_result: Job result to save
        """
        try:
            key = f"{self.RESULT_PREFIX}{job_result.job_id}"
            result_data = json.dumps(job_result.to_dict())
            self.redis_client.setex(key, 86400, result_data)  # 24 hours TTL
            
            # Update status
            self.set_status(job_result.job_id, job_result.status)
            
            logger.info("job_result_saved", job_id=job_result.job_id, status=job_result.status.value)
        except Exception as e:
            logger.error("job_result_save_failed", job_id=job_result.job_id, error=str(e), exc_info=True)
            raise
    
    def get_result(self, job_id: str) -> Optional[JobResult]:
        """
        Get job result.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job result or None if not found
        """
        try:
            key = f"{self.RESULT_PREFIX}{job_id}"
            result_data_str = self.redis_client.get(key)
            if not result_data_str:
                return None
            
            result_dict = json.loads(result_data_str)
            return JobResult(
                job_id=result_dict["job_id"],
                status=JobStatus(result_dict["status"]),
                result=result_dict.get("result"),
                error=result_dict.get("error"),
                metadata=result_dict.get("metadata", {}),
                created_at=datetime.fromisoformat(result_dict["created_at"]) if result_dict.get("created_at") else None,
                started_at=datetime.fromisoformat(result_dict["started_at"]) if result_dict.get("started_at") else None,
                completed_at=datetime.fromisoformat(result_dict["completed_at"]) if result_dict.get("completed_at") else None,
                execution_time=result_dict.get("execution_time")
            )
        except Exception as e:
            logger.error("job_result_get_failed", job_id=job_id, error=str(e), exc_info=True)
            return None
    
    def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            return self.redis_client.ping()
        except Exception:
            return False

