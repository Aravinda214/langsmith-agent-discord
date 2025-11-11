# Agent Testing Commands - Copy & Paste

## 🎯 Quick Agent Tests (One Command Each)

### Test 1: Full Demo with Sample Responses
```bash
cd src
python quick_demo.py
```
**What it does**: Runs 3 different personas with predefined responses:
- Python/ML Developer (intermediate)
- Career Switcher (beginner)
- Senior Developer (advanced)

**Expected**: Shows complete conversation flow and recommendations for each persona

---

### Test 2: Single Quick Test (Python Enthusiast)
```bash
cd src
python -c "import asyncio; from orchestrator import AgentOrchestrator; from config_loader import load_config; from test_data import get_mock_channels; async def test(): config = load_config(); orc = AgentOrchestrator(config); result = await orc.start_conversation(); print(f'\n🤖 Bot: {result[\"message\"]}\n'); responses = ['I am interested in Python programming', 'I am a software developer', 'intermediate', 'I want to learn machine learning']; for r in responses: print(f'👤 You: {r}'); result = await orc.process_user_response(r); print(f'🤖 Bot: {result[\"message\"]}\n'); if result['status'] == 'complete': break; channels = get_mock_channels(); analysis = await orc.analyze_channels(channels); print(f'📊 Found {len(analysis[\"recommendations\"])} recommendations'); for i, rec in enumerate(analysis['recommendations'][:3], 1): print(f'   {i}. #{rec[\"name\"]} ({rec[\"analysis\"][\"match_score\"]:.1%})'); asyncio.run(test())"
```
**What it does**: Tests with "I'm interested in Python programming" + other responses

---

### Test 3: Web Developer Persona
```bash
cd src
python -c "import asyncio; from orchestrator import AgentOrchestrator; from config_loader import load_config; from test_data import get_mock_channels; async def test(): config = load_config(); orc = AgentOrchestrator(config); await orc.start_conversation(); responses = ['I am interested in web development and React', 'I am a frontend developer', 'intermediate', 'I want to master modern frameworks']; for r in responses: result = await orc.process_user_response(r); if result['status'] == 'complete': break; channels = get_mock_channels(); analysis = await orc.analyze_channels(channels); print('Top Recommendations:'); for i, rec in enumerate(analysis['recommendations'][:3], 1): print(f'{i}. #{rec[\"name\"]} - {rec[\"analysis\"][\"match_score\"]:.1%} match'); asyncio.run(test())"
```

---

### Test 4: Data Science Beginner
```bash
cd src
python -c "import asyncio; from orchestrator import AgentOrchestrator; from config_loader import load_config; from test_data import get_mock_channels; async def test(): config = load_config(); orc = AgentOrchestrator(config); await orc.start_conversation(); responses = ['I am interested in data science and analytics', 'I am a student', 'beginner', 'I want to become a data analyst']; for r in responses: result = await orc.process_user_response(r); if result['status'] == 'complete': break; channels = get_mock_channels(); analysis = await orc.analyze_channels(channels); print('Top Recommendations:'); for i, rec in enumerate(analysis['recommendations'][:3], 1): print(f'{i}. #{rec[\"name\"]} - {rec[\"analysis\"][\"match_score\"]:.1%} match'); asyncio.run(test())"
```

---

### Test 5: Game Developer
```bash
cd src
python -c "import asyncio; from orchestrator import AgentOrchestrator; from config_loader import load_config; from test_data import get_mock_channels; async def test(): config = load_config(); orc = AgentOrchestrator(config); await orc.start_conversation(); responses = ['I am interested in game development and graphics', 'I am a game developer', 'intermediate', 'I want to build indie games']; for r in responses: result = await orc.process_user_response(r); if result['status'] == 'complete': break; channels = get_mock_channels(); analysis = await orc.analyze_channels(channels); print('Top Recommendations:'); for i, rec in enumerate(analysis['recommendations'][:3], 1): print(f'{i}. #{rec[\"name\"]} - {rec[\"analysis\"][\"match_score\"]:.1%} match'); asyncio.run(test())"
```

---

