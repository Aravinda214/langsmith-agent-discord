"""
Data Loader Module

This module handles loading channel data from different sources:
- JSON files (data/channels.json)
- CSV files (future implementation)
- Discord MCP server (future implementation)

This provides flexibility in where channel data comes from.
"""

import json
import os
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def load_channels_from_json(json_path: str = None) -> List[Dict[str, Any]]:
    """
    Load Discord channel data from a JSON file.
    
    Args:
        json_path: Path to the JSON file. If None, uses default path.
        
    Returns:
        List of channel dictionaries
        
    Raises:
        FileNotFoundError: If the JSON file doesn't exist
        json.JSONDecodeError: If the JSON file is malformed
    """
    # Default path: data/channels.json relative to project root
    if json_path is None:
        # Get project root (parent of src directory)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        json_path = os.path.join(project_root, "data", "channels.json")
    
    logger.info(f"Loading channels from: {json_path}")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # The JSON file has metadata and channels sections
        channels = data.get('channels', [])
        metadata = data.get('metadata', {})
        
        logger.info(f"Loaded {len(channels)} channels from JSON")
        logger.debug(f"Data version: {metadata.get('version', 'unknown')}")
        
        return channels
        
    except FileNotFoundError:
        logger.error(f"Channel data file not found: {json_path}")
        raise FileNotFoundError(
            f"Channel data file not found: {json_path}\n"
            f"Please ensure data/channels.json exists in the project root."
        )
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {json_path}: {e}")
        raise ValueError(f"Invalid JSON format in {json_path}: {e}")


def get_channel_metadata(json_path: str = None) -> Dict[str, Any]:
    """
    Get metadata about the channel data (matching criteria, version, etc.).
    
    Args:
        json_path: Path to the JSON file. If None, uses default path.
        
    Returns:
        Dictionary containing metadata
    """
    if json_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        json_path = os.path.join(project_root, "data", "channels.json")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get('metadata', {})
        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Could not load metadata: {e}")
        return {}


def save_channels_to_json(channels: List[Dict[str, Any]], json_path: str = None) -> None:
    """
    Save channel data to a JSON file.
    
    Useful for:
    - Saving channels fetched from Discord MCP
    - Creating custom channel lists
    - Backing up channel data
    
    Args:
        channels: List of channel dictionaries to save
        json_path: Path where to save. If None, uses default path.
    """
    if json_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        json_path = os.path.join(project_root, "data", "channels.json")
    
    # Create data structure with metadata
    data = {
        "metadata": {
            "description": "Discord channel data for recommendation system",
            "version": "1.0",
            "total_channels": len(channels),
            "matching_criteria": {
                "interests": {
                    "weight": 0.40,
                    "description": "Matches user interests with channel topics",
                    "field": "topics"
                },
                "experience_level": {
                    "weight": 0.30,
                    "description": "Matches user experience level with channel target audience",
                    "field": "target_audience"
                },
                "role": {
                    "weight": 0.20,
                    "description": "Matches user role with channel's intended audience",
                    "field": "target_audience"
                },
                "goals": {
                    "weight": 0.10,
                    "description": "Matches user goals with channel description and purpose",
                    "field": "description"
                }
            }
        },
        "channels": channels
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    # Save with pretty formatting
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(channels)} channels to {json_path}")


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Load channels
    channels = load_channels_from_json()
    print(f"\nLoaded {len(channels)} channels from JSON")
    
    # Get metadata
    metadata = get_channel_metadata()
    print(f"\nMatching Criteria:")
    for criterion, info in metadata.get('matching_criteria', {}).items():
        print(f"  {criterion}: {info['weight']*100}% - {info['description']}")
    
    # Show sample channels
    print("\nSample Channels:")
    for channel in channels[:3]:
        print(f"  - #{channel['name']}")
        print(f"    Topics: {', '.join(channel['topics'])}")
        print(f"    Target: {channel['target_audience']}")
        print()
