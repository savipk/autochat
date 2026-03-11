# State Management Architecture

How application state flows through the system and how threading is isolated via context variables.

## AppContext Flow

```mermaid
graph TB
    subgraph SessionInit["Session Initialization"]
        UserSession["Chainlit Session<br/>session_id generated"]
        OnMessage["on_message callback"]
        AppPyHandler["app.py handler<br/>builds AppContext"]
    end

    subgraph ContextConstruction["AppContext Construction"]
        UserProfile["Load user profile<br/>PROFILE_PATH env"]
        SessionData["Session data<br/>chat history"]
        Preferences["User preferences<br/>settings"]
        ThreadID["ThreadID<br/>session_id"]
        BuildContext["Build AppContext<br/>from components"]
    end

    subgraph ContextVar["ContextVar<br/>(contextvars)"]
        ContextVarDef["context_var = ContextVar<br/>('app_context')"]
        TokenSet["token = context_var.set<br/>(app_context)"]
        Isolation["Isolated per<br/>async task"]
    end

    subgraph AgentAccess["Agent Access"]
        GetContext["get_context()<br/>retrieve from ContextVar"]
        Profile["Access profile"]
        History["Access history"]
        Prefs["Access preferences"]
    end

    subgraph ThreadIDScoping["ThreadID Scoping"]
        ParentID["Parent ThreadID<br/>abc123"]
        ChildID["Child ThreadID<br/>abc123:ProfileAgent"]
        IsolatedHistory["Isolated message<br/>history per ThreadID"]
    end

    subgraph DataUpdate["Data Updates"]
        Persist["Persist changes<br/>to JSON/DB"]
        UpdateProfile["Update profile.json"]
        UpdateHistory["Update chat history<br/>data.db"]
    end

    UserSession --> OnMessage
    OnMessage --> AppPyHandler

    AppPyHandler --> UserProfile
    AppPyHandler --> SessionData
    AppPyHandler --> Preferences
    AppPyHandler --> ThreadID
    UserProfile --> BuildContext
    SessionData --> BuildContext
    Preferences --> BuildContext
    ThreadID --> BuildContext

    BuildContext --> ContextVarDef
    ContextVarDef --> TokenSet
    TokenSet --> Isolation

    Isolation --> GetContext
    GetContext --> Profile
    GetContext --> History
    GetContext --> Prefs

    ThreadID --> ParentID
    ParentID --> ChildID
    ChildID --> IsolatedHistory

    Profile --> Persist
    History --> Persist
    Persist --> UpdateProfile
    Persist --> UpdateHistory
```

## AppContext Data Structure

```mermaid
graph TB
    AppContext["AppContext<br/>Root"]

    Session["session_id<br/>string<br/>Unique session"]
    ThreadID["thread_id<br/>string<br/>Current thread"]
    UserID["user_id<br/>string<br/>User identifier"]

    Profile["profile<br/>UserProfile<br/>object"]
    ProfileName["name, email<br/>skills, experience<br/>education"]
    ProfileScore["scores<br/>compatibility, fit"]

    History["message_history<br/>List[Message]"]
    HistMsg["messages with<br/>timestamps<br/>and results"]

    Preferences["preferences<br/>dict"]
    PrefTheme["theme, language<br/>notification settings"]

    State["agent_state<br/>dict"]
    StateData["Current task data<br/>Intermediate results"]

    AppContext --> Session
    AppContext --> ThreadID
    AppContext --> UserID
    AppContext --> Profile
    AppContext --> History
    AppContext --> Preferences
    AppContext --> State

    Profile --> ProfileName
    Profile --> ProfileScore

    History --> HistMsg
    Preferences --> PrefTheme
    State --> StateData
```

## ThreadID Isolation Model

