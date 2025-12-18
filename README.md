# jdo ✨

**Just Do One thing at a time**

An AI-powered terminal app for people who want to achieve their goals without drowning in project management overhead. Have a conversation, and jdo turns your intentions into a structured plan you can actually follow through on.

---

## 🤔 Why jdo?

### The Problem with Todo Apps

Your todo list is a graveyard of good intentions. Todoist, TickTick, and their cousins are brilliant at *collecting* tasks—but terrible at helping you *complete* them. The list grows. The guilt grows. You reorganize, re-prioritize, declare "inbox zero"... and three weeks later you're drowning again.

**The uncomfortable truth:** A todo list has no skin in the game. Nobody's waiting. Nothing happens if you don't do it. That's why 41% of todo items are never completed.

### The Problem with Scheduling Apps

Sunsama and Motion took a different approach: time-block everything. If it's not on your calendar, it doesn't exist. The AI schedules your tasks around meetings, and you just... follow the plan.

Except you don't. Because life happens. Meetings run over. Energy crashes. And now you're rescheduling the same task for the fourth time this week, watching the AI shuffle your failures into tomorrow.

**Scheduling apps optimize for *time*. But time isn't the bottleneck—*integrity* is.**

### A Different Philosophy

jdo is built on a simple principle from the [Meta Performance™ Institute](https://metaperformanceinstitute.com/):

> **Commitments are promises, not preferences.**

A commitment isn't a task you *might* do. It's a promise to a specific person (your stakeholder) to deliver something specific by a specific time. When you make fewer commitments and keep them all, something shifts. People trust you. You trust yourself. Work actually gets done.

This is what MPI calls **integrity**—not morality, but *workability*. The engine that makes everything else possible.

**The three rules of integrity:**
1. 🎯 **Do what you said, by when you said**
2. 📢 **Notify stakeholders as soon as you know you can't**
3. 🧹 **Clean up the mess caused by any broken commitment**

jdo doesn't let you dump 47 items into a list and forget about them. Every commitment has a stakeholder, a deliverable, and a due date. You make fewer promises—and you keep them.

### How jdo is Different

| | Todo Apps | Scheduling Apps | jdo |
|:--|:--|:--|:--|
| **Mental model** | Infinite list | Calendar blocks | Promises to people |
| **Accountability** | None | Time pressure | Stakeholder relationships |
| **When you can't deliver** | Mark incomplete, feel guilty | Reschedule, feel guilty | Notify stakeholder, clean up, maintain trust |
| **Success metric** | Tasks checked off | Hours scheduled | Commitments kept |
| **Core belief** | More organization = more done | Better scheduling = more done | Fewer promises kept = more done |

---

## 💬 The Conversational Difference

Most productivity tools ask you to learn their system. jdo asks you one question: *What do you want to accomplish?*

Tell it in plain language. The AI extracts goals, milestones, commitments, and tasks—organizing everything into a hierarchy that makes sense. No forms to fill out. No clicking through menus. Just talk about what matters to you.

---

## ⚡ Features

| | |
|---|---|
| 💬 **Conversational Interface** | Chat naturally—the AI structures your goals for you |
| 🏗️ **Flexible Hierarchy** | Visions → Goals → Milestones → Commitments → Tasks |
| ⌨️ **Keyboard-First Design** | Navigate everything without touching your mouse |
| 🔄 **Recurring Commitments** | Set it once, generate instances automatically |
| 💾 **Draft Recovery** | Crash mid-thought? Pick up right where you left off |
| 🤖 **Multiple AI Providers** | Anthropic, OpenAI, or OpenRouter—your choice |
| 🔒 **Local-First Storage** | Your data stays on your machine, always |

---

## 📦 Installation

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
<summary>🔧 Install uv if you don't have it</summary>

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

</details>

---

## 🚀 Quick Start

**1. Configure your AI provider**

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

<details>
<summary>🔌 Using a different provider?</summary>

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."
export JDO_AI_PROVIDER="openai"

# OpenRouter
export OPENROUTER_API_KEY="sk-or-..."
export JDO_AI_PROVIDER="openrouter"
```

</details>

**2. Launch**

```bash
uv run jdo
```

**3. Press `n` to start a new chat and describe what you want to accomplish.**

---

## ⌨️ Keyboard Shortcuts

```
Navigation                      Views
─────────────────────────────────────────────────
n   New chat                    g   Goals
s   Settings                    c   Commitments
q   Quit                        v   Visions
d   Toggle dark/light mode      m   Milestones
                                h   Full hierarchy
                                o   Orphan commitments
```

---

## 🧠 How It Works

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

### Example Conversation

```
You: I want to get promoted to senior engineer this year

 AI: I've created a goal for you:

     Goal: "Get promoted to senior engineer"
     Due: December 31, 2025

     What would make this happen? Any specific milestones
     you're thinking about?

You: I need to lead a major project and improve my system design skills

 AI: Added two milestones:

     • Lead a major project
     • Improve system design skills

     Want to break either of these down into specific tasks?
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|:---------|:--------|:------------|
| `JDO_AI_PROVIDER` | `anthropic` | Provider: `anthropic`, `openai`, `openrouter` |
| `JDO_AI_MODEL` | `claude-sonnet-4-20250514` | Model identifier |
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
- `auth.json` — OAuth tokens (if using browser-based auth)

---

## 🛠️ Development

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
├── auth/       OAuth flows, API key management
├── commands/   Chat command parsing
├── config/     Settings, paths
├── db/         SQLite engine, migrations
├── models/     SQLModel entities
├── screens/    Textual screens (home, chat, settings)
├── widgets/    Reusable UI components
└── app.py      Application entry point
```

---

## 📋 Requirements

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) package manager
- Modern terminal with Unicode support
- API key from Anthropic, OpenAI, or OpenRouter

**Tested on:** macOS, Linux, Windows (Windows Terminal recommended)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Ensure `ruff check` and `pytest` pass
4. Submit a pull request

---

## 📄 License

MIT

---

<sub>Built with 💜 using [Textual](https://textual.textualize.io/) · [PydanticAI](https://ai.pydantic.dev/) · [SQLModel](https://sqlmodel.tiangolo.com/) · [Rich](https://rich.readthedocs.io/)</sub>
