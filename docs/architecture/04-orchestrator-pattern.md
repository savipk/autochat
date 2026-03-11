# Orchestrator Pattern

How the OrchestratorAgent discovers, wraps, and delegates to specialist agents.

## Orchestrator Architecture Diagram

```mermaid
graph TB
    subgraph OrchestratorFlow["OrchestratorAgent Flow"]
        Input["User Message<br/>+ Context"]
        Receive["on_message<br/>receives input"]
        LLMAnalyze["LLM analyzes intent<br/>Select specialist agent"]
        SelectAgent["Determine target agent<br/>based on message type"]
    end

    subgraph SubAgentWrapper["Sub-Agent Wrapping"]
        CreateWrapper["_create_sub_agent()<br/>factory function"]
        ConfigAgent["Wrap specialist agent<br/>as LangChain tool"]
        ThreadID["Create ThreadID<br/>parent:agent_name"]
        StateBinding["Bind state<br/>and context"]
    end

    subgraph Invocation["Sub-Agent Invocation"]
        InvokeSubAgent["invoke(message)<br/>on specialist"]
        AwaitResult["Await response"]
        ParseJSON["Parse structured JSON<br/>from specialist"]
    end

    subgraph Specialists["Available Specialists"]
        ProfileAgent["ProfileAgent<br/>Profile analysis,<br/>skill inference,<br/>updates"]
        JobAgent["JobDiscoveryAgent<br/>Job search,<br/>details lookup,<br/>Q&A"]
        OutreachAgent["OutreachAgent<br/>Draft messages,<br/>send communication,<br/>apply for roles"]
        JDAgent["JDGeneratorAgent<br/>Compose JD,<br/>edit sections,<br/>finalize"]
        CandidateAgent["CandidateSearchAgent<br/>Find employees,<br/>view profiles"]
    end

    subgraph Response["Response Aggregation"]
        AggResult["Aggregate specialist<br/>response"]
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

    StateBinding --> InvokeSubAgent
    InvokeSubAgent --> AwaitResult
    AwaitResult --> ParseJSON

    ParseJSON --> AggResult
    AggResult --> ConvertUI
    ConvertUI --> ReturnOrch

    RegList --> RegFetch
    ConfigAgent --> ProfileAgent
    ConfigAgent --> JobAgent
    ConfigAgent --> OutreachAgent
    ConfigAgent --> JDAgent
    ConfigAgent --> CandidateAgent
```

## Sub-Agent Tool Integration

```mermaid
graph LR
    Orch["OrchestratorAgent<br/>LLM Tools"]
    SubAgentTool["Sub-Agent Tool<br/>(wrapped specialist)"]
    Specialist["Specialist Agent<br/>(e.g., ProfileAgent)"]
    SpecTools["Specialist Tools<br/>(6 tools for Profile)"]

    Orch -->|calls| SubAgentTool
    SubAgentTool -->|invokes| Specialist
    Specialist -->|uses| SpecTools
    SpecTools -->|return| SubAgentTool
    SubAgentTool -->|returns| Orch
```

## ThreadID Namespacing

```mermaid
graph TB
    SessionStart["Session Started<br/>ThreadID: abc123"]
    OrchestratorThread["OrchestratorAgent<br/>ThreadID: abc123"]

    Call1["User asks: Analyze my profile"]
    SubAgent1["ProfileAgent<br/>ThreadID: abc123:ProfileAgent<br/>Isolated history"]

    Call2["User asks: Find jobs for me"]
    SubAgent2["JobDiscoveryAgent<br/>ThreadID: abc123:JobDiscoveryAgent<br/>Isolated history"]

    Call3["User asks: Draft outreach"]
    SubAgent3["OutreachAgent<br/>ThreadID: abc123:OutreachAgent<br/>Isolated history"]

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

## Key Design Patterns

### 1. **Sub-Agent Wrapping**
- Each specialist agent is dynamically wrapped as a LangChain tool
- Orchestrator can compose specialists without tight coupling
- Enables flexible routing based on intent

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
