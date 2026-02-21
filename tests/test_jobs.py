"""
Tests for job processing system.
"""
import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from jobs.models import JobRequest, JobResult, JobStatus
from jobs.queue import JobQueue
from jobs.manager import JobManager
from jobs.callback import CallbackNotifier
from utils.exceptions import ConfigurationError


class TestJobModels:
    """Tests for job models."""
    
    def test_job_request_init(self):
        """Test JobRequest initialization."""
        request = JobRequest(
            agent_name="test_agent",
            query="test query",
            context={"key": "value"},
            callback_url="http://example.com/callback"
        )
        
        assert request.agent_name == "test_agent"
        assert request.query == "test query"
        assert request.context == {"key": "value"}
        assert request.callback_url == "http://example.com/callback"
        assert request.job_id is not None
    
    def test_job_request_auto_id(self):
        """Test JobRequest auto-generates ID."""
        request1 = JobRequest(agent_name="test", query="query")
        request2 = JobRequest(agent_name="test", query="query")
        
        assert request1.job_id != request2.job_id
    
    def test_job_result_to_dict(self):
        """Test JobResult serialization."""
        result = JobResult(
            job_id="test-id",
            status=JobStatus.COMPLETED,
            result="test result",
            execution_time=1.5
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["job_id"] == "test-id"
        assert result_dict["status"] == "completed"
        assert result_dict["result"] == "test result"
        assert result_dict["execution_time"] == 1.5
        assert "created_at" in result_dict


class TestJobQueue:
    """Tests for JobQueue."""
    
    @patch('jobs.queue.redis.Redis')
    def test_job_queue_init(self, mock_redis_class):
        """Test JobQueue initialization."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis
        
        queue = JobQueue(redis_host="localhost", redis_port=6379)
        
        assert queue.redis_client == mock_redis
        mock_redis.ping.assert_called_once()
    
    @patch('jobs.queue.redis.Redis')
    def test_job_queue_init_failure(self, mock_redis_class):
        """Test JobQueue initialization failure."""
        import redis
        mock_redis_class.side_effect = redis.ConnectionError("Connection failed")
        
        with pytest.raises(ConfigurationError):
            JobQueue(redis_host="localhost", redis_port=6379)
    
    @patch('jobs.queue.redis.Redis')
    def test_enqueue(self, mock_redis_class):
        """Test job enqueue."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.hset.return_value = True
        mock_redis_class.return_value = mock_redis
        
        queue = JobQueue(redis_host="localhost", redis_port=6379)
        job_request = JobRequest(agent_name="test", query="query")
        
        job_id = queue.enqueue(job_request)
        
        assert job_id == job_request.job_id
        mock_redis.lpush.assert_called_once()
        mock_redis.hset.assert_called()
    
    @patch('jobs.queue.redis.Redis')
    def test_dequeue(self, mock_redis_class):
        """Test job dequeue."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        job_data = {"job_id": "test-id", "agent_name": "test", "query": "query"}
        mock_redis.brpop.return_value = (None, json.dumps(job_data))
        mock_redis_class.return_value = mock_redis
        
        queue = JobQueue(redis_host="localhost", redis_port=6379)
        result = queue.dequeue(timeout=1)
        
        assert result == job_data
    
    @patch('jobs.queue.redis.Redis')
    def test_set_status(self, mock_redis_class):
        """Test status update."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.hset.return_value = True
        mock_redis_class.return_value = mock_redis
        
        queue = JobQueue(redis_host="localhost", redis_port=6379)
        queue.set_status("test-id", JobStatus.PROCESSING)
        
        mock_redis.hset.assert_called()
        mock_redis.expire.assert_called()
    
    @patch('jobs.queue.redis.Redis')
    def test_get_status(self, mock_redis_class):
        """Test status retrieval."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.hgetall.return_value = {"status": "processing"}
        mock_redis_class.return_value = mock_redis
        
        queue = JobQueue(redis_host="localhost", redis_port=6379)
        status = queue.get_status("test-id")
        
        assert status == JobStatus.PROCESSING
    
    @patch('jobs.queue.redis.Redis')
    def test_save_result(self, mock_redis_class):
        """Test result saving."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.setex.return_value = True
        mock_redis.hset.return_value = True
        mock_redis_class.return_value = mock_redis
        
        queue = JobQueue(redis_host="localhost", redis_port=6379)
        result = JobResult(job_id="test-id", status=JobStatus.COMPLETED, result="result")
        
        queue.save_result(result)
        
        mock_redis.setex.assert_called_once()
        mock_redis.hset.assert_called()
    
    @patch('jobs.queue.redis.Redis')
    def test_get_result(self, mock_redis_class):
        """Test result retrieval."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        result_dict = {
            "job_id": "test-id",
            "status": "completed",
            "result": "test result",
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "execution_time": None,
            "error": None,
            "metadata": {}
        }
        mock_redis.get.return_value = json.dumps(result_dict)
        mock_redis_class.return_value = mock_redis
        
        queue = JobQueue(redis_host="localhost", redis_port=6379)
        result = queue.get_result("test-id")
        
        assert result is not None
        assert result.job_id == "test-id"
        assert result.status == JobStatus.COMPLETED
    
    @patch('jobs.queue.redis.Redis')
    def test_health_check(self, mock_redis_class):
        """Test health check."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis
        
        queue = JobQueue(redis_host="localhost", redis_port=6379)
        assert queue.health_check() is True
        
        mock_redis.ping.side_effect = Exception("Connection failed")
        assert queue.health_check() is False


class TestJobManager:
    """Tests for JobManager."""
    
    @patch('jobs.manager.JobQueue')
    def test_job_manager_init(self, mock_queue_class):
        """Test JobManager initialization."""
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        def executor(agent, query, context):
            return "result"
        
        manager = JobManager(
            job_queue=mock_queue,
            agent_executor=executor,
            num_workers=2
        )
        
        assert manager.job_queue == mock_queue
        assert manager.num_workers == 2
    
    @patch('jobs.manager.JobQueue')
    @patch('jobs.manager.threading.Thread')
    def test_start_workers(self, mock_thread, mock_queue_class):
        """Test worker thread startup."""
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        def executor(agent, query, context):
            return "result"
        
        manager = JobManager(
            job_queue=mock_queue,
            agent_executor=executor,
            num_workers=2
        )
        
        manager.start_workers()
        
        assert manager.running is True
        assert mock_thread.call_count == 2
    
    @patch('jobs.manager.JobQueue')
    def test_submit_job(self, mock_queue_class):
        """Test job submission."""
        mock_queue = Mock()
        mock_queue.enqueue.return_value = "test-job-id"
        mock_queue_class.return_value = mock_queue
        
        def executor(agent, query, context):
            return "result"
        
        manager = JobManager(
            job_queue=mock_queue,
            agent_executor=executor
        )
        
        job_request = JobRequest(agent_name="test", query="query")
        job_id = manager.submit_job(job_request)
        
        assert job_id == "test-job-id"
        mock_queue.enqueue.assert_called_once()


class TestCallbackNotifier:
    """Tests for CallbackNotifier."""
    
    @patch('jobs.callback.requests.post')
    def test_notify_success(self, mock_post):
        """Test successful callback notification."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        notifier = CallbackNotifier()
        result = JobResult(job_id="test-id", status=JobStatus.COMPLETED, result="result")
        
        notifier.notify("http://example.com/callback", result)
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://example.com/callback"
        assert "json" in call_args[1]
    
    @patch('jobs.callback.requests.post')
    def test_notify_failure(self, mock_post):
        """Test callback notification failure."""
        import requests
        mock_post.side_effect = requests.RequestException("Connection failed")
        
        notifier = CallbackNotifier()
        result = JobResult(job_id="test-id", status=JobStatus.COMPLETED, result="result")
        
        with pytest.raises(requests.RequestException):
            notifier.notify("http://example.com/callback", result)

