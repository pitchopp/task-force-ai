# TaskForce AI

**TaskForce AI** is a personal multi-agent system designed to execute tasks autonomously across both personal and professional contexts.

It acts as a **private AI-powered task force**: a team of intelligent agents that can understand instructions, collaborate, and take action on your behalf — all accessible through a single Telegram bot.

---

## Vision

The goal of TaskForce AI is to build a system where:

- You give a high-level instruction via Telegram
- A main orchestrator agent ("bras droit") understands your intent and delegates to specialized agents
- The system grows organically — when a capability is missing, it suggests creating a new agent
- You stay in control: low-risk tasks run autonomously, high-risk actions require your approval

Ultimately, TaskForce AI aims to become a **personal execution layer for everything you do**.

---

## Architecture

```
Telegram (aiogram 3.x)
    |
    v
FastAPI (webhook + API)
    |
    v
LangGraph (orchestration)
    |
    +---> Router node : intent analysis, flow decision
    |
    +---> Brain node : main agent ("bras droit")
    |         |
    |         +---> Claude Agent SDK
    |         |       +---> Built-in tools (Read, Edit, Bash, Grep...)
    |         |       +---> Custom MCP tools (telegram, approval, evolution)
    |         |
    |         +---> Sub-agent delegation
    |                 +---> Agents loaded from config/agents/*.yaml
    |
    +---> Approval node : human-in-the-loop via Telegram InlineKeyboard
    |
    +---> Response node : send result to user
    |
PostgreSQL (LangGraph checkpoints + task history)
Redis (FSM state + approval events)
```

### How LangGraph and Claude Agent SDK coexist

- **LangGraph** = flow orchestrator. Manages the state graph (router -> brain -> approval -> response), checkpointing (resume after crash), human-in-the-loop interrupts, and conversation persistence.
- **Claude Agent SDK** = execution engine inside the "brain" node. Calls Claude with agent prompts, runs tools (built-in + custom MCP), delegates to sub-agents via `AgentDefinition`.

In short: LangGraph orchestrates *when and what*, the SDK orchestrates *how* (with Claude).

---

## Core Concepts

### Agents
Autonomous units defined via YAML config files. Each agent has:
- A system prompt and description
- A set of tools (built-in + custom MCP)
- A model (Opus, Sonnet, or Haiku — configurable per agent)
- A risk level (low, medium, high, critical)
- Capabilities and limitations tags

### Agent Factory
A config-driven system to create new agents:
- Add a YAML file in `config/agents/`
- The factory loads it and registers an `AgentDefinition`
- The new agent is immediately available for delegation

### Evolution
When the main agent can't find a suitable sub-agent for a task:
1. It handles the task with its general capabilities
2. It flags the capability gap via Telegram
3. It suggests creating a new specialized agent
4. User approves → new YAML config is generated → agent is live

### Human-in-the-Loop
Hybrid autonomy model:
- **Low-risk** actions execute automatically
- **High-risk** actions trigger an approval request in Telegram (InlineKeyboard)
- User can approve, deny, or modify before execution proceeds

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12+ |
| Package Manager | uv |
| LLM | Claude API (Opus / Sonnet / Haiku, configurable per agent) |
| Agent Execution | Claude Agent SDK |
| Orchestration | LangGraph |
| Backend | FastAPI + Uvicorn |
| Interface | Telegram bot (aiogram 3.x) |
| Database | PostgreSQL (checkpoints + persistence) |
| Cache/Queue | Redis (FSM state + approval events) |
| Deployment | Docker + Dokploy |
| Migrations | Alembic |

---

## Project Structure

```
task-force-ai/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── alembic.ini
├── alembic/
│
├── config/
│   ├── settings.py                 # Pydantic Settings (env-based)
│   └── agents/                     # Agent YAML configs
│       └── _template.yaml
│
├── src/
│   └── taskforce/
│       ├── main.py                 # FastAPI entrypoint + lifespan
│       │
│       ├── telegram/
│       │   ├── bot.py              # Bot + Dispatcher + Router
│       │   ├── handlers.py         # Message/command handlers
│       │   ├── callbacks.py        # InlineKeyboard handlers (approvals)
│       │   └── middleware.py       # Auth (Telegram ID whitelist)
│       │
│       ├── api/
│       │   └── routes.py           # Webhook + health check
│       │
│       ├── graph/
│       │   ├── state.py            # GraphState (TypedDict)
│       │   ├── workflow.py         # LangGraph StateGraph
│       │   ├── nodes.py            # Node functions
│       │   └── checkpointer.py     # PostgreSQL checkpointer
│       │
│       ├── orchestrator/
│       │   ├── brain.py            # Brain node (Claude Agent SDK)
│       │   └── approval.py         # Approval workflow
│       │
│       ├── agents/
│       │   ├── factory.py          # YAML -> AgentDefinition
│       │   ├── registry.py         # Agent registry
│       │   └── evolution.py        # Gap detection + agent creation
│       │
│       ├── tools/
│       │   ├── telegram_tools.py   # MCP: send_message, send_file
│       │   ├── approval_tools.py   # MCP: request_approval
│       │   └── evolution_tools.py  # MCP: flag_capability_gap
│       │
│       ├── storage/
│       │   ├── database.py         # SQLAlchemy async engine
│       │   ├── models.py           # Task, AgentRun, ApprovalRequest
│       │   └── redis_client.py     # Redis async client
│       │
│       └── utils/
│           └── risk.py             # Risk matrix
│
└── tests/
```

---

## Roadmap

### Phase 1 — Skeleton + Telegram Bot
Set up project (uv), FastAPI + aiogram webhook, echo bot with auth middleware.

### Phase 2 — LangGraph + Brain
Wire LangGraph state graph with Claude Agent SDK in the brain node. First real AI responses via Telegram.

### Phase 3 — Agent Factory + Config
YAML-based agent definitions, factory loader, registry. Dynamic sub-agent delegation.

### Phase 4 — Human-in-the-Loop
Approval workflow for high-risk actions via Telegram InlineKeyboard. Risk matrix.

### Phase 5 — Evolution System
Capability gap detection, agent creation suggestions, auto-generation of YAML configs.

### Phase 6 — Persistence + History
PostgreSQL models for task tracking, agent runs, conversation history. Alembic migrations.

### Phase 7 — Docker + Dokploy
Dockerfile, docker-compose.yml (app, postgres, redis), production deployment via Dokploy.

---

## Development

```bash
# Setup
uv sync

# Run locally
cp .env.example .env
# Edit .env with your BOT_TOKEN (from @BotFather)

# Start infra (PostgreSQL + Redis)
docker compose up -d postgres redis

# Run DB migrations
uv run alembic upgrade head

# Start the bot (polling mode, no webhook needed for dev)
uv run uvicorn taskforce.main:app --reload

# Run with full Docker stack
docker compose up
```

---

## Philosophy

> You shouldn't do tasks.
> You should define outcomes — and let your agents handle the rest.
