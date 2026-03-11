# Middleware Stack Architecture

How middleware wraps agent execution and applies cross-cutting concerns.

## Middleware Stack Composition

```mermaid
graph TB
    subgraph Input["Agent Input"]
        Message["User message"]
        Context["AppContext"]
    end

    subgraph GlobalMW["Global Middleware<br/>(Applied to all agents)"]
        MW1["Tool Monitor Middleware<br/>core/middleware/tool_monitor.py<br/>Logs & tracks tool calls"]
        MW2["Summarization Middleware<br/>core/middleware/summarization.py<br/>Compresses history"]
    end

    subgraph AgentMW["Agent-Specific Middleware<br/>(agents/&lt;name&gt;/middleware.py)"]
        AMWP["ProfileAgent<br/>Custom middleware"]
        AMWJ["JobDiscoveryAgent<br/>Custom middleware"]
        AMWO["OutreachAgent<br/>Custom middleware"]
        AMWJD["JDGeneratorAgent<br/>Custom middleware"]
        AMWC["CandidateSearchAgent<br/>Custom middleware"]
    end

    subgraph Stack["Middleware Stack Order<br/>(in AgentConfig.middleware)"]
        Order["1. Agent-specific MW<br/>2. Tool Monitor MW<br/>3. Summarization MW<br/>4. [more if needed]"]
    end

    subgraph Execution["Agent Execution"]
        Setup["Setup state<br/>Apply middleware"]
        Invoke["invoke() with tools"]
        ToolLoop["Tool calling loop"]
    end

    subgraph Output["Agent Output"]
        Result["Structured result"]
    end

    Input --> GlobalMW
    GlobalMW --> MW1
    GlobalMW --> MW2

    Input --> AgentMW
    AgentMW --> AMWP
    AgentMW --> AMWJ
    AgentMW --> AMWO
    AgentMW --> AMWJD
    AgentMW --> AMWC

    GlobalMW --> Stack
    AgentMW --> Stack

    Stack --> Execution
    Execution --> Setup
    Setup --> Invoke
    Invoke --> ToolLoop
    ToolLoop --> Output
```

## Middleware Execution Flow

```mermaid
sequenceDiagram
    participant Agent as BaseAgent
    participant MW1 as Agent Custom MW
    participant MW2 as Tool Monitor MW
    participant MW3 as Summarization MW
    participant Core as Agent Core<br/>invoke()
    participant Tools as LangChain Tools

    Agent->>MW1: invoke(state)

    MW1->>MW1: Pre-process<br/>agent-specific logic

    MW1->>MW2: invoke(state)

    MW2->>MW2: Pre-process<br/>start timing

    MW2->>MW3: invoke(state)

    MW3->>MW3: Pre-process<br/>check history length

    MW3->>Core: invoke(state)

    Core->>Tools: Tool calling loop
    Tools-->>Core: Tool results

    Core-->>MW3: Execution complete

    MW3->>MW3: Post-process<br/>Compress history<br/>if needed

    MW3-->>MW2: Return state

    MW2->>MW2: Post-process<br/>Log timing & metadata

    MW2-->>MW1: Return state

    MW1->>MW1: Post-process<br/>Agent-specific cleanup

    MW1-->>Agent: Final result
```

## Tool Monitor Middleware

```mermaid
graph TB
    ToolMonitor["Tool Monitor Middleware<br/>core/middleware/tool_monitor.py"]

    subgraph Pre["Pre-Tool Logging"]
        LogCall["Log tool call<br/>Tool name + args"]
        Timestamp["Record start time"]
        Context["Capture context"]
    end

    subgraph Exec["Tool Execution<br/>(Passthrough)"]
        Call["Tool executes<br/>as normal"]
    end

    subgraph Post["Post-Tool Logging"]
        Duration["Calculate duration<br/>end_time - start_time"]
        LogResult["Log result status<br/>Success/Error/Partial"]
        Metrics["Record metrics<br/>(latency, tokens)"]
    end

    ToolMonitor --> Pre
    Pre --> LogCall
    Pre --> Timestamp
    Pre --> Context

    Context --> Exec
    Exec --> Call
    Call --> Post
    Post --> Duration
    Post --> LogResult
    Post --> Metrics
```

## Summarization Middleware

