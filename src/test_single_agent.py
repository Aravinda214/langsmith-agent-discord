"""
Test a single agent (Standard or ScaleDown) manually.

This lets you test ONE agent at a time without running the full comparison,
saving API credits and allowing you to debug issues.

Usage:
    python test_single_agent.py --agent standard
    python test_single_agent.py --agent scaledown
"""

import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.user_preference_agent import UserPreferenceAgent
from agents.channel_analyzer_agent import ChannelAnalyzerAgent
from agents.scaledown_user_preference_agent import ScaleDownUserPreferenceAgent
from agents.scaledown_channel_analyzer_agent import ScaleDownChannelAnalyzerAgent
from config_loader import load_config
from data_loader import load_channels_from_json

# Load environment
load_dotenv()


async def test_standard_agents(test_persona, config):
    """Test the standard (non-compressed) agents."""
    
    print("\n" + "="*80)
    print("TESTING STANDARD AGENTS (No Compression)")
    print("="*80)
    
    # Load config and data
    pref_config = config['agents']['user_preference_agent'].copy()
    pref_config['preference_questions'] = config['preference_questions']
    
    analyzer_config = config['agents']['channel_analyzer_agent'].copy()
    analyzer_config.update(config['channel_analysis'])
    
    channels = load_channels_from_json()
    
    # Initialize agents
    print("\n📋 Initializing agents...")
    pref_agent = UserPreferenceAgent(
        name=pref_config['name'],
        model_name=pref_config['model'],
        temperature=pref_config['temperature'],
        config=pref_config
    )
    
    analyzer_agent = ChannelAnalyzerAgent(
        name=analyzer_config['name'],
        model_name=analyzer_config['model'],
        temperature=analyzer_config['temperature'],
        config=analyzer_config
    )
    
    # Step 1: Greeting
    print("\n📤 Step 1: Getting greeting...")
    greeting_result = await pref_agent.execute({'mode': 'start'})
    print(f"\n💬 Greeting: {greeting_result.get('message', '')[:200]}...")
    
    # Step 2: Analyze channels
    print("\n🔍 Step 2: Analyzing channels...")
    print(f"   User preferences: {test_persona['name']}")
    print(f"   Interests: {test_persona['preferences']['interests'][:100]}...")
    
    analysis_result = await analyzer_agent.execute({
        'preferences': test_persona['preferences'],
        'channels': channels
    })
    
    # Show results
    print("\n✅ ANALYSIS COMPLETE")
    print(f"\n📊 Results:")
    print(f"   Total channels analyzed: {analysis_result.get('total_analyzed', 0)}")
    print(f"   Channels recommended: {len(analysis_result.get('recommendations', []))}")
    
    print(f"\n🎯 Top 3 Recommendations:")
    for i, rec in enumerate(analysis_result.get('recommendations', [])[:3], 1):
        score = rec.get('analysis', {}).get('match_score', 0)
        reasoning = rec.get('analysis', {}).get('reasoning', '')[:100]
        print(f"   {i}. #{rec.get('name')} (score: {score:.2f})")
        print(f"      {reasoning}...")
    
    print(f"\n💬 Message to user:")
    print(f"   {analysis_result.get('message', '')[:300]}...")
    
    # Estimate tokens (rough approximation since standard agents don't track tokens)
    print(f"\n📊 Estimated Token Usage (Standard):")
    # Rough estimate: ~1 token per 4 characters
    greeting_chars = len(str(greeting_result.get('message', '')))
    message_chars = len(str(analysis_result.get('message', '')))
    preferences_chars = len(str(test_persona['preferences']))
    
    # Estimate input tokens (preferences + channels data)
    channels_chars = sum(len(str(c)) for c in channels)
    estimated_input = (preferences_chars + channels_chars) // 4
    
    # Estimate output tokens (greeting + analysis message)
    estimated_output = (greeting_chars + message_chars) // 4
    
    estimated_total = estimated_input + estimated_output
    
    print(f"   Estimated input tokens: ~{estimated_input:,}")
    print(f"   Estimated output tokens: ~{estimated_output:,}")
    print(f"   Estimated total: ~{estimated_total:,}")
    print(f"   ⚠️  Note: These are rough estimates. Actual tokens may vary.")
    
    return analysis_result


