"""
Tests for async job API endpoints.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from api.job_routes import job_bp, init_job_system
from jobs.models import JobRequest, JobResult, JobStatus
from core.orchestrator import AgentOrchestrator
from agent_factory import AgentFactory


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(job_bp)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def mock_job_system():
    """Mock job system."""
    with patch('api.job_routes.JobQueue') as mock_queue_class, \
         patch('api.job_routes.JobManager') as mock_manager_class:
        
        mock_queue = Mock()
        mock_queue.health_check.return_value = True
        mock_queue.get_status.return_value = JobStatus.QUEUED
        mock_queue.get_result.return_value = None
        mock_queue_class.return_value = mock_queue
        
        mock_manager = Mock()
        mock_manager.submit_job.return_value = "test-job-id"
        mock_manager_class.return_value = mock_manager
        
        yield mock_queue, mock_manager


class TestJobSubmit:
    """Tests for job submission endpoint."""
    
    def test_submit_job_success(self, client, mock_job_system):
        """Test successful job submission."""
        mock_queue, mock_manager = mock_job_system
        
        # Initialize job system
        orchestrator = Mock(spec=AgentOrchestrator)
        factory = Mock(spec=AgentFactory)
        init_job_system(orchestrator, factory)
        
        response = client.post('/jobs/submit', json={
            "agent_name": "test_agent",
            "query": "test query",
            "callback_url": "http://example.com/callback"
        })
        
        assert response.status_code == 202
        data = json.loads(response.data)
        assert "job_id" in data
        assert data["status"] == "queued"
    
    def test_submit_job_missing_agent(self, client, mock_job_system):
        """Test job submission with missing agent_name."""
        orchestrator = Mock()
        factory = Mock()
        init_job_system(orchestrator, factory)
        
        response = client.post('/jobs/submit', json={
            "query": "test query"
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
    
    def test_submit_job_missing_query(self, client, mock_job_system):
        """Test job submission with missing query."""
        orchestrator = Mock()
        factory = Mock()
        init_job_system(orchestrator, factory)
        
        response = client.post('/jobs/submit', json={
            "agent_name": "test_agent"
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestJobStatus:
    """Tests for job status endpoint."""
    
    def test_get_status_success(self, client, mock_job_system):
        """Test getting job status."""
        mock_queue, mock_manager = mock_job_system
        mock_queue.get_status.return_value = JobStatus.PROCESSING
        
        orchestrator = Mock()
        factory = Mock()
        init_job_system(orchestrator, factory)
        
        response = client.get('/jobs/test-job-id/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "processing"
    
    def test_get_status_not_found(self, client, mock_job_system):
        """Test getting status for non-existent job."""
        mock_queue, mock_manager = mock_job_system
        mock_queue.get_status.return_value = None
        
        orchestrator = Mock()
        factory = Mock()
        init_job_system(orchestrator, factory)
        
        response = client.get('/jobs/non-existent/status')
        
        assert response.status_code == 404


class TestJobResult:
    """Tests for job result endpoint."""
    
    def test_get_result_completed(self, client, mock_job_system):
        """Test getting completed job result."""
        mock_queue, mock_manager = mock_job_system
        result = JobResult(
            job_id="test-job-id",
            status=JobStatus.COMPLETED,
            result="Test result"
        )
        mock_queue.get_result.return_value = result
        
        orchestrator = Mock()
        factory = Mock()
        init_job_system(orchestrator, factory)
        
        response = client.get('/jobs/test-job-id/result')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "completed"
        assert data["result"] == "Test result"
    
    def test_get_result_processing(self, client, mock_job_system):
        """Test getting result for processing job."""
        mock_queue, mock_manager = mock_job_system
        mock_queue.get_result.return_value = None
        mock_queue.get_status.return_value = JobStatus.PROCESSING
        
        orchestrator = Mock()
        factory = Mock()
        init_job_system(orchestrator, factory)
        
        response = client.get('/jobs/test-job-id/result')
        
        assert response.status_code == 202
        data = json.loads(response.data)
        assert data["status"] == "processing"


class TestJobHealth:
    """Tests for job health endpoint."""
    
    def test_health_check_healthy(self, client, mock_job_system):
        """Test health check when healthy."""
        mock_queue, mock_manager = mock_job_system
        mock_queue.health_check.return_value = True
        
        orchestrator = Mock()
        factory = Mock()
        init_job_system(orchestrator, factory)
        
        response = client.get('/jobs/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"
    
    def test_health_check_unhealthy(self, client, mock_job_system):
        """Test health check when unhealthy."""
        mock_queue, mock_manager = mock_job_system
        mock_queue.health_check.return_value = False
        
        orchestrator = Mock()
        factory = Mock()
        init_job_system(orchestrator, factory)
        
        response = client.get('/jobs/health')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data["status"] == "unhealthy"

