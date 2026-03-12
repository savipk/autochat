# Orchestrator Pattern

How the OrchestratorAgent discovers, wraps, and delegates to specialist agents.

## Orchestrator Architecture Diagram

```mermaid
graph TB
    subgraph OrchestratorFlow["OrchestratorAgent Flow"]
        Input["User Message<br/>+ AppContext"]
        Receive["on_message<br/>receives input"]
        LLMAnalyze["LLM analyzes intent<br/>Select specialist agent"]
        SelectAgent["Determine target agent<br/>based on message type"]
    end

    subgraph WorkerAgentWrapper["Worker Agent Wrapping"]
        CreateWrapper["_create_worker_agent()<br/>factory function"]
        ConfigAgent["Wrap specialist agent<br/>as LangChain tool"]
        ThreadID["Create ThreadID<br/>parent:agent_name"]
        StateBinding["Bind state<br/>and context"]
    end

    subgraph Invocation["Worker Agent Invocation"]
        InvokeWorkerAgent["invoke(message)<br/>on specialist"]
        AwaitResult["Await response"]
        ParseJSON["Parse structured JSON<br/>from specialist"]
        HandleHITL["Handle HITL interrupts<br/>(update_profile, rollback)"]
    end

    subgraph Specialists["Available Specialists"]
        ProfileAgent["ProfileAgent<br/>Profile analysis,<br/>skill inference,<br/>updates, rollback"]
        JobAgent["JobDiscoveryAgent<br/>Job search,<br/>details lookup,<br/>Q&A"]
        OutreachAgent["OutreachAgent<br/>Draft messages,<br/>send communication"]
        JDAgent["JDGeneratorAgent<br/>Compose JD,<br/>edit sections,<br/>finalize"]
        CandidateAgent["CandidateSearchAgent<br/>Find employees,<br/>view profiles"]
    end

    subgraph Response["Response Aggregation"]
        AggResult["Aggregate specialist<br/>response"]
        ExtractToolCalls["Extract inner tool_calls<br/>for adapter rendering"]
        ExtractInterrupts["Extract HITL interrupts<br/>for confirmation cards"]
        ConvertUI["Convert to UI<br/>via Chainlit Adapter"]
        ReturnOrch["Return to parent<br/>message loop"]
    end

    subgraph Registry["Agent Registry"]
        RegFetch["AgentRegistry.get()<br/>lookup specialist"]
        RegList["List registered agents<br/>at startup"]
    end

    Input --> Receive
    Receive --> LLMAnalyze
    LLMAnalyze --> SelectAgent
    SelectAgent --> RegFetch
    RegFetch --> CreateWrapper

    CreateWrapper --> ConfigAgent
    ConfigAgent --> ThreadID
    ThreadID --> StateBinding

    StateBinding --> InvokeWorkerAgent
    InvokeWorkerAgent --> AwaitResult
    AwaitResult --> ParseJSON
    ParseJSON --> HandleHITL

    HandleHITL --> AggResult
    AggResult --> ExtractToolCalls
    AggResult --> ExtractInterrupts
    ExtractToolCalls --> ConvertUI
    ExtractInterrupts --> ConvertUI
    ConvertUI --> ReturnOrch

    RegList --> RegFetch
    ConfigAgent --> ProfileAgent
    ConfigAgent --> JobAgent
    ConfigAgent --> OutreachAgent
    ConfigAgent --> JDAgent
    ConfigAgent --> CandidateAgent
```

## Worker Agent Tool Integration

```mermaid
graph LR
    Orch["OrchestratorAgent<br/>LLM Tools"]
    WorkerAgentTool["Worker Agent Tool<br/>(wrapped specialist)"]
    Specialist["Specialist Agent<br/>(e.g., ProfileAgent)"]
    SpecTools["Specialist Tools<br/>(e.g., 6 tools for Profile)"]

    Orch -->|calls| WorkerAgentTool
    WorkerAgentTool -->|invokes| Specialist
    Specialist -->|uses| SpecTools
    SpecTools -->|return| WorkerAgentTool
    WorkerAgentTool -->|returns JSON with<br/>tool_calls or interrupts| Orch
```

## Worker Agent Return Format

