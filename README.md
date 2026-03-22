# Discord Channel Selector

A Python-based multi-agent recommendation system that helps users discover the most relevant Discord channels for their interests, role, experience level, and goals.

## Overview

Discord communities often grow into dozens of channels, which makes onboarding difficult for new members. People join a server, see a long channel list, and do not know where to start.

This project solves that problem by using AI agents to:
- collect a user’s profile through a short conversation,
- analyze available Discord channels against that profile, and
- return ranked channel recommendations with reasoning.

The repository also includes an experimental **ScaleDown** integration that compresses prompts before sending them to the LLM, so the same workflow can be compared for token usage, cost, and latency.

## Problem Statement

When a Discord server has many topic-specific channels, users commonly face three problems:
- **Discovery friction:** they cannot quickly find the channels most relevant to them.
- **Poor onboarding:** beginners, career switchers, students, and advanced users all need different starting points.
- **Information overload:** large channel lists make the community feel harder to navigate.

The main idea of this project is to build an AI-assisted onboarding layer that recommends the best channels for each user based on structured preference matching.

## What Has Been Built

The project currently includes:
- a **multi-agent workflow** built in Python,
- a **conversational preference collection agent**,
- a **channel analysis and ranking agent**,
- a **JSON-backed channel dataset** with metadata and matching criteria,
- a **CLI entry point** for interactive use,
- **programmatic usage examples** for integration into other systems,
- **LangSmith tracing support** for observability, and
- **ScaleDown-based compressed agent variants** for prompt optimization experiments.

## How the System Works

### 1. Preference collection
The first agent greets the user and collects four main inputs:
- interests,
- role,
- experience level, and
- goals.

### 2. Channel analysis
The second agent compares those preferences against each Discord channel in the dataset and asks the LLM to produce:
- a match score,
- reasoning,
- key matches, and
- potential concerns.

### 3. Ranking and recommendations
Channels above the configured threshold are sorted by score and returned as the final recommendation list, along with a natural-language summary for the user.

## Architecture

### Core application flow

```text
User
  ↓
DiscordChannelSelector (src/main.py)
  ↓
AgentOrchestrator (src/orchestrator.py)
  ├─ UserPreferenceAgent
  └─ ChannelAnalyzerAgent
        ↓
     Channel dataset (data/channels.json)
        ↓
     OpenAI model
        ↓
  Ranked Discord channel recommendations
```

### Main components

- **`DiscordChannelSelector`**
  - Main application interface.
  - Supports interactive CLI and programmatic execution.

- **`AgentOrchestrator`**
  - Coordinates the end-to-end workflow.
  - Passes collected preferences into channel analysis.

- **`UserPreferenceAgent`**
  - Handles the onboarding conversation.
  - Validates and structures user responses.

- **`ChannelAnalyzerAgent`**
  - Scores each channel against the collected preferences.
  - Returns ranked recommendations.

- **`ScaleDownUserPreferenceAgent` / `ScaleDownChannelAnalyzerAgent`**
  - Alternative agent implementations that compress prompts before LLM calls.
  - Used for token/cost/latency comparison experiments.

## Infrastructure and Integrations

This project is built around a lightweight local Python application with external AI services.

### Runtime stack
- **Python 3.8+**
- **LangChain / langchain-openai** for model access
- **LangSmith** for traces, monitoring, and debugging
- **OpenAI models** for conversation and recommendation logic
- **PyYAML** for configuration
- **python-dotenv** for environment loading
- **requests** for ScaleDown API calls

### External services
- **OpenAI**: required for the standard agent workflow.
- **LangSmith**: optional but supported for tracing and observability.
- **ScaleDown**: optional; used by the compressed-agent experiment.
- **Discord MCP / Discord API**: not wired into the main interactive flow yet, but the project is structured to support real Discord data sources later.

## Data and Matching Logic

