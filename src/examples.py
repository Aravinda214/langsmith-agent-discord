"""
Example Usage Module

This demonstrates different ways to use the Discord Channel Selector system.
"""

import asyncio
from main import DiscordChannelSelector
from test_data import get_mock_channels


async def example_interactive():
    """
    Example 1: Interactive mode
    
    This is the recommended way for end users.
    The system will guide you through a conversation.
    """
    print("=" * 60)
    print("EXAMPLE 1: Interactive Mode")
    print("=" * 60)
    
    # Initialize the application
    app = DiscordChannelSelector()
    
    # Get channel data (in production, this would come from Discord API/MCP)
    channels = get_mock_channels()
    
    # Run interactive session
    await app.run_interactive(channels)


async def example_programmatic():
    """
    Example 2: Programmatic mode
    
    Use this when you want to integrate the system into another application
    or when you already have user preferences.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Programmatic Mode")
    print("=" * 60)
    
    # Initialize the application
    app = DiscordChannelSelector()
    
    # User preferences (could come from a form, database, etc.)
    preferences = {
        "interests": "Web development, React, and JavaScript",
        "role": "Frontend Developer",
        "experience_level": "intermediate",
        "goals": "Learn modern frontend frameworks and best practices"
    }
    
    # Get channel data
    channels = get_mock_channels()
    
    # Get recommendations
    result = await app.run_programmatic(preferences, channels)
    
    # Display results
    print(f"\n📊 Analysis Results:")
    print(f"   Analyzed: {result['total_analyzed']} channels")
    print(f"   Matched: {result['total_matching']} channels")
    print(f"\n{result['message']}")


async def example_custom_channels():
    """
    Example 3: Using custom channel data
    
    This shows how to provide your own channel data instead of using mock data.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Custom Channel Data")
    print("=" * 60)
    
    # Initialize the application
    app = DiscordChannelSelector()
    
    # Define custom channels
    # In a real application, you might fetch this from:
    # - Discord API
    # - Discord MCP server
    # - Your own database
    # - A configuration file
    custom_channels = [
        {
            "name": "python-help",
            "description": "Get help with Python programming",
            "topics": ["python", "programming", "help"],
            "activity_level": "high",
            "target_audience": "all levels"
        },
        {
            "name": "javascript-advanced",
            "description": "Advanced JavaScript techniques and patterns",
            "topics": ["javascript", "advanced", "es6", "patterns"],
            "activity_level": "medium",
            "target_audience": "advanced"
        },
        {
            "name": "career-tech",
            "description": "Tech career advice and job hunting",
            "topics": ["career", "jobs", "tech", "advice"],
            "activity_level": "medium",
            "target_audience": "all levels"
        }
    ]
    
    # User preferences
    preferences = {
        "interests": "Python programming",
        "role": "Software Developer",
        "experience_level": "beginner",
        "goals": "Get better at Python and find a job"
    }
    
    # Get recommendations
    result = await app.run_programmatic(preferences, custom_channels)
    
    print(f"\n📊 Found {len(result['recommendations'])} matching channels")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"\n{i}. #{rec['name']}")
        print(f"   Match: {rec['analysis']['match_score']:.1%}")
        print(f"   {rec['description']}")


async def example_agent_access():
    """
    Example 4: Direct agent access
    
    This shows how to work with individual agents directly,
    useful for more complex integrations.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Direct Agent Access")
    print("=" * 60)
    
    from config_loader import load_config
    from agents.channel_analyzer_agent import ChannelAnalyzerAgent
    import os
    
    # Load configuration from parent directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config.yaml")
    config = load_config(config_path)
    
    # Create analyzer agent directly
    analyzer = ChannelAnalyzerAgent(
        name="Custom Analyzer",
        model_name="gpt-4",
        temperature=0.3,
        config=config.get('channel_analysis', {})
    )
    
    # Set channel data
    channels = get_mock_channels()
    analyzer.set_channels_data(channels)
    
    # Run analysis with custom preferences
    result = await analyzer.execute({
        'preferences': {
            'interests': 'Game development and graphics programming',
            'role': 'Game Developer',
            'experience_level': 'intermediate',
            'goals': 'Build indie games'
        }
    })
    
    print(f"\n📊 Found {len(result['recommendations'])} recommendations")
    for rec in result['recommendations']:
        print(f"   - #{rec['name']}: {rec['analysis']['match_score']:.1%} match")


async def main():
    """
    Main function to run all examples.
    
    Comment out examples you don't want to run.
    """
    # Example 1: Interactive (full conversation)
    # await example_interactive()
    
    # Example 2: Programmatic (skip conversation)
    await example_programmatic()
    
    # Example 3: Custom channel data
    await example_custom_channels()
    
    # Example 4: Direct agent access
    await example_agent_access()


if __name__ == "__main__":
    asyncio.run(main())
