# jdo

**Just Do One thing at a time**

An AI-powered conversational CLI for people who want to achieve their goals without drowning in project management overhead. Have a conversation, and jdo turns your intentions into a structured plan you can actually follow through on.

---

## Why jdo?

### The Problem with Todo Apps

Your todo list is a graveyard of good intentions. Todoist, TickTick, and their cousins are brilliant at *collecting* tasks—but terrible at helping you *complete* them. The list grows. The guilt grows. You reorganize, re-prioritize, declare "inbox zero"... and three weeks later you're drowning again.

**The uncomfortable truth:** A todo list has no skin in the game. Nobody's waiting. Nothing happens if you don't do it. That's why 41% of todo items are never completed.

### The Problem with Scheduling Apps

Sunsama and Motion took a different approach: time-block everything. If it's not on your calendar, it doesn't exist. The AI schedules your tasks around meetings, and you just... follow the plan.

Except you don't. Because life happens. Meetings run over. Energy crashes. And now you're rescheduling the same task for the fourth time this week, watching the AI shuffle your failures into tomorrow.

**Scheduling apps optimize for *time*. But time isn't the bottleneck—*integrity* is.**

### A Different Philosophy

jdo is built on a simple principle from the [Meta Performance Institute](https://metaperformanceinstitute.com/):

> **Commitments are promises, not preferences.**

A commitment isn't a task you *might* do. It's a promise to a specific person (your stakeholder) to deliver something specific by a specific time. When you make fewer commitments and keep them all, something shifts. People trust you. You trust yourself. Work actually gets done.

This is what MPI calls **integrity**—not morality, but *workability*. The engine that makes everything else possible.

**The three rules of integrity:**
1. **Do what you said, by when you said**
2. **Notify stakeholders as soon as you know you can't**
3. **Clean up the mess caused by any broken commitment**

jdo doesn't let you dump 47 items into a list and forget about them. Every commitment has a stakeholder, a deliverable, and a due date. You make fewer promises—and you keep them.

---

## The Conversational Difference

Most productivity tools ask you to learn their system. jdo asks you one question: *What do you want to accomplish?*

Tell it in plain language. The AI extracts goals, milestones, commitments, and tasks—organizing everything into a hierarchy that makes sense. No forms to fill out. No clicking through menus. Just talk about what matters to you.

---

## Features

| | |
|---|---|
| **Conversational Interface** | Chat naturally—the AI structures your goals for you |
| **Flexible Hierarchy** | Visions, Goals, Milestones, Commitments, Tasks |
| **Streaming AI Responses** | Responses appear token-by-token for a responsive feel |
| **Hybrid Input** | Natural language primary, slash commands for power users |
| **Recurring Commitments** | Set it once, generate instances automatically |
| **Multiple AI Providers** | OpenAI or OpenRouter—your choice |
| **Local-First Storage** | Your data stays on your machine, always |

---

## Installation

**Requirements:** Python 3.11+ and [uv](https://docs.astral.sh/uv/)

```bash
# Clone the repository
git clone https://github.com/JRedeker/jdo.git
cd jdo

# Install dependencies
uv sync

# Run the app
uv run jdo
```

<details>
<summary>Install uv if you don't have it</summary>

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

</details>

---

## Quick Start

**1. Configure your AI provider**

```bash
export OPENAI_API_KEY="sk-..."
```

<details>
<summary>Using OpenRouter?</summary>

```bash
export OPENROUTER_API_KEY="sk-or-..."
export JDO_AI_PROVIDER="openrouter"
```

</details>

**2. Launch**

```bash
uv run jdo
```

**3. Start talking about what you want to accomplish.**

---

## Example Conversation

```
> I need to send the quarterly report to Sarah by Friday

I'll create a commitment:
  Deliverable: Send quarterly report
  Stakeholder: Sarah
  Due: Friday, Jan 17

Does this look right?

> yes

Created commitment #a1b2c3: Send quarterly report

> show my commitments

ID      Deliverable              Stakeholder    Due         Status
------  -----------------------  -------------  ----------  --------
a1b2c3  Send quarterly report    Sarah          Fri Jan 17  pending

1 active commitment(s)

> I want to get promoted to senior engineer this year

I'll create a goal for you:
  Title: Get promoted to senior engineer
  Target: December 31, 2025

Does this look right?
```

---

## Slash Commands

For power users who prefer instant, deterministic actions:

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/list` | List commitments (default) |
| `/list goals` | List all goals |
| `/list visions` | List all visions |
| `/commit "..."` | Create a new commitment |
| `/review` | Review visions due for quarterly review |

Or just type naturally—the AI understands plain English.

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `jdo` | Launch the conversational REPL |
| `jdo capture "text"` | Quick capture for later triage |
| `jdo db status` | Show database migration status |
| `jdo db upgrade` | Apply pending migrations |

---

## How It Works

### The Hierarchy

jdo organizes your work into five levels. Use as many or as few as you need:

```
Vision ─────────────── "Become financially independent"
   │
   └── Goal ────────── "Build passive income stream" (due: Dec 2025)
          │
          └── Milestone ─── "Launch info product"
                 │
                 └── Commitment ─── "Send draft to editor by Friday"
                        │
                        └── Task ────── "Write course outline"
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|:---------|:--------|:------------|
| `JDO_AI_PROVIDER` | `openai` | Provider: `openai`, `openrouter` |
| `JDO_AI_MODEL` | `gpt-4o` | Model identifier |
| `JDO_TIMEZONE` | `America/New_York` | Your local timezone |
| `JDO_DATABASE_PATH` | *(platform default)* | Custom database location |

### Data Location

All data is stored locally using platform-appropriate directories:

| Platform | Location |
|:---------|:---------|
| Linux | `~/.local/share/jdo/` |
| macOS | `~/Library/Application Support/jdo/` |
| Windows | `%LOCALAPPDATA%\jdo\` |

**Files:**
- `jdo.db` — SQLite database containing all your data
- `auth.json` — API credentials storage

---

## Development

### Setup

```bash
git clone https://github.com/JRedeker/jdo.git
cd jdo
uv sync --all-groups
```

### Commands

```bash
uv run jdo                              # Run the app

uv run ruff check --fix src/ tests/     # Lint
uv run ruff format src/ tests/          # Format
uvx pyrefly check src/                  # Type check
uv run pytest                           # Test
```

### Structure

```
src/jdo/
├── ai/         Agent, tools, context extraction
├── auth/       API key management
├── commands/   Command parsing and handlers
├── config/     Settings, paths
├── db/         SQLite engine, migrations
├── models/     SQLModel entities
├── output/     Rich formatters for CLI output
├── repl/       REPL loop and session management
└── cli.py      CLI entry point
```

---

## Requirements

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) package manager
- Modern terminal with Unicode support
- API key from OpenAI or OpenRouter

**Tested on:** macOS, Linux, Windows (Windows Terminal recommended)

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Ensure `ruff check` and `pytest` pass
4. Submit a pull request

---

## License

MIT

---

<sub>Built with [PydanticAI](https://ai.pydantic.dev/) · [SQLModel](https://sqlmodel.tiangolo.com/) · [Rich](https://rich.readthedocs.io/) · [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/)</sub>
