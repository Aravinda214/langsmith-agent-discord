"""
Discord Channel Extractor

This script helps you extract channel information from a Discord server
and convert it into the format needed for the Channel Analyzer Agent.

You'll need:
1. Discord Bot Token (create at https://discord.com/developers/applications)
2. Server ID (right-click server name with Developer Mode enabled)

Steps to use:
1. Create a Discord bot at https://discord.com/developers/applications
2. Enable "Message Content Intent" and "Server Members Intent" in Bot settings
3. Invite bot to ScaleDown server with these permissions:
   - Read Messages/View Channels
   - Read Message History
4. Get the Server ID (right-click server, Copy ID - enable Developer Mode in Settings)
5. Run this script
"""

import discord
import json
import os
from dotenv import load_dotenv
import asyncio
from typing import List, Dict, Any

load_dotenv()

# Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')  # Add to your .env file
GUILD_ID = None  # Will prompt user to enter


class ChannelExtractor:
    """Extract channel information from Discord server."""
    
    def __init__(self, token: str):
        """Initialize the Discord client."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        self.client = discord.Client(intents=intents)
        self.token = token
        self.channels_data = []
        
        @self.client.event
        async def on_ready():
            print(f'✅ Logged in as {self.client.user}')
            await self.extract_channels()
            await self.client.close()
    
    async def extract_channels(self):
        """Extract all text channels from the guild."""
        guild_id = input("\n🔑 Enter Discord Server ID (right-click server name → Copy ID): ")
        
        try:
            guild = self.client.get_guild(int(guild_id))
            if not guild:
                print(f"❌ Could not find server with ID: {guild_id}")
                print("   Make sure the bot is invited to the server!")
                return
            
            print(f"\n📊 Extracting channels from: {guild.name}")
            print("=" * 60)
            
            # Get all text channels
            text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
            
            print(f"\n✅ Found {len(text_channels)} text channels")
            
            for channel in text_channels:
                channel_info = await self.analyze_channel(channel)
                self.channels_data.append(channel_info)
                print(f"  ✓ {channel.name}")
            
            # Save to file
            self.save_channels()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def analyze_channel(self, channel: discord.TextChannel) -> Dict[str, Any]:
        """
        Analyze a channel and extract relevant information.
        
        Args:
            channel: Discord text channel
            
        Returns:
            Dictionary with channel information
        """
        # Get channel description/topic
        description = channel.topic or "No description available"
        
        # Try to infer topics from channel name and description
        topics = self.infer_topics(channel.name, description)
        
        # Estimate activity level from recent messages
        activity_level = await self.estimate_activity(channel)
        
        # Categorize the channel
        category_name = channel.category.name if channel.category else "Uncategorized"
        
        return {
            "name": channel.name,
            "description": description,
            "topics": topics,
            "category": category_name,
            "activity_level": activity_level,
            "member_count": len(channel.members) if hasattr(channel, 'members') else 0
        }
    
    def infer_topics(self, channel_name: str, description: str) -> List[str]:
        """
        Infer topics from channel name and description.
        
        Args:
            channel_name: Name of the channel
            description: Channel description/topic
            
        Returns:
            List of inferred topics
        """
        topics = []
        text = f"{channel_name} {description}".lower()
        
        # Common topic keywords
        topic_keywords = {
            "python": ["python", "py"],
            "javascript": ["javascript", "js", "node"],
            "web": ["web", "frontend", "backend"],
            "ai": ["ai", "ml", "machine learning", "artificial intelligence"],
            "data": ["data", "analytics", "database"],
            "general": ["general", "chat", "discussion"],
            "help": ["help", "support", "questions"],
            "projects": ["projects", "showcase", "portfolio"],
            "resources": ["resources", "learning", "tutorials"],
            "beginners": ["beginner", "newbie", "starter"],
            "advanced": ["advanced", "expert", "pro"],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                topics.append(topic)
        
        # If no topics found, use channel name
        if not topics:
            topics.append(channel_name.replace('-', ' '))
        
        return topics[:5]  # Limit to 5 topics
    
    async def estimate_activity(self, channel: discord.TextChannel) -> str:
        """
        Estimate channel activity level from recent messages.
        
        Args:
            channel: Discord text channel
            
        Returns:
            Activity level: "high", "medium", or "low"
        """
        try:
            # Try to fetch last 100 messages
            messages = []
            async for msg in channel.history(limit=100):
                messages.append(msg)
            
            if len(messages) >= 50:
                return "high"
            elif len(messages) >= 20:
                return "medium"
            else:
                return "low"
        except discord.Forbidden:
            # No permission to read messages
            return "unknown"
        except Exception:
            return "unknown"
    
    def save_channels(self):
        """Save extracted channels to JSON file."""
        output_file = "../data/scaledown_channels.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.channels_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n" + "=" * 60)
        print(f"✅ Saved {len(self.channels_data)} channels to: {output_file}")
        print("=" * 60)
        
        # Also print a summary
        print("\n📋 Channel Summary:")
        print("-" * 60)
        for ch in self.channels_data[:5]:  # Show first 5
            print(f"\n#{ch['name']}")
            print(f"  Description: {ch['description'][:80]}...")
            print(f"  Topics: {', '.join(ch['topics'])}")
            print(f"  Activity: {ch['activity_level']}")
        
        if len(self.channels_data) > 5:
            print(f"\n... and {len(self.channels_data) - 5} more channels")
    
    def run(self):
        """Start the bot."""
        if not self.token:
            print("❌ DISCORD_BOT_TOKEN not found in .env file!")
            print("\nSteps to get a bot token:")
            print("1. Go to https://discord.com/developers/applications")
            print("2. Click 'New Application'")
            print("3. Go to 'Bot' section")
            print("4. Click 'Reset Token' and copy it")
            print("5. Add to .env: DISCORD_BOT_TOKEN=your_token_here")
            return
        
        print("🤖 Starting Discord Channel Extractor...")
        print("=" * 60)
        self.client.run(self.token)


async def manual_extraction():
    """
    Manual extraction method if you don't want to use a bot.
    
    You can manually fill in channel information based on what you see
    in the ScaleDown Discord server.
    """
    print("\n📝 Manual Channel Extraction")
    print("=" * 60)
    print("\nSince you've joined the ScaleDown Discord, you can manually")
    print("fill in channel information by observing the server.")
    print("\nFor each channel, note:")
    print("  - Channel name")
    print("  - Channel description/topic")
    print("  - Topics discussed")
    print("  - Activity level")
    
    channels = []
    
    while True:
        print("\n" + "-" * 60)
        name = input("Channel name (or 'done' to finish): ").strip()
        
        if name.lower() == 'done':
            break
        
        description = input("Description: ").strip()
        topics = input("Topics (comma-separated): ").strip().split(',')
        topics = [t.strip() for t in topics if t.strip()]
        activity = input("Activity level (high/medium/low): ").strip().lower()
        
        channels.append({
            "name": name,
            "description": description,
            "topics": topics,
            "activity_level": activity,
            "category": "ScaleDown"
        })
        
        print(f"✅ Added #{name}")
    
    # Save to file
    output_file = "../data/scaledown_channels.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(channels, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(channels)} channels to: {output_file}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("Discord Channel Extractor for ScaleDown")
    print("=" * 60)
    
    print("\nChoose extraction method:")
    print("1. Automated (using Discord bot)")
    print("2. Manual (fill in channel details yourself)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == '1':
        extractor = ChannelExtractor(DISCORD_BOT_TOKEN)
        extractor.run()
    elif choice == '2':
        asyncio.run(manual_extraction())
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()
