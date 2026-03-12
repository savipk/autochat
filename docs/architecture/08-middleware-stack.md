# Middleware Stack Architecture

How middleware wraps agent execution and applies cross-cutting concerns.

## Middleware Types

HR Agent uses three middleware decorator types:

| Type | Decorator | Purpose |
|------|-----------|---------|
| **dynamic_prompt** | `@dynamic_prompt` | Appends context to system prompt before agent runs |
| **wrap_tool_call** | `@wrap_tool_call` | Wraps individual tool call execution (pre/post) |
| **state middleware** | `create_*_middleware()` | Transforms full agent state (messages, history) |

## Middleware Inventory

```mermaid
graph TB
    subgraph CoreMW["Core Middleware<br/>(core/middleware/)"]
        SumMW["SummarizationMiddleware<br/>create_summarization_middleware()<br/>Compresses history when > 10 messages"]
        ToolMonMW["tool_monitor_middleware<br/>@wrap_tool_call<br/>Logs tool calls with timing"]
    end

    subgraph SharedMW["Shared Middleware<br/>(agents/shared/middleware.py)"]
        FirstTouch["first_touch_profile_middleware<br/>@dynamic_prompt<br/>Auto-analyzes profile on first touch"]
        EmpPers["employee_personalization<br/>@dynamic_prompt<br/>Injects user name/title/skills"]
        HMPers["hiring_manager_personalization<br/>@dynamic_prompt<br/>Injects HM name/title"]
        ProfWarn["profile_warning_middleware<br/>@wrap_tool_call<br/>Warns if profile < 50% complete"]
    end

    subgraph OrchestratorMW["Orchestrator Middleware<br/>(agents/orchestrator/middleware.py)"]
        OrchPers["orchestrator_personalization<br/>@dynamic_prompt<br/>Injects user first_name"]
    end

    subgraph HITLMW["HITL Middleware<br/>(core/middleware/)"]
        HITL["HumanInTheLoopMiddleware<br/>Intercepts specified tools<br/>Raises interrupt for user approval"]
    end
```

## Middleware Composition by Agent

```mermaid
graph TB
    subgraph OrchestratorConfig["OrchestratorAgent"]
        OC["middleware = [<br/>  SummarizationMW,<br/>  orchestrator_personalization,<br/>  tool_monitor_middleware<br/>]"]
    end

    subgraph ProfileConfig["ProfileAgent"]
        PC["middleware = [<br/>  SummarizationMW,<br/>  first_touch_profile_middleware,<br/>  employee_personalization,<br/>  tool_monitor_middleware,<br/>  HumanInTheLoopMW<br/>    (update_profile, rollback_profile)<br/>]"]
    end

    subgraph JobConfig["JobDiscoveryAgent"]
        JC["middleware = [<br/>  SummarizationMW,<br/>  employee_personalization,<br/>  profile_warning_middleware,<br/>  tool_monitor_middleware<br/>]"]
    end

    subgraph OutreachConfig["OutreachAgent"]
        OutC["middleware = [<br/>  SummarizationMW,<br/>  employee_personalization,<br/>  tool_monitor_middleware<br/>]"]
    end

    subgraph CandidateConfig["CandidateSearchAgent"]
        CC["middleware = [<br/>  SummarizationMW,<br/>  hiring_manager_personalization,<br/>  tool_monitor_middleware<br/>]"]
    end

    subgraph JDConfig["JDGeneratorAgent"]
        JDC["middleware = [<br/>  SummarizationMW,<br/>  hiring_manager_personalization,<br/>  tool_monitor_middleware<br/>]"]
    end
```

## Middleware Execution Flow

```mermaid
sequenceDiagram
    participant Agent as BaseAgent
    participant DynPrompt as Dynamic Prompt MW<br/>(personalization)
    participant Sum as Summarization MW
    participant Core as Agent Core<br/>invoke()
    participant ToolMon as Tool Monitor MW<br/>(per tool call)
    participant HITL as HITL MW<br/>(per tool call)
    participant Tool as LangChain Tool

    Agent->>DynPrompt: Pre-process:<br/>Append user context to system prompt
    DynPrompt->>Sum: Pre-process:<br/>Check message count

    Sum->>Core: invoke(state)

    loop Tool Calling Loop
        Core->>ToolMon: Tool call intercepted
        ToolMon->>ToolMon: Log start + timestamp
        ToolMon->>HITL: Check if tool needs approval

        alt Tool requires HITL approval
            HITL->>HITL: Raise interrupt
            HITL-->>Core: Return interrupt payload
        else Tool allowed
            HITL->>Tool: Execute tool
            Tool-->>HITL: Tool result
        end

        HITL-->>ToolMon: Result
        ToolMon->>ToolMon: Log duration + result
        ToolMon-->>Core: Return result
    end

    Core-->>Sum: Execution complete
    Sum->>Sum: Post-process:<br/>Compress history if > threshold
    Sum-->>DynPrompt: Return state
    DynPrompt-->>Agent: Final result
```

## Summarization Middleware Detail

