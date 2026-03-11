# AutoChat Architecture Documentation

Complete visual architecture diagrams for the AutoChat multi-agent orchestration framework.

## 📋 Documentation Index

### 1. **[System Architecture Overview](./01-system-architecture.md)**
   - High-level component relationships
   - All major layers (UI, App, Orchestration, Agents, Tools, Framework, Data, Adapters)
   - How components connect together
   - **Best for**: Getting a complete picture of the entire system

### 2. **[Message Flow: End-to-End](./02-message-flow.md)**
   - Step-by-step flow from user input to response
   - Sequence diagram showing all interactions
   - Tool calling loop lifecycle
   - ThreadID namespacing
   - **Best for**: Understanding how a request travels through the system

### 3. **[Core Framework Architecture](./03-core-framework.md)**
   - BaseAgent implementation
   - AgentConfig dataclass structure
   - AgentRegistry for agent discovery
   - AppContext and state management
   - LLM factory, Profile management, Skill registry
   - Agent-to-Agent (A2A) protocol
   - **Best for**: Deep dive into foundational framework components

### 4. **[Orchestrator Pattern](./04-orchestrator-pattern.md)**
   - How OrchestratorAgent routes to specialists
   - Sub-agent wrapping mechanism
   - Dynamic agent discovery via registry
   - ThreadID namespacing for isolation
   - **Best for**: Understanding the orchestration and routing strategy

### 5. **[Specialist Agents Architecture](./05-specialist-agents.md)**
   - Detailed breakdown of all 5 specialist agents
   - ProfileAgent (6 tools)
   - JobDiscoveryAgent (3 tools)
   - OutreachAgent (3 tools)
   - JDGeneratorAgent (5 tools + skill loader)
   - CandidateSearchAgent (2 tools)
   - MyCareer shared tools (11 tools)
   - **Best for**: Understanding what each agent does and their tools

### 6. **[Tool Execution Pipeline](./06-tool-execution-pipeline.md)**
   - How tools are called and executed
   - LLM decision loop
   - Tool registry lookup
   - Data source access patterns
   - Result processing and aggregation
   - UI adaptation and React component rendering
   - **Best for**: Understanding tool execution and the adapter pattern

### 7. **[State Management Architecture](./07-state-management.md)**
   - AppContext lifecycle and structure
   - ContextVar isolation model
   - ThreadID scoping for history isolation
   - Async isolation guarantees
   - Profile caching strategy
   - Context cleanup and lifecycle
   - **Best for**: Understanding how state flows and is isolated

### 8. **[Middleware Stack Architecture](./08-middleware-stack.md)**
   - Middleware composition and ordering
   - Pre/post processing pattern
   - Tool Monitor Middleware (logging, timing)
   - Summarization Middleware (history compression)
   - Custom agent-specific middleware
   - Middleware chain execution
   - **Best for**: Understanding cross-cutting concerns and the middleware pattern

### 9. **[UI Component Architecture](./09-ui-component-tree.md)**
   - React component hierarchy
   - JobCard, ProfileScore, DraftMessage, CandidateCard, SkillsCard components
   - Microsoft Teams styling guide
   - Color palette and button styles
   - Component data flow
   - **Best for**: Understanding frontend components and UI design system

---

## 🎯 Quick Navigation by Use Case

### "I want to understand the whole system"
→ Start with **01-system-architecture.md**, then **02-message-flow.md**

### "I need to add a new agent"
→ **04-orchestrator-pattern.md**, **05-specialist-agents.md**, **03-core-framework.md**

### "I need to understand tool execution"
→ **06-tool-execution-pipeline.md**, **03-core-framework.md**

### "I need to debug state issues"
→ **07-state-management.md**, **02-message-flow.md**

### "I need to add new middleware"
→ **08-middleware-stack.md**, **03-core-framework.md**

### "I need to add new UI components"
→ **09-ui-component-tree.md**, **06-tool-execution-pipeline.md**

### "I need to understand routing"
→ **04-orchestrator-pattern.md**, **02-message-flow.md**

---

## 🏗️ Architecture Highlights

### Key Design Patterns

1. **Multi-Agent Orchestration**
   - OrchestratorAgent routes to specialist agents
   - Each agent handles a specific domain
   - Agents are discoverable via AgentRegistry
   - Enables scalability and separation of concerns

2. **ThreadID Namespacing**
   - Parent thread: `{session_id}`
   - Child thread: `{parent_thread_id}:{agent_name}`
   - Isolates conversation history per agent
   - Prevents cross-contamination in async execution

3. **ContextVar Isolation**
   - Each async task gets its own AppContext
   - No global state
   - Enables concurrent request handling
   - Clean cleanup via token reset

4. **Middleware Chain**
   - Pre/post processing hooks
   - Agent-specific customization
   - Global concerns (monitoring, summarization)
   - Composable and extensible

5. **Adapter Pattern**
   - Agent results → React components
   - ChainlitAdapter handles conversion
   - Enables rich UI with structured data
   - Decouples backend from frontend

6. **Tool Registry**
   - LangChain tools are discoverable
   - Dynamic tool registration
   - Supports custom tools per agent
   - Tool results feed back into LLM loop

### Technology Stack

- **LLM**: Azure OpenAI
- **Framework**: LangChain / LangGraph
- **Web UI**: Chainlit
- **Frontend Components**: React (TypeScript)
- **Styling**: Microsoft Teams design system (#6264A7)
- **Storage**: JSON files + SQLite
- **State Management**: contextvars + ContextVar
- **Async**: Python async/await

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| BaseAgent | `core/agent/base.py` | LangChain wrapper with middleware |
| AgentConfig | `core/agent/config.py` | Agent configuration dataclass |
| AgentRegistry | `core/agent/registry.py` | Agent discovery and lookup |
| AppContext | `core/state.py` | Global application context |
| OrchestratorAgent | `agents/orchestrator/agent.py` | Main routing agent |
| Specialist Agents | `agents/*/agent.py` | Domain-specific agents |
| Tools | `agents/*/tools/` | LangChain tools per agent |
| Middleware | `core/middleware/` | Cross-cutting concerns |
| Adapters | `core/adapters/chainlit_adapter.py` | Result → UI conversion |
| UI Components | `public/elements/*.jsx` | React card components |

---

## 📚 File Organization

```
docs/architecture/
├── README.md                      (this file)
├── 01-system-architecture.md      (high-level overview)
├── 02-message-flow.md             (request flow)
├── 03-core-framework.md           (framework components)
├── 04-orchestrator-pattern.md     (routing strategy)
├── 05-specialist-agents.md        (all agents + tools)
├── 06-tool-execution-pipeline.md  (tool execution)
├── 07-state-management.md         (state & context)
├── 08-middleware-stack.md         (middleware pattern)
└── 09-ui-component-tree.md        (frontend components)
```

---

## 🔗 Related Documentation

- **CLAUDE.md**: Project setup and commands
- **agents/catalog.py**: Agent registration
- **core/config.py**: Framework configuration
- **.chainlit/config.toml**: Chainlit UI configuration

---

## 💡 Tips for Using These Diagrams

1. **Mermaid Rendering**: All diagrams use Mermaid syntax. They render automatically in:
   - GitHub markdown
   - GitLab markdown
   - Notion
   - Most markdown editors

2. **Copy & Adapt**: Feel free to copy any diagram and adapt it for presentations or documentation

3. **Update on Changes**: Keep these diagrams in sync when making architectural changes

4. **Reference**: Link to specific diagrams when discussing architecture in PRs or issues

---

Generated: March 11, 2026
Last Updated: March 11, 2026
