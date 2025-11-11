"""
Test Runner Module

This module provides automated tests for the agent workflow.
It tests the system with different user personas and evaluates performance.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_loader import load_config, setup_logging
from orchestrator import AgentOrchestrator
from test_data import get_mock_channels, get_test_user_preferences


class TestRunner:
    """
    Automated test runner for the agent system.
    
    This class:
    1. Runs the system with different user personas
    2. Measures performance metrics
    3. Generates a test report
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the test runner."""
        # Default to config.yaml in the parent directory
        if config_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(project_root, "config.yaml")
        
        self.config = load_config(config_path)
        setup_logging(self.config)
        self.results = []
    
    async def run_test_case(self, test_name: str, user_preferences: dict, 
                           channels: list) -> dict:
        """
        Run a single test case.
        
        Args:
            test_name: Name of the test case
            user_preferences: User preferences to test
            channels: Channel data
            
        Returns:
            Dictionary with test results
        """
        print(f"\n{'='*60}")
        print(f"Running Test: {test_name}")
        print(f"{'='*60}")
        
        # Create a fresh orchestrator for each test
        orchestrator = AgentOrchestrator(self.config)
        
        # Set channel data
        orchestrator.channel_analyzer.set_channels_data(channels)
        
        # Measure execution time
        start_time = datetime.now()
        
        try:
            # Run analysis
            result = await orchestrator.channel_analyzer.execute({
                'preferences': user_preferences
            })
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Compile test results
            test_result = {
                "test_name": test_name,
                "status": "success",
                "execution_time_seconds": execution_time,
                "total_channels": result['total_analyzed'],
                "matching_channels": result['total_matching'],
                "recommendations_count": len(result['recommendations']),
                "top_recommendation": result['recommendations'][0]['name'] if result['recommendations'] else None,
                "top_match_score": result['recommendations'][0]['analysis']['match_score'] if result['recommendations'] else 0,
                "user_preferences": user_preferences,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"✅ Test passed in {execution_time:.2f}s")
            print(f"   Found {result['total_matching']} matching channels")
            if result['recommendations']:
                top_rec = result['recommendations'][0]
                print(f"   Top recommendation: #{top_rec['name']} ({top_rec['analysis']['match_score']:.1%} match)")
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            test_result = {
                "test_name": test_name,
                "status": "failed",
                "execution_time_seconds": execution_time,
                "error": str(e),
                "user_preferences": user_preferences,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"❌ Test failed: {e}")
        
        return test_result
    
    async def run_all_tests(self):
        """Run all test cases and generate a report."""
        print("\n" + "="*60)
        print("Discord Channel Selector - Automated Test Suite")
        print("="*60)
        
        # Get test data
        channels = get_mock_channels()
        test_users = get_test_user_preferences()
        
        print(f"\nTest Configuration:")
        print(f"  - Total channels: {len(channels)}")
        print(f"  - Test personas: {len(test_users)}")
        
        # Run each test case
        for test_user in test_users:
            result = await self.run_test_case(
                test_user['name'],
                test_user['preferences'],
                channels
            )
            self.results.append(result)
        
        # Generate report
        self._generate_report()
    
    def _generate_report(self):
        """Generate and display test report."""
        print("\n" + "="*60)
        print("TEST REPORT")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['status'] == 'success')
        failed_tests = total_tests - passed_tests
        
        total_time = sum(r['execution_time_seconds'] for r in self.results)
        avg_time = total_time / total_tests if total_tests > 0 else 0
        
        print(f"\nSummary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  ✅ Passed: {passed_tests}")
        print(f"  ❌ Failed: {failed_tests}")
        print(f"  Total Execution Time: {total_time:.2f}s")
        print(f"  Average Time per Test: {avg_time:.2f}s")
        
        # Detailed results
        print(f"\nDetailed Results:")
        for result in self.results:
            status_icon = "✅" if result['status'] == 'success' else "❌"
            print(f"\n{status_icon} {result['test_name']}")
            print(f"   Time: {result['execution_time_seconds']:.2f}s")
            
            if result['status'] == 'success':
                print(f"   Matching Channels: {result['matching_channels']}/{result['total_channels']}")
                print(f"   Top Match: #{result['top_recommendation']} ({result['top_match_score']:.1%})")
            else:
                print(f"   Error: {result['error']}")
        
        # Save detailed report to JSON
        report_file = "test_report.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "total_time": total_time,
                    "average_time": avg_time
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")


async def main():
    """Main entry point for test runner."""
    runner = TestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