```mermaid
graph TB
    SumMW["SummarizationMiddleware<br/>core/middleware/summarization.py"]

    subgraph Config["Configuration<br/>(core/config.py)"]
        Threshold["MAX_MESSAGES_BEFORE_SUMMARIZATION = 10"]
        Keep["MESSAGES_TO_KEEP_AFTER_SUMMARIZATION = 5"]
        TokenEstimate["~500 tokens per message estimate"]
    end

    subgraph Check["Compression Check"]
        CountMsgs["Count messages<br/>in history"]
        Compare["Compare to threshold (10)"]
        Decision["Decision:<br/>Compress or pass-through"]
    end

    subgraph Compress["Compression Pipeline"]
        SelectOld["Select oldest<br/>messages beyond keep limit"]
        CreateSummary["LLM summarizes<br/>Extract key points"]
        Replace["Replace old messages<br/>with summary"]
        KeepRecent["Keep 5 most recent<br/>messages intact"]
    end

    subgraph Output["Output"]
        CompressedHist["Compressed history<br/>+ 5 fresh messages"]
        PassThrough["Original history<br/>unchanged"]
    end

    SumMW --> Config
    Config --> Check
    Check --> CountMsgs
    CountMsgs --> Compare
    Compare --> Decision

    Decision -->|> 10 messages| Compress
    Decision -->|≤ 10 messages| PassThrough

    Compress --> SelectOld
    SelectOld --> CreateSummary
    CreateSummary --> Replace
    Replace --> KeepRecent
    KeepRecent --> CompressedHist
```

## Tool Monitor Middleware Detail

```mermaid
graph TB
    ToolMonitor["tool_monitor_middleware<br/>core/middleware/tool_monitor.py<br/>@wrap_tool_call"]

    subgraph Pre["Pre-Tool Logging"]
        LogCall["Log: 'Calling {tool_name}'<br/>with args"]
        Timestamp["Record start time<br/>(perf_counter)"]
    end

    subgraph Exec["Tool Execution<br/>(Passthrough)"]
        Call["Tool executes<br/>as normal"]
    end

    subgraph Post["Post-Tool Logging"]
        Duration["Calculate duration<br/>(milliseconds)"]
        LogResult["Log: 'Tool {name} completed<br/>in {ms}ms'"]
        LogError["Log exception<br/>if tool fails"]
    end

    ToolMonitor --> Pre
    Pre --> LogCall
    Pre --> Timestamp

    Timestamp --> Exec
    Exec --> Call
    Call --> Post
    Post --> Duration
    Post --> LogResult
    Post --> LogError
```

## Employee Personalization Middleware

```mermaid
graph TB
    EmpPers["employee_personalization<br/>agents/shared/middleware.py<br/>@dynamic_prompt"]

    subgraph Input["Reads From"]
        Profile["load_profile()"]
        Identity["get_user_identity()"]
    end

    subgraph Injects["Appends to System Prompt"]
        Name["Employee name"]
        Title["Job title"]
        Rank["Corporate level"]
        TopSkills["Top 3 skills"]
        Completion["Profile completion %"]
    end

    EmpPers --> Input
    Input --> Profile
    Input --> Identity
    Identity --> Injects
```

## First Touch Profile Middleware

```mermaid
graph TB
    FirstTouch["first_touch_profile_middleware<br/>agents/shared/middleware.py<br/>@dynamic_prompt"]

    subgraph Logic["Logic"]
        CheckCache["Check per-thread cache<br/>(5-minute TTL)"]
        RunAnalyzer["Run profile_analyzer<br/>on first touch only"]
        CacheResult["Cache result"]
    end

    subgraph Injects["Appends to System Prompt"]
        Score["Completion score"]
        Missing["Missing sections"]
        TopRecs["Top 3 recommendations"]
    end

    FirstTouch --> Logic
    Logic --> CheckCache
    CheckCache -->|miss| RunAnalyzer
    RunAnalyzer --> CacheResult
    CacheResult --> Injects
    CheckCache -->|hit| Injects
```

## HITL Middleware

```mermaid
graph TB
    HITL["HumanInTheLoopMiddleware"]

    subgraph Config["Configuration"]
        Tools["Intercepted tools:<br/>update_profile, rollback_profile"]
    end

    subgraph Flow["Flow"]
        Intercept["Intercept tool call"]
        RaiseInterrupt["Raise interrupt<br/>with action_requests"]
        WaitApproval["Agent paused<br/>waiting for user"]
        Resume["agent.resume(decision)"]
    end

    subgraph Outcomes["Outcomes"]
        Approve["Approved → Execute tool"]
        Reject["Rejected → Return rejection message"]
    end

    HITL --> Config
    Config --> Flow
    Flow --> Intercept
    Intercept --> RaiseInterrupt
    RaiseInterrupt --> WaitApproval
    WaitApproval --> Resume
    Resume --> Outcomes
    Outcomes --> Approve
    Outcomes --> Reject
```

## Key Points

1. **Three MW Types** — `@dynamic_prompt` (pre-invoke), `@wrap_tool_call` (per-tool), state transforms (full state)
2. **Ordered Stack** — Middleware applied in order defined in AgentConfig
3. **Agent-Specific Stacks** — Different agents have different middleware combinations
4. **Employee vs HM Personalization** — Employee-facing agents get user context; HM-facing agents get HM context
5. **First Touch Analysis** — Profile agent auto-analyzes on first interaction (cached 5 min)
6. **Profile Warning** — Job Discovery warns when profile completion is low
7. **HITL Interrupts** — Profile updates require user approval before persisting
8. **History Management** — Summarization keeps token usage under control (threshold: 10 messages)
9. **Tool Monitoring** — Universal tool tracking with millisecond timing