The worker agent wrapper extracts inner tool calls and HITL interrupts from specialist responses:

```mermaid
graph TB
    WorkerResult["Worker Agent Result JSON"]

    ToolCalls["tool_calls: [<br/>  {name: 'get_matches', content: {...}},<br/>  {name: 'profile_analyzer', content: {...}}<br/>]"]

    Interrupts["interrupts: [<br/>  {value: {action_requests: [<br/>    {name: 'update_profile', args: {...}}<br/>  ]}}<br/>]"]

    AgentName["agent_name: 'profile'"]

    WorkerResult --> ToolCalls
    WorkerResult --> Interrupts
    WorkerResult --> AgentName
```

## ThreadID Namespacing

```mermaid
graph TB
    SessionStart["Session Started<br/>ThreadID: abc123"]
    OrchestratorThread["OrchestratorAgent<br/>ThreadID: abc123"]

    Call1["User asks: Analyze my profile"]
    SubAgent1["ProfileAgent<br/>ThreadID: abc123:profile<br/>Isolated history"]

    Call2["User asks: Find jobs for me"]
    SubAgent2["JobDiscoveryAgent<br/>ThreadID: abc123:job_discovery<br/>Isolated history"]

    Call3["User asks: Draft outreach"]
    SubAgent3["OutreachAgent<br/>ThreadID: abc123:outreach<br/>Isolated history"]

    SessionStart --> OrchestratorThread
    Call1 --> SubAgent1
    Call2 --> SubAgent2
    Call3 --> SubAgent3

    OrchestratorThread -.->|parent| SubAgent1
    OrchestratorThread -.->|parent| SubAgent2
    OrchestratorThread -.->|parent| SubAgent3

    SubAgent1 -.->|isolated| SubAgent2
    SubAgent1 -.->|isolated| SubAgent3
    SubAgent2 -.->|isolated| SubAgent3
```

## HITL Interrupt Flow

```mermaid
sequenceDiagram
    participant User as User
    participant App as app.py
    participant Orch as OrchestratorAgent
    participant Worker as Worker Agent
    participant Profile as ProfileAgent
    participant HITL as HumanInTheLoopMiddleware

    User->>App: "Add Python to my skills"
    App->>Orch: invoke(message)
    Orch->>Worker: call profile worker
    Worker->>Profile: invoke(message)
    Profile->>HITL: update_profile tool call intercepted
    HITL-->>Profile: Interrupt raised
    Profile-->>Worker: Returns interrupts JSON
    Worker-->>Orch: Returns {interrupts: [...]}
    Orch-->>App: Response with interrupts

    App->>App: render_interrupt_elements()<br/>Show ProfileUpdateConfirmation card

    User->>App: Clicks "Approve" button
    App->>App: action_callback("approve_profile_update")
    App->>Profile: agent.resume(decision="approve")
    Profile->>Profile: Execute update_profile
    Profile-->>App: Return result
    App->>App: Render updated response
```

## Key Design Patterns

### 1. **Worker Agent Wrapping**
- Each specialist agent is dynamically wrapped as a LangChain tool via `_create_worker_agent()`
- Orchestrator can compose specialists without tight coupling
- Worker tools return JSON with `tool_calls` (inner results) and `interrupts` (HITL)

### 2. **ThreadID Namespacing**
- Parent thread: `{session_id}`
- Child thread: `{parent_thread_id}:{agent_name}`
- Prevents conversation history cross-contamination
- Each agent has isolated context and tool history

### 3. **Dynamic Registration**
- Agents registered in `agents/catalog.py`
- Orchestrator discovers agents at runtime via AgentRegistry
- Adding new agent requires only:
  1. Create agent
  2. Register in catalog
  3. Orchestrator auto-discovers it

### 4. **Structured Routing**
- Orchestrator LLM analyzes user intent
- Routes to best-fit specialist based on message content
- Specialist executes independently with full context
- Results aggregated and adapted for UI

### 5. **Human-in-the-Loop**
- Profile updates and rollbacks require user confirmation
- `HumanInTheLoopMiddleware` intercepts specified tool calls
- Interrupts bubble up through worker agent → orchestrator → app.py
- User approves/rejects via UI card action callbacks
- Agent resumes with decision via `agent.resume()`
