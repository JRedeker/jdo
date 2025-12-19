# ai-provider Spec Delta

## MODIFIED Requirements

### Requirement: Agent Configuration

The system SHALL provide a PydanticAI agent configured for commitment management assistance.

#### Scenario: Create agent with OpenAI provider
- **WHEN** settings specify `ai_provider=openai` and `ai_model=gpt-4o`
- **THEN** agent is created with model identifier "openai:gpt-4o"

#### Scenario: Create agent with OpenRouter provider
- **WHEN** settings specify `ai_provider=openrouter` and `ai_model=anthropic/claude-3.5-sonnet`
- **THEN** agent is created with model identifier "openrouter:anthropic/claude-3.5-sonnet"

#### Scenario: Agent has system prompt
- **WHEN** agent is created
- **THEN** it has a system prompt focused on commitment tracking assistance

#### Scenario: Agent has tools registered
- **WHEN** agent is created via `create_agent()`
- **THEN** all query tools are registered (commitments, goals, milestones, visions)
- **AND** tools are ready to be called during agent execution

## ADDED Requirements

### Requirement: Agent Tool Registration

The system SHALL register all query tools when creating the agent.

#### Scenario: Tools registered on creation
- **WHEN** `create_agent()` is called
- **THEN** `register_tools()` is called on the agent
- **AND** all 5 query tools are available for agent use

#### Scenario: Tools accessible during execution
- **WHEN** AI agent determines it needs commitment data
- **THEN** it can call the appropriate query tool
- **AND** tool results are incorporated into the response

