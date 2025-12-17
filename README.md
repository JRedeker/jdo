# jdo

**Just Do One thing at a time**

An AI-powered terminal app for people who want to achieve their goals without drowning in project management overhead. Have a conversation, and jdo turns your intentions into a structured plan you can actually follow through on.

---

## Why jdo?

Most productivity tools ask you to learn their system. jdo asks you one question: *What do you want to accomplish?*

Tell it in plain language. The AI extracts goals, milestones, tasks, and commitments—organizing everything into a hierarchy that makes sense. No forms to fill out. No clicking through menus. Just talk about what matters to you.

---

## Features

| | |
|---|---|
| **Conversational Interface** | Chat naturally—the AI structures your goals for you |
| **Flexible Hierarchy** | Visions → Goals → Milestones → Tasks → Commitments |
| **Keyboard-First Design** | Navigate everything without touching your mouse |
| **Draft Recovery** | Crash mid-thought? Pick up right where you left off |
| **Multiple AI Providers** | Anthropic, OpenAI, or OpenRouter—your choice |
| **Local-First Storage** | Your data stays on your machine, always |

---

## Installation

**Requirements:** Python 3.11+

```bash
pip install jdo
```

<details>
<summary>Alternative: install with uv</summary>

```bash
uv pip install jdo
```

</details>

---

## Quick Start

**1. Configure your AI provider**

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

<details>
<summary>Using a different provider?</summary>

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
jdo
```

**3. Press `n` to start a new chat and describe what you want to accomplish.**

---

## Keyboard Shortcuts

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
                 └── Task ────── "Write course outline"
                        │
                        └── Commitment ─── "Send draft to editor by Friday"
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

## Configuration

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

## Development

### Setup

```bash
git clone https://github.com/your-username/jdo.git
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

## Requirements

- Python 3.11 or later
- Modern terminal with Unicode support
- API key from Anthropic, OpenAI, or OpenRouter

**Tested on:** macOS, Linux, Windows (Windows Terminal recommended)

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Ensure `ruff check` and `pytest` pass
4. Submit a pull request

---

## License

*[Add your license here]*

---

<sub>Built with [Textual](https://textual.textualize.io/) · [PydanticAI](https://ai.pydantic.dev/) · [SQLModel](https://sqlmodel.tiangolo.com/) · [Rich](https://rich.readthedocs.io/)</sub>
