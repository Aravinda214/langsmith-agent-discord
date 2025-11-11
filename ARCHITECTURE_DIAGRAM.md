# Discord Channel Selector - Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                             │
│                    (Discord / CLI Interface)                         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AGENT ORCHESTRATOR                              │
│                  (Coordinates Multi-Agent Workflow)                  │
└───────────────┬──────────────────────────────┬──────────────────────┘
                │                              │
                ▼                              ▼
┌───────────────────────────┐    ┌────────────────────────────────────┐
│  USER PREFERENCE AGENT    │    │   CHANNEL ANALYZER AGENT           │
│                           │    │                                    │
│  • Greets user            │    │  • Receives user preferences       │
│  • Asks onboarding Qs     │    │  • Analyzes 15+ channels           │
│  • Validates responses    │───▶│  • Scores each channel (0.0-1.0)  │
│  • Extracts preferences   │    │  • Returns top 3-5 matches         │
└───────────┬───────────────┘    └──────────────┬─────────────────────┘
            │                                   │
            │                                   │
            └──────────┬────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │     TWO IMPLEMENTATION MODES      │
        └──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────────┐        ┌──────────────────────┐
│ STANDARD AGENTS  │        │  SCALEDOWN AGENTS    │
│                  │        │                      │
│ Direct GPT-4o    │        │ ScaleDown API        │
│ API Calls        │        │ + GPT-4o             │
│                  │        │                      │
│ No Compression   │        │ Prompt Compression   │
│                  │        │ (36% token savings)  │
└────────┬─────────┘        └──────────┬───────────┘
         │                             │
         └──────────┬──────────────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │   EXTERNAL APIS      │
         └─────────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌──────────────────────┐
│  OpenAI API     │   │  ScaleDown API       │
│  (GPT-4o)       │   │  (Compression)       │
│                 │   │                      │
│  • Processes    │   │  • Compresses        │
│    prompts      │   │    context           │
│  • Generates    │   │  • Reduces tokens    │
│    responses    │   │  • Preserves meaning │
│  • Returns      │   │  • Returns           │
│    token stats  │   │    compression stats │
└─────────────────┘   └──────────────────────┘
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │   LANGSMITH          │
         │   (Monitoring)       │
         │                      │
         │  • Traces all runs   │
         │  • Logs prompts      │
         │  • Tracks tokens     │
         │  • Measures latency  │
         │  • A/B comparison    │
         └─────────────────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │   DATA SOURCES       │
         └─────────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
┌──────────────┐      ┌─────────────────┐
│ channels.json│      │  config.yaml    │
│              │      │                 │
│ 15 Discord   │      │ Agent settings  │
│ channels     │      │ Model configs   │
│ with metadata│      │ Matching rules  │
└──────────────┘      └─────────────────┘
```

## Data Flow

```
1. USER INPUT → Orchestrator
   ↓
2. User Preference Agent
   • Mode: "start" → Generates greeting
   • Mode: "collect" → Asks questions → Validates responses
   ↓
3. Collected Preferences (JSON)
   {
     "interests": "...",
     "role": "...",
     "experience_level": "...",
     "goals": "..."
   }
   ↓
4. Channel Analyzer Agent
   • Loads 15 channels from channels.json
   • For each channel: Scores match (0.0-1.0)
   • Sorts by score
   • Returns top 3-5 recommendations
   ↓
5. USER OUTPUT
   • Personalized message
   • Top channel recommendations with reasoning
   • Match scores
```

## Token Flow Comparison

### Standard Flow:
```
User Input → Full Prompt (1000 tokens) → GPT-4o → Response
                                          ↓
                                     Cost: $X
                                     Latency: Y seconds
```

### ScaleDown Flow:
```
User Input → Full Prompt (1000 tokens) → ScaleDown API → Compressed (640 tokens)
                                              ↓
                                          GPT-4o → Response
                                              ↓
                                         Cost: $X * 0.64
                                         Latency: Y + compression time
                                         Savings: 36%
```

## Matching Algorithm

```
Channel Score = Weighted Sum of:
  ┌────────────────────────────┐
  │ Interests Match:     40%   │ ← Topics alignment
  │ Experience Match:    30%   │ ← Beginner/Intermediate/Advanced
  │ Role Match:          20%   │ ← Student/Developer/etc.
  │ Goals Match:         10%   │ ← Career/Learning objectives
  └────────────────────────────┘
         ↓
  Final Score (0.0 - 1.0)
         ↓
  Minimum threshold: 0.6
         ↓
  Top 5 recommendations
```

## Key Metrics Tracked

| Metric | Standard | ScaleDown | Benefit |
|--------|----------|-----------|---------|
| **Tokens** | ~2,100 | ~1,400 | 36% reduction |
| **Cost** | $0.005 | $0.003 | 40% cheaper |
| **Latency** | 2.5s | 2.8s | +0.3s (compression overhead) |
| **Accuracy** | ✓ | ✓ | Same recommendations |

## Technology Stack

- **Language:** Python 3.10+
- **LLM:** OpenAI GPT-4o
- **Compression:** ScaleDown API (rate=auto)
- **Framework:** LangChain (agent orchestration)
- **Monitoring:** LangSmith (tracing & metrics)
- **Data Format:** JSON (channels), YAML (config)
- **Testing:** Custom comparison framework

## File Structure

```
langsmith-agent-discord/
├── src/
│   ├── agents/
│   │   ├── base_agent.py                    # Base class
│   │   ├── user_preference_agent.py         # Standard user agent
│   │   ├── channel_analyzer_agent.py        # Standard analyzer
│   │   ├── scaledown_base_agent.py          # ScaleDown base
│   │   ├── scaledown_user_preference_agent.py
│   │   └── scaledown_channel_analyzer_agent.py
│   ├── orchestrator.py                      # Multi-agent coordinator
│   ├── compare_agents.py                    # A/B testing framework
│   ├── main.py                              # Interactive demo
│   └── test_data.py                         # Test personas
├── data/
│   └── channels.json                        # Channel catalog
├── config.yaml                              # Agent configurations
└── .env                                     # API keys
```

---

**Generated:** November 11, 2025  
**Version:** 1.0
