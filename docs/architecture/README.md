# HR Agent Architecture Documentation

Complete visual architecture diagrams for the HR Agent multi-agent orchestration framework.

## Documentation Index

### 1. **[System Architecture Overview](./01-system-architecture.md)**
   - High-level component relationships
   - All major layers (UI, App, Orchestration, Agents, Tools, Framework, Data, Adapters)
   - How components connect together
   - **Best for**: Getting a complete picture of the entire system

### 2. **[Message Flow: End-to-End](./02-message-flow.md)**
   - Step-by-step flow from user input to response
   - Sequence diagram showing all interactions
   - HITL interrupt flow for profile updates
   - Tool calling loop lifecycle
   - ThreadID namespacing
   - **Best for**: Understanding how a request travels through the system

### 3. **[Core Framework Architecture](./03-core-framework.md)**
   - BaseAgent implementation (invoke, stream, resume)
   - AgentConfig dataclass structure
   - AgentRegistry for agent discovery
   - BaseContext / AppContext and agent-specific contexts
   - LLM factory, Profile management (loader, scorer, manager, routes, schema)
   - Skill registry and dynamic skill loading
   - Agent-to-Agent (A2A) protocol
   - **Best for**: Deep dive into foundational framework components

### 4. **[Orchestrator Pattern](./04-orchestrator-pattern.md)**
   - How OrchestratorAgent routes to specialists
   - Worker agent wrapping via `_create_worker_agent()`
   - Dynamic agent discovery via registry
   - ThreadID namespacing for isolation
   - HITL interrupt handling and approval flow
   - **Best for**: Understanding the orchestration and routing strategy

### 5. **[Specialist Agents Architecture](./05-specialist-agents.md)**
   - Detailed breakdown of all 5 specialist agents
   - ProfileAgent (6 tools, HITL middleware)
   - JobDiscoveryAgent (3 tools, profile warning)
   - OutreachAgent (2 tools)
   - JDGeneratorAgent (6 tools incl. skill loader)
   - CandidateSearchAgent (2 tools)
   - Shared tools (11 tools in agents/shared/tools/)
   - Middleware stack per agent
   - **Best for**: Understanding what each agent does and their tools

### 6. **[Tool Execution Pipeline](./06-tool-execution-pipeline.md)**
   - How tools are called and executed
   - LLM decision loop
   - Tool registry lookup
   - Data source access patterns
   - Result processing and aggregation
   - UI adaptation: 10 React components + SSE side panels
   - Complete tool → UI component mapping table
   - **Best for**: Understanding tool execution and the adapter pattern

### 7. **[State Management Architecture](./07-state-management.md)**
   - BaseContext / AppContext fields (thread_id, first_name, display_name)
   - Agent-specific context classes (ProfileContext, etc.)
   - ContextVar isolation model
   - ThreadID scoping for history isolation
   - LangGraph checkpointing for HITL pause/resume
   - Profile caching strategy
   - **Best for**: Understanding how state flows and is isolated

### 8. **[Middleware Stack Architecture](./08-middleware-stack.md)**
   - Three middleware types: dynamic_prompt, wrap_tool_call, state transforms
   - Complete middleware inventory (9 middleware functions)
   - Middleware composition per agent
   - Summarization (threshold: 10 messages, keep: 5)
   - Tool monitoring with timing
   - Employee/HM personalization
   - First-touch profile analysis (cached 5 min)
   - Profile warning for low completion
   - HITL interrupt middleware
   - **Best for**: Understanding cross-cutting concerns and the middleware pattern

### 9. **[UI Component Architecture](./09-ui-component-tree.md)**
   - 10 React component hierarchy
   - Component → tool mapping table
   - JobCard, ProfileScore, SkillsCard, DraftMessage, SendConfirmation
   - ProfileUpdateConfirmation (HITL), JdQaCard, CandidateCard, RequisitionCard, JdFinalizedCard
   - SSE-driven side panels (Profile editor, JD editor, Job details)
   - Microsoft Teams styling guide
   - Color palette and button styles
   - Component data flow with action callbacks
   - **Best for**: Understanding frontend components and UI design system

---

## Quick Navigation by Use Case

### "I want to understand the whole system"
Start with **01-system-architecture.md**, then **02-message-flow.md**

### "I need to add a new agent"
**04-orchestrator-pattern.md**, **05-specialist-agents.md**, **03-core-framework.md**

### "I need to understand tool execution"
**06-tool-execution-pipeline.md**, **03-core-framework.md**

### "I need to debug state issues"
**07-state-management.md**, **02-message-flow.md**

### "I need to add new middleware"
**08-middleware-stack.md**, **03-core-framework.md**

### "I need to add new UI components"
**09-ui-component-tree.md**, **06-tool-execution-pipeline.md**

