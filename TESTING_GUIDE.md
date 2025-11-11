# Testing Guide - Verify Your Setup

This guide provides all the commands to test if the Discord Channel Selector is working correctly.

## 🔍 Pre-Flight Checks

### 1. Verify Python Installation
```bash
python --version
```
**Expected Output**: `Python 3.8.x` or higher

### 2. Verify Virtual Environment (if using one)
```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```
**Expected Output**: Your prompt should show `(venv)` or `(aiagent)`

### 3. Verify Dependencies
```bash
pip list | findstr langchain
```
**Expected Output**: Should show `langchain`, `langchain-core`, `langchain-openai`

### 4. Check Configuration Files
```bash
# Check if config.yaml exists
dir config.yaml

# Check if .env exists (should be created from .env.example)
dir .env
```
**Expected Output**: Both files should be found

### 5. Verify .env File Has API Key
```bash
type .env
```
**Expected Output**: Should show your OPENAI_API_KEY (not "your_openai_api_key_here")

## 🧪 Functional Tests

### Test 1: Import Check (Quick Smoke Test)
```bash
cd src
python -c "from agents.base_agent import BaseAgent; print('✓ BaseAgent imported')"
python -c "from agents.user_preference_agent import UserPreferenceAgent; print('✓ UserPreferenceAgent imported')"
python -c "from agents.channel_analyzer_agent import ChannelAnalyzerAgent; print('✓ ChannelAnalyzerAgent imported')"
python -c "from orchestrator import AgentOrchestrator; print('✓ AgentOrchestrator imported')"
python -c "from config_loader import load_config; print('✓ Config loader imported')"
```
**Expected Output**: All 5 import success messages

### Test 2: Configuration Loading
```bash
cd src
python -c "from config_loader import load_config; config = load_config(); print('✓ Config loaded successfully'); print(f'Agents configured: {len(config.get(\"agents\", {}))}')"
```
**Expected Output**: 
```
✓ Config loaded successfully
Agents configured: 2
```

### Test 3: Mock Data Check
```bash
cd src
python -c "from test_data import get_mock_channels, get_test_user_preferences; print(f'✓ Mock channels: {len(get_mock_channels())}'); print(f'✓ Test personas: {len(get_test_user_preferences())}')"
```
**Expected Output**:
```
✓ Mock channels: 15
✓ Test personas: 5
```

### Test 4: Agent Creation
```bash
cd src
python -c "from agents.base_agent import AgentFactory; from agents.user_preference_agent import UserPreferenceAgent; from agents.channel_analyzer_agent import ChannelAnalyzerAgent; print(f'✓ Registered agents: {AgentFactory.list_agent_types()}')"
```
**Expected Output**: Should show registered agent types

### Test 5: Run Automated Test Suite
```bash
cd src
python run_tests.py
```
**Expected Output**:
```
Discord Channel Selector - Automated Test Suite
Test Configuration:
  - Total channels: 15
  - Test personas: 5

Running Test: Python Beginner
✅ Test passed in X.XXs
   Found X matching channels
   Top recommendation: #python-beginners (XX% match)

[... 4 more tests ...]

TEST REPORT
Summary:
  Total Tests: 5
  ✅ Passed: 5
  ❌ Failed: 0
  Total Execution Time: XX.XXs
  Average Time per Test: X.XXs

📄 Detailed report saved to: test_report.json
```

### Test 6: Run Example Scripts (Non-Interactive)
```bash
cd src
python -c "import sys; sys.path.insert(0, '..'); from examples import example_programmatic; import asyncio; asyncio.run(example_programmatic())"
```
**Expected Output**: Should show analysis results with recommendations

### Test 7: Main Application (Interactive Mode)
```bash
cd src
python main.py
```
**Expected Output**:
```
Discord Channel Selector initialized successfully!
============================================================

🤖 Discord Channel Selector - Interactive Mode
============================================================

🤖 Bot: [Greeting message]
```

**To test interactively**:
1. Type: `I'm interested in Python programming`
2. Type: `I'm a software developer`
3. Type: `intermediate`
4. Type: `I want to learn machine learning`

**Expected**: Should show channel recommendations

### Test 8: Verify LangSmith Tracing (Optional)
If you have LangSmith API key configured:
```bash
# Check environment variable
echo %LANGCHAIN_API_KEY%

# This should be set in .env
type .env | findstr LANGCHAIN
```

Then run a test and check https://smith.langchain.com/ for traces.

## 🔧 Component-Specific Tests

