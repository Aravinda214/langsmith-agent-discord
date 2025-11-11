# Discord Integration Guide

## How to Deploy Agents to Real Discord Servers

Your current agents can be integrated into Discord in multiple ways to analyze real conversations and recommend channels in real-time.

---

## **Option 1: Discord Bot (Interactive Onboarding)**

### Overview
Create a Discord bot that DMs users or responds to commands to collect preferences and recommend channels.

### How It Works

```
User joins server → Bot sends DM → Asks onboarding questions → Recommends channels
                                              ↓
                                    OR user types: /find-channels
                                              ↓
                                    Bot starts conversation in DM
```

### Implementation Steps

#### 1. Install Discord.py
```bash
pip install discord.py
```

#### 2. Create Discord Bot Application
1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Go to "Bot" → Create Bot
4. Enable these **Privileged Gateway Intents**:
   - ✅ SERVER MEMBERS INTENT (to detect new members)
   - ✅ MESSAGE CONTENT INTENT (to read messages)
5. Copy the **Bot Token**
6. Add to `.env`:
   ```
   DISCORD_BOT_TOKEN=your_bot_token_here
   ```

#### 3. Invite Bot to Server
Generate OAuth2 URL with these permissions:
- Bot scope
- Permissions: Send Messages, Read Messages, Manage Roles (optional)

URL format:
```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8&scope=bot
```

#### 4. Create Discord Bot Code

**File:** `src/discord_bot.py`

```python
"""
Discord Bot Integration

This bot integrates the AI agents with Discord to:
1. Onboard new members via DM
2. Collect preferences through conversation
3. Recommend channels based on user interests
4. (Optional) Analyze user conversations to suggest channels
"""

import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

from config_loader import load_config
from data_loader import load_channels_from_json
from agents.user_preference_agent import UserPreferenceAgent
from agents.channel_analyzer_agent import ChannelAnalyzerAgent
# Or use ScaleDown versions:
# from agents.scaledown_user_preference_agent import ScaleDownUserPreferenceAgent
# from agents.scaledown_channel_analyzer_agent import ScaleDownChannelAnalyzerAgent

load_dotenv()

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Load config and agents
config = load_config()
channels_data = load_channels_from_json()

# Store active conversations (user_id -> conversation_state)
active_conversations = {}


class ConversationState:
    """Track conversation state for each user"""
    def __init__(self, user_id):
        self.user_id = user_id
        self.preference_agent = None
        self.channel_analyzer = None
        self.status = "not_started"  # not_started, collecting, analyzing, complete
        
    def initialize_agents(self):
        """Initialize agents for this user"""
        pref_config = config['agents']['user_preference_agent'].copy()
        pref_config['preference_questions'] = config['preference_questions']
        
        analyzer_config = config['agents']['channel_analyzer_agent'].copy()
        analyzer_config.update(config['channel_analysis'])
        
        self.preference_agent = UserPreferenceAgent(
            name=pref_config['name'],
            model_name=pref_config['model'],
            temperature=pref_config['temperature'],
            config=pref_config
        )
        
        self.channel_analyzer = ChannelAnalyzerAgent(
            name=analyzer_config['name'],
            model_name=analyzer_config['model'],
            temperature=analyzer_config['temperature'],
            config=analyzer_config
        )
        self.channel_analyzer.set_channels_data(channels_data)


@bot.event
async def on_ready():
    print(f'✅ Bot connected as {bot.user}')
    print(f'📊 Loaded {len(channels_data)} channels for recommendations')


@bot.event
async def on_member_join(member):
    """When a new member joins, send them a DM to start onboarding"""
    try:
        # Create conversation state
        conversation = ConversationState(member.id)
        conversation.initialize_agents()
        active_conversations[member.id] = conversation
        
        # Start preference collection
        result = await conversation.preference_agent.execute({'mode': 'start'})
        conversation.status = "collecting"
        
        # Send greeting via DM
        await member.send(result['message'])
        
    except discord.Forbidden:
        print(f"⚠️  Could not DM user {member.name} (DMs disabled)")
    except Exception as e:
        print(f"❌ Error onboarding {member.name}: {e}")


@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Handle DM conversations
    if isinstance(message.channel, discord.DMChannel):
        await handle_dm_conversation(message)


async def handle_dm_conversation(message):
    """Handle ongoing conversation in DMs"""
    user_id = message.author.id
    
    # Check if user has an active conversation
    if user_id not in active_conversations:
        # User messaged bot without being onboarded, start fresh
        await start_onboarding(message.author)
        return
    
    conversation = active_conversations[user_id]
    
    if conversation.status == "collecting":
        # Continue preference collection
        result = await conversation.preference_agent.execute({
            'mode': 'collect',
            'user_response': message.content
        })
        
        if result['status'] == 'complete':
            # Preferences collected, analyze channels
            conversation.status = "analyzing"
            await message.channel.send("🔍 Analyzing channels for you...")
            
            # Get recommendations
            analysis = await conversation.channel_analyzer.execute({
                'preferences': result['preferences']
            })
            
            # Send recommendations
            await send_recommendations(message.channel, analysis)
            conversation.status = "complete"
            
            # Clean up
            del active_conversations[user_id]
        else:
            # Send next question
            await message.channel.send(result['message'])


async def start_onboarding(user):
    """Start onboarding process for a user"""
    conversation = ConversationState(user.id)
    conversation.initialize_agents()
    active_conversations[user.id] = conversation
    
    result = await conversation.preference_agent.execute({'mode': 'start'})
    conversation.status = "collecting"
    
    await user.send(result['message'])


async def send_recommendations(channel, analysis):
    """Send channel recommendations to user"""
    # Create embed for nice formatting
    embed = discord.Embed(
        title="🎯 Recommended Channels for You",
        description=analysis['message'],
        color=discord.Color.blue()
    )
    
    # Add top channels
    for i, rec in enumerate(analysis['recommendations'][:5], 1):
        match_score = rec['analysis']['match_score']
        embed.add_field(
            name=f"{i}. #{rec['name']} ({match_score:.0%} match)",
            value=f"{rec['description']}\n*Why: {rec['analysis']['reasoning'][:100]}...*",
            inline=False
        )
    
    embed.set_footer(text=f"Found {len(analysis['recommendations'])} matching channels")
    
    await channel.send(embed=embed)


@bot.command(name='find-channels')
async def find_channels_command(ctx):
    """Command to manually start channel recommendation process"""
    if isinstance(ctx.channel, discord.DMChannel):
        await start_onboarding(ctx.author)
    else:
        await ctx.send("I'll DM you to learn about your interests! 📬")
        await start_onboarding(ctx.author)


@bot.command(name='reset')
async def reset_conversation(ctx):
    """Reset conversation state"""
    if ctx.author.id in active_conversations:
        del active_conversations[ctx.author.id]
        await ctx.send("✅ Conversation reset! Use `!find-channels` to start over.")
    else:
        await ctx.send("No active conversation to reset.")


# Run bot
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    if not TOKEN:
        print("❌ DISCORD_BOT_TOKEN not found in .env file")
    else:
        bot.run(TOKEN)
```