```mermaid
graph TB
    SumMW["Summarization Middleware<br/>core/middleware/summarization.py"]

    subgraph Config["Configuration<br/>(core/config.py)"]
        Threshold["Message Threshold<br/>e.g., 50 messages"]
        SummaryInterval["Summarization Interval<br/>How often to compress"]
    end

    subgraph Check["Compression Check"]
        CountMsgs["Count messages<br/>in history"]
        Compare["Compare to threshold"]
        Decision["Decision:<br/>Compress or pass-through"]
    end

    subgraph Compress["Compression Pipeline"]
        SelectOld["Select oldest<br/>messages"]
        CreateSummary["LLM summarizes<br/>Extract key points"]
        Replace["Replace old messages<br/>with summary token"]
    end

    subgraph Output["Output"]
        CompressedHist["Compressed history<br/>+ fresh messages"]
        PassThrough["Original history<br/>unchanged"]
    end

    SumMW --> Config
    Config --> Threshold
    Config --> SummaryInterval

    Threshold --> Check
    SummaryInterval --> Check

    Check --> CountMsgs
    CountMsgs --> Compare
    Compare --> Decision

    Decision -->|threshold exceeded| Compress
    Decision -->|under threshold| PassThrough

    Compress --> SelectOld
    SelectOld --> CreateSummary
    CreateSummary --> Replace
    Replace --> CompressedHist
```

## Custom Agent Middleware Example

```mermaid
graph TB
    CustomMW["Custom Middleware<br/>agents/profile/middleware.py<br/>(Example)"]

    subgraph Pre["Pre-Agent Setup"]
        LoadProfile["Load user profile"]
        ValidateProfile["Validate profile schema"]
        EnrichContext["Enrich context with<br/>profile metadata"]
    end

    subgraph Exec["Agent Execution"]
        AgentRuns["Agent runs normally<br/>with enriched context"]
    end

    subgraph Post["Post-Agent Processing"]
        ParseResult["Parse agent result<br/>Extract profile updates"]
        ValidateUpdate["Validate updates<br/>against schema"]
        BackupProfile["Create backup<br/>of old profile"]
        ApplyUpdate["Apply updates<br/>to profile"]
    end

    CustomMW --> Pre
    Pre --> LoadProfile
    Pre --> ValidateProfile
    Pre --> EnrichContext

    EnrichContext --> Exec
    Exec --> AgentRuns

    AgentRuns --> Post
    Post --> ParseResult
    Post --> ValidateUpdate
    Post --> BackupProfile
    Post --> ApplyUpdate
```

## Middleware Composition

```mermaid
graph TB
    subgraph ProfileAgentConfig["ProfileAgent AgentConfig"]
        Config1["middleware = [<br/>  ProfileCustomMW(),<br/>  ToolMonitorMW(),<br/>  SummarizationMW()<br/>]"]
    end

    subgraph JobAgentConfig["JobDiscoveryAgent AgentConfig"]
        Config2["middleware = [<br/>  JobDiscoveryCustomMW(),<br/>  ToolMonitorMW(),<br/>  SummarizationMW()<br/>]"]
    end

    subgraph OutreachAgentConfig["OutreachAgent AgentConfig"]
        Config3["middleware = [<br/>  OutreachCustomMW(),<br/>  ToolMonitorMW(),<br/>  SummarizationMW()<br/>]"]
    end

    ProfileAgentConfig -->|ordered execution| ExecutionOrder
    JobAgentConfig -->|ordered execution| ExecutionOrder
    OutreachAgentConfig -->|ordered execution| ExecutionOrder

    subgraph ExecutionOrder["Execution Order<br/>(Top to Bottom)"]
        Step1["1. Agent-specific<br/>pre-processing"]
        Step2["2. Tool monitoring<br/>Start timing"]
        Step3["3. History summarization<br/>Check threshold"]
        Step4["4. Agent.invoke()<br/>Tool loop"]
        Step5["3. History summarization<br/>Compress if needed"]
        Step6["2. Tool monitoring<br/>Log metrics"]
        Step7["1. Agent-specific<br/>post-processing"]
    end

    Step1 --> Step2
    Step2 --> Step3
    Step3 --> Step4
    Step4 --> Step5
    Step5 --> Step6
    Step6 --> Step7
```

## Middleware Chain Pattern

```mermaid
graph TB
    Input["Input:<br/>Message + State"]

    MW["Middleware<br/>Instance"]

    Pre["Pre-handler<br/>transform input"]

    Next["Call next<br/>middleware<br/>or core agent"]

    Result["Result from<br/>next in chain"]

    Post["Post-handler<br/>transform output"]

    Output["Output:<br/>Modified result"]

    Input --> MW
    MW --> Pre
    Pre -->|modified| Next
    Next --> Result
    Result -->|returned| Post
    Post -->|modified| Output
```

## Key Points

1. **Ordered Stack** — Middleware applied in order defined in AgentConfig
2. **Pre/Post Processing** — Middleware can modify input and output
3. **Passthrough** — Each middleware can skip if not applicable
4. **Agent-Specific** — Different agents have different middleware
5. **Composable** — New middleware can be added without modifying agents
6. **Tool Monitoring** — Universal tool tracking and timing
7. **History Management** — Summarization keeps token usage under control
8. **Custom Logic** — Each agent can implement domain-specific concerns
