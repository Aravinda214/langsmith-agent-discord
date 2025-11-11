# Quick Test Commands - One-Page Reference

## 🚀 Essential Tests (Run These First)

### 1. Quick Health Check
```bash
cd src
python -c "from main import DiscordChannelSelector; print('✅ System OK')"
```

### 2. Run Automated Test Suite
```bash
cd src
python run_tests.py
```
**Expected**: 5 tests pass, generates `test_report.json`

### 3. Run Interactive Demo
```bash
cd src
python main.py
```
**Expected**: Greeting from the bot, asks about your preferences

### 4. Run Programmatic Example
```bash
python examples.py
```
**Expected**: Shows recommendations for different user personas

---

## 📋 Complete Test Sequence (Copy & Paste)

```bash
# Navigate to project
cd langsmith-agent-discord

# Verify setup
python --version
dir config.yaml
dir .env

# Go to source
cd src

# Test 1: Imports
python -c "from agents.base_agent import BaseAgent; from agents.user_preference_agent import UserPreferenceAgent; from agents.channel_analyzer_agent import ChannelAnalyzerAgent; from orchestrator import AgentOrchestrator; print('✅ All imports successful')"

# Test 2: Configuration
python -c "from config_loader import load_config; config = load_config(); print(f'✅ Config loaded: {len(config.get(\"agents\", {}))} agents configured')"

# Test 3: Mock Data
python -c "from test_data import get_mock_channels, get_test_user_preferences; print(f'✅ Data ready: {len(get_mock_channels())} channels, {len(get_test_user_preferences())} personas')"

# Test 4: Full Test Suite
python run_tests.py

# Test 5: Interactive Mode
python main.py
```

---

## ⚡ Quick Verification (30 seconds)

```bash
cd langsmith-agent-discord\src
python -c "from main import DiscordChannelSelector; from test_data import get_mock_channels; import asyncio; async def test(): app = DiscordChannelSelector(); result = await app.run_programmatic({'interests': 'Python', 'role': 'Developer', 'experience_level': 'beginner', 'goals': 'Learn'}, get_mock_channels()); print(f'✅ WORKING! Found {len(result[\"recommendations\"])} recommendations'); return result; asyncio.run(test())"
```

---

## 🎯 Expected Results Summary

| Test | Expected Output |
|------|----------------|
| Import test | `✅ All imports successful` |
| Config test | `✅ Config loaded: 2 agents configured` |
| Data test | `✅ Data ready: 15 channels, 5 personas` |
| Test suite | `Total Tests: 5, ✅ Passed: 5, ❌ Failed: 0` |
| Interactive | Bot greeting and questions |
| Programmatic | Channel recommendations displayed |

---

## 🔍 Troubleshooting Quick Fixes

**Problem**: `ModuleNotFoundError`
```bash
pip install -r requirements.txt
```

**Problem**: `FileNotFoundError: config.yaml`
```bash
# Make sure you're in src/ directory
cd src
python main.py
```

**Problem**: API Key error
```bash
# Check .env file exists and has your key
type ..\  .env
```

**Problem**: All tests fail
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

---

## 📊 Performance Expectations

- ✅ Import test: < 2 seconds
- ✅ Config load: < 1 second  
- ✅ Single test: 5-15 seconds
- ✅ Full suite: 45-120 seconds
- ✅ Interactive session: 30-60 seconds

---

## ✅ Success Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with OpenAI API key
- [ ] `config.yaml` exists in project root
- [ ] Import test passes
- [ ] Config test passes
- [ ] Test suite runs successfully
- [ ] Interactive mode starts

**All checked?** Your system is ready! 🎉

---

For detailed testing instructions, see `TESTING_GUIDE.md`
