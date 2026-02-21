"""
Tests for Flask API.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from api.app import app


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"


class TestAgentsEndpoint:
    """Tests for agents endpoints."""
    
    @patch('api.app.factory')
    def test_list_agents(self, mock_factory, client):
        """Test listing agents."""
        mock_factory.config_manager.list_agents.return_value = ["agent1", "agent2"]
        
        response = client.get('/agents')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "agent1" in data["agents"]
        assert data["count"] == 2
    
    @patch('api.app.factory')
    def test_get_agent_info(self, mock_factory, client):
        """Test getting agent info."""
        mock_factory.config_manager.load_agent.return_value = {
            "name": "test_agent",
            "description": "Test agent",
            "tools": [{"name": "tool1"}]
        }
        
        response = client.get('/agents/test_agent')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "test_agent"
    
    @patch('api.app.factory')
    def test_get_agent_info_not_found(self, mock_factory, client):
        """Test getting non-existent agent info."""
        from utils.exceptions import ConfigurationError
        mock_factory.config_manager.load_agent.side_effect = ConfigurationError("Not found", "path")
        
        response = client.get('/agents/nonexistent')
        assert response.status_code == 404
    
    @patch('api.app.orchestrator')
    @patch('api.app.factory')
    def test_query_agent(self, mock_factory, mock_orchestrator, client):
        """Test querying an agent."""
        mock_agent = Mock()
        mock_agent.get_name.return_value = "test_agent"
        mock_agent.get_description.return_value = "Test agent"
        
        mock_orchestrator.get_agent.return_value = None
        mock_factory.create_agent.return_value = mock_agent
        mock_orchestrator.execute.return_value = "Test response"
        
        response = client.post(
            '/agents/test_agent/query',
            json={"query": "test question"}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["response"] == "Test response"
    
    def test_query_agent_missing_query(self, client):
        """Test querying agent without query parameter."""
        response = client.post(
            '/agents/test_agent/query',
            json={}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestDatabasesEndpoint:
    """Tests for databases endpoint."""
    
    @patch('databases.factory.DatabaseFactory.list_supported_types')
    def test_list_databases(self, mock_list_types, client):
        """Test listing databases."""
        mock_list_types.return_value = ["clickhouse", "mitre"]
        
        response = client.get('/databases')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "clickhouse" in data["databases"]


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data

