"""
Agents Package

This package contains all agent implementations for the Discord channel selector.

Package Structure:
- base_agent.py: Abstract base class that all agents inherit from
- user_preference_agent.py: Collects user preferences through conversation
- channel_analyzer_agent.py: Analyzes Discord channels and makes recommendations
"""

from .base_agent import BaseAgent, AgentFactory

__all__ = ['BaseAgent', 'AgentFactory']
