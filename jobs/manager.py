"""
Job manager for processing async agent jobs.
"""
import time
import threading
from typing import Optional, Callable
from datetime import datetime
from utils.logger import get_logger
from jobs.queue import JobQueue
from jobs.models import JobRequest, JobResult, JobStatus
from jobs.callback import CallbackNotifier

logger = get_logger(__name__)


class JobManager:
    """
    Manages job processing and worker threads.
    """
    
    def __init__(
        self,
        job_queue: JobQueue,
        agent_executor: Callable[[str, str, Optional[dict]], str],
        callback_notifier: Optional[CallbackNotifier] = None,
        num_workers: int = 2
    ):
        """
        Initialize job manager.
        
        Args:
            job_queue: Job queue instance
            agent_executor: Function to execute agent (agent_name, query, context) -> result
            callback_notifier: Optional callback notifier
            num_workers: Number of worker threads
        """
        self.job_queue = job_queue
        self.agent_executor = agent_executor
        self.callback_notifier = callback_notifier or CallbackNotifier()
        self.num_workers = num_workers
        self.workers: list[threading.Thread] = []
        self.running = False
        logger.info("job_manager_initialized", num_workers=num_workers)
    
    def start_workers(self):
        """Start worker threads."""
        if self.running:
            logger.warning("workers_already_running")
            return
        
        self.running = True
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"JobWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
            logger.info("worker_started", worker_id=i)
    
    def stop_workers(self):
        """Stop worker threads."""
        self.running = False
        logger.info("stopping_workers", count=len(self.workers))
        for worker in self.workers:
            worker.join(timeout=5)
        self.workers.clear()
        logger.info("workers_stopped")
    
    def _worker_loop(self):
        """Main worker loop."""
        logger.info("worker_loop_started", thread_name=threading.current_thread().name)
        
        while self.running:
            try:
                # Get job from queue (blocking with timeout)
                job_data = self.job_queue.dequeue(timeout=1)
                if job_data is None:
                    continue
                
                job_id = job_data["job_id"]
                agent_name = job_data["agent_name"]
                query = job_data["query"]
                context = job_data.get("context", {})
                callback_url = job_data.get("callback_url")
                
                logger.info("job_processing_started", job_id=job_id, agent_name=agent_name)
                
                # Update status to processing
                self.job_queue.set_status(job_id, JobStatus.PROCESSING)
                
                # Execute job
                start_time = time.time()
                started_at = datetime.utcnow()
                
                try:
                    result = self.agent_executor(agent_name, query, context)
                    execution_time = time.time() - start_time
                    
                    # Create success result
                    job_result = JobResult(
                        job_id=job_id,
                        status=JobStatus.COMPLETED,
                        result=result,
                        started_at=started_at,
                        completed_at=datetime.utcnow(),
                        execution_time=execution_time,
                        metadata={"agent_name": agent_name}
                    )
                    
                    logger.info("job_completed", job_id=job_id, execution_time=execution_time)
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    error_msg = str(e)
                    
                    # Create failure result
                    job_result = JobResult(
                        job_id=job_id,
                        status=JobStatus.FAILED,
                        error=error_msg,
                        started_at=started_at,
                        completed_at=datetime.utcnow(),
                        execution_time=execution_time,
                        metadata={"agent_name": agent_name}
                    )
                    
                    logger.error("job_failed", job_id=job_id, error=error_msg, exc_info=True)
                
                # Save result
                self.job_queue.save_result(job_result)
                
                # Send callback if provided
                if callback_url:
                    try:
                        self.callback_notifier.notify(callback_url, job_result)
                        logger.info("callback_sent", job_id=job_id, callback_url=callback_url)
                    except Exception as e:
                        logger.error("callback_failed", job_id=job_id, error=str(e), exc_info=True)
                
            except Exception as e:
                logger.error("worker_error", error=str(e), exc_info=True)
                time.sleep(1)  # Prevent tight loop on errors
        
        logger.info("worker_loop_stopped", thread_name=threading.current_thread().name)
    
    def submit_job(self, job_request: JobRequest) -> str:
        """
        Submit a job for processing.
        
        Args:
            job_request: Job request
            
        Returns:
            Job ID
        """
        job_id = self.job_queue.enqueue(job_request)
        logger.info("job_submitted", job_id=job_id, agent_name=job_request.agent_name)
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status."""
        return self.job_queue.get_status(job_id)
    
    def get_job_result(self, job_id: str) -> Optional[JobResult]:
        """Get job result."""
        return self.job_queue.get_result(job_id)