### Test 6: Career Advice Seeker
```bash
cd src
python -c "import asyncio; from orchestrator import AgentOrchestrator; from config_loader import load_config; from test_data import get_mock_channels; async def test(): config = load_config(); orc = AgentOrchestrator(config); await orc.start_conversation(); responses = ['I am interested in career growth and job hunting', 'I am a junior developer', 'beginner', 'I want to advance my career and find better opportunities']; for r in responses: result = await orc.process_user_response(r); if result['status'] == 'complete': break; channels = get_mock_channels(); analysis = await orc.analyze_channels(channels); print('Top Recommendations:'); for i, rec in enumerate(analysis['recommendations'][:3], 1): print(f'{i}. #{rec[\"name\"]} - {rec[\"analysis\"][\"match_score\"]:.1%} match'); asyncio.run(test())"
```

---

## 📋 Test Different User Inputs

### Custom Test Template (Modify the responses)
```python
# Save as test_custom.py
import asyncio
from orchestrator import AgentOrchestrator
from config_loader import load_config
from test_data import get_mock_channels

async def test():
    config = load_config()
    orc = AgentOrchestrator(config)
    
    # Start conversation
    result = await orc.start_conversation()
    print(f"\n🤖 Bot: {result['message']}\n")
    
    # YOUR CUSTOM RESPONSES HERE
    responses = [
        "I'm interested in Python programming",  # Your interests
        "I'm a software developer",              # Your role
        "intermediate",                          # Your experience
        "I want to learn machine learning"       # Your goals
    ]
    
    # Process responses
    for r in responses:
        print(f"👤 You: {r}")
        result = await orc.process_user_response(r)
        print(f"🤖 Bot: {result['message']}\n")
        if result['status'] == 'complete':
            break
    
    # Get recommendations
    channels = get_mock_channels()
    analysis = await orc.analyze_channels(channels)
    
    print("=" * 60)
    print("📊 YOUR RECOMMENDATIONS:")
    print("=" * 60)
    for i, rec in enumerate(analysis['recommendations'], 1):
        score = rec['analysis']['match_score']
        print(f"\n{i}. #{rec['name']} ({score:.1%} match)")
        print(f"   {rec['description']}")
        print(f"   Reasoning: {rec['analysis']['reasoning']}")

asyncio.run(test())
```

Then run:
```bash
cd src
python test_custom.py
```

---

## 🎬 Recommended Testing Sequence

```bash
# 1. Quick demo with 3 personas (EASIEST - START HERE)
cd src
python quick_demo.py

# 2. Test individual agents (verify each works)
python run_tests.py

# 3. Try custom inputs (modify responses in test_custom.py)
python test_custom.py

# 4. Interactive mode (type your own responses)
python main.py
```

---

## 📊 Sample Conversation Flows

### Flow 1: Python Learner
```
Interests: "I'm interested in Python programming"
Role: "I'm a software developer"
Experience: "intermediate"
Goals: "I want to learn machine learning"

Expected Top Matches:
- #machine-learning
- #python-advanced
- #data-science-beginners
```

### Flow 2: Web Developer
```
Interests: "I'm interested in web development and React"
Role: "I'm a frontend developer"
Experience: "intermediate"
Goals: "I want to master modern frameworks"

Expected Top Matches:
- #web-development
- #mobile-development (React Native)
- #open-source
```

### Flow 3: Complete Beginner
```
Interests: "I'm interested in learning to code"
Role: "I'm a student"
Experience: "beginner"
Goals: "I want to get my first programming job"

Expected Top Matches:
- #python-beginners
- #student-projects
- #career-advice
- #algorithm-challenges
```

### Flow 4: Career Changer
```
Interests: "I'm interested in data science and analytics"
Role: "I'm switching careers to tech"
Experience: "beginner"
Goals: "I want to become a data analyst"

Expected Top Matches:
- #data-science-beginners
- #python-beginners
- #career-advice
```

---

## ✅ What to Look For (Success Indicators)

When running tests, verify:
- ✅ Bot greets you
- ✅ Bot asks 4 questions (interests, role, experience, goals)
- ✅ Bot acknowledges your responses
- ✅ Analysis completes without errors
- ✅ At least 3-5 recommendations provided
- ✅ Match scores are reasonable (60-95%)
- ✅ Reasoning makes sense

---

## 🚀 Quick Copy-Paste Test

**Fastest way to test everything:**

```bash
cd langsmith-agent-discord\src
python quick_demo.py
```

This will run all 3 demo personas and show you complete results!
