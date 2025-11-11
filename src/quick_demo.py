"""
Quick Demo Script - Test Agents with Sample Inputs

This script demonstrates the agents with predefined user responses,
so you can see how they work without manual typing.
"""

import asyncio
import os
from config_loader import load_config, setup_logging
from orchestrator import AgentOrchestrator
from test_data import get_mock_channels


async def demo_conversation():
    """
    Demonstrate the full conversation flow with sample responses.
    """
    print("=" * 70)
    print("DISCORD CHANNEL SELECTOR - AUTOMATED DEMO")
    print("=" * 70)
    print("\nThis demo shows how the agents work with sample user responses.\n")
    
    # Load configuration from parent directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config.yaml")
    config = load_config(config_path)
    setup_logging(config)
    orchestrator = AgentOrchestrator(config)
    
    # Get mock channel data
    channels = get_mock_channels()
    
    # Sample user responses
    sample_responses = [
        "I'm interested in Python programming",
        "I'm a software developer",
        "intermediate",
        "I want to learn machine learning and build ML projects"
    ]
    
    print("🤖 Starting conversation...\n")
    
    # Start the conversation
    result = await orchestrator.start_conversation()
    print(f"🤖 Bot: {result['message']}\n")
    
    # Process each sample response
    for i, response in enumerate(sample_responses, 1):
        print(f"👤 You: {response}\n")
        
        result = await orchestrator.process_user_response(response)
        print(f"🤖 Bot: {result['message']}\n")
        
        if result['status'] == 'complete':
            break
    
    # Analyze channels
    print("=" * 70)
    print("🔍 Analyzing Discord channels...")
    print("=" * 70)
    
    analysis_result = await orchestrator.analyze_channels(channels)
    
    print(f"\n📊 Analysis Complete!")
    print(f"   - Total channels analyzed: {analysis_result['total_analyzed']}")
    print(f"   - Channels matching criteria: {analysis_result['total_matching']}")
    print(f"   - Top recommendations: {len(analysis_result['recommendations'])}\n")
    
    print(f"🤖 Bot: {analysis_result['message']}\n")
    
    # Display detailed recommendations
    print("=" * 70)
    print("📋 DETAILED RECOMMENDATIONS")
    print("=" * 70)
    
    for i, rec in enumerate(analysis_result['recommendations'], 1):
        analysis = rec['analysis']
        print(f"\n{i}. #{rec['name']}")
        print(f"   Match Score: {analysis['match_score']:.1%}")
        print(f"   Description: {rec.get('description', 'No description')}")
        print(f"   Topics: {', '.join(rec.get('topics', []))}")
        print(f"   Activity: {rec.get('activity_level', 'Unknown')}")
        print(f"   Target: {rec.get('target_audience', 'All')}")
        print(f"   ✓ Reasoning: {analysis['reasoning']}")
        if analysis['key_matches']:
            print(f"   ✓ Matches: {', '.join(analysis['key_matches'][:3])}")
    
    print("\n" + "=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70)
    
    return analysis_result


async def demo_different_persona():
    """
    Demonstrate with a different user persona.
    """
    print("\n\n" + "=" * 70)
    print("DEMO 2: CAREER SWITCHER PERSONA")
    print("=" * 70)
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config.yaml")
    config = load_config(config_path)
    orchestrator = AgentOrchestrator(config)
    channels = get_mock_channels()
    
    # Different persona
    sample_responses = [
        "I'm interested in web development, React, and JavaScript",
        "I'm a career switcher from marketing to tech",
        "beginner",
        "I want to get my first developer job"
    ]
    
    print("\n🤖 Starting conversation...\n")
    
    result = await orchestrator.start_conversation()
    print(f"🤖 Bot: {result['message']}\n")
    
    for response in sample_responses:
        print(f"👤 You: {response}\n")
        result = await orchestrator.process_user_response(response)
        print(f"🤖 Bot: {result['message']}\n")
        if result['status'] == 'complete':
            break
    
    print("🔍 Analyzing channels...\n")
    analysis_result = await orchestrator.analyze_channels(channels)
    
    print(f"📊 Top 3 Recommendations:")
    for i, rec in enumerate(analysis_result['recommendations'][:3], 1):
        print(f"   {i}. #{rec['name']} ({rec['analysis']['match_score']:.1%} match)")
    
    print("\n✅ Demo 2 Complete!")


async def demo_advanced_user():
    """
    Demonstrate with an advanced user persona.
    """
    print("\n\n" + "=" * 70)
    print("DEMO 3: SENIOR DEVELOPER PERSONA")
    print("=" * 70)
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config.yaml")
    config = load_config(config_path)
    orchestrator = AgentOrchestrator(config)
    channels = get_mock_channels()
    
    # Advanced persona
    sample_responses = [
        "Software architecture, design patterns, and cloud infrastructure",
        "Senior Software Engineer",
        "advanced",
        "Stay updated with best practices and mentor others"
    ]
    
    print("\n🤖 Starting conversation...\n")
    
    result = await orchestrator.start_conversation()
    print(f"🤖 Bot: {result['message']}\n")
    
    for response in sample_responses:
        print(f"👤 You: {response}\n")
        result = await orchestrator.process_user_response(response)
        print(f"🤖 Bot: {result['message']}\n")
        if result['status'] == 'complete':
            break
    
    print("🔍 Analyzing channels...\n")
    analysis_result = await orchestrator.analyze_channels(channels)
    
    print(f"📊 Top 3 Recommendations:")
    for i, rec in enumerate(analysis_result['recommendations'][:3], 1):
        print(f"   {i}. #{rec['name']} ({rec['analysis']['match_score']:.1%} match)")
    
    print("\n✅ Demo 3 Complete!")


async def main():
    """Run all demos."""
    print("\n🎬 Running Automated Agent Demos\n")
    
    # Demo 1: Python/ML enthusiast
    await demo_conversation()
    
    # Demo 2: Career switcher
    await demo_different_persona()
    
    # Demo 3: Senior developer
    await demo_advanced_user()
    
    print("\n\n" + "=" * 70)
    print("🎉 ALL DEMOS COMPLETE!")
    print("=" * 70)
    print("\nThe agents are working correctly!")
    print("\nTo run interactive mode: python main.py")
    print("To run automated tests: python run_tests.py")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
