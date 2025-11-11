# Data Flow Diagram

## 📁 Channel Data Source Evolution

### BEFORE (Hardcoded in Python)
```
src/test_data.py
  └─ get_mock_channels()
      └─ return [{"name": "python-beginners", ...}, ...]
          ↓
      Hardcoded list of 15 dictionaries
```

### AFTER (JSON-based)
```
data/channels.json                  ← External data file (easy to edit)
  │
  ├─ metadata (matching criteria weights)
  └─ channels[] (15 channels)
          ↓
src/data_loader.py
  └─ load_channels_from_json()
      └─ Reads JSON file
      └─ Returns list of dicts
          ↓
src/test_data.py
  └─ get_mock_channels()
      └─ Calls load_channels_from_json()
          ↓
src/main.py
  └─ channels = get_mock_channels()
      └─ Passes to orchestrator
```

## 🔄 Complete Data Flow Through System

```
┌──────────────────────────────────────────────────────────────┐
│ 1. DATA SOURCE                                               │
│    data/channels.json                                        │
│    ├─ 15 Discord channels                                    │
│    ├─ Each with: name, description, topics,                 │
│    │              target_audience, best_for_roles, etc.      │
│    └─ Metadata: matching criteria weights                   │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. DATA LOADING                                              │
│    src/data_loader.py                                        │
│    └─ load_channels_from_json()                             │
│       ├─ Opens data/channels.json                           │
│       ├─ Parses JSON                                         │
│       ├─ Extracts channels[] array                          │
│       └─ Returns List[Dict]                                  │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. TEST DATA WRAPPER                                         │
│    src/test_data.py                                          │
│    └─ get_mock_channels()                                   │
│       └─ Calls load_channels_from_json()                    │
│       └─ Returns same List[Dict]                            │
│          (Maintains backward compatibility)                  │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. MAIN APPLICATION                                          │
│    src/main.py                                               │
│    └─ main()                                                 │
│       ├─ channels = get_mock_channels()                     │
│       └─ await app.run_interactive(channels)                │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. ORCHESTRATOR                                              │
│    src/orchestrator.py                                       │
│    └─ AgentOrchestrator                                     │
│       ├─ Receives channels list                             │
│       └─ Passes to ChannelAnalyzerAgent                     │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ 6. USER PREFERENCE COLLECTION                                │
│    src/agents/user_preference_agent.py                       │
│    └─ Asks 4 questions:                                     │
│       ├─ What are your interests?                           │
│       ├─ What is your role?                                 │
│       ├─ What is your experience level?                     │
│       └─ What are your goals?                               │
│                                                              │
│    Collects user responses → preferences dict               │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ 7. CHANNEL ANALYSIS & MATCHING                               │
│    src/agents/channel_analyzer_agent.py                      │
│    └─ For each channel:                                     │
│       ├─ Combine preferences + channel data                 │
│       ├─ Send to LLM (GPT-4)                                │
│       ├─ LLM analyzes match on 4 criteria:                  │
│       │   • Interests (40% weight)                          │
│       │   • Experience Level (30% weight)                   │
│       │   • Role (20% weight)                               │
│       │   • Goals (10% weight)                              │
│       └─ Returns JSON: {match_score: 0.0-1.0, reasoning}    │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ 8. RANKING & RECOMMENDATION                                  │
│    src/agents/channel_analyzer_agent.py                      │
│    └─ _generate_recommendation_message()                    │
│       ├─ Sort channels by match_score (high to low)         │
│       ├─ Take top 3-5 channels                              │
│       ├─ Generate friendly message via LLM                  │
│       └─ Return recommendations to user                     │
└──────────────────────────────────────────────────────────────┘
```

## 🎯 Matching Criteria Mapping

How user preferences map to channel attributes:

