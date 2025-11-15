# Command Reference Guide

Complete reference for all commands to run, test, and compare agents in this project.

---

## **Table of Contents**
1. [Setup Commands](#setup-commands)
2. [Interactive Mode](#interactive-mode)
3. [Testing Commands](#testing-commands)
4. [Comparison Commands](#comparison-commands)
5. [Development Commands](#development-commands)
6. [Discord Bot Commands](#discord-bot-commands)

---

## **Setup Commands**

### Initial Setup
```bash
# Create virtual environment
python -m venv aiagent

# Activate virtual environment (Windows)
aiagent\Scripts\activate

# Activate virtual environment (Mac/Linux)
source aiagent/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
```bash
# Create .env file (copy from template)
cp .env.example .env

# Edit .env file with your API keys
notepad .env  # Windows
nano .env     # Mac/Linux
```

Required environment variables:
```env
OPENAI_API_KEY=sk-...
SCALEDOWN_API_KEY=your_scaledown_key
LANGSMITH_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=discord-channel-selector
```

---

## **Interactive Mode**

### Run with Standard Agents (No Compression)
```bash
cd src
python main.py --agent standard
```
OR (standard is default):
```bash
python main.py
```

**What it does:**
- ✅ Starts interactive conversation
- ✅ Asks onboarding questions
- ✅ Collects user preferences
- ✅ Recommends Discord channels
- ✅ Uses GPT-4o directly (no compression)
- ✅ Logged in LangSmith

**Output:**
```
Starting Discord Channel Selector with STANDARD agents...
✅ Standard agents loaded!
Discord Channel Selector initialized successfully!
============================================================

🤖 Discord Channel Selector - Interactive Mode
============================================================

🤖 Bot: Hello and welcome! I'm here to help you find...
```



**What it does:**
- ✅ Same interactive experience as standard
- ✅ Uses ScaleDown API for prompt compression
- ✅ Reduces token usage by ~36%
- ✅ Logged in LangSmith with compression metrics

**Output:**
```
Starting Discord Channel Selector with SCALEDOWN agents...
🔄 Switching to ScaleDown agents...
✅ ScaleDown agents loaded!
Discord Channel Selector initialized successfully!
```

---

## **Testing Commands**

### Test Single Agent (Manual Testing)

#### Test Standard Agent
```bash
cd src
python test_single_agent.py --agent standard
```

Optional: Specify test persona
```bash
python test_single_agent.py --agent standard --persona beginner
```

**Available personas:**
- `beginner` - Python Beginner
- `senior` - Senior Developer

**What it does:**
- Tests ONLY the standard agent
- Shows greeting, channel analysis, recommendations
- Displays estimated token usage
- No comparison, minimal API usage

**Output:**
```
================================================================================
SINGLE AGENT TESTER
================================================================================

Agent Type: STANDARD
Test Persona: Python Beginner

📋 Initializing agents...
📤 Step 1: Getting greeting...
💬 Greeting: Hello there! 😊 I'm thrilled to help you...

🔍 Step 2: Analyzing channels...
✅ ANALYSIS COMPLETE

📊 Results:
   Total channels analyzed: 15
   Channels recommended: 4

🎯 Top 3 Recommendations:
   1. #data-science-beginners (score: 0.90)
   2. #python-beginners (score: 0.85)
   3. #student-projects (score: 0.80)

📊 Estimated Token Usage (Standard):
   Estimated total: ~2,112
```

#### Test ScaleDown Agent
```bash
cd src
python test_single_agent.py --agent scaledown
```

**What it does:**
- Tests ONLY the ScaleDown agent
- Shows compression metrics
- Displays actual token savings
- Minimal API usage for debugging

**Output:**
```
================================================================================
SINGLE AGENT TESTER
================================================================================

Agent Type: SCALEDOWN
Test Persona: Python Beginner

📋 Initializing ScaleDown agents...

📤 Step 1: Getting greeting with compression...

💬 Greeting: Hello and welcome! I'm here to help you find...

📊 Compression Stats (Greeting):
   Original tokens: 60
   Compressed tokens: 43
   Tokens saved: 17 (28.3%)
   Compression time: 1.22s

🔍 Step 2: Analyzing channels with compression...

✅ ANALYSIS COMPLETE

📊 Compression Summary (Total):
   Total original tokens: 290
   Total compressed tokens: 185
   Total saved: 105 (36.2%)
```

### Test ScaleDown Compression (No OpenAI)
```bash
cd src
python test_scaledown_compression.py
```

**What it does:**
- Tests ONLY ScaleDown compression
- Does NOT call OpenAI (saves API credits)
- Shows compression at different rates
- Useful for debugging compression issues

**Output:**
```
================================================================================
SCALEDOWN COMPRESSION TESTER
================================================================================

Testing compression with different rates...

📊 Compression Rate: auto
   Original tokens: 290
   Compressed tokens: 185
   Compression: 36.2%
   ✅ Success

📊 Compression Rate: 0.3 (30% target)
   Original tokens: 290
   Compressed tokens: 203
   Compression: 30.0%
   ✅ Success
```

---

## **Comparison Commands**

### Full Agent Comparison
```bash
cd src
python compare_agents.py
```

**What it does:**
- Runs BOTH standard and ScaleDown agents
- Compares across multiple test cases (currently 2)
- Measures: tokens, latency, cost, accuracy
- Generates comparison_results.json
- Logs metrics to LangSmith

**Output:**
```
================================================================================
AGENT COMPARISON: Standard vs ScaleDown
================================================================================

Running 2 test cases...

================================================================================
TEST CASE 1: Python Beginner
================================================================================

User Profile: Learning Python programming and data analysis...

[1/2] Running STANDARD agents...
[2/2] Running SCALEDOWN agents...

📊 Results:
  Standard Agent:
    - Tokens: 2,112
    - Cost: $0.0053
    - Time: 2.5s
    - Top Channel: #data-science-beginners

  ScaleDown Agent:
    - Compressed Tokens: 1,348
    - Cost: $0.0034
    - Time: 2.8s
    - Top Channel: #data-science-beginners

  📈 Comparison:
    - Token Savings: 764 (36.2%)
    - Cost Savings: $0.0019 (35.8%)
    - Latency Diff: +0.3s
    - ✅ Same top recommendation

================================================================================
FINAL SUMMARY
================================================================================

Total Test Cases: 2
Avg Token Savings: 36.1%
Avg Cost Savings: 35.9%
Accuracy Match: 100% (2/2 cases)

💾 Results saved to: comparison_results.json
```

### View Comparison Results
```bash
# View JSON results
type comparison_results.json         # Windows
cat comparison_results.json          # Mac/Linux

# Pretty print JSON
python -m json.tool comparison_results.json
```

---

## **Development Commands**

### Extract Real Discord Channels
```bash
cd src
python extract_discord_channels.py
```

**What it does:**
- Extracts channel information from a Discord server
- Two modes: Automated (bot) or Manual (type in details)
- Saves to `data/scaledown_channels.json`
- Use this to get real ScaleDown Discord channels

**Output:**
```
Choose extraction method:
1. Automated (using Discord bot)
2. Manual (fill in channel details yourself)

Enter choice (1 or 2): 2

📝 Manual Channel Extraction
Channel name: api-help
Description: Get help with ScaleDown API
Topics: scaledown, api, support
Activity level: high
✅ Added #api-help
```

### Run All Unit Tests (if available)
```bash
cd src
python run_tests.py
```

### Quick Demo
```bash
cd src
python quick_demo.py
```

### Check Imports
```bash
cd src
python -c "from agents.base_agent import BaseAgent; from agents.user_preference_agent import UserPreferenceAgent; from agents.channel_analyzer_agent import ChannelAnalyzerAgent; from orchestrator import AgentOrchestrator; print('✅ All imports successful')"
```

### Validate Channel Data
```bash
cd src
python data_loader.py
```

**Output:**
```
✅ Loaded 15 channels from data/channels.json

Channels:
  - #python-beginners: For those just starting with Python
  - #python-advanced: Advanced Python concepts and patterns
  - #web-development: Web development with modern frameworks
  ...
```

### Check Configuration
```bash
cd src
python config_loader.py
```

---

## **Discord Bot Commands**

### Run Discord Bot (Standard Agents)
```bash
cd src
python discord_bot.py
```

**What it does:**
- Connects bot to Discord
- Listens for new members
- Sends onboarding DM
- Collects preferences
- Recommends channels

**Discord Commands:**
- `!find-channels` - Start channel recommendation
- `!reset` - Reset conversation state

### Run Discord Analyzer Bot (Passive Analysis)
```bash
cd src
python discord_analyzer_bot.py
```

**Discord Commands:**
- `!suggest-channels` - Analyze conversation history and suggest channels

---

## **Common Workflows**

### 1. First Time Setup
```bash
# Clone/download project
cd langsmith-agent-discord

# Create environment
python -m venv aiagent
aiagent\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env with your API keys

# Test installation
cd src
python main.py --agent standard
```

### 2. Testing During Development
```bash
# Test compression only (no OpenAI charges)
python test_scaledown_compression.py

# Test single agent (minimal OpenAI usage)
python test_single_agent.py --agent scaledown

# Full comparison (uses both agents)
python compare_agents.py
```

### 3. Interactive Demo for Stakeholders
```bash
# Show standard approach
python main.py --agent standard

# Show comparison results
type comparison_results.json
```

### 4. Discord Deployment
```bash
# Set up Discord bot token in .env
DISCORD_BOT_TOKEN=your_token_here

# Run bot
python discord_bot.py

# Invite to server and test
# Use !find-channels in Discord
```

---

## **LangSmith Integration**

All commands automatically log to LangSmith when properly configured.

### View Traces
1. Go to https://smith.langchain.com
2. Select project: `discord-channel-selector`
3. View recent runs

### Filter by Agent Type
- Standard agents: Look for `user_preference_agent_execute`, `channel_analyzer_execute`
- ScaleDown agents: Look for `scaledown_collect_preferences`, `scaledown_analyze_channels`

### View Comparison Metrics
Check console output after running `compare_agents.py` - metrics are logged with structured data.

---

## **Troubleshooting Commands**

### Check Python Version
```bash
python --version
# Should be Python 3.10 or higher
```

### Verify API Keys
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OpenAI:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'); print('ScaleDown:', 'SET' if os.getenv('SCALEDOWN_API_KEY') else 'NOT SET'); print('LangSmith:', 'SET' if os.getenv('LANGSMITH_API_KEY') else 'NOT SET')"
```

### Test OpenAI Connection
```bash
python -c "import os; from dotenv import load_dotenv; from langchain_openai import ChatOpenAI; load_dotenv(); model = ChatOpenAI(model='gpt-4o'); print('✅ OpenAI connection successful')"
```

### Test ScaleDown API
```bash
cd src
python -c "import os; import requests; from dotenv import load_dotenv; load_dotenv(); url = 'https://api.scaledown.xyz/compress/raw/'; headers = {'Authorization': f'Bearer {os.getenv(\"SCALEDOWN_API_KEY\")}'}; payload = {'context': 'Test', 'prompt': 'Hello', 'model': 'gpt-4o', 'scaledown': {'rate': 'auto'}}; r = requests.post(url, headers=headers, json=payload); print('✅ ScaleDown API working' if r.status_code == 200 else f'❌ Error: {r.status_code}')"
```

### Clear Python Cache
```bash
# Windows
del /s /q __pycache__
del /s /q *.pyc

# Mac/Linux
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

---

## **File Structure Reference**

```
langsmith-agent-discord/
├── src/
│   ├── main.py                          # Main entry point
│   ├── orchestrator.py                  # Agent coordinator
│   ├── compare_agents.py                # Comparison framework
│   ├── test_single_agent.py             # Single agent testing
│   ├── test_scaledown_compression.py    # Compression testing
│   ├── discord_bot.py                   # Discord bot (interactive)
│   ├── discord_analyzer_bot.py          # Discord bot (passive)
│   ├── config_loader.py                 # Configuration loader
│   ├── data_loader.py                   # Channel data loader
│   ├── test_data.py                     # Test personas
│   └── agents/
│       ├── base_agent.py                # Base agent class
│       ├── user_preference_agent.py     # Standard preference agent
│       ├── channel_analyzer_agent.py    # Standard analyzer agent
│       ├── scaledown_base_agent.py      # ScaleDown base class
│       ├── scaledown_user_preference_agent.py
│       └── scaledown_channel_analyzer_agent.py
├── data/
│   └── channels.json                    # Discord channel catalog
├── config.yaml                          # Agent configurations
├── .env                                 # API keys (create from .env.example)
├── requirements.txt                     # Python dependencies
└── comparison_results.json              # Latest comparison results
```

---

## **Quick Command Summary**

| Task | Command |
|------|---------|
| **Extract ScaleDown Channels** | `python extract_discord_channels.py` |
| **Interactive (Standard)** | `python main.py --agent standard` |
| **Interactive (ScaleDown)** | `python main.py --agent scaledown` |
| **Test Standard Only** | `python test_single_agent.py --agent standard` |
| **Test ScaleDown Only** | `python test_single_agent.py --agent scaledown` |
| **Test Compression** | `python test_scaledown_compression.py` |
| **Full Comparison** | `python compare_agents.py` |
| **Discord Bot** | `python discord_bot.py` |
| **View Results** | `type comparison_results.json` |

---

## **Tips & Best Practices**

### 1. Cost Management
- Use `test_scaledown_compression.py` first (no OpenAI charges)
- Use `test_single_agent.py` for debugging (minimal API usage)
- Only use `compare_agents.py` when ready (uses both agents)

### 2. Testing Workflow
```bash
# 1. Test compression first (free)
python test_scaledown_compression.py

# 2. Test one agent (cheap)
python test_single_agent.py --agent scaledown

# 3. Run comparison when confident (more expensive)
python compare_agents.py
```

### 3. Reducing Test Cases
Edit `src/test_data.py` to enable/disable test cases:
```python
# Comment out test cases you don't need
# {
#     "name": "Career Switcher",
#     "preferences": { ... }
# },
```

### 4. Monitoring in LangSmith
- Always check LangSmith UI after testing
- Look for token usage patterns
- Compare standard vs ScaleDown traces
- Check for errors or warnings

---

**Last Updated:** November 11, 2025  
**Version:** 1.0  
**Project:** Discord Channel Selector with ScaleDown Integration