```mermaid
graph TB
    subgraph Session1["Session: abc123"]
        OrchestratorThread["OrchestratorAgent<br/>ThreadID: abc123"]

        subgraph SubThread1["ProfileAgent<br/>ThreadID: abc123:ProfileAgent"]
            ProfHistory["Message history<br/>isolated"]
            ProfState["Agent state<br/>isolated"]
        end

        subgraph SubThread2["JobDiscoveryAgent<br/>ThreadID: abc123:JobDiscoveryAgent"]
            JobHistory["Message history<br/>isolated"]
            JobState["Agent state<br/>isolated"]
        end

        subgraph SubThread3["OutreachAgent<br/>ThreadID: abc123:OutreachAgent"]
            OutHistory["Message history<br/>isolated"]
            OutState["Agent state<br/>isolated"]
        end
    end

    OrchestratorThread -->|parent| SubThread1
    OrchestratorThread -->|parent| SubThread2
    OrchestratorThread -->|parent| SubThread3

    SubThread1 -.->|no cross-talk| SubThread2
    SubThread1 -.->|no cross-talk| SubThread3
    SubThread2 -.->|no cross-talk| SubThread3

    style SubThread1 fill:#e1f5ff
    style SubThread2 fill:#f3e5f5
    style SubThread3 fill:#e8f5e9
```

## Async Isolation via ContextVar

```mermaid
graph TB
    subgraph Main["Main Thread"]
        Task1["Task 1<br/>ThreadID: abc123:Agent1"]
        Task2["Task 2<br/>ThreadID: abc123:Agent2"]
        Task3["Task 3<br/>ThreadID: abc123:Agent3"]
    end

    subgraph ContextVars["ContextVar Storage"]
        CV1["Token for Task 1<br/>context_var → AppContext 1"]
        CV2["Token for Task 2<br/>context_var → AppContext 2"]
        CV3["Token for Task 3<br/>context_var → AppContext 3"]
    end

    subgraph Isolation["Isolation Guarantee"]
        I1["Task 1 calls<br/>get_context()<br/>→ AppContext 1"]
        I2["Task 2 calls<br/>get_context()<br/>→ AppContext 2"]
        I3["Task 3 calls<br/>get_context()<br/>→ AppContext 3"]
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
    participant Agent as Agent
    participant DataStore as Data Store

    User->>Session: Start conversation
    Session->>AppPy: on_message(message)

    AppPy->>AppPy: Load profile from<br/>PROFILE_PATH

    AppPy->>AppPy: Build AppContext<br/>with profile, history

    AppPy->>ContextMgr: context_var.set(app_context)<br/>returns token

    ContextMgr->>Agent: Invoke agent with context

    Agent->>ContextMgr: get_context()<br/>retrieve AppContext

    Agent->>Agent: Use context<br/>profile, history, prefs

    Agent->>DataStore: Update profile<br/>or state

    DataStore->>DataStore: Persist to JSON/DB

    Agent-->>AppPy: Return results

    AppPy->>ContextMgr: token.reset()<br/>cleanup context

    AppPy-->>Session: Send response<br/>to Chainlit

    Session-->>User: Display result
```

## Profile Caching

```mermaid
graph TB
    ProfilePath["PROFILE_PATH<br/>env variable<br/>e.g., /path/to/profile.json"]

    LoadProfile["load_profile()<br/>core/profile.py"]

    CheckCache["Check in-memory<br/>cache"]

    Cache["Profile cache<br/>dictionary"]

    ReadFile["Read JSON file<br/>from disk"]

    Parse["Parse JSON<br/>Validate schema"]

    StoreCache["Store in cache<br/>for future use"]

    ProfileObj["UserProfile<br/>object"]

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

## Context Cleanup

```mermaid
graph TB
    Token["ContextVar token<br/>from context_var.set()"]

    AgentExec["Agent execution<br/>completes"]

    AgentExec --> Token

    Reset["token.reset()<br/>restore previous value"]

    Cleanup["ContextVar<br/>cleaned up"]

    NextTask["Next task<br/>fresh context"]

    Token --> Reset
    Reset --> Cleanup
    Cleanup --> NextTask
```

## Key Design Principles

1. **ContextVar Isolation** — Each async task gets its own AppContext via contextvars
2. **ThreadID Namespacing** — Parent:Child hierarchy prevents history cross-contamination
3. **Profile Caching** — User profile loaded once and cached for session
4. **Preference Persistence** — User settings maintained across conversation
5. **Cleanup** — ContextVar tokens reset after agent execution
6. **No Global State** — All context passed explicitly, enabling concurrent requests
7. **Session Binding** — AppContext tied to Chainlit session lifecycle