```
USER PREFERENCES          CHANNEL ATTRIBUTES        WEIGHT
────────────────         ──────────────────        ──────
interests                topics[]                  40%
  ↓                        ↓
"Python, data"           ["python", "data science"]
                         Keyword matching


experience_level         target_audience           30%
  ↓                        ↓
"beginner"               "beginners"
                         Exact/fuzzy matching


role                     best_for_roles[]          20%
  ↓                        ↓
"student"                ["student", "learner"]
                         List membership


goals                    best_for_goals[] +        10%
  ↓                      description
"get a job"              ["career", "interview prep"]
                         Semantic matching
```

## 📊 Example: User → Channel Match

```
┌─────────────────────────────────────────────────────────┐
│ USER INPUT                                              │
├─────────────────────────────────────────────────────────┤
│ Interests: "Python programming and data science"       │
│ Role: "Student"                                         │
│ Experience Level: "beginner"                            │
│ Goals: "Learn data analysis and build portfolio"       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ CHANNEL: data-science-beginners                         │
├─────────────────────────────────────────────────────────┤
│ topics: ["data science", "python", "pandas"]            │
│ target_audience: "beginners"                            │
│ best_for_roles: ["student", "analyst"]                  │
│ best_for_goals: ["learning data analysis"]             │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ LLM ANALYSIS                                            │
├─────────────────────────────────────────────────────────┤
│ Interest Match: 0.95 × 0.40 = 0.38                      │
│ Level Match:    1.00 × 0.30 = 0.30                      │
│ Role Match:     1.00 × 0.20 = 0.20                      │
│ Goal Match:     0.90 × 0.10 = 0.09                      │
│ ────────────────────────────────                        │
│ TOTAL SCORE:    0.97 (97%)                              │
│                                                          │
│ VERDICT: ⭐⭐⭐⭐⭐ Excellent Match!                    │
└─────────────────────────────────────────────────────────┘
```

## 🔧 How to Modify Channel Data

### Option 1: Edit JSON directly
```bash
# Open in your favorite editor
notepad data/channels.json

# Add/modify channels in the "channels" array
# Each channel needs these fields:
{
  "name": "channel-name",
  "description": "What it's about",
  "topics": ["keyword1", "keyword2"],
  "activity_level": "low/medium/high",
  "target_audience": "beginners/intermediate/advanced",
  "best_for_roles": ["role1", "role2"],
  "best_for_goals": ["goal1", "goal2"]
}
```

### Option 2: Use Python to programmatically update
```python
from data_loader import load_channels_from_json, save_channels_to_json

# Load existing
channels = load_channels_from_json()

# Add a new channel
new_channel = {
    "name": "rust-programming",
    "description": "Learn Rust systems programming",
    "topics": ["rust", "systems", "performance"],
    "activity_level": "medium",
    "target_audience": "intermediate",
    "best_for_roles": ["systems programmer", "backend developer"],
    "best_for_goals": ["learning rust", "performance optimization"]
}
channels.append(new_channel)

# Save back
save_channels_to_json(channels)
```

### Option 3: Future - Fetch from Discord MCP
```python
# In channel_analyzer_agent.py
async def fetch_channels_from_mcp(self):
    # Connect to Discord MCP server
    channels = await mcp_client.get_channels()
    
    # Transform to our format
    formatted = [transform_mcp_channel(c) for c in channels]
    
    # Save to JSON for caching
    save_channels_to_json(formatted)
    
    return formatted
```

## 📈 Benefits of JSON-based Approach

✅ **Easy to Edit** - No Python knowledge needed to add channels  
✅ **Version Control** - Can track changes in Git  
✅ **Portable** - Can share/import channel lists  
✅ **Extensible** - Easy to add new fields  
✅ **Cacheable** - Can store fetched MCP data  
✅ **Testable** - Can swap different JSON files for testing  

## 📚 Key Files

| File | Purpose |
|------|---------|
| `data/channels.json` | Channel data store (15 channels + metadata) |
| `src/data_loader.py` | Loads/saves JSON data |
| `src/test_data.py` | Wrapper for backward compatibility |
| `src/agents/channel_analyzer_agent.py` | Matching logic |
| `MATCHING_CRITERIA.md` | Detailed explanation of matching algorithm |
