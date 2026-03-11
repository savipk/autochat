# Message Flow: End-to-End Request Processing

Detailed sequence of how a user message flows through the entire AutoChat system.

## Message Flow Diagram

```mermaid
sequenceDiagram
    participant User as Chainlit User
    participant UI as Chainlit UI
    participant AppPy as app.py<br/>on_message
    participant Orchestrator as OrchestratorAgent
    participant SubAgent as Specialist Agent<br/>(Wrapped)
    participant Tools as Agent Tools
    participant DataSrc as Data Source<br/>(API/DB/JSON)
    participant Adapter as Chainlit Adapter
    participant CardComponent as UI Component<br/>(React Card)
    participant ResponseUI as Chainlit Chat

    User->>UI: Types message
    UI->>AppPy: Triggers on_message callback
    AppPy->>AppPy: Build AppContext<br/>from session
    AppPy->>Orchestrator: invoke(message, context)

    Orchestrator->>Orchestrator: Analyze intent<br/>Select specialist agent

    Orchestrator->>SubAgent: Create sub-agent wrapper<br/>ThreadID: parent:agent_name
    Orchestrator->>SubAgent: invoke(message, context)

    SubAgent->>SubAgent: Initialize state<br/>Apply middleware

    loop Tool Calling Loop
        SubAgent->>Tools: LLM selects tool to call
        Tools->>DataSrc: Execute tool<br/>(fetch data/compute)
        DataSrc-->>Tools: Return results
        Tools-->>SubAgent: Tool result
        SubAgent->>SubAgent: Process result<br/>Continue loop until done
    end

    SubAgent-->>Orchestrator: Return structured JSON<br/>(e.g., JobCard data)

    Orchestrator->>Adapter: Convert tool results<br/>to UI elements
    Adapter->>CardComponent: Create React component<br/>(JobCard, ProfileScore, etc.)
    CardComponent-->>Adapter: Component object

    Adapter-->>Orchestrator: UI element

    Orchestrator-->>AppPy: Structured response

    AppPy->>ResponseUI: cl.Message.send()<br/>(with custom element)
    ResponseUI->>UI: Render message + card
    UI-->>User: Display response
```

## Process Steps

1. **User Input** → Chainlit UI receives message
2. **Session Context** → app.py builds AppContext from session
3. **Orchestration** → OrchestratorAgent analyzes intent and selects specialist
4. **Sub-Agent Invocation** → Specialist agent created with namespaced ThreadID
5. **Tool Execution Loop** → Agent iteratively calls tools until task complete
6. **Data Fetching** → Tools query data sources (JSON, APIs, databases)
7. **Result Processing** → Tool results aggregated and structured
8. **UI Adaptation** → ChainlitAdapter converts results to React components
9. **Response Rendering** → Chainlit displays message with custom UI elements
10. **User Sees Result** → Chat shows both text and visual component

## Thread ID Namespacing

- Parent thread: `{session_id}`
- Child thread: `{parent_thread_id}:{agent_name}`
- Example: `abc123:ProfileAgent` (ensures isolated histories per agent)
