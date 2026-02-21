"""
Async job processing routes for the API.
"""
import os
from flask import Blueprint, request, jsonify
from typing import Dict, Any, Optional
from utils.logger import get_logger
from jobs.queue import JobQueue
from jobs.manager import JobManager
from jobs.models import JobRequest, JobStatus
from jobs.callback import CallbackNotifier
from core.orchestrator import AgentOrchestrator
from agent_factory import AgentFactory
from utils.exceptions import ConfigurationError

logger = get_logger(__name__)

# Create blueprint
job_bp = Blueprint('jobs', __name__, url_prefix='/jobs')

# Initialize job queue and manager
_job_queue: Optional[JobQueue] = None
_job_manager: Optional[JobManager] = None


def init_job_system(orchestrator: AgentOrchestrator, factory: AgentFactory):
    """
    Initialize job system with orchestrator and factory.
    
    Args:
        orchestrator: Agent orchestrator instance
        factory: Agent factory instance
    """
    global _job_queue, _job_manager
    
    # Initialize Redis connection
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_db = int(os.getenv("REDIS_DB", 0))
    redis_password = os.getenv("REDIS_PASSWORD")
    
    try:
        _job_queue = JobQueue(
            redis_host=redis_host,
            redis_port=redis_port,
            redis_db=redis_db,
            redis_password=redis_password
        )
        
        # Create agent executor function
        def agent_executor(agent_name: str, query: str, context: Optional[dict]) -> str:
            """Execute agent query."""
            agent = orchestrator.get_agent(agent_name)
            if not agent:
                agent = factory.create_agent(agent_name)
                orchestrator.register_agent(agent)
            return orchestrator.execute(agent_name, query, context)
        
        # Initialize job manager
        num_workers = int(os.getenv("JOB_WORKERS", "2"))
        _job_manager = JobManager(
            job_queue=_job_queue,
            agent_executor=agent_executor,
            callback_notifier=CallbackNotifier(),
            num_workers=num_workers
        )
        
        # Start workers
        _job_manager.start_workers()
        
        logger.info("job_system_initialized", 
                   redis_host=redis_host,
                   redis_port=redis_port,
                   num_workers=num_workers)
    except Exception as e:
        logger.error("job_system_init_failed", error=str(e), exc_info=True)
        raise


@job_bp.route('/submit', methods=['POST'])
def submit_job():
    """
    Submit a job for async processing.
    
    Request body:
    {
        "agent_name": "clickhouse_analyst",
        "query": "How many users are in the database?",
        "context": {},  // optional
        "callback_url": "https://example.com/callback"  // optional
    }
    
    Returns:
        202 Accepted with job_id
    """
    try:
        data = request.get_json() or {}
        
        agent_name = data.get("agent_name")
        query = data.get("query")
        context = data.get("context")
        callback_url = data.get("callback_url")
        
        if not agent_name:
            return jsonify({"error": "Missing 'agent_name' parameter"}), 400
        
        if not query:
            return jsonify({"error": "Missing 'query' parameter"}), 400
        
        if not _job_queue:
            return jsonify({"error": "Job system not initialized"}), 503
        
        # Create job request
        job_request = JobRequest(
            agent_name=agent_name,
            query=query,
            context=context,
            callback_url=callback_url
        )
        
        # Submit job
        job_id = _job_manager.submit_job(job_request)
        
        logger.info("job_submitted", job_id=job_id, agent_name=agent_name)
        
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "message": "Job submitted successfully"
        }), 202
        
    except Exception as e:
        logger.error("job_submit_error", error=str(e), exc_info=True)
        return jsonify({"error": str(e)}), 500


@job_bp.route('/<job_id>/status', methods=['GET'])
def get_job_status(job_id: str):
    """
    Get job status.
    
    Returns:
        200 OK with status
    """
    try:
        if not _job_queue:
            return jsonify({"error": "Job system not initialized"}), 503
        
        status = _job_queue.get_status(job_id)
        
        if status is None:
            return jsonify({"error": "Job not found"}), 404
        
        return jsonify({
            "job_id": job_id,
            "status": status.value
        }), 200
        
    except Exception as e:
        logger.error("job_status_error", job_id=job_id, error=str(e), exc_info=True)
        return jsonify({"error": str(e)}), 500


@job_bp.route('/<job_id>/result', methods=['GET'])
def get_job_result(job_id: str):
    """
    Get job result.
    
    Returns:
        200 OK with result if completed
        202 Accepted if still processing
        404 Not Found if job doesn't exist
    """
    try:
        if not _job_queue:
            return jsonify({"error": "Job system not initialized"}), 503
        
        result = _job_queue.get_result(job_id)
        
        if result is None:
            # Check if job exists
            status = _job_queue.get_status(job_id)
            if status is None:
                return jsonify({"error": "Job not found"}), 404
            
            # Job exists but result not ready
            return jsonify({
                "job_id": job_id,
                "status": status.value,
                "message": "Job still processing"
            }), 202
        
        # Return result
        return jsonify(result.to_dict()), 200
        
    except Exception as e:
        logger.error("job_result_error", job_id=job_id, error=str(e), exc_info=True)
        return jsonify({"error": str(e)}), 500


@job_bp.route('/health', methods=['GET'])
def job_health_check():
    """Check job system health."""
    try:
        if not _job_queue:
            return jsonify({
                "status": "unhealthy",
                "error": "Job system not initialized"
            }), 503
        
        is_healthy = _job_queue.health_check()
        
        return jsonify({
            "status": "healthy" if is_healthy else "unhealthy",
            "redis_connected": is_healthy
        }), 200 if is_healthy else 503
        
    except Exception as e:
        logger.error("job_health_check_error", error=str(e), exc_info=True)
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503

