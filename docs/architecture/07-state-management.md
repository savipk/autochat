# State Management Architecture

How application state flows through the system and how threading is isolated via context variables.

## AppContext Flow

```mermaid
graph TB
    subgraph SessionInit["Session Initialization"]
        UserSession["Chainlit Session<br/>session_id generated"]
        OnChatStart["on_chat_start callback<br/>Auth user, load profile"]
        AppPyHandler["on_message handler<br/>builds AppContext"]
    end

    subgraph ContextConstruction["AppContext Construction"]
        ThreadID["thread_id<br/>from session"]
        FirstName["first_name<br/>from user profile"]
        DisplayName["display_name<br/>from user metadata"]
        BuildContext["Build AppContext<br/>from components"]
    end

    subgraph ContextVar["ContextVar<br/>(contextvars)"]
        ContextVarDef["context_var = ContextVar<br/>('app_context')"]
        TokenSet["token = context_var.set<br/>(app_context)"]
        Isolation["Isolated per<br/>async task"]
    end

    subgraph AgentAccess["Agent Access"]
        GetContext["get_context()<br/>retrieve from ContextVar"]
        AccessName["Access first_name"]
        AccessDisplay["Access display_name"]
        AccessThread["Access thread_id"]
    end

    subgraph ThreadIDScoping["ThreadID Scoping"]
        ParentID["Parent ThreadID<br/>abc123"]
        ChildID["Child ThreadID<br/>abc123:profile"]
        IsolatedHistory["Isolated message<br/>history per ThreadID"]
    end

    subgraph DataUpdate["Data Updates"]
        Persist["Persist changes<br/>to JSON/DB"]
        UpdateProfile["Update profile.json<br/>via ProfileManager"]
        UpdateHistory["Update chat history<br/>data.db (SQLite)"]
    end

    UserSession --> OnChatStart
    OnChatStart --> AppPyHandler

    AppPyHandler --> ThreadID
    AppPyHandler --> FirstName
    AppPyHandler --> DisplayName
    ThreadID --> BuildContext
    FirstName --> BuildContext
    DisplayName --> BuildContext

    BuildContext --> ContextVarDef
    ContextVarDef --> TokenSet
    TokenSet --> Isolation

    Isolation --> GetContext
    GetContext --> AccessName
    GetContext --> AccessDisplay
    GetContext --> AccessThread

    ThreadID --> ParentID
    ParentID --> ChildID
    ChildID --> IsolatedHistory

    AccessName --> Persist
    Persist --> UpdateProfile
    Persist --> UpdateHistory
```

## AppContext Data Structure

```mermaid
graph TB
    BaseContext["BaseContext<br/>(core/state.py)"]

    ThreadID["thread_id: str<br/>(default: '')"]

    AppContext["AppContext(BaseContext)<br/>(core/state.py)"]

    FirstName["first_name: str<br/>User's first name"]
    DisplayName["display_name: str<br/>Full display name"]

    AgentContexts["Agent-Specific Contexts"]

    ProfileContext["ProfileContext(BaseContext)<br/>completion_score: int = 100"]
    JobContext["JobDiscoveryContext(BaseContext)<br/>(no extra fields)"]
    OutreachContext["OutreachContext(BaseContext)<br/>(no extra fields)"]
    CandidateContext["CandidateSearchContext(BaseContext)<br/>(no extra fields)"]
    JDContext["JDGeneratorContext(BaseContext)<br/>(no extra fields)"]

    BaseContext --> ThreadID
    AppContext --> BaseContext
    AppContext --> FirstName
    AppContext --> DisplayName

    AgentContexts --> ProfileContext
    AgentContexts --> JobContext
    AgentContexts --> OutreachContext
    AgentContexts --> CandidateContext
    AgentContexts --> JDContext

    ProfileContext --> BaseContext
    JobContext --> BaseContext
    OutreachContext --> BaseContext
    CandidateContext --> BaseContext
    JDContext --> BaseContext
```

## ThreadID Isolation Model

```mermaid
graph TB
    subgraph Session1["Session: abc123"]
        OrchestratorThread["OrchestratorAgent<br/>ThreadID: abc123"]

        subgraph SubThread1["ProfileAgent<br/>ThreadID: abc123:profile"]
            ProfHistory["Message history<br/>isolated"]
            ProfState["ProfileContext<br/>completion_score"]
        end

        subgraph SubThread2["JobDiscoveryAgent<br/>ThreadID: abc123:job_discovery"]
            JobHistory["Message history<br/>isolated"]
            JobState["JobDiscoveryContext"]
        end

        subgraph SubThread3["OutreachAgent<br/>ThreadID: abc123:outreach"]
            OutHistory["Message history<br/>isolated"]
            OutState["OutreachContext"]
        end

        subgraph SubThread4["JDGeneratorAgent<br/>ThreadID: abc123:jd_generator"]
            JDHistory["Message history<br/>isolated"]
            JDState["JDGeneratorContext"]
        end

        subgraph SubThread5["CandidateSearchAgent<br/>ThreadID: abc123:candidate_search"]
            CandHistory["Message history<br/>isolated"]
            CandState["CandidateSearchContext"]
        end
    end

    OrchestratorThread -->|parent| SubThread1
    OrchestratorThread -->|parent| SubThread2
    OrchestratorThread -->|parent| SubThread3
    OrchestratorThread -->|parent| SubThread4
    OrchestratorThread -->|parent| SubThread5

    SubThread1 -.->|no cross-talk| SubThread2
    SubThread1 -.->|no cross-talk| SubThread3
    SubThread2 -.->|no cross-talk| SubThread3

    style SubThread1 fill:#e1f5ff
    style SubThread2 fill:#f3e5f5
    style SubThread3 fill:#e8f5e9
    style SubThread4 fill:#fff3e0
    style SubThread5 fill:#fce4ec
```

