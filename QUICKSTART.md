# Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will get you running the Discord Channel Selector quickly.

### Step 1: Install Dependencies (2 minutes)

```bash
# Navigate to project
cd langsmith-agent-discord

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### Step 2: Setup API Keys (1 minute)

```bash
# Copy environment file
copy .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-key-here
```

### Step 3: Run the Application (2 minutes)

```bash
# Run interactive mode
python src/main.py
```

Follow the prompts to get channel recommendations!

### Step 4: Run Tests (Optional)

```bash
# Run automated tests
python src/run_tests.py
```

## 📖 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Customize `config.yaml` for your needs
- Add your own channel data
- Explore the code with extensive comments

## 🆘 Quick Troubleshooting

**Problem**: Import errors
**Solution**: Make sure you activated the virtual environment and ran `pip install -r requirements.txt`

**Problem**: API key error
**Solution**: Check that `.env` file exists and contains your OpenAI API key

**Problem**: No recommendations
**Solution**: Lower `minimum_match_score` in `config.yaml` to 0.4

## 💡 Example Interaction

```
🤖 Bot: Hello! I'm here to help you find the perfect Discord channels...

👤 You: I'm interested in Python and machine learning

🤖 Bot: Great! What's your role or profession?

👤 You: I'm a data scientist

🤖 Bot: What's your experience level?

👤 You: Intermediate

🤖 Bot: What are you hoping to achieve?

👤 You: I want to improve my ML skills and work on projects

🔍 Analyzing Discord channels...

📊 Analysis Complete!
   - Top recommendations: 5
   
🤖 Bot: Based on your preferences, here are my top recommendations:

1. #machine-learning (95% match)
   Perfect for intermediate data scientists interested in ML...
   
2. #python-advanced (88% match)
   Great for advancing your Python skills...
```

Enjoy exploring Discord channels! 🎉
