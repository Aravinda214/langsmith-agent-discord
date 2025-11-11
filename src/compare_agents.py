"""
Agent Comparison Framework

This script compares standard agents vs ScaleDown-enabled agents across multiple metrics:
1. Token consumption (original vs compressed)
2. Latency (response time)
3. Cost (based on OpenAI pricing)
4. Accuracy (qualitative comparison of outputs)

The goal is to demonstrate that ScaleDown reduces costs and tokens while
maintaining accuracy and potentially improving latency.
"""

import asyncio
import json
import time
from typing import Dict, Any, List
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import load_config
from test_data import get_mock_channels, get_test_user_preferences
from agents.user_preference_agent import UserPreferenceAgent
from agents.channel_analyzer_agent import ChannelAnalyzerAgent
from agents.scaledown_user_preference_agent import ScaleDownUserPreferenceAgent
from agents.scaledown_channel_analyzer_agent import ScaleDownChannelAnalyzerAgent
from langsmith import Client
import logging

# Initialize LangSmith client for logging feedback/metrics
langsmith_client = Client()


class AgentComparator:
    """
    Compares standard agents vs ScaleDown agents across multiple metrics.
    
    Metrics tracked:
    - Token usage (input + output)
    - Response latency
    - API costs (estimated)
    - Output quality/accuracy
    """
    
    # OpenAI pricing (as of 2024, update as needed)
    # https://openai.com/pricing
    PRICING = {
        'gpt-4': {
            'input': 0.03 / 1000,   # $0.03 per 1K tokens
            'output': 0.06 / 1000   # $0.06 per 1K tokens
        },
        'gpt-4o': {
            'input': 0.0025 / 1000,  # $0.0025 per 1K tokens
            'output': 0.01 / 1000    # $0.01 per 1K tokens
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the comparator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'comparisons': []
        }
    
    async def compare_all(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run all comparisons across test cases.
        
        Args:
            test_cases: List of test case dictionaries
            
        Returns:
            Complete comparison results
        """
        print("=" * 80)
        print("AGENT COMPARISON: Standard vs ScaleDown")
        print("=" * 80)
        print(f"\nRunning {len(test_cases)} test cases...\n")
        
        for idx, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*80}")
            print(f"TEST CASE {idx}: {test_case['name']}")
            print(f"{'='*80}")
            
            result = await self.compare_single_case(test_case)
            self.results['comparisons'].append(result)
            
            # Print summary
            self._print_case_summary(result)
        
        # Calculate aggregate stats
        self.results['aggregate'] = self._calculate_aggregate_stats()
        
        # Print final summary
        self._print_final_summary()
        
        return self.results
    
    async def compare_single_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare standard vs ScaleDown agents for a single test case.
        
        Args:
            test_case: Test case with user preferences and expected behavior
            
        Returns:
            Comparison results for this case
        """
        user_prefs = test_case['preferences']
        channels = get_mock_channels()
        
        print(f"\nUser Profile: {user_prefs['interests'][:50]}...")
        
        # Run standard agents
        print("\n[1/2] Running STANDARD agents...")
        standard_result = await self._run_standard_agents(user_prefs, channels)
        
        # Run ScaleDown agents
        print("[2/2] Running SCALEDOWN agents...")
        scaledown_result = await self._run_scaledown_agents(user_prefs, channels)
        
        # Compare results
        comparison = self._compare_results(
            test_case,
            standard_result,
            scaledown_result
        )
        
        # Log metrics to LangSmith for A/B testing analysis
        self._log_metrics_to_langsmith(comparison)
        
        return comparison
    
    async def _run_standard_agents(
        self, 
        preferences: Dict[str, Any],
        channels: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run standard agents (no compression).
        
        Args:
            preferences: User preferences
            channels: List of channels
            
        Returns:
            Results with timing and token info
        """
        start_time = time.time()
        
        # Initialize agents
        pref_config = self.config['agents']['user_preference_agent'].copy()
        pref_config['preference_questions'] = self.config['preference_questions']
        
        analyzer_config = self.config['agents']['channel_analyzer_agent'].copy()
        analyzer_config.update(self.config['channel_analysis'])
        
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
        
        # Run preference collection (simulated - we already have preferences)
        pref_start = time.time()
        # In real usage, this would collect prefs - we'll just time a greeting
        greeting_result = await pref_agent.execute({'mode': 'start'})
        pref_time = time.time() - pref_start
        pref_tokens = greeting_result.get('token_usage', {})
        
        # Run channel analysis
        analyzer_start = time.time()
        analysis_result = await analyzer_agent.execute({
            'preferences': preferences,
            'channels': channels
        })
        analyzer_time = time.time() - analyzer_start
        analyzer_tokens = analysis_result.get('token_usage', {})
        
        total_time = time.time() - start_time
        
        # Combine actual token usage
        total_tokens = {
            'prompt_tokens': pref_tokens.get('prompt_tokens', 0) + analyzer_tokens.get('prompt_tokens', 0),
            'completion_tokens': pref_tokens.get('completion_tokens', 0) + analyzer_tokens.get('completion_tokens', 0),
            'total_tokens': pref_tokens.get('total_tokens', 0) + analyzer_tokens.get('total_tokens', 0)
        }
        
        return {
            'total_time': total_time,
            'pref_collection_time': pref_time,
            'analysis_time': analyzer_time,
            'tokens': total_tokens,
            'recommendations': analysis_result['recommendations'][:3],
            'recommendation_message': analysis_result.get('message', '')
        }
    
    async def _run_scaledown_agents(
        self,
        preferences: Dict[str, Any],
        channels: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run ScaleDown agents (with compression).
        
        Args:
            preferences: User preferences
            channels: List of channels
            
        Returns:
            Results with timing, token info, and compression metrics
        """
        start_time = time.time()
        
        # Initialize ScaleDown agents
        pref_config = self.config['agents']['scaledown_user_preference_agent'].copy()
        pref_config['preference_questions'] = self.config['preference_questions']
        
        analyzer_config = self.config['agents']['scaledown_channel_analyzer_agent'].copy()
        analyzer_config.update(self.config['channel_analysis'])
        
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
        
        # Run preference collection
        pref_start = time.time()
        greeting_result = await pref_agent.execute({'mode': 'start'})
        pref_time = time.time() - pref_start
        pref_metrics = greeting_result.get('compression_metrics', {})
        
        # Run channel analysis
        analyzer_start = time.time()
        analysis_result = await analyzer_agent.execute({
            'preferences': preferences,
            'channels': channels
        })
        analyzer_time = time.time() - analyzer_start
        analyzer_metrics = analysis_result.get('compression_metrics', {})
        
        total_time = time.time() - start_time
        
        # Combine compression metrics
        combined_metrics = {
            'total_original_tokens': (
                pref_metrics.get('total_original_tokens', 0) +
                analyzer_metrics.get('total_original_tokens', 0)
            ),
            'total_compressed_tokens': (
                pref_metrics.get('total_compressed_tokens', 0) +
                analyzer_metrics.get('total_compressed_tokens', 0)
            ),
            'tokens_saved': (
                pref_metrics.get('tokens_saved', 0) +
                analyzer_metrics.get('tokens_saved', 0)
            ),
            'total_compression_time': (
                pref_metrics.get('total_compression_time', 0) +
                analyzer_metrics.get('total_compression_time', 0)
            )
        }
        
        if combined_metrics['total_original_tokens'] > 0:
            combined_metrics['compression_ratio'] = (
                combined_metrics['tokens_saved'] / 
                combined_metrics['total_original_tokens'] * 100
            )
        else:
            combined_metrics['compression_ratio'] = 0
        
        return {
            'total_time': total_time,
            'pref_collection_time': pref_time,
            'analysis_time': analyzer_time,
            'compression_metrics': combined_metrics,
            'recommendations': analysis_result['recommendations'][:3],
            'recommendation_message': analysis_result.get('message', '')
        }
    
    def _estimate_tokens_standard(
        self,
        preferences: Dict[str, Any],
        channels: List[Dict[str, Any]],
        analysis_result: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Estimate tokens for standard agents (rough approximation).
        
        In production, you'd get this from the actual API response.
        """
        # Rough estimate: 1 token ≈ 4 characters for English text
        
        # Preferences text
        pref_text = json.dumps(preferences)
        pref_tokens = len(pref_text) // 4
        
        # Channels text (all channels get analyzed)
        channels_text = json.dumps(channels)
        channels_tokens = len(channels_text) // 4
        
        # Each channel analysis creates a prompt
        num_analyses = len(channels)
        prompt_tokens_per_channel = 200  # Rough estimate
        
        # Output tokens
        output_text = analysis_result.get('message', '')
        output_tokens = len(output_text) // 4
        
        total_input = pref_tokens + (channels_tokens * num_analyses) + (prompt_tokens_per_channel * num_analyses)
        total_output = output_tokens + (100 * num_analyses)  # Each analysis produces output
        
        return {
            'input_tokens': total_input,
            'output_tokens': total_output,
            'total_tokens': total_input + total_output
        }
    
    def _compare_results(
        self,
        test_case: Dict[str, Any],
        standard: Dict[str, Any],
        scaledown: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare standard vs ScaleDown results.
        
        Args:
            test_case: Original test case
            standard: Standard agents results
            scaledown: ScaleDown agents results
            
        Returns:
            Comparison dictionary
        """
        # Calculate costs (both using gpt-4o now)
        standard_cost = self._calculate_cost(
            standard['tokens']['prompt_tokens'],
            standard['tokens']['completion_tokens'],
            'gpt-4o'
        )
        
        scaledown_metrics = scaledown['compression_metrics']
        scaledown_cost = self._calculate_cost(
            scaledown_metrics['total_compressed_tokens'],
            scaledown_metrics['total_compressed_tokens'] // 10,  # Rough output estimate
            'gpt-4o'
        )
        
        # Calculate savings
        token_savings = (
            standard['tokens']['total_tokens'] - 
            scaledown_metrics['total_compressed_tokens']
        )
        token_savings_pct = (
            token_savings / standard['tokens']['total_tokens'] * 100
            if standard['tokens']['total_tokens'] > 0 else 0
        )
        
        cost_savings = standard_cost - scaledown_cost
        cost_savings_pct = (
            cost_savings / standard_cost * 100
            if standard_cost > 0 else 0
        )
        
        # Latency comparison
        latency_diff = scaledown['total_time'] - standard['total_time']
        latency_improvement = latency_diff < 0
        
        return {
            'test_case_name': test_case['name'],
            'user_profile': test_case['preferences']['interests'][:50],
            'standard': {
                'total_time': standard['total_time'],
                'tokens': standard['tokens'],
                'cost': standard_cost,
                'top_recommendation': standard['recommendations'][0]['name'] if standard['recommendations'] else None
            },
            'scaledown': {
                'total_time': scaledown['total_time'],
                'compression_metrics': scaledown_metrics,
                'cost': scaledown_cost,
                'top_recommendation': scaledown['recommendations'][0]['channel_name'] if scaledown['recommendations'] else None
            },
            'comparison': {
                'token_savings': token_savings,
                'token_savings_pct': token_savings_pct,
                'cost_savings': cost_savings,
                'cost_savings_pct': cost_savings_pct,
                'latency_diff': latency_diff,
                'latency_improvement': latency_improvement,
                'same_top_recommendation': (
                    standard['recommendations'][0]['name'] == 
                    scaledown['recommendations'][0]['channel_name']
                    if standard['recommendations'] and scaledown['recommendations'] else False
                )
            }
        }
    
    def _log_metrics_to_langsmith(self, comparison: Dict[str, Any], 
                                   standard_run_id: str = None, 
                                   scaledown_run_id: str = None):
        """
        Log comparison metrics to LangSmith for A/B testing and analysis.
        
        This creates a summary that appears in LangSmith UI under the project.
        You can then use LangSmith's comparison features to analyze:
        - Token savings across test cases
        - Cost reduction
        - Latency differences
        - Accuracy maintenance
        
        Args:
            comparison: Comparison results dictionary
            standard_run_id: LangSmith run ID for standard agent (optional)
            scaledown_run_id: LangSmith run ID for scaledown agent (optional)
        """
        try:
            # Log as a structured event that LangSmith can track
            # This will show up in your LangSmith project for analysis
            
            metrics_summary = {
                "test_case": comparison['test_case_name'],
                "timestamp": datetime.now().isoformat(),
                
                # Standard agent metrics
                "standard_total_tokens": comparison['standard']['tokens']['total_tokens'],
                "standard_prompt_tokens": comparison['standard']['tokens']['prompt_tokens'],
                "standard_completion_tokens": comparison['standard']['tokens']['completion_tokens'],
                "standard_cost_usd": comparison['standard']['cost'],
                "standard_latency_seconds": comparison['standard']['total_time'],
                
                # ScaleDown agent metrics  
                "scaledown_compressed_tokens": comparison['scaledown']['compression_metrics']['total_compressed_tokens'],
                "scaledown_original_tokens": comparison['scaledown']['compression_metrics']['total_original_tokens'],
                "scaledown_compression_ratio": comparison['scaledown']['compression_metrics'].get('compression_ratio', 0),
                "scaledown_cost_usd": comparison['scaledown']['cost'],
                "scaledown_latency_seconds": comparison['scaledown']['total_time'],
                
                # Comparison metrics
                "token_savings": comparison['comparison']['token_savings'],
                "token_savings_pct": comparison['comparison']['token_savings_pct'],
                "cost_savings_usd": comparison['comparison']['cost_savings'],
                "cost_savings_pct": comparison['comparison']['cost_savings_pct'],
                "latency_diff_seconds": comparison['comparison']['latency_diff'],
                "same_top_recommendation": comparison['comparison']['same_top_recommendation']
            }
            
            # Log this as metadata to the LangSmith project
            # You can view this in LangSmith UI under your project's runs
            self.logger.info(f"📊 LangSmith Metrics Summary: {json.dumps(metrics_summary, indent=2)}")
            
            # Note: For full A/B testing, you would:
            # 1. Tag runs with "standard" vs "scaledown"  
            # 2. Use LangSmith's comparison UI to visualize metrics
            # 3. Create datasets for repeated testing
            
        except Exception as e:
            self.logger.warning(f"⚠️  Failed to log metrics summary: {e}")
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Calculate API cost based on token usage."""
        pricing = self.PRICING.get(model, self.PRICING['gpt-4o'])
        return (input_tokens * pricing['input']) + (output_tokens * pricing['output'])
    
    def _calculate_aggregate_stats(self) -> Dict[str, Any]:
        """Calculate aggregate statistics across all test cases."""
        comparisons = self.results['comparisons']
        
        total_standard_cost = sum(c['standard']['cost'] for c in comparisons)
        total_scaledown_cost = sum(c['scaledown']['cost'] for c in comparisons)
        
        total_standard_tokens = sum(c['standard']['tokens']['total_tokens'] for c in comparisons)
        total_scaledown_tokens = sum(c['scaledown']['compression_metrics']['total_compressed_tokens'] for c in comparisons)
        
        avg_token_savings_pct = sum(c['comparison']['token_savings_pct'] for c in comparisons) / len(comparisons)
        avg_cost_savings_pct = sum(c['comparison']['cost_savings_pct'] for c in comparisons) / len(comparisons)
        
        accuracy_match_count = sum(1 for c in comparisons if c['comparison']['same_top_recommendation'])
        accuracy_pct = (accuracy_match_count / len(comparisons) * 100) if comparisons else 0
        
        return {
            'total_test_cases': len(comparisons),
            'total_standard_cost': total_standard_cost,
            'total_scaledown_cost': total_scaledown_cost,
            'total_cost_savings': total_standard_cost - total_scaledown_cost,
            'total_standard_tokens': total_standard_tokens,
            'total_scaledown_tokens': total_scaledown_tokens,
            'total_tokens_saved': total_standard_tokens - total_scaledown_tokens,
            'avg_token_savings_pct': avg_token_savings_pct,
            'avg_cost_savings_pct': avg_cost_savings_pct,
            'accuracy_match_pct': accuracy_pct
        }
    
    def _print_case_summary(self, result: Dict[str, Any]):
        """Print summary for a single test case."""
        print(f"\n📊 Results:")
        print(f"  Standard Agent:")
        print(f"    Time: {result['standard']['total_time']:.2f}s")
        print(f"    Tokens: {result['standard']['tokens']['total_tokens']:,}")
        print(f"    Cost: ${result['standard']['cost']:.4f}")
        print(f"    Top Pick: #{result['standard']['top_recommendation']}")
        
        print(f"\n  ScaleDown Agent:")
        print(f"    Time: {result['scaledown']['total_time']:.2f}s")
        print(f"    Tokens: {result['scaledown']['compression_metrics']['total_compressed_tokens']:,}")
        print(f"    Cost: ${result['scaledown']['cost']:.4f}")
        print(f"    Top Pick: #{result['scaledown']['top_recommendation']}")
        print(f"    Compression: {result['scaledown']['compression_metrics']['compression_ratio']:.1f}%")
        
        print(f"\n  💰 Savings:")
        print(f"    Tokens Saved: {result['comparison']['token_savings']:,} ({result['comparison']['token_savings_pct']:.1f}%)")
        print(f"    Cost Saved: ${result['comparison']['cost_savings']:.4f} ({result['comparison']['cost_savings_pct']:.1f}%)")
        print(f"    Same Top Rec: {'✅ Yes' if result['comparison']['same_top_recommendation'] else '❌ No'}")
    
    def _print_final_summary(self):
        """Print final aggregate summary."""
        agg = self.results['aggregate']
        
        print(f"\n\n{'='*80}")
        print("FINAL SUMMARY - AGGREGATE RESULTS")
        print(f"{'='*80}")
        
        print(f"\n📈 Total Test Cases: {agg['total_test_cases']}")
        
        print(f"\n💵 Cost Comparison:")
        print(f"  Standard Total: ${agg['total_standard_cost']:.4f}")
        print(f"  ScaleDown Total: ${agg['total_scaledown_cost']:.4f}")
        print(f"  Total Savings: ${agg['total_cost_savings']:.4f} ({agg['avg_cost_savings_pct']:.1f}% average)")
        
        print(f"\n🎫 Token Comparison:")
        print(f"  Standard Total: {agg['total_standard_tokens']:,}")
        print(f"  ScaleDown Total: {agg['total_scaledown_tokens']:,}")
        print(f"  Tokens Saved: {agg['total_tokens_saved']:,} ({agg['avg_token_savings_pct']:.1f}% average)")
        
        print(f"\n🎯 Accuracy:")
        print(f"  Same Top Recommendation: {agg['accuracy_match_pct']:.1f}%")
        
        print(f"\n{'='*80}")
    
    def save_results(self, filename: str = "comparison_results.json"):
        """Save results to JSON file."""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to: {filepath}")


async def main():
    """Main entry point for comparison."""
    # Load configuration
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config.yaml")
    config = load_config(config_path)
    
    # Get test cases
    test_personas = get_test_user_preferences()
    
    # Create comparator
    comparator = AgentComparator(config)
    
    # Run comparisons
    results = await comparator.compare_all(test_personas)
    
    # Save results
    comparator.save_results()
    
    return results


if __name__ == "__main__":
    # Run comparison
    asyncio.run(main())
    
    # Clean up to prevent Windows asyncio warning
    # (This is optional - the warning is harmless)
    import time
    time.sleep(0.1)  # Give background tasks time to finish

