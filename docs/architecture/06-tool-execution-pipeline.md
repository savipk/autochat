# Tool Execution Pipeline

How tools are called, executed, and results are converted to UI elements.

## Tool Execution Flow

```mermaid
sequenceDiagram
    participant Agent as Specialist Agent
    participant LLM as Azure OpenAI LLM
    participant ToolExec as Tool Executor
    participant Tool as LangChain Tool
    participant DataSrc as Data Source
    participant Middleware as Middleware<br/>Stack

    Agent->>LLM: invoke() with tools
    LLM->>LLM: Analyze context<br/>Select tool to call
    LLM-->>Agent: Tool call decision<br/>(tool_name, args)

    Agent->>Middleware: Process tool call<br/>via middleware

    Middleware->>ToolExec: Execute with monitoring

    ToolExec->>Tool: Invoke LangChain tool<br/>with arguments

    Tool->>DataSrc: Query/modify data<br/>(JSON, API, DB)

    DataSrc-->>Tool: Return results
    Tool-->>ToolExec: Structured result

    ToolExec-->>Middleware: Log execution<br/>Record timing

    Middleware-->>Agent: Tool result

    Agent->>Agent: Process result<br/>Add to context

    loop Continue if not done
        Agent->>LLM: invoke() with updated context
        Note over LLM,Agent: Loop until LLM<br/>decides task complete
    end

    Agent-->>Agent: Aggregate results
    Agent-->>Agent: Format as JSON<br/>(for serialization)
```

## Tool Execution Detailed View

```mermaid
graph TB
    subgraph AgentState["Agent State"]
        messages["messages<br/>Conversation history"]
        intermediate["intermediate_steps<br/>Tool calls & results"]
        toolcalls["tool_calls<br/>Current invocation"]
    end

    subgraph LLMDecision["LLM Decision"]
        analyze["Analyze state"]
        decide["Decide next action<br/>Call tool or finish"]
        format_call["Format tool call<br/>name + arguments"]
    end

    subgraph ToolRegistry["Tool Registry"]
        lookup["Lookup tool<br/>by name"]
        tool["Tool instance<br/>LangChain Tool"]
        schema["Tool schema<br/>description, args"]
    end

    subgraph ToolInvoke["Tool Invocation"]
        validate["Validate arguments<br/>against schema"]
        exec["Execute function<br/>args → output"]
        result["Capture result<br/>Success or error"]
    end

    subgraph DataAccess["Data Access"]
        json["JSON file read<br/>profiles.json, etc."]
        api["API call<br/>External service"]
        db["Database query<br/>employee_directory"]
        compute["Computation<br/>in-process"]
    end

    subgraph ResultProcessing["Result Processing"]
        parse["Parse result<br/>Structured data"]
        enrich["Enrich with<br/>context/analysis"]
        serialize["Serialize<br/>for LLM"]
    end

    subgraph AgentContinue["Agent Loop"]
        append["Append to history<br/>messages + tool result"]
        recheck["LLM: continue or done?"]
        aggregate["Aggregate all results"]
        output["Format output JSON"]
    end

    AgentState --> LLMDecision
    LLMDecision --> analyze
    analyze --> decide
    decide --> format_call

    format_call --> ToolRegistry
    ToolRegistry --> lookup
    lookup --> tool
    tool --> schema

    schema --> ToolInvoke
    ToolInvoke --> validate
    validate --> exec

    exec --> DataAccess
    DataAccess --> json
    DataAccess --> api
    DataAccess --> db
    DataAccess --> compute

    json --> result
    api --> result
    db --> result
    compute --> result

    result --> ResultProcessing
    ResultProcessing --> parse
    parse --> enrich
    enrich --> serialize

    serialize --> AgentContinue
    AgentContinue --> append
    append --> recheck
    recheck -->|continue| LLMDecision
    recheck -->|done| aggregate
    aggregate --> output
```

## UI Adaptation Pipeline