#### 5. Run the Bot

```bash
cd src
python discord_bot.py
```

---

## **Option 2: Real-Time Conversation Analysis**

### Overview
Analyze user messages in real-time to suggest channels based on what they talk about (passive recommendation).

### How It Works

```
User posts messages → Bot analyzes conversation history → Suggests relevant channels
```

### Implementation

**File:** `src/discord_analyzer_bot.py`

```python
"""
Passive Channel Recommendation Bot

Analyzes user conversations over time and suggests channels they might be interested in.
"""

import discord
from discord.ext import commands, tasks
from collections import defaultdict
import os
from dotenv import load_dotenv

from config_loader import load_config
from data_loader import load_channels_from_json
from agents.channel_analyzer_agent import ChannelAnalyzerAgent

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Track user message history
user_messages = defaultdict(list)  # user_id -> [messages]
MESSAGE_HISTORY_LIMIT = 50

config = load_config()
channels_data = load_channels_from_json()


def initialize_analyzer():
    """Initialize channel analyzer agent"""
    analyzer_config = config['agents']['channel_analyzer_agent'].copy()
    analyzer_config.update(config['channel_analysis'])
    
    analyzer = ChannelAnalyzerAgent(
        name=analyzer_config['name'],
        model_name=analyzer_config['model'],
        temperature=analyzer_config['temperature'],
        config=analyzer_config
    )
    analyzer.set_channels_data(channels_data)
    return analyzer


analyzer = initialize_analyzer()


@bot.event
async def on_ready():
    print(f'✅ Analyzer Bot connected as {bot.user}')
    print('👂 Listening to conversations...')


@bot.event
async def on_message(message):
    # Ignore bots
    if message.author.bot:
        return
    
    # Track message history (for analysis)
    user_id = message.author.id
    user_messages[user_id].append(message.content)
    
    # Keep only recent messages
    if len(user_messages[user_id]) > MESSAGE_HISTORY_LIMIT:
        user_messages[user_id] = user_messages[user_id][-MESSAGE_HISTORY_LIMIT:]
    
    # Process commands
    await bot.process_commands(message)


@bot.command(name='suggest-channels')
async def suggest_channels(ctx):
    """Analyze user's conversation history and suggest channels"""
    user_id = ctx.author.id
    
    if user_id not in user_messages or len(user_messages[user_id]) < 5:
        await ctx.send("I haven't seen enough messages from you yet to make good recommendations. Keep chatting! 💬")
        return
    
    await ctx.send("🔍 Analyzing your conversation history...")
    
    # Analyze message history to extract interests
    message_text = " ".join(user_messages[user_id])
    
    # Extract preferences from conversation
    # (Simplified - you could use an LLM to extract this properly)
    inferred_preferences = {
        'interests': message_text[:500],  # Use recent messages as interests
        'role': 'Discord Member',
        'experience_level': 'intermediate',  # Could be inferred
        'goals': 'Engage with community'
    }
    
    # Get recommendations
    try:
        analysis = await analyzer.execute({
            'preferences': inferred_preferences
        })
        
        # Send recommendations
        embed = discord.Embed(
            title="📊 Channel Suggestions Based on Your Activity",
            description="Based on what you've been talking about, here are some channels you might like:",
            color=discord.Color.green()
        )
        
        for i, rec in enumerate(analysis['recommendations'][:3], 1):
            match_score = rec['analysis']['match_score']
            embed.add_field(
                name=f"{i}. #{rec['name']} ({match_score:.0%} match)",
                value=rec['description'],
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error analyzing: {e}")


# Run bot
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    if not TOKEN:
        print("❌ DISCORD_BOT_TOKEN not found in .env file")
    else:
        bot.run(TOKEN)
```