### Test UserPreferenceAgent
```bash
cd src
python -c "
import asyncio
from config_loader import load_config
from agents.user_preference_agent import UserPreferenceAgent

async def test():
    config = load_config()
    agent = UserPreferenceAgent(config=config.get('agents', {}).get('user_preference_agent', {}))
    result = await agent.execute({'mode': 'start'})
    print('✓ UserPreferenceAgent working')
    print(f'Status: {result.get(\"status\")}')
    return result

asyncio.run(test())
"
```
**Expected Output**: 
```
✓ UserPreferenceAgent working
Status: greeting
```

### Test ChannelAnalyzerAgent
```bash
cd src
python -c "
import asyncio
from config_loader import load_config
from agents.channel_analyzer_agent import ChannelAnalyzerAgent
from test_data import get_mock_channels

async def test():
    config = load_config()
    channels = get_mock_channels()
    agent = ChannelAnalyzerAgent(config=config.get('channel_analysis', {}))
    agent.set_channels_data(channels)
    
    preferences = {
        'interests': 'Python programming',
        'role': 'Developer',
        'experience_level': 'beginner',
        'goals': 'Learn Python'
    }
    
    result = await agent.execute({'preferences': preferences})
    print('✓ ChannelAnalyzerAgent working')
    print(f'Recommendations: {len(result.get(\"recommendations\", []))}')
    print(f'Total analyzed: {result.get(\"total_analyzed\")}')
    return result

asyncio.run(test())
"
```
**Expected Output**:
```
✓ ChannelAnalyzerAgent working
Recommendations: X
Total analyzed: 15
```

## 📊 Performance Benchmarks

### Quick Performance Test
```bash
cd src
python -c "
import asyncio
import time
from main import DiscordChannelSelector
from test_data import get_mock_channels

async def benchmark():
    start = time.time()
    app = DiscordChannelSelector()
    channels = get_mock_channels()
    
    preferences = {
        'interests': 'Python and ML',
        'role': 'Data Scientist',
        'experience_level': 'intermediate',
        'goals': 'Build projects'
    }
    
    result = await app.run_programmatic(preferences, channels)
    elapsed = time.time() - start
    
    print(f'✓ Complete workflow: {elapsed:.2f}s')
    print(f'✓ Recommendations: {len(result[\"recommendations\"])}')
    print(f'✓ Top match: {result[\"recommendations\"][0][\"name\"]} ({result[\"recommendations\"][0][\"analysis\"][\"match_score\"]:.1%})')

asyncio.run(benchmark())
"
```
**Expected Output**: Should complete in 5-15 seconds

## 🎯 Expected Performance Metrics

| Metric | Expected Value |
|--------|---------------|
| Import time | < 2 seconds |
| Config loading | < 1 second |
| Single LLM call | 1-5 seconds |
| Preference collection | 15-30 seconds (interactive) |
| Channel analysis (15 channels) | 30-60 seconds |
| Full workflow | 45-90 seconds |
| Test suite (5 personas) | 3-5 minutes |

## ❌ Common Issues & Solutions

### Issue: ModuleNotFoundError
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

### Issue: OpenAI API Key Error
```bash
# Solution: Check .env file
type .env
# Make sure OPENAI_API_KEY is set correctly
```

### Issue: Config file not found
```bash
# Solution: Make sure you're in the right directory
cd src
python main.py
```

### Issue: Rate limit errors
```bash
# Solution: Add delay between tests or use lower tier models
# Edit config.yaml and change model to "gpt-3.5-turbo"
```

## ✅ Quick Validation Checklist

Run these in order for a complete system check:

```bash
# 1. Check Python
python --version

# 2. Go to src directory
cd src

# 3. Test imports
python -c "from main import DiscordChannelSelector; print('✓ Imports OK')"

# 4. Test config
python -c "from config_loader import load_config; load_config(); print('✓ Config OK')"

# 5. Test data
python -c "from test_data import get_mock_channels; print(f'✓ Data OK: {len(get_mock_channels())} channels')"

# 6. Run full test suite
python run_tests.py

# 7. If all passed, try interactive mode
python main.py
```

## 🎉 Success Criteria

Your system is working correctly if:
- ✅ All imports succeed
- ✅ Configuration loads without errors
- ✅ Test suite passes all 5 tests
- ✅ Interactive mode starts and greets you
- ✅ Recommendations are generated
- ✅ No Python errors or exceptions

## 📝 Test Report Verification

After running `python run_tests.py`, check the generated `test_report.json`:

```bash
# View the test report
type test_report.json
```

**Expected structure**:
```json
{
  "summary": {
    "total_tests": 5,
    "passed": 5,
    "failed": 0,
    "total_time": "XX.XX",
    "average_time": "X.XX"
  },
  "results": [...]
}
```

All tests should show `"status": "success"`.

---

**Need Help?** If any test fails, check:
1. Error messages for specific issues
2. README.md for setup instructions
3. .env file for correct API keys
4. config.yaml for proper configuration