async def test_scaledown_agents(test_persona, config):
    """Test the ScaleDown (compressed) agents."""
    
    print("\n" + "="*80)
    print("TESTING SCALEDOWN AGENTS (With Compression)")
    print("="*80)
    
    # Load config and data
    pref_config = config['agents']['scaledown_user_preference_agent'].copy()
    pref_config['preference_questions'] = config['preference_questions']
    
    analyzer_config = config['agents']['scaledown_channel_analyzer_agent'].copy()
    analyzer_config.update(config['channel_analysis'])
    
    channels = load_channels_from_json()
    
    # Initialize agents
    print("\n📋 Initializing ScaleDown agents...")
    pref_agent = ScaleDownUserPreferenceAgent(
        name=pref_config['name'],
        model_name=pref_config['model'],
        temperature=pref_config['temperature'],
        config=pref_config
    )
    
    analyzer_agent = ScaleDownChannelAnalyzerAgent(
        name=analyzer_config['name'],
        model_name=analyzer_config['model'],
        temperature=analyzer_config['temperature'],
        config=analyzer_config
    )
    
    # Step 1: Greeting (with compression)
    print("\n📤 Step 1: Getting greeting (with compression)...")
    greeting_result = await pref_agent.execute({'mode': 'start'})
    print(f"\n💬 Greeting: {greeting_result.get('message', '')[:200]}...")
    
    if 'compression_metrics' in greeting_result:
        metrics = greeting_result['compression_metrics']
        print(f"\n📊 Compression Stats (Greeting):")
        print(f"   Original tokens: {metrics.get('original_tokens', 0)}")
        print(f"   Compressed tokens: {metrics.get('compressed_tokens', 0)}")
        if metrics.get('original_tokens', 0) > 0:
            ratio = (1 - metrics.get('compressed_tokens', 0) / metrics.get('original_tokens', 1)) * 100
            print(f"   Compression: {ratio:.1f}%")
    
    # Step 2: Analyze channels (with compression)
    print("\n🔍 Step 2: Analyzing channels (with compression)...")
    print(f"   User preferences: {test_persona['name']}")
    print(f"   Interests: {test_persona['preferences']['interests'][:100]}...")
    
    analysis_result = await analyzer_agent.execute({
        'preferences': test_persona['preferences'],
        'channels': channels
    })
    
    # Show results
    print("\n✅ ANALYSIS COMPLETE")
    print(f"\n📊 Results:")
    print(f"   Total channels analyzed: {analysis_result.get('total_channels_analyzed', 0)}")
    print(f"   Channels recommended: {len(analysis_result.get('recommendations', []))}")
    
    print(f"\n🎯 Top 3 Recommendations:")
    for i, rec in enumerate(analysis_result.get('recommendations', [])[:3], 1):
        score = rec.get('match_score', 0)
        reasoning = rec.get('reasoning', '')[:100]
        print(f"   {i}. #{rec.get('channel', {}).get('name', 'Unknown')} (score: {score:.2f})")
        print(f"      {reasoning}...")
    
    print(f"\n💬 Message to user:")
    print(f"   {analysis_result.get('recommendation_message', '')[:300]}...")
    
    # Show compression stats
    if 'compression_metrics' in analysis_result:
        metrics = analysis_result['compression_metrics']
        print(f"\n📊 Compression Stats (Total):")
        print(f"   Original tokens: {metrics.get('total_original_tokens', 0)}")
        print(f"   Compressed tokens: {metrics.get('total_compressed_tokens', 0)}")
        if metrics.get('total_original_tokens', 0) > 0:
            ratio = (1 - metrics.get('total_compressed_tokens', 0) / metrics.get('total_original_tokens', 1)) * 100
            print(f"   Overall compression: {ratio:.1f}%")
        print(f"   Compression time: {metrics.get('total_compression_time', 0):.2f}s")
        print(f"   LLM time: {metrics.get('total_llm_time', 0):.2f}s")
    
    return analysis_result


def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(description='Test a single agent (standard or scaledown)')
    parser.add_argument(
        '--agent',
        choices=['standard', 'scaledown'],
        required=True,
        help='Which agent to test: "standard" (no compression) or "scaledown" (with compression)'
    )
    parser.add_argument(
        '--persona',
        choices=['beginner', 'senior', 'career-switcher', 'ml', 'student'],
        default='beginner',
        help='Which test persona to use (default: beginner)'
    )
    
    args = parser.parse_args()
    
    # Define test personas
    personas = {
        'beginner': {
            'name': 'Python Beginner',
            'preferences': {
                'interests': 'python, data science, machine learning, data analysis, pandas, numpy',
                'role': 'student',
                'experience_level': 'beginner',
                'goals': 'learning fundamentals, building projects, getting job-ready'
            }
        },
        'senior': {
            'name': 'Senior Developer',
            'preferences': {
                'interests': 'software architecture, design patterns, cloud infrastructure, microservices, system design',
                'role': 'senior developer',
                'experience_level': 'advanced',
                'goals': 'mastering architecture, leading teams, scaling systems'
            }
        },
        'career-switcher': {
            'name': 'Career Switcher',
            'preferences': {
                'interests': 'web development, react, javascript, frontend, user experience',
                'role': 'career switcher',
                'experience_level': 'beginner',
                'goals': 'career transition, building portfolio, job hunting'
            }
        },
        'ml': {
            'name': 'ML Enthusiast',
            'preferences': {
                'interests': 'machine learning, artificial intelligence, deep learning, neural networks, tensorflow',
                'role': 'data scientist',
                'experience_level': 'intermediate',
                'goals': 'mastering ML, building AI projects, research'
            }
        },
        'student': {
            'name': 'Student Developer',
            'preferences': {
                'interests': 'programming, algorithms, data structures, interview prep, competitive coding',
                'role': 'student',
                'experience_level': 'intermediate',
                'goals': 'passing interviews, landing internship, improving skills'
            }
        }
    }
    
    test_persona = personas[args.persona]
    
    print("\n" + "="*80)
    print("SINGLE AGENT TESTER")
    print("="*80)
    print(f"\nAgent Type: {args.agent.upper()}")
    print(f"Test Persona: {test_persona['name']}")
    print(f"\nThis will test ONLY the {args.agent} agent to help you debug and understand behavior.")
    print("It will NOT run comparisons or use excessive API credits.")
    
    # Load configuration
    config = load_config('../config.yaml')
    
    # Run the test
    if args.agent == 'standard':
        asyncio.run(test_standard_agents(test_persona, config))
    else:
        asyncio.run(test_scaledown_agents(test_persona, config))
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print(f"\n💡 To test the other agent, run:")
    print(f"   python test_single_agent.py --agent {'scaledown' if args.agent == 'standard' else 'standard'}")
    print(f"\n💡 To run the full comparison (both agents), run:")
    print(f"   python compare_agents.py")


if __name__ == "__main__":
    main()
