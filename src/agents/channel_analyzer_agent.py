"""
Channel Analyzer Agent Module

This agent is responsible for:
1. Analyzing available Discord channels
2. Matching channels to user preferences
3. Providing ranked recommendations

The agent can work with:
- Mock data (for testing)
- Discord MCP server (for real Discord data)
"""

from typing import Dict, Any, List, Optional
from langsmith import traceable
import json
import logging

from agents.base_agent import BaseAgent, AgentFactory


class ChannelAnalyzerAgent(BaseAgent):
    """
    Agent that analyzes Discord channels and recommends the best matches.
    
    This agent:
    1. Receives user preferences (from UserPreferenceAgent)
    2. Analyzes available Discord channels
    3. Scores each channel based on how well it matches preferences
    4. Returns a ranked list of recommendations
    
    The matching algorithm considers:
    - Topic/interest alignment
    - Experience level appropriateness
    - Activity level and engagement
    - Channel goals vs. user goals
    """
    
    # Template for analyzing a single channel
    CHANNEL_ANALYSIS_TEMPLATE = """You are analyzing whether a Discord channel matches a user's preferences.

User Preferences:
- Interests: {interests}
- Role: {role}
- Experience Level: {experience_level}
- Goals: {goals}

Channel Information:
- Name: {channel_name}
- Description: {channel_description}
- Topics: {channel_topics}
- Activity Level: {activity_level}
- Target Audience: {target_audience}

Analyze how well this channel matches the user's preferences. Return ONLY a JSON object:
{{
    "match_score": 0.0-1.0,
    "reasoning": "brief explanation of the score",
    "key_matches": ["list", "of", "matching", "aspects"],
    "potential_concerns": ["list", "of", "potential", "issues"]
}}

Be objective and consider all factors."""

    # Template for generating final recommendations
    RECOMMENDATION_TEMPLATE = """You are presenting Discord channel recommendations to a user.

User Preferences:
- Interests: {interests}
- Role: {role}
- Experience Level: {experience_level}
- Goals: {goals}

Top Recommended Channels:
{channel_summaries}

Generate a friendly, personalized message presenting these recommendations. Include:
1. A brief introduction
2. Top 3-5 channels with why each is recommended
3. Encouragement to explore

Keep it conversational and helpful."""

    def __init__(self, name: str = "Channel Analyzer", 
                 model_name: str = "gpt-4", 
                 temperature: float = 0.3,
                 config: Dict[str, Any] = None):
        """
        Initialize the Channel Analyzer Agent.
        
        Args:
            name: Agent name
            model_name: LLM model to use
            temperature: Lower temperature for more consistent analysis
            config: Configuration including analysis settings
        """
        super().__init__(name, model_name, temperature, config)
        
        # Analysis configuration
        self.max_recommendations = config.get('max_recommendations', 5)
        self.minimum_match_score = config.get('minimum_match_score', 0.6)
        self.consider_activity = config.get('consider_activity_level', True)
        
        # Channel data source
        self.channels_data: Optional[List[Dict[str, Any]]] = None
        self.mcp_enabled = config.get('mcp_enabled', False)
    
    def set_channels_data(self, channels: List[Dict[str, Any]]):
        """
        Set the Discord channels data to analyze.
        
        This can come from:
        - Mock data (for testing)
        - MCP server (for real Discord data)
        - External API
        
        Args:
            channels: List of channel dictionaries
        """
        self.channels_data = channels
        self.logger.info(f"Loaded {len(channels)} channels for analysis")
    
    @traceable(name="channel_analyzer_execute")
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute channel analysis and recommendation.
        
        Args:
            input_data: Dictionary with:
                - preferences: User preferences from UserPreferenceAgent
                - channels: (optional) Override channel data
                
        Returns:
            Dictionary with:
                - recommendations: List of recommended channels with scores
                - message: Friendly presentation of recommendations
        """
        preferences = input_data.get('preferences', {})
        
        # Use provided channels or fall back to set channels
        channels = input_data.get('channels', self.channels_data)
        
        if not channels:
            raise ValueError("No channel data available for analysis")
        
        if not preferences:
            raise ValueError("No user preferences provided")
        
        self.logger.info(f"Analyzing {len(channels)} channels for user preferences")
        
        # Analyze each channel
        analyzed_channels = []
        for channel in channels:
            analysis = await self._analyze_channel(channel, preferences)
            
            # Only include channels that meet minimum score
            if analysis['match_score'] >= self.minimum_match_score:
                analyzed_channels.append({
                    **channel,
                    'analysis': analysis
                })
        
        # Sort by match score
        analyzed_channels.sort(
            key=lambda x: x['analysis']['match_score'], 
            reverse=True
        )
        
        # Take top N recommendations
        top_recommendations = analyzed_channels[:self.max_recommendations]
        
        self.logger.info(f"Found {len(top_recommendations)} channels meeting minimum score")
        
        # Generate friendly recommendation message
        recommendation_message = await self._generate_recommendation_message(
            preferences,
            top_recommendations
        )
        
        return {
            "recommendations": top_recommendations,
            "message": recommendation_message,
            "total_analyzed": len(channels),
            "total_matching": len(analyzed_channels)
        }
    
    async def _analyze_channel(self, channel: Dict[str, Any], 
                               preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single channel against user preferences.
        
        Args:
            channel: Channel information
            preferences: User preferences
            
        Returns:
            Analysis results with match score and reasoning
        """
        # Create the analysis prompt
        analysis_prompt = self._create_prompt(
            self.CHANNEL_ANALYSIS_TEMPLATE,
            interests=preferences.get('interests', 'Not specified'),
            role=preferences.get('role', 'Not specified'),
            experience_level=preferences.get('experience_level', 'Not specified'),
            goals=preferences.get('goals', 'Not specified'),
            channel_name=channel.get('name', 'Unknown'),
            channel_description=channel.get('description', 'No description'),
            channel_topics=', '.join(channel.get('topics', [])),
            activity_level=channel.get('activity_level', 'Unknown'),
            target_audience=channel.get('target_audience', 'General')
        )
        
        # Get analysis from model
        analysis_response = await self._invoke_model(analysis_prompt)
        
        try:
            analysis = json.loads(analysis_response)
            return analysis
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse analysis for {channel.get('name')}")
            # Return a default low-confidence analysis
            return {
                "match_score": 0.5,
                "reasoning": "Unable to complete full analysis",
                "key_matches": [],
                "potential_concerns": ["Analysis incomplete"]
            }
    
    async def _generate_recommendation_message(self, 
                                               preferences: Dict[str, Any],
                                               recommendations: List[Dict[str, Any]]) -> str:
        """
        Generate a friendly message presenting the recommendations.
        
        Args:
            preferences: User preferences
            recommendations: Analyzed and scored channels
            
        Returns:
            Personalized recommendation message
        """
        # Format channel summaries
        channel_summaries = []
        for i, channel in enumerate(recommendations, 1):
            analysis = channel['analysis']
            summary = f"{i}. #{channel['name']} (Match: {analysis['match_score']:.0%})\n"
            summary += f"   {channel.get('description', 'No description')}\n"
            summary += f"   Why: {analysis['reasoning']}"
            channel_summaries.append(summary)
        
        summaries_text = "\n\n".join(channel_summaries)
        
        # Generate personalized message
        message_prompt = self._create_prompt(
            self.RECOMMENDATION_TEMPLATE,
            interests=preferences.get('interests', 'Not specified'),
            role=preferences.get('role', 'Not specified'),
            experience_level=preferences.get('experience_level', 'Not specified'),
            goals=preferences.get('goals', 'Not specified'),
            channel_summaries=summaries_text
        )
        
        message = await self._invoke_model(message_prompt)
        return message
    
    async def fetch_channels_from_mcp(self) -> List[Dict[str, Any]]:
        """
        Fetch Discord channels from MCP server.
        
        This method would integrate with the Discord MCP server
        to get real Discord channel data.
        
        Note: This is a placeholder for MCP integration.
        Actual implementation would use the MCP protocol.
        
        Returns:
            List of channel dictionaries
        """
        if not self.mcp_enabled:
            self.logger.warning("MCP is not enabled, using mock data")
            return []
        
        # TODO: Implement actual MCP server communication
        # This would involve:
        # 1. Connecting to the Discord MCP server
        # 2. Sending a request for available channels
        # 3. Parsing the response
        # 4. Structuring the data
        
        self.logger.info("MCP integration not yet implemented")
        return []


# Register this agent with the factory
AgentFactory.register_agent('channel_analyzer', ChannelAnalyzerAgent)
