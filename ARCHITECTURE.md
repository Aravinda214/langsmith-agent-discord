# Architecture & Design Documentation

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│                    (CLI / Programmatic API)                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Main Application                            │
│                  (DiscordChannelSelector)                        │
│  - Configuration Loading                                         │
│  - Logging Setup                                                 │
│  - High-level Orchestration                                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                            │
│  - Workflow Coordination                                         │
│  - Agent Lifecycle Management                                    │
│  - Data Flow Between Agents                                      │
└────────────┬───────────────────────────┬────────────────────────┘
             │                           │
             ▼                           ▼
┌────────────────────────┐    ┌─────────────────────────┐
│  UserPreferenceAgent   │    │  ChannelAnalyzerAgent   │
│  ────────────────────  │    │  ─────────────────────  │
│  - Greet users         │    │  - Analyze channels     │
│  - Collect preferences │    │  - Calculate matches    │
│  - Validate responses  │    │  - Generate rankings    │
│  - Structure data      │    │  - Create recommendations│
└────────┬───────────────┘    └────────┬────────────────┘
         │                              │
         │      ┌──────────────────┐   │
         └─────►│   BaseAgent      │◄──┘
                │   (Abstract)     │
                │  ──────────────  │
                │  - LLM Interface │
                │  - Prompt Mgmt   │
                │  - LangSmith     │
                │  - Common Utils  │
                └────────┬─────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Services                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │   OpenAI     │  │  LangSmith   │  │  Discord MCP       │   │
│  │   (GPT-4)    │  │  (Tracing)   │  │  (Optional)        │   │
│  └──────────────┘  └──────────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Workflow Sequence

### Interactive Mode Flow

```
1. User starts application
   │
   ▼
2. DiscordChannelSelector initializes
   │ - Load config.yaml
   │ - Setup logging
   │ - Create AgentOrchestrator
   ▼
3. AgentOrchestrator creates agents
   │ - UserPreferenceAgent
   │ - ChannelAnalyzerAgent
   ▼
4. Start conversation
   │ - UserPreferenceAgent.execute(mode='start')
   │ - Generate greeting
   │ - Display to user
   ▼
5. Collect preferences (loop)
   │ - User provides response
   │ - UserPreferenceAgent.execute(mode='collect')
   │ - Validate response
   │ - Ask next question or mark complete
   │ - Repeat until all preferences collected
   ▼
6. Analyze channels
   │ - Get channel data (mock/MCP/API)
   │ - ChannelAnalyzerAgent.execute(preferences, channels)
   │ - For each channel:
   │   │ - Calculate match score
   │   │ - Generate reasoning
   │   └─ Store analysis
   │ - Sort by match score
   │ - Select top N recommendations
   ▼
7. Present recommendations
   │ - Generate friendly message
   │ - Display detailed results
   │ - Show match scores and reasoning
   ▼
8. Complete
```

## 🎯 Design Patterns Used

### 1. Abstract Factory Pattern
**Where**: `BaseAgent` and `AgentFactory`

**Why**: Provides a flexible way to create different types of agents without tight coupling.

**Benefits**:
- Easy to add new agent types
- Centralized agent creation
- Consistent initialization

### 2. Template Method Pattern
**Where**: `BaseAgent.execute()` is abstract, implemented by subclasses

**Why**: Defines the skeleton of the algorithm while allowing subclasses to customize specific steps.

**Benefits**:
- Common interface for all agents
- Enforces implementation of required methods
- Reusable base functionality

### 3. Strategy Pattern
**Where**: Different agents implement different strategies for their tasks

**Why**: Allows switching between different algorithms (preference collection vs. channel analysis) at runtime.

**Benefits**:
- Flexible behavior switching
- Isolated algorithm implementations
- Easy to test individual strategies

### 4. Facade Pattern
**Where**: `DiscordChannelSelector` and `AgentOrchestrator`

**Why**: Provides a simple interface to a complex subsystem.

**Benefits**:
- Simplified API for users
- Hides complexity
- Decouples clients from subsystem

## 🧩 Component Details

### BaseAgent
**Responsibility**: Provide common functionality for all agents

**Key Features**:
- LLM integration (ChatOpenAI)
- Prompt management
- LangSmith tracing
- Error handling
- Logging

**Extension Points**:
- `execute()`: Must be implemented by subclasses
- Custom prompt templates
- Additional utility methods

### UserPreferenceAgent
**Responsibility**: Collect and structure user preferences

**Key Features**:
- Natural conversation flow
- Dynamic question generation
- Response validation
- Preference structuring

**Algorithm**:
1. Generate greeting using LLM
2. For each preference question:
   - Generate contextual question
   - Collect user response
   - Validate response quality
   - Request clarification if needed
   - Store validated preference
3. Return structured preferences

### ChannelAnalyzerAgent
**Responsibility**: Analyze channels and generate recommendations

**Key Features**:
- Multi-factor matching algorithm
- Configurable scoring thresholds
- Detailed reasoning generation
- Ranked recommendations

**Algorithm**:
1. For each channel:
   - Create analysis prompt with user preferences and channel info
   - LLM generates match score (0.0-1.0) and reasoning
   - Parse and validate analysis
2. Filter channels by minimum score
3. Sort by match score (descending)
4. Select top N recommendations
5. Generate friendly presentation message

### AgentOrchestrator
**Responsibility**: Coordinate multi-agent workflow

**Key Features**:
- Agent lifecycle management
- Data flow coordination
- State management
- Error handling

