"""
Configuration Module

This module handles loading and validating configuration from:
- config.yaml (main configuration)
- .env (environment variables like API keys)
"""

import yaml
import os
from typing import Dict, Any
from dotenv import load_dotenv
import logging


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file and environment variables.
    
    This function:
    1. Loads environment variables from .env file (API keys, etc.)
    2. Loads configuration from config.yaml
    3. Validates required settings
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Dictionary with complete configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If required configuration is missing
    """
    # Get the directory containing the config file
    config_dir = os.path.dirname(os.path.abspath(config_path))
    
    # Load environment variables from .env file in the same directory
    env_path = os.path.join(config_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        # Try loading from current directory as fallback
        load_dotenv()
    
    # Load YAML configuration
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required environment variables
    required_env_vars = ['OPENAI_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            "Please copy .env.example to .env and fill in your API keys."
        )
    
    # Add environment variables to config
    config['env'] = {
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'langchain_api_key': os.getenv('LANGCHAIN_API_KEY'),
        'langchain_tracing': os.getenv('LANGCHAIN_TRACING_V2', 'false').lower() == 'true',
        'langchain_project': os.getenv('LANGCHAIN_PROJECT', 'discord-channel-selector')
    }
    
    return config


def setup_logging(config: Dict[str, Any]):
    """
    Set up logging based on configuration.
    
    Args:
        config: Configuration dictionary
    """
    log_config = config.get('logging', {})
    level = getattr(logging, log_config.get('level', 'INFO'))
    format_str = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(
        level=level,
        format=format_str
    )
