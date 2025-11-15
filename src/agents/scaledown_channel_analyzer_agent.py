"""
ScaleDown Channel Analyzer Agent Module

This is a ScaleDown-enabled version of the ChannelAnalyzerAgent that uses
prompt compression to reduce token usage when analyzing Discord channels.

Key Benefit: Channel analysis requires sending large amounts of channel data
to the LLM. ScaleDown compression can significantly reduce these tokens while
maintaining recommendation accuracy.
"""

from typing import Dict, Any, List
from langsmith import traceable
import json
import logging

from agents.scaledown_base_agent import ScaleDownBaseAgent, ScaleDownAgentFactory


class ScaleDownChannelAnalyzerAgent(ScaleDownBaseAgent):
    """
    ScaleDown-enabled agent that analyzes channels and provides recommendations.
    
    This agent:
    1. Takes user preferences
    2. Analyzes available Discord channels (with compression)
    3. Scores each channel based on match
    4. Returns ranked recommendations
    
    Uses ScaleDown to compress the large channel dataset before analysis,
    reducing token usage by 40-60% typically.
    """
    
    # Context template for analyzing a single channel
    CHANNEL_ANALYSIS_CONTEXT = """You are analyzing whether a Discord channel matches a user's preferences.

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
- Target Audience: {target_audience}"""
    
    CHANNEL_ANALYSIS_PROMPT = """Analyze how well this channel matches the user's preferences. Return ONLY a JSON object:
{
    "match_score": 0.0-1.0,
    "reasoning": "brief explanation of the score",
    "key_matches": ["list", "of", "matching", "aspects"],
    "potential_concerns": ["list", "of", "potential", "issues"]
}

Be objective and consider all factors."""
    
    # Context for generating final recommendations
    RECOMMENDATION_CONTEXT_TEMPLATE = """You are presenting Discord channel recommendations to a user.

User Preferences:
- Interests: {interests}
- Role: {role}
- Experience Level: {experience_level}
- Goals: {goals}

Top Recommended Channels (sorted by match score):
{channel_summaries}"""
    
    RECOMMENDATION_PROMPT = """Generate a friendly, personalized message presenting these channel recommendations. 

Include:
1. A brief introduction (1-2 sentences)
2. Top 3-5 channels with why each is recommended
3. Encouragement to explore

Be conversational and supportive."""
    
    def __init__(self, name: str = "ScaleDown Channel Analyzer",
                 model_name: str = "gpt-4o",
                 temperature: float = 0.3,
                 config: Dict[str, Any] = None):
        """
        Initialize the ScaleDown Channel Analyzer Agent.
        
        Args:
            name: Agent name
            model_name: LLM model to use
            temperature: Lower temp for more consistent analysis
            config: Configuration for analysis parameters
        """
        super().__init__(name, model_name, temperature, config)
        
        # Analysis parameters
        self.max_recommendations = config.get('max_recommendations', 5)
        self.minimum_match_score = config.get('minimum_match_score', 0.6)
        
        self.logger.info(
            f"Initialized {self.name} "
            f"(max_recs: {self.max_recommendations}, "
            f"min_score: {self.minimum_match_score})"
        )
    
    @traceable(name="scaledown_analyze_channels")
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution: analyze channels and provide recommendations.
        
        Args:
            input_data: Must contain:
                - preferences: User preferences dict
                - channels: List of channel dictionaries
                
        Returns:
            Dictionary with:
                - recommendations: List of recommended channels
                - analysis_details: Scoring details for each channel
                - compression_metrics: Token usage statistics
        """
        preferences = input_data.get('preferences', {})
        channels = input_data.get('channels', [])
        
        if not preferences:
            raise ValueError("User preferences are required")
        if not channels:
            raise ValueError("Channel list is required")
        
        self.logger.info(
            f"Analyzing {len(channels)} channels for user with preferences: "
            f"{list(preferences.keys())}"
        )
        
        # Analyze each channel
        analysis_results = []
        all_metrics = []
        
        for channel in channels:
            result = await self._analyze_channel(preferences, channel)
            analysis_results.append(result)
            all_metrics.append(result['compression_metrics'])
        
        # Sort by match score
        analysis_results.sort(
            key=lambda x: x['match_score'], 
            reverse=True
        )
        
        # Filter by minimum score and limit
        top_channels = [
            r for r in analysis_results 
            if r['match_score'] >= self.minimum_match_score
        ][:self.max_recommendations]
        
        # Generate recommendation message
        recommendation_result = await self._generate_recommendation_message(
            preferences, 
            top_channels
        )
        all_metrics.append(recommendation_result['compression_metrics'])
        
        # Aggregate metrics
        aggregate_metrics = self._aggregate_metrics(all_metrics)
        
        return {
            'recommendations': top_channels,
            'recommendation_message': recommendation_result['message'],
            'total_channels_analyzed': len(channels),
            'channels_recommended': len(top_channels),
            'compression_metrics': aggregate_metrics
        }
    
    @traceable(name="scaledown_analyze_single_channel")
    async def _analyze_channel(
        self, 
        preferences: Dict[str, Any],
        channel: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a single channel with ScaleDown compression.
        
        Args:
            preferences: User preferences
            channel: Channel data
            
        Returns:
            Dictionary with match score, reasoning, and metrics
        """
        # Build context with all channel information
        context = self.CHANNEL_ANALYSIS_CONTEXT.format(
            interests=preferences.get('interests', 'Not specified'),
            role=preferences.get('role', 'Not specified'),
            experience_level=preferences.get('experience_level', 'Not specified'),
            goals=preferences.get('goals', 'Not specified'),
            channel_name=channel.get('name', 'Unknown'),
            channel_description=channel.get('description', 'No description'),
            channel_topics=', '.join(channel.get('topics', [])),
            activity_level=channel.get('activity_level', 'unknown'),
            target_audience=channel.get('target_audience', 'all')
        )
        
        # Compress and analyze
        result = await self._invoke_model_with_compression(
            context=context,
            prompt=self.CHANNEL_ANALYSIS_PROMPT
        )
        
        response_text = result['response'].strip()
        
        # Parse JSON response
        try:
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            analysis_data = json.loads(response_text)
            
            return {
                'channel_name': channel.get('name'),
                'channel': channel,
                'match_score': analysis_data.get('match_score', 0.0),
                'reasoning': analysis_data.get('reasoning', ''),
                'key_matches': analysis_data.get('key_matches', []),
                'potential_concerns': analysis_data.get('potential_concerns', []),
                'compression_metrics': result['compression_metrics']
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse channel analysis: {e}")
            self.logger.error(f"Response text was: {response_text[:200]}")
            return {
                'channel_name': channel.get('name'),
                'channel': channel,
                'match_score': 0.0,
                'reasoning': 'Analysis failed',
                'key_matches': [],
                'potential_concerns': ['Failed to analyze'],
                'compression_metrics': result['compression_metrics']
            }
    
    async def _generate_recommendation_message(
        self,
        preferences: Dict[str, Any],
        top_channels: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a friendly recommendation message with ScaleDown compression.
        
        Args:
            preferences: User preferences
            top_channels: List of top-ranked channels
            
        Returns:
            Dictionary with recommendation message and metrics
        """
        # Build channel summaries
        summaries = []
        for idx, channel_data in enumerate(top_channels, 1):
            summary = (
                f"{idx}. #{channel_data['channel_name']} "
                f"(Match: {channel_data['match_score']:.0%})\n"
                f"   Why: {channel_data['reasoning']}\n"
                f"   Matches: {', '.join(channel_data['key_matches'][:3])}"
            )
            summaries.append(summary)
        
        summaries_text = "\n\n".join(summaries)
        
        context = self.RECOMMENDATION_CONTEXT_TEMPLATE.format(
            interests=preferences.get('interests', 'Not specified'),
            role=preferences.get('role', 'Not specified'),
            experience_level=preferences.get('experience_level', 'Not specified'),
            goals=preferences.get('goals', 'Not specified'),
            channel_summaries=summaries_text
        )
        
        result = await self._invoke_model_with_compression(
            context=context,
            prompt=self.RECOMMENDATION_PROMPT
        )
        
        return {
            'message': result['response'],
            'compression_metrics': result['compression_metrics']
        }
    
    def _aggregate_metrics(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate compression metrics from multiple calls.
        
        Args:
            metrics_list: List of compression_metrics dictionaries
            
        Returns:
            Aggregated metrics
        """
        total_original = sum(m.get('original_tokens', 0) for m in metrics_list)
        total_compressed = sum(m.get('compressed_tokens', 0) for m in metrics_list)
        total_compression_time = sum(m.get('compression_time', 0) for m in metrics_list)
        total_llm_time = sum(m.get('llm_time', 0) for m in metrics_list)
        total_time = sum(m.get('total_time', 0) for m in metrics_list)
        
        compression_ratio = 0
        if total_original > 0:
            compression_ratio = (
                (total_original - total_compressed) / total_original * 100
            )
        
        return {
            'total_calls': len(metrics_list),
            'total_original_tokens': total_original,
            'total_compressed_tokens': total_compressed,
            'tokens_saved': total_original - total_compressed,
            'compression_ratio': compression_ratio,
            'total_compression_time': total_compression_time,
            'total_llm_time': total_llm_time,
            'total_time': total_time
        }


# Register this agent with the ScaleDown factory
ScaleDownAgentFactory.register_agent('scaledown_channel_analyzer', ScaleDownChannelAnalyzerAgent)
