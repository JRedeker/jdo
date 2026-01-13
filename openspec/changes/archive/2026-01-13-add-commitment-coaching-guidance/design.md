# Design: Commitment Coaching Guidance

## Context

JDO differentiates itself from task managers by focusing on commitments - promises with stakeholders and due dates. However, users naturally default to task-list thinking ("I need to do X") rather than commitment thinking ("I promised to deliver X to Y by Z").

The AI agent should recognize this pattern and guide users toward the commitment mindset without blocking their workflow.

## Goals

1. Help users discover the commitment behind task-like inputs
2. Educate users on the task vs commitment distinction
3. Reinforce JDO's core philosophy through conversational coaching
4. Maintain a helpful, non-blocking tone

## Non-Goals

1. Prevent users from creating tasks entirely (tasks are valid within commitments)
2. Force lengthy interrogations for simple inputs
3. Lecture users repeatedly about the same concepts
4. Make the AI pedantic or annoying

## Decisions

### Decision 1: Add Commitment-First Coaching to System Prompt

**What**: Extend the agent system prompt with guidance on recognizing task-like inputs and asking commitment-focused questions.

**Why**: The system prompt is the primary mechanism for shaping AI behavior. Adding explicit coaching instructions ensures consistent behavior across conversations.

**Alternatives Considered**:
- Separate coaching agent: Adds complexity, latency
- Hard-coded pattern matching: Brittle, misses nuanced cases
- User preference to disable: Premature optimization; start with coaching enabled

### Decision 2: Single Question at a Time (Already Implemented)

**What**: The AI asks one clarifying question, waits for response, then follows up if needed.

**Why**: Respects the recently-added "one question at a time" behavior. Coaching questions integrate naturally.

### Decision 3: Graceful Degradation

**What**: If user insists on a task without commitment context, AI acknowledges and explains they'll need to link it to a commitment later.

**Why**: Non-blocking experience. User education without frustration.

### Decision 4: Contextual Awareness

**What**: AI uses conversation history to avoid repetitive coaching. If user has already created a commitment in this session, AI can suggest adding tasks to it.

**Why**: Smart coaching that gets out of the way once user understands.

## Coaching Flow

```
User: "I need to gather the Q4 sales data"

AI (recognizes task-like input without deliverable/stakeholder):
  "What will you deliver with this data? For example, are you preparing 
   a report or presentation for someone?"

User: "It's for the quarterly business review with the leadership team"

AI (now has context for commitment):
  "Got it! Let me create this as a commitment:
   
   Deliverable: Q4 business review presentation
   Stakeholder: Leadership team
   Due: [asks for date]
   
   Then we can add 'gather Q4 sales data' as a task within it."
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| AI becomes annoying with too many questions | Limit to 1-2 coaching questions per input; accept gracefully if user pushes back |
| Users feel "lectured" | Use conversational, helpful tone; avoid jargon like "commitment-based thinking" |
| Slows down power users | Power users learn quickly and provide full context; coaching naturally fades |
| AI misidentifies commitment vs task | Err on side of asking; let user clarify |

## Open Questions

1. Should there be a way to disable coaching guidance? (Defer - start with always-on)
2. Should coaching adapt based on user's history with JDO? (Future enhancement)

## Research Validation

This design was validated through architectural research on 2026-01-13.

### Validated Patterns ✅

| Decision | Research Finding | Source |
|----------|------------------|--------|
| System prompt coaching | Standard pattern for LLM behavior shaping | PydanticAI docs, Aider implementation |
| One question at a time | Reduces cognitive load, mirrors natural conversation | clig.dev, CHI 2024 research, NN/g |
| Non-blocking guidance | Aligns with nudge theory ("liberty-preserving") | Blink UX, LSE research |
| Conversation history for context | PydanticAI native pattern; no additional state needed | PydanticAI message-history docs |

### Psychology Research Nuances ⚠️

The Cialdini Commitment-Consistency principle is **validated for external deliverables** but requires nuance:

- **Effective**: Commitments to *external stakeholders* with defined deliverables (JDO's model)
- **Potentially counterproductive**: Public announcements of *personal identity goals* (Gollwitzer 2009)

JDO's commitment model (deliverable + stakeholder + due date) correctly applies the psychology because it creates external accountability, not mere "identity symbols."

**Key sources:**
- Gollwitzer et al. (2009) "When Intentions Go Public" - Psychological Science
- ASTD study: 65-95% goal completion with accountability partners
- PRINCE2: Deliverables methodology for accountability

### Simplification Applied 🎯

Original proposal had 3 requirements. Research found 2 are emergent behaviors:

| Requirement | Research Finding | Action |
|-------------|------------------|--------|
| Commitment-First Coaching | Core behavior, needs explicit prompt | **Keep** |
| Task vs Commitment Education | Emergent from coaching questions | **Remove** - LLMs naturally explain when asked |
| Contextual Commitment Suggestions | Handled by existing message history | **Remove** - already works |

**Result**: Single requirement, ~10-15 lines of prompt additions vs ~50 lines originally proposed.

### Future Considerations

1. **Prompt maintainability**: Current system prompt is 124 lines. Consider migrating to PydanticAI's `@agent.instructions` decorator pattern if it grows beyond ~200 lines.

2. **Token optimization**: If coaching prompts grow, consider `history_processors` to summarize old coaching exchanges while preserving key facts.

### Research Sources

- PydanticAI Documentation: https://ai.pydantic.dev/agents/, https://ai.pydantic.dev/message-history/
- Command Line Interface Guidelines: https://clig.dev/
- Nielsen Norman Group - Commitment Consistency: https://www.nngroup.com/articles/commitment-consistency-ux/
- Nielsen Norman Group - Progressive Disclosure: https://www.nngroup.com/articles/progressive-disclosure/
- Gollwitzer et al. (2009): https://journals.sagepub.com/doi/10.1111/j.1467-9280.2009.02336.x
- CHI 2024 Chatbot Cognitive Load: https://dl.acm.org/doi/10.1145/3706599.3719862
- Blink UX - Nudge Theory: https://blinkux.com/ideas/how-design-nudges-can-effect-behavior-change
