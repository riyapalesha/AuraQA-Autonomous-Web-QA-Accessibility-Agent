# ⚡ AgentFlow: Conversational Enterprise Workflow Orchestration Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/ui-Streamlit-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AgentFlow** is an enterprise-grade agentic AI platform that transforms conversational natural language requests into structured, executable Directed Acyclic Graph (DAG) workflows across enterprise tools. It incorporates **Human-in-the-Loop (HITL) safety gates** to prevent unauthorized mutations, stateful checkpointing for pause-and-resume operations, and real-time execution monitoring.

---

## 🎯 Key Features

- **Natural Language Intent Decomposition:** Decomposes complex user requests into discrete, typed workflow tasks with dependency resolution.
- **Human-in-the-Loop (HITL) Safety Gates:** Non-destructive operations (read/diagnostics) execute autonomously, while sensitive mutations (database updates, alerts, access grants) halt the state graph and request approval via interactive UI cards.
- **State Machine Architecture (LangGraph):** Built using cyclical state graphs with conditional routing and state persistence rather than rigid linear chains.
- **Session Checkpointing & Audit Trail:** Persists conversation states and full execution audit trails into SQLite, enabling zero-loss recovery across restarts.
- **Interactive Dual-Panel UI:** Features a conversational interface alongside a live visual task monitor showing execution status and output inspectability.
- **Zero-Dependency Demo Mode:** Ships with an intelligent built-in mock LLM engine so the platform can be evaluated immediately without external API keys or cloud dependencies.

---

## 🏗️ Architecture

```
                               ┌────────────────────────┐
                               │   User Conversational   │
                               │      Chat Input        │
                               └───────────┬────────────┘
                                           │
                                           ▼
                               ┌────────────────────────┐
                               │   Planner Node (LLM)   │
                               │ (Intent Decomposition) │
                               └───────────┬────────────┘
                                           │
                                           ▼
                             ┌────────────────────────────┐
                             │    Conditional Router      │◄──────────┐
                             └──────┬──────────────┬──────┘           │
                 Requires Approval? │              │ Safe / Approved  │
                                    ▼              ▼                  │
                     ┌──────────────────┐    ┌──────────────────┐     │
                     │  HITL Gate Node  │    │  Executor Node   │     │
                     │ (Pauses for User)│    │ (Tool Invocation)│─────┘
                     └────────┬─────────┘    └──────────────────┘
                              │
                    User Click: Approve / Reject
                              │
                              ▼
                     ┌──────────────────┐
                     │ Synthesizer Node │
                     │   (Report/RCA)   │
                     └──────────────────┘
```

---

## 🚀 Quick Start

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone <your-repo-url>
cd AI-Project
pip install -r requirements.txt
```

### 2. Run the Application
Launch the interactive Streamlit dashboard:
```bash
python main.py
# Or directly:
streamlit run ui/app.py
```

### 3. (Optional) Configure Real LLM Providers
By default, AgentFlow runs in **Mock Demo Mode** for immediate zero-config testing. To use external models, copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Set `LLM_PROVIDER` to `openai`, `groq`, `gemini`, or `ollama` and provide your API key.

---

## 🧪 Testing

Run the automated test suite verifying state transitions, HITL gates, and rejection branches:
```bash
python -m pytest
```

---

## 💼 Master's Resume & Interview Preparation

For an in-depth breakdown of architecture decisions, interview questions, and resume bullet points, see the [Interview Guide](docs/INTERVIEW_GUIDE.md).