Channel data is stored in `data/channels.json` and currently contains 15 example channels with fields such as:
- `name`
- `description`
- `topics`
- `activity_level`
- `target_audience`
- `best_for_roles`
- `best_for_goals`

The metadata in the JSON file documents the matching weights used by the project:
- **Interests:** 40%
- **Experience level:** 30%
- **Role:** 20%
- **Goals:** 10%

## Repository Structure

```text
langsmith-agent-discord/
├── data/
│   └── channels.json
├── src/
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── user_preference_agent.py
│   │   ├── channel_analyzer_agent.py
│   │   ├── scaledown_base_agent.py
│   │   ├── scaledown_user_preference_agent.py
│   │   └── scaledown_channel_analyzer_agent.py
│   ├── config_loader.py
│   ├── data_loader.py
│   ├── orchestrator.py
│   ├── main.py
│   ├── examples.py
│   ├── compare_agents.py
│   ├── run_tests.py
│   ├── test_single_agent.py
│   └── test_scaledown_compression.py
├── config.yaml
├── requirements.txt
├── setup.sh
├── setup.bat
└── README.md
```

## Setup

### Prerequisites
- Python 3.8 or newer
- An OpenAI API key
- Optional: LangSmith API key
- Optional: ScaleDown API key

### 1. Create a virtual environment

#### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create a `.env` file

Create a file named `.env` in the project root and add the values you need:

```env
OPENAI_API_KEY=your_openai_api_key
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=discord-channel-selector
SCALEDOWN_API_KEY=your_scaledown_api_key
```

Notes:
- `OPENAI_API_KEY` is required.
- `LANGCHAIN_*` values are optional unless you want LangSmith tracing.
- `SCALEDOWN_API_KEY` is only needed for the ScaleDown scripts.

### 4. Review configuration

Project behavior is configured in `config.yaml`, including:
- model names,
- agent temperature,
- preference questions,
- recommendation limits, and
- score threshold.

## How to Run

### Interactive CLI
Run the standard interactive onboarding flow:

```bash
python src/main.py
```

This will:
- start the application,
- greet the user,
- ask preference questions,
- analyze the channel dataset, and
- print ranked recommendations.

### Programmatic examples

```bash
python src/examples.py
```

### Agent comparison: standard vs ScaleDown

```bash
python src/compare_agents.py
```

This script compares the regular workflow with the compressed-agent workflow.

### Single-agent test

```bash
python src/test_single_agent.py
```

### ScaleDown compression test

```bash
python src/test_scaledown_compression.py
```

### Automated test suite

```bash
python src/run_tests.py
```

## Typical Use Cases

This repository can be used as:
- a prototype for **Discord onboarding assistants**,
- a reference implementation for **LangSmith-observable agent systems**,
- a starting point for **recommendation workflows over structured community data**, or
- an experiment bed for **prompt compression and cost optimization**.

## Current Scope

What the project does today:
- works with a curated JSON dataset of Discord channels,
- supports conversational preference collection,
- produces scored recommendations,
- supports standard and compressed agent variants,
- includes comparison and test scripts.

What is still future-facing:
- live Discord server ingestion,
- production bot deployment,
- web UI or dashboard,
- persistent storage for users and recommendation history.

## Documentation in the Repo

If you want more detail beyond this README, the repository also includes:
- `ARCHITECTURE.md` for system design details,
- `DATA_FLOW.md` for the data movement through the app,
- `PROJECT_SUMMARY.md` for a deliverables summary,
- `COMMANDS_REFERENCE.md` for script references, and
- `TESTING_GUIDE.md` / `ACCURACY_MEASUREMENT_GUIDE.md` for evaluation notes.

## Why This Project Matters

This project is a practical example of how AI agents can improve community navigation and onboarding. Instead of forcing users to manually browse every Discord channel, it turns a noisy server structure into a guided recommendation experience.

In short, the project aims to make Discord communities easier to enter, easier to understand, and more personalized for each member.
