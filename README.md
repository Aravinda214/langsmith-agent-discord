# Discord Channel Selector - LangSmith Agent Framework

A beginner-friendly, extensible multi-agent system built with LangSmith that helps users find the best Discord channels based on their interests, role, experience level, and goals.

## 🎯 What This Does

This application uses two AI agents working together:
1. **User Preference Agent**: Greets users and collects their preferences through conversation
2. **Channel Analyzer Agent**: Analyzes available Discord channels and recommends the best matches

## 🧠 Key Concepts Explained (For Beginners)

### What is an Agent?
An **agent** is a piece of software powered by AI (like GPT-4) that can:
- Understand natural language
- Make decisions
- Take actions
- Learn from context

Think of it like a smart assistant that specializes in a specific task.

### What is LangSmith?
**LangSmith** is a platform for:
- Monitoring your AI agents (see what they're doing)
- Debugging (find out why something went wrong)
- Tracking performance (how fast? how accurate?)

It's like having a security camera for your AI agents - you can see everything they do.

### What is Multi-Agent System?
Instead of one agent doing everything, we have **multiple specialized agents** that work together:
- **User Preference Agent**: Expert at talking to users and understanding what they want
- **Channel Analyzer Agent**: Expert at analyzing Discord channels and finding matches

This is like having a team where each member has a specific expertise.

### What is Object-Oriented Programming (OOP)?
The code uses OOP principles:
- **Classes**: Blueprints for creating objects (e.g., `BaseAgent` is a blueprint for all agents)
- **Inheritance**: Agents inherit common functionality from `BaseAgent`
- **Encapsulation**: Each agent manages its own data and behavior
- **Abstraction**: Common interface, different implementations

## 📁 Project Structure

```
langsmith-agent-discord/
├── src/
│   ├── agents/
│   │   ├── __init__.py              # Package initialization
│   │   ├── base_agent.py            # Abstract base class for all agents
│   │   ├── user_preference_agent.py # Collects user preferences
│   │   └── channel_analyzer_agent.py # Analyzes and recommends channels
│   ├── config_loader.py             # Configuration management
│   ├── orchestrator.py              # Coordinates multi-agent workflow
│   ├── main.py                      # Main application entry point
│   ├── test_data.py                 # Mock Discord data for testing
│   └── run_tests.py                 # Automated test suite
├── config.yaml                      # Application configuration
├── .env.example                     # Environment variables template
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## � **Accuracy & Performance**

### **ScaleDown Integration Results**

We integrated ScaleDown API to compress prompts before sending to OpenAI, achieving:

- ✅ **36.2% token reduction** (290 → 185 tokens average)
- ✅ **35.8% cost savings** (same recommendations, lower cost)
- ✅ **100% accuracy maintained** (same top channel recommendations)
- ⚠️ **+0.3s latency** (compression overhead - acceptable)

**Key Insight:** ScaleDown maintains identical recommendation quality while reducing costs by ~36%.

### **Running Accuracy Comparison**

```bash
cd src
python compare_agents.py
```

See [ACCURACY_MEASUREMENT_GUIDE.md](ACCURACY_MEASUREMENT_GUIDE.md) for methodology.

---

## �🚀 **Quick Start**

### **1. Extract ScaleDown Discord Channels**

```bash
cd src
python extract_discord_channels.py
```

Choose automated (needs bot) or manual (type in details). See [QUICK_START_SCALEDOWN.md](QUICK_START_SCALEDOWN.md).

### **2. Test Agents**

```bash
# Interactive mode with standard agents
python main.py --agent standard

# Interactive mode with ScaleDown agents
python main.py --agent scaledown

# Compare both agents
python compare_agents.py
```

See [COMMANDS_REFERENCE.md](COMMANDS_REFERENCE.md) for all commands.

---

### Prerequisites
- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- LangSmith API key (optional, [Get one here](https://smith.langchain.com/))

### Step 1: Install Dependencies

```bash
# Navigate to the project directory
cd langsmith-agent-discord

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
# Copy the example environment file
copy .env.example .env

# Edit .env and add your API keys
# Use notepad or any text editor
notepad .env
```

Add your API keys:
```
OPENAI_API_KEY=sk-your-openai-api-key-here
LANGCHAIN_API_KEY=your-langsmith-api-key-here  # Optional
LANGCHAIN_TRACING_V2=true                       # Set to false if not using LangSmith
```

### Step 3: Customize Configuration (Optional)

Edit `config.yaml` to customize:
- Agent models (GPT-4, GPT-3.5-turbo, etc.)
- Temperature settings (creativity level)
- Preference questions
- Matching criteria

## 🎮 How to Use

### Interactive Mode (Recommended for First-Time Users)

Run the main application:
```bash
python src/main.py
```

The application will:
1. Greet you
2. Ask about your interests, role, experience level, and goals
3. Analyze available Discord channels
4. Recommend the best matches for you

### Programmatic Mode (For Integration)

```python
from src.main import DiscordChannelSelector
from src.test_data import get_mock_channels
import asyncio

async def example():
    # Initialize the app
    app = DiscordChannelSelector()
    
    # Your user preferences
    preferences = {
        "interests": "Python programming and machine learning",
        "role": "Data Scientist",
        "experience_level": "intermediate",
        "goals": "Build ML projects and improve coding skills"
    }
    
    # Get channels (could be from Discord API, MCP server, etc.)
    channels = get_mock_channels()
    
    # Get recommendations
    result = await app.run_programmatic(preferences, channels)
    
    print(result['message'])

# Run it
asyncio.run(example())
```

### Running Automated Tests

Test the system with multiple user personas:
```bash
python src/run_tests.py
```

This will:
- Test 5 different user personas
- Measure performance metrics
- Generate a detailed test report (`test_report.json`)

## 📊 Understanding the Code

### BaseAgent (src/agents/base_agent.py)

This is the **foundation** that all agents build upon:
```python
class BaseAgent(ABC):  # ABC = Abstract Base Class
    def __init__(self, name, model_name, temperature, config):
        # Initialize the AI model (the "brain" of the agent)
        self.model = ChatOpenAI(model=model_name, temperature=temperature)
    
    @abstractmethod  # This MUST be implemented by child classes
    async def execute(self, input_data):
        pass  # Each agent implements this differently
```

**Key points:**
- `@abstractmethod` means every agent MUST implement `execute()`
- `@traceable` decorator sends execution data to LangSmith for monitoring
- Temperature controls randomness (0.0 = focused, 1.0 = creative)

### UserPreferenceAgent (src/agents/user_preference_agent.py)

Handles conversation with users:
```python
class UserPreferenceAgent(BaseAgent):
    async def execute(self, input_data):
        mode = input_data.get('mode')
        
        if mode == 'start':
            return await self._greet_user()  # Say hello
        elif mode == 'collect':
            return await self._collect_preferences(...)  # Ask questions
```

**How it works:**
1. Uses prompt templates to create natural language instructions for the AI
2. Validates user responses to ensure quality data
3. Stores collected preferences in a structured format

### ChannelAnalyzerAgent (src/agents/channel_analyzer_agent.py)

Analyzes channels and finds matches:
```python
class ChannelAnalyzerAgent(BaseAgent):
    async def execute(self, input_data):
        preferences = input_data['preferences']
        channels = input_data['channels']
        
        # Analyze each channel
        for channel in channels:
            score = await self._analyze_channel(channel, preferences)
            # Scoring based on topic match, experience level, etc.
        
        # Return top recommendations
```

**Matching logic:**
- Compares user interests with channel topics
- Considers experience level appropriateness
- Evaluates activity level and engagement
- Generates match score (0.0 to 1.0)

### AgentOrchestrator (src/orchestrator.py)

The **conductor** that coordinates agents:
```python
class AgentOrchestrator:
    def __init__(self, config):
        # Create both agents
        self.preference_agent = UserPreferenceAgent(...)
        self.channel_analyzer = ChannelAnalyzerAgent(...)
    
    async def start_conversation(self):
        # Step 1: Greet user
        
    async def process_user_response(self, user_response):
        # Step 2: Collect preferences
        
    async def analyze_channels(self, channels_data):
        # Step 3: Analyze and recommend
```

**Workflow:**
1. Initialize agents with configuration
2. Run preference collection
3. Pass preferences to channel analyzer
4. Return recommendations

## 🔧 Extending the System

### Adding a New Agent

1. Create a new file in `src/agents/`:
```python
from .base_agent import BaseAgent, AgentFactory

class MyNewAgent(BaseAgent):
    async def execute(self, input_data):
        # Your agent logic here
        pass

# Register with factory
AgentFactory.register_agent('my_new_agent', MyNewAgent)
```

2. Configure in `config.yaml`:
```yaml
agents:
  my_new_agent:
    name: "My Agent"
    model: "gpt-4"
    temperature: 0.7
```

3. Use in orchestrator:
```python
from agents.my_new_agent import MyNewAgent

# In orchestrator
self.my_agent = MyNewAgent(...)
```

### Adding New Preference Questions

Edit `config.yaml`:
```yaml
preference_questions:
  - field: "new_field"
    question: "What is your question?"
    required: true
```

### Customizing Matching Logic

Edit `channel_analyzer_agent.py`, modify `_analyze_channel()` method:
```python
async def _analyze_channel(self, channel, preferences):
    # Add custom scoring logic
    # E.g., bonus points for certain topics
    # or penalties for mismatched experience levels
```

## 📈 Performance Testing

The test suite (`run_tests.py`) measures:
- **Execution Time**: How fast each test completes
- **Match Quality**: Number and quality of recommendations
- **Success Rate**: Percentage of successful test cases

**Sample test report:**
```json
{
  "summary": {
    "total_tests": 5,
    "passed": 5,
    "failed": 0,
    "total_time": 45.2,
    "average_time": 9.04
  },
  "results": [...]
}
```

## 🔍 LangSmith Monitoring

When enabled, LangSmith tracks:
- **Agent Executions**: Every time an agent runs
- **LLM Calls**: All interactions with GPT-4
- **Latency**: How long operations take
- **Token Usage**: API costs
- **Errors**: Any failures or exceptions

**View in LangSmith dashboard:**
1. Go to https://smith.langchain.com/
2. Select your project
3. View traces, metrics, and logs

## 🐛 Troubleshooting

### "Import langchain_openai could not be resolved"
This is a linting warning. The imports will work once you install dependencies with `pip install -r requirements.txt`.

### "Missing required environment variables"
Make sure you:
1. Copied `.env.example` to `.env`
2. Added your actual API keys
3. Saved the file

### "Rate limit exceeded"
You're making too many API calls:
- Add delays between requests
- Use a higher-tier OpenAI plan
- Reduce the number of channels being analyzed

### Low match scores
Adjust in `config.yaml`:
```yaml
channel_analysis:
  minimum_match_score: 0.4  # Lower threshold
```

## 🎓 Learning Resources

### Understanding Agents
- [LangChain Agents Documentation](https://python.langchain.com/docs/modules/agents/)
- [What are AI Agents?](https://www.langchain.com/agents)

### LangSmith Tracing
- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangSmith Tutorial](https://python.langchain.com/docs/langsmith/)

### Object-Oriented Programming
- [Python OOP Tutorial](https://realpython.com/python3-object-oriented-programming/)
- [Abstract Base Classes](https://docs.python.org/3/library/abc.html)

### Async Python
- [Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Async/Await Tutorial](https://realpython.com/async-io-python/)

## 📝 Configuration Reference

### Agent Settings
- `model`: Which OpenAI model to use (gpt-4, gpt-3.5-turbo)
- `temperature`: 0.0-1.0, controls creativity (lower = more focused)
- `max_tokens`: Maximum response length

### Channel Analysis Settings
- `max_recommendations`: How many channels to recommend (default: 5)
- `minimum_match_score`: Minimum score to include (0.0-1.0, default: 0.6)
- `consider_activity_level`: Whether to factor in channel activity

## 🤝 Contributing

To add features or fix bugs:
1. Follow the OOP patterns established in `base_agent.py`
2. Add comprehensive docstrings
3. Register new agents with `AgentFactory`
4. Update configuration in `config.yaml`
5. Add tests in `run_tests.py`

## 📄 License

This project is provided as-is for educational purposes.

## 🙋 Support

For questions or issues:
1. Check the troubleshooting section above
2. Review the code comments (heavily documented)
3. Test with `run_tests.py` to isolate issues
4. Check LangSmith traces for detailed execution logs

---


