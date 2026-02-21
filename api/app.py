"""
Flask API application for the multi-agent LLM framework.

This module provides REST API endpoints for:
- Agent management and querying
- Async job processing
- Health checks and system information
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.logger import get_logger
from utils.exceptions import AgentFrameworkError, ConfigurationError
from agent_factory import AgentFactory
from core.orchestrator import AgentOrchestrator
from api.request_parser import parse_request
from api.job_routes import job_bp, init_job_system

logger = get_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize core components
factory = AgentFactory()
orchestrator = AgentOrchestrator()

# Initialize job system (async processing)
try:
    init_job_system(orchestrator, factory)
    logger.info("job_system_initialized_successfully")
except Exception as e:
    logger.warning("job_system_init_failed_continuing_without_async", error=str(e))


# ============================================================================
# Health & System Endpoints
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        200 OK with service status
    """
    return jsonify({
        "status": "healthy",
        "service": "multi-agent-llm-framework",
        "version": "1.0.0"
    }), 200


@app.route('/agents', methods=['GET'])
def list_agents():
    """
    List all available agents.
    
    Returns:
        200 OK with list of agent names
    """
    try:
        agents = factory.config_manager.list_agents()
        return jsonify({
            "agents": agents,
            "count": len(agents)
        }), 200
    except Exception as e:
        logger.error("list_agents_error", error=str(e), exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/agents/<agent_name>', methods=['GET'])
def get_agent_info(agent_name: str):
    """
    Get information about a specific agent.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        200 OK with agent information
        404 Not Found if agent doesn't exist
    """
    try:
        agent_config = factory.config_manager.load_agent(agent_name, validate=False)
        return jsonify({
            "name": agent_config.get("name"),
            "description": agent_config.get("description", ""),
            "tools": [t.get("name") for t in agent_config.get("tools", [])]
        }), 200
    except ConfigurationError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error("get_agent_info_error", agent_name=agent_name, error=str(e), exc_info=True)
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Agent Query Endpoints
# ============================================================================

@app.route('/agents/<agent_name>/query', methods=['POST', 'GET'])
def query_agent(agent_name: str):
    """
    Execute a query on an agent (synchronous).
    
    For async processing, use POST /jobs/submit instead.
    
    Supports multiple request formats:
    - POST JSON: {"query": "question", "context": {}}
    - POST form: query=question
    - GET query params: ?query=question
    - POST plain text: "question"
    - POST with any JSON structure containing query-like fields
    
    Args:
        agent_name: Name of the agent to query
        
    Request body (optional for GET):
    {
        "query": "user question",
        "context": {}  // optional context
    }
    
    Returns:
        200 OK with agent response
        400 Bad Request if query is missing
        404 Not Found if agent doesn't exist
        500 Internal Server Error on processing failure
    """
    try:
        # Parse request data (handles multiple formats)
        data = parse_request(request)
        query = data.get("query")
        context = data.get("context", {})
        
        if not query:
            return jsonify({
                "error": "Missing 'query' parameter",
                "hint": "Provide query via JSON body, form data, query params, or plain text"
            }), 400
        
        # Get or create agent
        agent = orchestrator.get_agent(agent_name)
        if not agent:
            try:
                agent = factory.create_agent(agent_name)
                orchestrator.register_agent(agent)
            except ConfigurationError as e:
                return jsonify({"error": f"Agent '{agent_name}' not found: {str(e)}"}), 404
        
        # Execute query
        logger.info("orchestrator_execute", agent_name=agent_name, query=query)
        response = orchestrator.execute(agent_name, query, context)
        
        return jsonify({
            "agent": agent_name,
            "query": query,
            "response": response,
            "context_used": context
        }), 200
        
    except ConfigurationError as e:
        logger.error("query_agent_config_error", agent_name=agent_name, error=str(e))
        return jsonify({"error": str(e)}), 404
    except AgentFrameworkError as e:
        logger.error("query_agent_framework_error", agent_name=agent_name, error=str(e))
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error("query_agent_error", agent_name=agent_name, error=str(e), exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# ============================================================================
# Database Information Endpoints
# ============================================================================

@app.route('/databases', methods=['GET'])
def list_databases():
    """
    List all supported database types.
    
    Returns:
        200 OK with list of database types
    """
    try:
        from databases.factory import DatabaseFactory
        db_types = DatabaseFactory.list_supported_types()
        return jsonify({
            "databases": db_types,
            "count": len(db_types)
        }), 200
    except Exception as e:
        logger.error("list_databases_error", error=str(e), exc_info=True)
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        "error": "Method not allowed",
        "message": "The HTTP method is not allowed for this endpoint"
    }), 405


@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 errors."""
    logger.error("internal_server_error", error=str(error))
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500


# ============================================================================
# Register Blueprints
# ============================================================================

# Register job routes (async processing)
app.register_blueprint(job_bp)


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    """
    Run the Flask development server.
    
    For production, use a WSGI server like gunicorn:
    gunicorn -w 4 -b 0.0.0.0:5000 api.app:app
    """
    app.run(debug=True, host='0.0.0.0', port=5000)