---

## **Option 3: Discord MCP Server (Advanced)**

Use Model Context Protocol to directly access Discord data.

### Overview
Connect to Discord via MCP, fetch real channel data, and analyze them.

### Implementation

1. **Set up Discord MCP Server** (if available)
2. **Modify agents** to fetch real Discord channels instead of mock data
3. **Use MCP protocol** to read messages, channels, and members

**File:** `src/agents/channel_analyzer_agent.py` (modification)

```python
async def fetch_channels_from_mcp(self) -> List[Dict[str, Any]]:
    """
    Fetch Discord channels from MCP server.
    
    This would integrate with the Discord MCP server
    to get real Discord channel data.
    """
    if not self.mcp_enabled:
        self.logger.warning("MCP is not enabled, using mock data")
        return []
    
    # TODO: Implement actual MCP server communication
    # Example:
    # async with mcp_client.connect("discord") as server:
    #     channels = await server.list_channels(guild_id=...)
    #     return channels
    
    self.logger.info("MCP integration not yet implemented")
    return []
```

---

## **Comparison of Approaches**

| Feature | Discord Bot (DM) | Conversation Analysis | MCP Server |
|---------|------------------|----------------------|------------|
| **Interaction** | Active (DMs) | Passive (suggestions) | Hybrid |
| **User Control** | High | Medium | High |
| **Privacy** | Better (1-on-1) | Moderate (analyzes public msgs) | Best |
| **Complexity** | Low | Medium | High |
| **Best For** | Onboarding | Existing users | Advanced integrations |

---

## **Quick Start: Testing Discord Bot**

### 1. Update .env
```bash
OPENAI_API_KEY=your_openai_key
SCALEDOWN_API_KEY=your_scaledown_key
DISCORD_BOT_TOKEN=your_discord_bot_token
LANGSMITH_API_KEY=your_langsmith_key
```

### 2. Run Bot
```bash
cd src
python discord_bot.py
```

### 3. Test Commands in Discord
- Join a server with the bot
- Type: `!find-channels`
- Answer questions in DM
- Get recommendations!

---

## **Real-Time Enhancements**

### 1. Channel Auto-Assignment
After recommendations, bot can automatically assign user to channels:

```python
# Add to send_recommendations function
for rec in analysis['recommendations'][:3]:
    channel = discord.utils.get(ctx.guild.channels, name=rec['name'])
    if channel:
        await channel.set_permissions(ctx.author, read_messages=True)
        await ctx.send(f"✅ Added you to #{rec['name']}")
```

### 2. Periodic Re-Analysis
Every week, re-analyze user activity and suggest new channels:

```python
@tasks.loop(hours=168)  # Weekly
async def weekly_channel_suggestions():
    for guild in bot.guilds:
        for member in guild.members:
            # Re-analyze and suggest
            pass
```

### 3. Analytics Dashboard
Track which channels users engage with after recommendations:

```python
# Track engagement
user_engagement = {}  # user_id -> {channel_id: message_count}

@bot.event
async def on_message(message):
    user_id = message.author.id
    channel_id = message.channel.id
    user_engagement[user_id][channel_id] = user_engagement[user_id].get(channel_id, 0) + 1
```

---

## **Production Considerations**

### 1. Rate Limiting
Discord has rate limits - implement queues:
```python
from asyncio import Queue
message_queue = Queue()
```

### 2. Caching
Cache recommendations for users:
```python
from functools import lru_cache
from datetime import datetime, timedelta

recommendation_cache = {}  # user_id -> (timestamp, recommendations)
CACHE_DURATION = timedelta(hours=24)
```

### 3. Error Handling
Handle Discord API errors gracefully:
```python
try:
    await member.send(greeting)
except discord.Forbidden:
    # User has DMs disabled
    await guild.system_channel.send(f"{member.mention}, please enable DMs!")
```

### 4. Database Storage
Store user preferences and recommendations:
```python
# Use SQLite, PostgreSQL, or MongoDB
import sqlite3
conn = sqlite3.connect('user_preferences.db')
```

---

## **Next Steps**

1. ✅ Choose an integration approach (Bot recommended)
2. ✅ Create Discord application and get bot token
3. ✅ Implement `discord_bot.py` using the code above
4. ✅ Test in a private Discord server
5. ✅ Monitor LangSmith for bot interactions
6. ✅ Deploy to production server (Heroku, Railway, AWS)

---

**Generated:** November 11, 2025  
**Status:** Ready for Discord deployment
