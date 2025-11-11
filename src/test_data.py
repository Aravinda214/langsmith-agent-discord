"""
Test Data Module

This module provides mock Discord channel data for testing and demonstration.
Now loads data from data/channels.json instead of hardcoded dictionaries.

In a real application, this data would come from:
- JSON/CSV files (current implementation)
- Discord MCP server (future)
- Discord API (future)
- Database (future)

The mock data is designed to test various matching scenarios.
"""

from typing import List, Dict, Any
from data_loader import load_channels_from_json


def get_mock_channels() -> List[Dict[str, Any]]:
    """
    Get mock Discord channel data for testing.
    
    Now loads from data/channels.json file.
    
    Each channel includes:
    - name: Channel name
    - description: What the channel is about
    - topics: List of relevant topics/keywords (used for INTEREST matching)
    - activity_level: How active the channel is (low, medium, high)
    - target_audience: Who the channel is designed for (used for EXPERIENCE LEVEL matching)
    - best_for_roles: Roles that fit this channel (used for ROLE matching)
    - best_for_goals: Goals this channel helps with (used for GOAL matching)
    
    Matching Criteria (see data/channels.json metadata):
    - Interests: 40% weight - matches user interests with channel topics
    - Experience Level: 30% weight - matches user level with target_audience
    - Role: 20% weight - matches user role with best_for_roles
    - Goals: 10% weight - matches user goals with best_for_goals and description
    
    Returns:
        List of channel dictionaries loaded from JSON
    """
    return load_channels_from_json()


def get_test_user_preferences() -> List[Dict[str, Any]]:
    """
    Get sample user preferences for testing.
    
    These represent different user personas to test the matching algorithm.
    Comment/uncomment test cases as needed to control test execution time.
    
    Returns:
        List of user preference dictionaries
    """
    return [
        # Active test cases (2 tests - faster execution)
        {
            "name": "Python Beginner",
            "preferences": {
                "interests": "Learning Python programming and data analysis",
                "role": "Student",
                "experience_level": "beginner",
                "goals": "Build projects and get a job as a data analyst"
            }
        },
        {
            "name": "Senior Developer",
            "preferences": {
                "interests": "Software architecture, design patterns, and cloud infrastructure",
                "role": "Senior Software Engineer",
                "experience_level": "advanced",
                "goals": "Stay updated with best practices and mentor others"
            }
        },
        
        # Optional test cases (uncomment to add more tests)
        {
            "name": "Career Switcher",
            "preferences": {
                "interests": "Web development, React, and modern JavaScript",
                "role": "Career switcher from marketing to tech",
                "experience_level": "beginner",
                "goals": "Learn web development and get my first developer job"
            }
        },
        {
            "name": "ML Enthusiast",
            "preferences": {
                "interests": "Machine learning, AI, and deep learning",
                "role": "Data Scientist",
                "experience_level": "intermediate",
                "goals": "Advance my ML skills and work on real-world AI projects"
            }
        },
        {
            "name": "Student Developer",
            "preferences": {
                "interests": "Programming, algorithms, and interview preparation",
                "role": "Computer Science Student",
                "experience_level": "intermediate",
                "goals": "Practice coding challenges and prepare for technical interviews"
            }
        }
    ]


# Example of how to use this data
if __name__ == "__main__":
    channels = get_mock_channels()
    print(f"Mock data includes {len(channels)} Discord channels")
    
    test_users = get_test_user_preferences()
    print(f"Test data includes {len(test_users)} user personas")
    
    print("\nSample channels:")
    for channel in channels[:3]:
        print(f"  - #{channel['name']}: {channel['description']}")