```mermaid
graph TB
    subgraph AgentOutput["Agent Output<br/>(JSON)"]
        JobData["Job listing data<br/>{title, company, skills}"]
        ProfileData["Profile analysis<br/>{scores, summary}"]
        MessageData["Draft message<br/>{template, personalized}"]
        CandidateData["Candidate info<br/>{name, skills, role}"]
    end

    subgraph Adapter["Chainlit Adapter<br/>(core/adapters/chainlit_adapter.py)"]
        JobMapper["JobCard mapper<br/>JSON → JobCard props"]
        ProfileMapper["ProfileScore mapper<br/>JSON → ProfileScore props"]
        MessageMapper["DraftMessage mapper<br/>JSON → DraftMessage props"]
        CandidateMapper["CandidateCard mapper<br/>JSON → CandidateCard props"]
    end

    subgraph Components["React Components<br/>(public/elements/)"]
        JobCard["JobCard.jsx<br/>Teams-style card<br/>Display job info<br/>Apply button"]
        ProfileScore["ProfileScore.jsx<br/>Score visualization<br/>Skill badges<br/>Action buttons"]
        DraftMessage["DraftMessage.jsx<br/>Message preview<br/>Edit controls<br/>Send button"]
        CandidateCard["CandidateCard.jsx<br/>Candidate info<br/>Skill match<br/>View profile"]
        SkillsCard["SkillsCard.jsx<br/>Skills display<br/>Endorsement UI"]
    end

    subgraph ChainlitUI["Chainlit UI"]
        Message["cl.Message<br/>with custom elements"]
        Display["Browser render"]
        Interaction["User interaction<br/>clicks, edits"]
    end

    JobData --> JobMapper
    ProfileData --> ProfileMapper
    MessageData --> MessageMapper
    CandidateData --> CandidateMapper

    JobMapper --> JobCard
    ProfileMapper --> ProfileScore
    MessageMapper --> DraftMessage
    CandidateMapper --> CandidateCard

    JobCard --> Message
    ProfileScore --> Message
    DraftMessage --> Message
    CandidateCard --> Message
    SkillsCard --> Message

    Message --> Display
    Display --> Interaction
```

## Middleware Execution Order

```mermaid
graph TB
    Input["Tool call input"]

    M1["1. Custom Agent<br/>Middleware<br/>(agents/&lt;name&gt;/middleware.py)"]
    M2["2. Tool Monitor<br/>Middleware<br/>(core/middleware/tool_monitor.py)"]
    M3["3. Summarization<br/>Middleware<br/>(core/middleware/summarization.py)"]

    Exec["Tool Execution"]

    M3b["3. Summarization<br/>Post-processing"]
    M2b["2. Tool Monitor<br/>Logging & timing"]
    M1b["1. Custom Agent<br/>Post-processing"]

    Output["Tool result output"]

    Input --> M1
    M1 --> M2
    M2 --> M3
    M3 --> Exec

    Exec --> M3b
    M3b --> M2b
    M2b --> M1b
    M1b --> Output
```

## Tool Result Format

```mermaid
graph TB
    ToolResult["Tool Result"]

    Success["Success<br/>{<br/>  'status': 'success',<br/>  'data': {...},<br/>  'metadata': {...}<br/>}"]

    Error["Error<br/>{<br/>  'status': 'error',<br/>  'error': 'message',<br/>  'details': {...}<br/>}"]

    Partial["Partial<br/>{<br/>  'status': 'partial',<br/>  'data': {...},<br/>  'remaining': [...]<br/>}"]

    ToolResult --> Success
    ToolResult --> Error
    ToolResult --> Partial
```

## Key Points

1. **LLM Decision Loop** — Agent keeps looping until LLM decides task is complete
2. **Middleware Wrapping** — Each tool call is wrapped in middleware chain
3. **Tool Registry Lookup** — Tools resolved dynamically by name
4. **Data Source Abstraction** — Tools can query JSON, APIs, databases, or compute
5. **UI Adaptation** — Agent JSON results mapped to React components via adapter
6. **Rich UI Components** — Teams-style cards with interaction handlers
7. **Streaming Support** — Results can be streamed back to UI in real-time