**Methods**:
- `start_conversation()`: Initialize preference collection
- `process_user_response()`: Handle user input
- `analyze_channels()`: Run channel analysis
- `reset()`: Clear state for new session

## 📊 Data Flow

### Preference Collection Data Flow
```
User Input (string)
    │
    ▼
UserPreferenceAgent
    │
    ├─► LLM (validate response)
    │
    ├─► conversation_history (append)
    │
    └─► collected_preferences (store)
         │
         └─► {
              "interests": "...",
              "role": "...",
              "experience_level": "...",
              "goals": "..."
             }
```

### Channel Analysis Data Flow
```
Preferences + Channels
    │
    ▼
ChannelAnalyzerAgent
    │
    ├─► For each channel:
    │    │
    │    ├─► Create analysis prompt
    │    │
    │    ├─► LLM (analyze match)
    │    │
    │    └─► Parse JSON response
    │         {
    │           "match_score": 0.85,
    │           "reasoning": "...",
    │           "key_matches": [...],
    │           "potential_concerns": [...]
    │         }
    │
    ├─► Filter by minimum_match_score
    │
    ├─► Sort by match_score
    │
    └─► Top N recommendations
         │
         └─► {
              "recommendations": [...],
              "message": "...",
              "total_analyzed": 15,
              "total_matching": 8
             }
```

## 🔐 Configuration Management

### Configuration Hierarchy
```
Environment Variables (.env)
    │ - API Keys (sensitive)
    │ - Feature flags
    │
    ▼
config.yaml
    │ - Agent settings
    │ - Preference questions
    │ - Analysis parameters
    │ - Logging config
    │
    ▼
Runtime Configuration
    │ - Merged environment + YAML
    │ - Validated required values
    │ - Passed to components
```

### Configuration Loading Process
1. Load `.env` using `python-dotenv`
2. Read `config.yaml` using `pyyaml`
3. Validate required environment variables
4. Merge configurations
5. Return unified config dictionary

## 🔍 LangSmith Integration

### Tracing Hierarchy
```
orchestrator_run_workflow [Root Trace]
    │
    ├─► agent_execute [UserPreferenceAgent]
    │    │
    │    ├─► llm_call [Generate greeting]
    │    │
    │    ├─► llm_call [Ask question]
    │    │
    │    └─► llm_call [Validate response]
    │
    └─► agent_execute [ChannelAnalyzerAgent]
         │
         ├─► llm_call [Analyze channel 1]
         │
         ├─► llm_call [Analyze channel 2]
         │
         ├─► llm_call [Analyze channel N]
         │
         └─► llm_call [Generate recommendation message]
```

### Traced Information
- **Inputs**: All parameters passed to agents
- **Outputs**: Agent responses and results
- **Latency**: Time for each operation
- **Tokens**: Token usage for cost tracking
- **Errors**: Any exceptions or failures
- **Metadata**: Agent names, models, temperatures

## 🧪 Testing Strategy

### Test Types

1. **Unit Tests** (Individual agents)
   - Test agent initialization
   - Test prompt generation
   - Test response parsing

2. **Integration Tests** (Agent interaction)
   - Test preference collection flow
   - Test channel analysis flow
   - Test orchestrator coordination

3. **End-to-End Tests** (Full workflow)
   - Test with different user personas
   - Test with various channel configurations
   - Measure performance metrics

### Test Data
- Mock channels (15 diverse channels)
- User personas (5 different types)
- Expected match patterns

## 🚀 Performance Considerations

### Optimization Strategies

1. **Parallel Processing**
   - Could analyze multiple channels concurrently
   - Use `asyncio.gather()` for parallel LLM calls

2. **Caching**
   - Cache channel analyses for repeated preferences
   - Cache LLM responses for identical prompts

3. **Prompt Optimization**
   - Minimize token usage
   - Structured output (JSON) for faster parsing

4. **Batch Processing**
   - Analyze multiple users at once
   - Batch channel data loading

### Current Performance
- Average analysis time: ~9 seconds for 15 channels
- Bottleneck: Sequential LLM calls
- Improvement potential: ~3x with parallelization

## 🔮 Future Extensions

### Planned Features

1. **Discord MCP Integration**
   - Real-time channel data
   - Live activity metrics
   - Member demographics

2. **Learning System**
   - Track user feedback
   - Improve matching algorithm
   - Personalized recommendations

3. **Web Interface**
   - React frontend
   - Real-time chat interface
   - Visual channel previews

4. **Advanced Matching**
   - Semantic similarity (embeddings)
   - Collaborative filtering
   - Time-based recommendations

5. **Multi-Server Support**
   - Analyze channels across servers
   - Cross-server recommendations
   - Server discovery

## 📚 Code Quality Principles

### Applied in This Project

1. **DRY (Don't Repeat Yourself)**
   - BaseAgent contains shared logic
   - Reusable prompt templates
   - Common utility functions

2. **SOLID Principles**
   - **S**ingle Responsibility: Each agent has one job
   - **O**pen/Closed: Extensible via inheritance
   - **L**iskov Substitution: All agents are BaseAgent
   - **I**nterface Segregation: Minimal required methods
   - **D**ependency Inversion: Depend on abstractions

3. **Clean Code**
   - Descriptive names
   - Comprehensive docstrings
   - Type hints
   - Consistent formatting

4. **Testability**
   - Dependency injection
   - Mock data support
   - Isolated components

This architecture enables easy extension, maintenance, and scaling of the system.
