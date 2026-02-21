"""
Callback notification system for job completion.
"""
import requests
from typing import Optional
from utils.logger import get_logger
from jobs.models import JobResult
from utils.retry import retry_with_backoff

logger = get_logger(__name__)


class CallbackNotifier:
    """
    Handles callback notifications when jobs complete.
    """
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """
        Initialize callback notifier.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0, exceptions=(requests.RequestException,))
    def notify(self, callback_url: str, job_result: JobResult):
        """
        Send callback notification.
        
        Args:
            callback_url: URL to send callback to
            job_result: Job result to send
        """
        try:
            payload = job_result.to_dict()
            
            response = requests.post(
                callback_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            logger.info("callback_success", 
                      job_id=job_result.job_id,
                      callback_url=callback_url,
                      status_code=response.status_code)
        except requests.RequestException as e:
            logger.error("callback_failed",
                        job_id=job_result.job_id,
                        callback_url=callback_url,
                        error=str(e))
            raise

