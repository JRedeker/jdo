# Change: Add Commitment Coaching Guidance

## Why

Users approaching JDO may default to "task list" thinking, entering isolated action items like "gather data" or "write code" without connecting them to meaningful deliverables and stakeholders. This undermines JDO's core philosophy: **commitments are promises, not preferences**.

Research supports this approach:
- Cialdini's Commitment-Consistency principle shows that explicit commitments to *external stakeholders* create stronger follow-through than private task lists (NN/g)
- Deliverables create accountability by assigning clear responsibility and stakeholder ownership (PRINCE2, Adapt Consulting)
- ASTD research shows 65% goal completion with verbal commitment to another person, rising to 95% with scheduled accountability appointments

**Important nuance**: This applies to *external deliverables* (promises to others), not personal identity goals. Gollwitzer (2009) found that publicly announcing *personal aspirations* can actually reduce follow-through. JDO's model is specifically about deliverables to stakeholders, which is the effective application of commitment psychology.

The AI should proactively guide users to think in terms of "what am I delivering, to whom, and by when?" rather than accepting isolated tasks.

## What Changes

- **AI Coaching Behavior**: Add ~10-15 lines to the existing "Coaching Behaviors" section in the system prompt to recognize task-like inputs and guide users toward commitment-level thinking
- **Deliverable-First Prompting**: When users describe work without a stakeholder or deliverable, AI asks ONE clarifying question to surface the larger commitment
- **Graceful Acceptance**: Users can still create tasks within commitments - coaching educates without blocking

**Simplification note**: Task vs commitment education and contextual suggestions are *emergent behaviors* from the coaching prompt and existing conversation history. They don't require separate implementation.

## Impact

- **Affected specs**: `ai-conversation` (adds new coaching requirement)
- **Affected code**:
  - `src/jdo/ai/agent.py` (system prompt modifications)
  - `tests/unit/ai/test_agent.py` (verify prompt contains coaching section)
- **User experience**: More guided onboarding, clearer mental model, stronger commitment framing
- **No breaking changes**: Existing functionality preserved; this adds proactive guidance

## Research Summary

### Key Insight: Commitments Create Accountability, Tasks Don't

| Aspect | Task-List Thinking | Commitment Thinking |
|--------|-------------------|---------------------|
| Framing | "What do I need to do?" | "What am I promising to deliver?" |
| Accountability | To myself (easily broken) | To a stakeholder (social contract) |
| Completion | Checked off a list | Delivered to someone who cares |
| Psychology | Optional activity | Promise with integrity implications |

### Examples of Coaching Opportunities

| User Says | Hidden Commitment | AI Should Ask |
|-----------|-------------------|---------------|
| "Gather sales data" | Quarterly report for VP Sales | "What will you deliver with this data, and who needs it?" |
| "Write unit tests" | Feature release to QA team | "What feature or deliverable do these tests support?" |
| "Review PR" | Code review for teammate | "Who is waiting for this review, and when do they need it?" |
| "Prepare slides" | Presentation to stakeholders | "What's the presentation for, and who's the audience?" |

### JDO Philosophy Alignment

From README.md:
> "A commitment isn't a task you *might* do. It's a promise to a specific person (your stakeholder) to deliver something specific by a specific time."

The AI should embody this philosophy by helping users discover the commitment behind every task.

## Research Validation

This proposal was validated through architectural research. See `design.md` for detailed findings.

**Validated decisions:**
- ✅ System prompt coaching is the standard pattern (PydanticAI, Aider)
- ✅ One question at a time reduces cognitive load (clig.dev, NN/g, CHI 2024)
- ✅ Non-blocking guidance aligns with nudge theory (liberty-preserving)
- ✅ Conversation history handles context naturally (no additional state needed)

**Simplifications applied:**
- Reduced from 3 requirements to 1 (others are emergent behaviors)
- Prompt additions minimized to ~10-15 lines vs original ~50
- Leverages existing "Coaching Behaviors" section structure

**Sources:**
- Cialdini, R. "Influence: Science and Practice" via NN/g
- Gollwitzer et al. (2009) "When Intentions Go Public" - Psychological Science
- clig.dev - Command Line Interface Guidelines
- PydanticAI documentation - Message History patterns
- PRINCE2 methodology - Deliverables and accountability
