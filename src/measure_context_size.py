"""
Context Size Measurement Tool

This script measures the actual context sizes being sent to OpenAI
for both standard and ScaleDown agents, helping identify why ScaleDown
has higher latency (typically happens with contexts <2000 tokens).

Usage:
    cd ..  # Go to project root
    python src/measure_context_size.py
    
    OR
    
    cd src
    python measure_context_size.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import tiktoken
from typing import Dict, Any, List

# Add parent directory to path if running from src
if os.path.basename(os.getcwd()) == 'src':
    sys.path.insert(0, os.path.dirname(os.getcwd()))
    # Change to parent directory for config loading
    os.chdir(os.path.dirname(os.getcwd()))

# Import agents and test data
from src.agents.user_preference_agent import UserPreferenceAgent
from src.agents.channel_analyzer_agent import ChannelAnalyzerAgent
from src.agents.scaledown_user_preference_agent import ScaleDownUserPreferenceAgent
from src.agents.scaledown_channel_analyzer_agent import ScaleDownChannelAnalyzerAgent
from src.config_loader import load_config
from src.data_loader import load_channels_from_json
from src.test_data import get_test_user_preferences

load_dotenv()


class ContextSizeMeasurer:
    """Measure context sizes for agents."""
    
    def __init__(self):
        """Initialize the measurer."""
        self.encoding = tiktoken.encoding_for_model("gpt-4o")
        self.config = load_config()
        
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))
    
    async def measure_preference_collection(
        self, 
        agent_type: str = "standard"
    ) -> Dict[str, Any]:
        """
        Measure context size during preference collection.
        
        Args:
            agent_type: "standard" or "scaledown"
            
        Returns:
            Dictionary with measurements
        """
        print(f"\n{'='*70}")
        print(f"Measuring Preference Collection ({agent_type.upper()})")
        print(f"{'='*70}")
        
        # Initialize agent
        if agent_type == "standard":
            agent = UserPreferenceAgent(config=self.config)
        else:
            agent = ScaleDownUserPreferenceAgent(config=self.config)
        
        measurements = {
            'agent_type': agent_type,
            'greeting_tokens': 0,
            'question_tokens': [],
            'validation_tokens': [],
            'total_tokens': 0
        }
        
        # Measure greeting
        if agent_type == "standard":
            greeting_prompt = agent.GREETING_TEMPLATE
        else:
            greeting_prompt = agent.GREETING_CONTEXT + "\n" + agent.GREETING_PROMPT
        
        greeting_tokens = self.count_tokens(greeting_prompt)
        measurements['greeting_tokens'] = greeting_tokens
        
        print(f"\n1. Greeting Prompt:")
        print(f"   Tokens: {greeting_tokens}")
        print(f"   Sample: {greeting_prompt[:100]}...")
        
        # Measure questions (estimate based on template)
        if agent_type == "standard":
            question_template = agent.QUESTION_TEMPLATE
        else:
            question_template = getattr(agent, 'QUESTION_CONTEXT_TEMPLATE', '')
        
        for i, q in enumerate(agent.preference_questions, 1):
            # Build question context
            if agent_type == "standard":
                question_text = question_template.format(
                    field=q['field'],
                    question=q['question'],
                    required="Yes" if q['required'] else "No",
                    conversation_history="Assistant: Hello!\nUser: Hi"
                )
            else:
                question_text = question_template.format(
                    field=q['field'],
                    question=q['question'],
                    required=q['required'],
                    conversation_history="Assistant: Hello!\nUser: Hi"
                )
            
            question_tokens = self.count_tokens(question_text)
            measurements['question_tokens'].append(question_tokens)
            
            print(f"\n2.{i} Question {i} ({q['field']}):")
            print(f"   Tokens: {question_tokens}")
        
        # Measure validation (estimate)
        if agent_type == "standard":
            validation_template = agent.VALIDATION_TEMPLATE
            validation_text = validation_template.format(
                question=agent.preference_questions[0]['question'],
                user_response="Python programming and data analysis"
            )
        else:
            validation_template = agent.VALIDATION_CONTEXT_TEMPLATE
            validation_text = validation_template.format(
                question=agent.preference_questions[0]['question'],
                user_response="Python programming and data analysis"
            ) + "\n" + agent.VALIDATION_PROMPT
        
        validation_tokens = self.count_tokens(validation_text)
        measurements['validation_tokens'] = [validation_tokens] * len(agent.preference_questions)
        
        print(f"\n3. Validation Prompt (average):")
        print(f"   Tokens per validation: {validation_tokens}")
        
        # Calculate total
        total = (
            measurements['greeting_tokens'] +
            sum(measurements['question_tokens']) +
            sum(measurements['validation_tokens'])
        )
        measurements['total_tokens'] = total
        
        print(f"\n{'='*70}")
        print(f"TOTAL PREFERENCE COLLECTION TOKENS: {total}")
        print(f"{'='*70}")
        
        return measurements
    
    async def measure_channel_analysis(
        self,
        agent_type: str = "standard",
        num_channels: int = 15
    ) -> Dict[str, Any]:
        """
        Measure context size during channel analysis.
        
        Args:
            agent_type: "standard" or "scaledown"
            num_channels: Number of channels to analyze
            
        Returns:
            Dictionary with measurements
        """
        print(f"\n{'='*70}")
        print(f"Measuring Channel Analysis ({agent_type.upper()}) - {num_channels} channels")
        print(f"{'='*70}")
        
        # Load channels
        channels = load_channels_from_json()[:num_channels]
        
        # Initialize agent
        if agent_type == "standard":
            agent = ChannelAnalyzerAgent(config=self.config)
        else:
            agent = ScaleDownChannelAnalyzerAgent(config=self.config)
        
        # Sample user preferences
        test_cases = get_test_user_preferences()
        preferences = test_cases[0]['preferences']
        
        measurements = {
            'agent_type': agent_type,
            'num_channels': num_channels,
            'tokens_per_channel': [],
            'recommendation_tokens': 0,
            'total_tokens': 0
        }
        
        # Measure per-channel analysis
        print(f"\nPer-Channel Analysis:")
        
        for i, channel in enumerate(channels[:3], 1):  # Show first 3 as examples
            if agent_type == "standard":
                analysis_prompt = agent.CHANNEL_ANALYSIS_TEMPLATE.format(
                    interests=preferences.get('interests', ''),
                    role=preferences.get('role', ''),
                    experience_level=preferences.get('experience_level', ''),
                    goals=preferences.get('goals', ''),
                    channel_name=channel['name'],
                    channel_description=channel.get('description', ''),
                    channel_topics=', '.join(channel.get('topics', [])),
                    activity_level=channel.get('activity_level', 'Unknown'),
                    target_audience=channel.get('target_audience', 'General')
                )
            else:
                analysis_prompt = agent.CHANNEL_ANALYSIS_CONTEXT.format(
                    interests=preferences.get('interests', ''),
                    role=preferences.get('role', ''),
                    experience_level=preferences.get('experience_level', ''),
                    goals=preferences.get('goals', ''),
                    channel_name=channel['name'],
                    channel_description=channel.get('description', ''),
                    channel_topics=', '.join(channel.get('topics', [])),
                    activity_level=channel.get('activity_level', 'Unknown'),
                    target_audience=channel.get('target_audience', 'General')
                ) + "\n" + agent.CHANNEL_ANALYSIS_PROMPT
            
            tokens = self.count_tokens(analysis_prompt)
            measurements['tokens_per_channel'].append(tokens)
            
            print(f"  Channel {i} (#{channel['name']}): {tokens} tokens")
        
        # Estimate for remaining channels
        avg_tokens_per_channel = sum(measurements['tokens_per_channel']) / len(measurements['tokens_per_channel'])
        total_channel_tokens = int(avg_tokens_per_channel * num_channels)
        
        print(f"\n  Average per channel: {int(avg_tokens_per_channel)} tokens")
        print(f"  Total for {num_channels} channels: {total_channel_tokens} tokens")
        
        # Measure recommendation message generation
        if agent_type == "standard":
            rec_template = agent.RECOMMENDATION_TEMPLATE
            rec_prompt = rec_template.format(
                interests=preferences.get('interests', ''),
                role=preferences.get('role', ''),
                experience_level=preferences.get('experience_level', ''),
                goals=preferences.get('goals', ''),
                channel_summaries="Sample channel list..."
            )
        else:
            rec_prompt = agent.RECOMMENDATION_CONTEXT_TEMPLATE.format(
                interests=preferences.get('interests', ''),
                role=preferences.get('role', ''),
                experience_level=preferences.get('experience_level', ''),
                goals=preferences.get('goals', ''),
                channel_summaries="Sample channel list..."
            ) + "\n" + agent.RECOMMENDATION_PROMPT
        
        rec_tokens = self.count_tokens(rec_prompt)
        measurements['recommendation_tokens'] = rec_tokens
        
        print(f"\nRecommendation Message Generation: {rec_tokens} tokens")
        
        # Calculate total
        total = total_channel_tokens + rec_tokens
        measurements['total_tokens'] = total
        
        print(f"\n{'='*70}")
        print(f"TOTAL CHANNEL ANALYSIS TOKENS: {total}")
        print(f"{'='*70}")
        
        return measurements
    
    def print_summary(
        self,
        pref_standard: Dict[str, Any],
        pref_scaledown: Dict[str, Any],
        channel_standard: Dict[str, Any],
        channel_scaledown: Dict[str, Any]
    ):
        """
        Print summary comparison.
        
        Args:
            pref_standard: Standard preference measurements
            pref_scaledown: ScaleDown preference measurements
            channel_standard: Standard channel measurements
            channel_scaledown: ScaleDown channel measurements
        """
        print(f"\n\n{'='*70}")
        print("SUMMARY: CONTEXT SIZE COMPARISON")
        print(f"{'='*70}")
        
        print(f"\n1. PREFERENCE COLLECTION:")
        print(f"   Standard:  {pref_standard['total_tokens']:,} tokens")
        print(f"   ScaleDown: {pref_scaledown['total_tokens']:,} tokens (before compression)")
        
        print(f"\n2. CHANNEL ANALYSIS ({channel_standard['num_channels']} channels):")
        print(f"   Standard:  {channel_standard['total_tokens']:,} tokens")
        print(f"   ScaleDown: {channel_scaledown['total_tokens']:,} tokens (before compression)")
        
        total_standard = pref_standard['total_tokens'] + channel_standard['total_tokens']
        total_scaledown = pref_scaledown['total_tokens'] + channel_scaledown['total_tokens']
        
        print(f"\n3. TOTAL PER RECOMMENDATION:")
        print(f"   Standard:  {total_standard:,} tokens")
        print(f"   ScaleDown: {total_scaledown:,} tokens (before compression)")
        
        print(f"\n{'='*70}")
        print("CONTEXT SIZE ANALYSIS")
        print(f"{'='*70}")
        
        if total_standard < 2000:
            print(f"\n⚠️  SMALL CONTEXT DETECTED!")
            print(f"   Current total: {total_standard:,} tokens")
            print(f"   Threshold: 2,000 tokens")
            print(f"   \n   This explains why ScaleDown has higher latency.")
            print(f"   Compression overhead isn't offset by reduced LLM processing time.")
        else:
            print(f"\n✅ Context size ({total_standard:,} tokens > 2,000)")
        
        # print(f"\n{'='*70}")
        # print("RECOMMENDATIONS TO INCREASE CONTEXT SIZE")
        # print(f"{'='*70}")
        
        # print(f"\nOption 1: Analyze more channels")
        # for num_channels in [30, 50, 100]:
        #     estimated = total_standard + (channel_standard['total_tokens'] // channel_standard['num_channels']) * (num_channels - channel_standard['num_channels'])
        #     print(f"   - {num_channels} channels: ~{estimated:,} tokens")
        
        # print(f"\nOption 2: Include conversation history")
        # print(f"   - Add last 10 messages: ~500-1,000 tokens")
        # print(f"   - Estimated total: ~{total_standard + 750:,} tokens")
        
        # print(f"\nOption 3: Add channel metadata")
        # print(f"   - Member count, activity stats, sample messages")
        # print(f"   - Estimated addition: ~200 tokens per channel")
        # print(f"   - Estimated total: ~{total_standard + (200 * channel_standard['num_channels']):,} tokens")
        
        # print(f"\nOption 4: Batch multiple recommendations")
        # print(f"   - Process 3 users at once: ~{total_standard * 3:,} tokens")
        # print(f"   - Process 5 users at once: ~{total_standard * 5:,} tokens")
        
        # print(f"\n{'='*70}\n")


async def main():
    """Main entry point."""
    measurer = ContextSizeMeasurer()
    
    print("\n" + "="*70)
    print("CONTEXT SIZE MEASUREMENT TOOL")
    print("="*70)
    print("\nThis tool measures the actual context sizes being sent to OpenAI")
    print("to help understand latency issues with ScaleDown compression.")
    
    # Measure preference collection
    pref_standard = await measurer.measure_preference_collection("standard")
    pref_scaledown = await measurer.measure_preference_collection("scaledown")
    
    # Measure channel analysis
    channel_standard = await measurer.measure_channel_analysis("standard", num_channels=15)
    channel_scaledown = await measurer.measure_channel_analysis("scaledown", num_channels=15)
    
    # Print summary
    measurer.print_summary(
        pref_standard,
        pref_scaledown,
        channel_standard,
        channel_scaledown
    )
    
    # Prepare JSON results
    results = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "standard": {
                "preference_collection_tokens": pref_standard['total_tokens'],
                "channel_analysis_tokens": channel_standard['total_tokens'],
                "total_tokens_per_recommendation": pref_standard['total_tokens'] + channel_standard['total_tokens'],
                "breakdown": {
                    "greeting": pref_standard['greeting_tokens'],
                    "questions": sum(pref_standard['question_tokens']),
                    "validation": sum(pref_standard['validation_tokens']),
                    "channel_analysis": channel_standard['total_tokens'] - channel_standard['recommendation_tokens'],
                    "recommendation_message": channel_standard['recommendation_tokens']
                }
            },
            "scaledown": {
                "preference_collection_tokens": pref_scaledown['total_tokens'],
                "channel_analysis_tokens": channel_scaledown['total_tokens'],
                "total_tokens_per_recommendation": pref_scaledown['total_tokens'] + channel_scaledown['total_tokens'],
                "estimated_compressed_tokens": int((pref_scaledown['total_tokens'] + channel_scaledown['total_tokens']) * 0.49),  # Based on 51% compression ratio
                "breakdown": {
                    "greeting": pref_scaledown['greeting_tokens'],
                    "questions": sum(pref_scaledown['question_tokens']),
                    "validation": sum(pref_scaledown['validation_tokens']),
                    "channel_analysis": channel_scaledown['total_tokens'] - channel_scaledown['recommendation_tokens'],
                    "recommendation_message": channel_scaledown['recommendation_tokens']
                }
            },
            "comparison": {
                "num_channels_analyzed": channel_standard['num_channels'],
                "above_2000_token_threshold": (pref_standard['total_tokens'] + channel_standard['total_tokens']) > 2000,
                "scaledown_compressed_above_threshold": int((pref_scaledown['total_tokens'] + channel_scaledown['total_tokens']) * 0.49) > 2000,
                # "notes": [
                #     "Both agents now use identical prompts (matching criteria removed)",
                #     "ScaleDown shows ~51% compression ratio based on actual results",
                #     "Context size is above 2000 token threshold for optimal ScaleDown performance"
                # ]
            }
        },
        "detailed_measurements": {
            "preference_collection": {
                "standard": pref_standard,
                "scaledown": pref_scaledown
            },
            "channel_analysis": {
                "standard": channel_standard,
                "scaledown": channel_scaledown
            }
        }
    }
    
    # Save to JSON file
    output_file = "context_size_measurements.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*70}")
    
    # Ask about testing larger contexts
    print("\nWould you like to test with a larger context? (y/n): ", end="")
    response = input().strip().lower()
    
    if response == 'y':
        print("\nHow many channels to analyze? (default: 50): ", end="")
        try:
            num_channels = int(input().strip() or "50")
        except ValueError:
            num_channels = 50
        
        print(f"\nTesting with {num_channels} channels...")
        channel_standard_large = await measurer.measure_channel_analysis("standard", num_channels=num_channels)
        channel_scaledown_large = await measurer.measure_channel_analysis("scaledown", num_channels=num_channels)
        
        measurer.print_summary(
            pref_standard,
            pref_scaledown,
            channel_standard_large,
            channel_scaledown_large
        )


if __name__ == "__main__":
    asyncio.run(main())
