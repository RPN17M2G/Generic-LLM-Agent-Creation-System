"""
Dynamic prompt construction from templates.
"""
from typing import Dict, Any, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
from utils.logger import get_logger

logger = get_logger(__name__)


class PromptBuilder:
    """
    Builds prompts from templates with variable substitution.
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize prompt builder.
        
        Args:
            template_dir: Directory containing prompt templates (default: ./templates)
        """
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            self.template_dir = Path("templates")
        
        self.template_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False
        )
    
    def build_from_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Build a prompt from a template file.
        
        Args:
            template_name: Name of the template file
            context: Variables to substitute in template
            
        Returns:
            Rendered prompt string
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error("prompt_template_error", template=template_name, error=str(e))
            raise RuntimeError(f"Failed to render template {template_name}: {e}") from e
    
    def build_from_string(
        self,
        template_string: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Build a prompt from a template string.
        
        Args:
            template_string: Template as string
            context: Variables to substitute in template
            
        Returns:
            Rendered prompt string
        """
        try:
            template = Template(template_string)
            return template.render(**context)
        except Exception as e:
            logger.error("prompt_string_template_error", error=str(e))
            raise RuntimeError(f"Failed to render template string: {e}") from e

