"""
Workflow Orchestrator Module

This module coordinates the multi-agent workflow:
1. UserPreferenceAgent collects user information
2. ChannelAnalyzerAgent analyzes and recommends channels
3. Results are presented to the user

Think of this as the "conductor" that coordinates the two agents.
"""

from typing import Dict, Any, Optional
from langsmith import traceable
import logging

from agents.user_preference_agent import UserPreferenceAgent
from agents.channel_analyzer_agent import ChannelAnalyzerAgent


class AgentOrchestrator:
    """
    Orchestrates the workflow between multiple agents.
    
    This class manages the overall process:
    1. Initialize agents
    2. Run UserPreferenceAgent to collect preferences
    3. Pass preferences to ChannelAnalyzerAgent
    4. Return final recommendations
    
    The orchestrator handles:
    - Agent lifecycle (creation, execution, cleanup)
    - Data flow between agents
    - Error handling
    - LangSmith tracing for the entire workflow
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the orchestrator with configuration.
        
        Args:
            config: Configuration dictionary with agent settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize agents
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Create and configure all agents."""
        # Get agent configurations
        preference_config = self.config.get('agents', {}).get('user_preference_agent', {})
        analyzer_config = self.config.get('agents', {}).get('channel_analyzer_agent', {})
        
        # Add additional config from other sections
        preference_config['preference_questions'] = self.config.get('preference_questions', [])
        
        # Extract channel analysis settings
        analysis_settings = self.config.get('channel_analysis', {})
        analyzer_config.update(analysis_settings)
        
        # Create agents
        self.preference_agent = UserPreferenceAgent(
            name=preference_config.get('name', 'Preference Collector'),
            model_name=preference_config.get('model', 'gpt-4'),
            temperature=preference_config.get('temperature', 0.7),
            config=preference_config
        )
        
        self.channel_analyzer = ChannelAnalyzerAgent(
            name=analyzer_config.get('name', 'Channel Analyzer'),
            model_name=analyzer_config.get('model', 'gpt-4'),
            temperature=analyzer_config.get('temperature', 0.3),
            config=analyzer_config
        )
        
        self.logger.info("Agents initialized successfully")
    
    @traceable(name="orchestrator_run_workflow")
    async def run_workflow(self, channels_data: list) -> Dict[str, Any]:
        """
        Run the complete workflow.
        
        This is a simplified version that runs the complete process
        in one go. For interactive applications, use run_interactive().
        
        Args:
            channels_data: List of Discord channels to analyze
            
        Returns:
            Dictionary with complete workflow results
        """
        self.logger.info("Starting complete workflow")
        
        # This method would be used in a non-interactive context
        # For now, we'll focus on the interactive version
        raise NotImplementedError(
            "Use run_interactive() for step-by-step interaction"
        )
    
    async def start_conversation(self) -> Dict[str, Any]:
        """
        Start the conversation by greeting the user.
        
        Returns:
            Dictionary with greeting message
        """
        self.logger.info("Starting user conversation")
        result = await self.preference_agent.execute({'mode': 'start'})
        return result
    
    async def process_user_response(self, user_response: str) -> Dict[str, Any]:
        """
        Process a user's response during preference collection.
        
        Args:
            user_response: The user's message
            
        Returns:
            Dictionary with agent response and status
        """
        self.logger.info(f"Processing user response: {user_response[:50]}...")
        
        result = await self.preference_agent.execute({
            'mode': 'collect',
            'user_response': user_response
        })
        
        return result
    
    async def analyze_channels(self, channels_data: list) -> Dict[str, Any]:
        """
        Analyze channels and generate recommendations.
        
        This should be called after preference collection is complete.
        
        Args:
            channels_data: List of Discord channels to analyze
            
        Returns:
            Dictionary with recommendations and message
        """
        # Get collected preferences
        preferences = self.preference_agent.collected_preferences
        
        if not preferences:
            raise ValueError("No preferences collected. Run conversation first.")
        
        self.logger.info("Analyzing channels with collected preferences")
        
        # Set channel data
        self.channel_analyzer.set_channels_data(channels_data)
        
        # Run analysis
        result = await self.channel_analyzer.execute({
            'preferences': preferences
        })
        
        return result
    
    def reset(self):
        """Reset all agents for a new conversation."""
        self.preference_agent.reset()
        self.logger.info("Orchestrator reset")
    
    def get_collected_preferences(self) -> Dict[str, Any]:
        """Get the preferences collected so far."""
        return self.preference_agent.collected_preferences.copy()