## Async Isolation via ContextVar

```mermaid
graph TB
    subgraph Main["Main Thread"]
        Task1["Task 1<br/>ThreadID: abc123:profile"]
        Task2["Task 2<br/>ThreadID: def456:job_discovery"]
        Task3["Task 3<br/>ThreadID: ghi789:outreach"]
    end

    subgraph ContextVars["ContextVar Storage"]
        CV1["Token for Task 1<br/>context_var → ProfileContext"]
        CV2["Token for Task 2<br/>context_var → JobDiscoveryContext"]
        CV3["Token for Task 3<br/>context_var → OutreachContext"]
    end

    subgraph Isolation["Isolation Guarantee"]
        I1["Task 1 calls<br/>get_context()<br/>→ ProfileContext"]
        I2["Task 2 calls<br/>get_context()<br/>→ JobDiscoveryContext"]
        I3["Task 3 calls<br/>get_context()<br/>→ OutreachContext"]
    end

    Task1 -->|set| CV1
    Task2 -->|set| CV2
    Task3 -->|set| CV3

    CV1 --> I1
    CV2 --> I2
    CV3 --> I3

    I1 -.->|no interference| I2
    I1 -.->|no interference| I3
    I2 -.->|no interference| I3
```

## State Lifecycle

```mermaid
sequenceDiagram
    participant User as User
    participant Session as Chainlit Session
    participant AppPy as app.py
    participant ContextMgr as ContextVar Manager
    participant Orch as OrchestratorAgent
    participant Worker as Worker Agent
    participant DataStore as Data Store

    User->>Session: Start conversation
    Session->>AppPy: on_chat_start()
    AppPy->>AppPy: Authenticate user<br/>Load profile metadata

    User->>Session: Send message
    Session->>AppPy: on_message(message)

    AppPy->>AppPy: Build AppContext<br/>(thread_id, first_name, display_name)

    AppPy->>ContextMgr: context_var.set(app_context)<br/>returns token

    AppPy->>Orch: orchestrator.invoke(message, context)

    Orch->>Orch: Apply middleware<br/>(summarization, personalization)
    Orch->>Worker: Route to specialist via worker tool
    Worker->>Worker: context_factory creates<br/>agent-specific Context

    Worker->>DataStore: Execute tools<br/>(read/write JSON)

    DataStore->>DataStore: Persist to JSON/SQLite

    Worker-->>Orch: Return results
    Orch-->>AppPy: Return response

    AppPy-->>Session: Send response<br/>to Chainlit

    Session-->>User: Display result
```

## Profile Caching

```mermaid
graph TB
    ProfilePath["PROFILE_PATH<br/>env variable<br/>default: data/miro_profile.json"]

    LoadProfile["load_profile()<br/>core/profile.py"]

    CheckCache["Check module-level<br/>cache"]

    Cache["Profile cache<br/>(module variable)"]

    ReadFile["Read JSON file<br/>from disk"]

    Parse["Parse JSON"]

    StoreCache["Store in cache"]

    ProfileObj["Profile dict"]

    ProfilePath --> LoadProfile
    LoadProfile --> CheckCache

    CheckCache -->|hit| Cache
    Cache --> ProfileObj

    CheckCache -->|miss| ReadFile
    ReadFile --> Parse
    Parse --> StoreCache
    StoreCache --> Cache
    Cache --> ProfileObj
```

## Checkpointing (LangGraph)

```mermaid
graph TB
    Checkpointer["MemorySaver<br/>(in-memory checkpointer)"]

    AgentState["Agent state<br/>(messages, tool results)"]

    SaveState["Save checkpoint<br/>after each step"]

    ResumeState["Resume from checkpoint<br/>(for HITL interrupts)"]

    Checkpointer --> SaveState
    Checkpointer --> ResumeState
    AgentState --> SaveState
    ResumeState --> AgentState
```

## Key Design Principles

1. **ContextVar Isolation** — Each async task gets its own context via contextvars
2. **ThreadID Namespacing** — `{parent}:{agent_name}` hierarchy prevents history cross-contamination
3. **Agent-Specific Contexts** — Each agent type has its own Context subclass (ProfileContext with completion_score, etc.)
4. **Profile Caching** — User profile loaded once and cached at module level
5. **LangGraph Checkpointing** — MemorySaver enables pause/resume for HITL workflows
6. **No Global State** — All context passed explicitly, enabling concurrent requests
7. **Session Binding** — AppContext tied to Chainlit session lifecycle
8. **Worker Agent Context Factory** — Each worker invocation creates a fresh agent-specific context