### "I need to understand routing"
**04-orchestrator-pattern.md**, **02-message-flow.md**

### "I need to understand HITL / approval flows"
**04-orchestrator-pattern.md**, **08-middleware-stack.md**, **09-ui-component-tree.md**

---

## Architecture Highlights

### Key Design Patterns

1. **Multi-Agent Orchestration**
   - OrchestratorAgent wraps specialists as worker agent tools
   - Each agent handles a specific domain
   - Agents are discoverable via AgentRegistry
   - Enables scalability and separation of concerns

2. **ThreadID Namespacing**
   - Parent thread: `{session_id}`
   - Child thread: `{parent_thread_id}:{agent_name}`
   - Isolates conversation history per agent
   - Prevents cross-contamination in async execution

3. **ContextVar Isolation**
   - Each async task gets its own context (BaseContext subclass)
   - No global state
   - Enables concurrent request handling

4. **Human-in-the-Loop (HITL)**
   - HumanInTheLoopMiddleware intercepts profile updates and rollbacks
   - Interrupts bubble up through worker → orchestrator → app.py
   - User approves/rejects via ProfileUpdateConfirmation card
   - Agent resumes with decision via `agent.resume()`

5. **Middleware Chain**
   - Three types: `@dynamic_prompt`, `@wrap_tool_call`, state transforms
   - Agent-specific customization (personalization, warnings, HITL)
   - Global concerns (monitoring, summarization)
   - Composable and extensible

6. **Adapter Pattern**
   - Agent tool results → React components via UI Adapter
   - 10 custom React components + SSE-driven side panels
   - `extract_tool_calls_from_messages()` unwraps inner tool calls
   - `extract_interrupts_from_messages()` extracts HITL interrupts
   - Decouples backend from frontend

7. **Tool Registry**
   - 19 tools across 5 specialist agents
   - Dynamic tool registration per agent
   - Skill loader for runtime knowledge fetching

### Technology Stack

- **LLM**: Azure OpenAI
- **Framework**: LangChain / LangGraph
- **Web UI**: HR Assistant App
- **Frontend Components**: React (JSX)
- **Styling**: Microsoft Teams design system (#6264A7)
- **Storage**: JSON files + SQLite
- **State Management**: contextvars + LangGraph MemorySaver
- **Async**: Python async/await

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| BaseAgent | `core/agent/base.py` | LangChain wrapper with middleware |
| AgentConfig | `core/agent/config.py` | Agent configuration dataclass |
| AgentRegistry | `core/agent/registry.py` | Agent discovery and lookup |
| BaseContext / AppContext | `core/state.py` | Context with thread_id, first_name, display_name |
| OrchestratorAgent | `agents/orchestrator/agent.py` | Main routing agent |
| Specialist Agents | `agents/*/agent.py` | Domain-specific agents (5 total) |
| Shared Tools | `agents/shared/tools/` | 11 LangChain tools |
| Core Middleware | `core/middleware/` | Summarization, tool monitor, HITL |
| Shared Middleware | `agents/shared/middleware.py` | Personalization, profile warning, first touch |
| Adapters | `core/adapters/chainlit_adapter.py` | Result → UI conversion |
| UI Components | `public/elements/*.jsx` | 10 React card components |
| Profile Management | `core/profile*.py` | Loader, scorer, schema, manager, routes |
| Skill Registry | `core/skills/` | Dynamic skill loading |

### Tool Distribution

| Agent | Tools |
|-------|-------|
| ProfileAgent | 6: profile_analyzer, update_profile, infer_skills, list_profile_entries, open_profile_panel, rollback_profile |
| JobDiscoveryAgent | 3: get_matches, view_job, ask_jd_qa |
| OutreachAgent | 2: draft_message, send_message |
| CandidateSearchAgent | 2: search_candidates, view_candidate |
| JDGeneratorAgent | 6: get_requisition, jd_search, jd_compose, section_editor, jd_finalize, load_skill |

---

## File Organization

```
docs/architecture/
├── README.md                      (this file)
├── 01-system-architecture.md      (high-level overview)
├── 02-message-flow.md             (request flow + HITL)
├── 03-core-framework.md           (framework components)
├── 04-orchestrator-pattern.md     (routing + HITL strategy)
├── 05-specialist-agents.md        (all agents + tools + middleware)
├── 06-tool-execution-pipeline.md  (tool execution + UI mapping)
├── 07-state-management.md         (state, context, checkpointing)
├── 08-middleware-stack.md          (middleware pattern + inventory)
└── 09-ui-component-tree.md        (10 frontend components)
```

---

## Related Documentation

- **CLAUDE.md**: Project setup and commands
- **agents/catalog.py**: Agent registration
- **core/config.py**: Framework configuration
- **.chainlit/config.toml**: UI configuration

---

Generated: March 11, 2026
Last Updated: March 12, 2026
