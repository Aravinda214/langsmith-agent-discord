"""
Main Application Module

This is the main entry point for the Discord Channel Selector application.
It provides both interactive (CLI) and programmatic interfaces.
"""

import asyncio
import sys
from typing import Optional
import os

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_loader import load_config, setup_logging
from orchestrator import AgentOrchestrator


class DiscordChannelSelector:
    """
    Main application class for Discord channel selection.
    
    This class provides a high-level interface for the entire system.
    It handles:
    - Configuration loading
    - Agent orchestration
    - User interaction (CLI or programmatic)
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the application.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        # Default to config.yaml in the parent directory
        if config_path is None:
            # Get the project root directory (parent of src/)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(project_root, "config.yaml")
        
        self.config = load_config(config_path)
        setup_logging(self.config)
        
        # Initialize orchestrator
        self.orchestrator = AgentOrchestrator(self.config)
        
        print("Discord Channel Selector initialized successfully!")
        print("=" * 60)
    
    async def run_interactive(self, channels_data: list):
        """
        Run the application in interactive CLI mode.
        
        This guides the user through:
        1. Greeting and preference collection
        2. Channel analysis
        3. Recommendation presentation
        
        Args:
            channels_data: List of Discord channels to analyze
        """
        print("\n🤖 Discord Channel Selector - Interactive Mode")
        print("=" * 60)
        
        # Start conversation
        greeting_result = await self.orchestrator.start_conversation()
        print(f"\n🤖 Bot: {greeting_result['message']}\n")
        
        # Collect preferences through conversation
        while True:
            # Get user input
            user_input = input("👤 You: ").strip()
            
            if not user_input:
                print("Please provide a response.\n")
                continue
            
            # Process response
            result = await self.orchestrator.process_user_response(user_input)
            
            print(f"\n🤖 Bot: {result['message']}\n")
            
            # Check if collection is complete
            if result['status'] == 'complete':
                break
        
        # Analyze channels
        print("\n🔍 Analyzing Discord channels...")
        print("=" * 60)
        
        analysis_result = await self.orchestrator.analyze_channels(channels_data)
        
        print(f"\n📊 Analysis Complete!")
        print(f"   - Total channels analyzed: {analysis_result['total_analyzed']}")
        print(f"   - Channels matching criteria: {analysis_result['total_matching']}")
        print(f"   - Top recommendations: {len(analysis_result['recommendations'])}")
        
        print(f"\n🤖 Bot: {analysis_result['message']}\n")
        
        # Display detailed recommendations
        print("\n📋 Detailed Recommendations:")
        print("=" * 60)
        for i, rec in enumerate(analysis_result['recommendations'], 1):
            analysis = rec['analysis']
            print(f"\n{i}. #{rec['name']}")
            print(f"   Match Score: {analysis['match_score']:.1%}")
            print(f"   Description: {rec.get('description', 'No description')}")
            print(f"   Topics: {', '.join(rec.get('topics', []))}")
            print(f"   Reasoning: {analysis['reasoning']}")
            if analysis['key_matches']:
                print(f"   ✓ Key Matches: {', '.join(analysis['key_matches'])}")
            if analysis['potential_concerns']:
                print(f"   ⚠ Considerations: {', '.join(analysis['potential_concerns'])}")
        
        print("\n" + "=" * 60)
        print("✅ Recommendation complete! Happy chatting on Discord!")
        
        return analysis_result
    
    async def run_programmatic(self, user_preferences: dict, channels_data: list):
        """
        Run the application programmatically (without interactive CLI).
        
        Useful for:
        - Integration with other systems
        - Batch processing
        - Testing
        
        Args:
            user_preferences: Dictionary with user preferences
            channels_data: List of Discord channels
            
        Returns:
            Dictionary with recommendations
        """
        # Directly analyze channels with provided preferences
        self.orchestrator.channel_analyzer.set_channels_data(channels_data)
        
        result = await self.orchestrator.channel_analyzer.execute({
            'preferences': user_preferences
        })
        
        return result


async def main():
    """Main entry point for the application."""
    # This is a simple example of how to use the application
    print("Starting Discord Channel Selector...")
    
    # Initialize app
    app = DiscordChannelSelector()
    
    # For demonstration, we'll use mock data
    # In a real scenario, this would come from Discord MCP or API
    from test_data import get_mock_channels
    
    channels = get_mock_channels()
    
    # Run interactive mode
    await app.run_interactive(channels)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
