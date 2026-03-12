# Message Flow: End-to-End Request Processing

Detailed sequence of how a user message flows through the entire HR Agent system.

## Message Flow Diagram

```mermaid
sequenceDiagram
    participant User as Chainlit User
    participant UI as Chainlit UI
    participant AppPy as app.py<br/>on_message
    participant Orchestrator as OrchestratorAgent
    participant Worker as Worker Agent<br/>(Wrapped Specialist)
    participant Tools as Agent Tools
    participant DataSrc as Data Source<br/>(JSON/DB)
    participant Adapter as Chainlit Adapter
    participant CardComponent as UI Component<br/>(React Card)
    participant ResponseUI as Chainlit Chat

    User->>UI: Types message
    UI->>AppPy: Triggers on_message callback
    AppPy->>AppPy: Build AppContext<br/>(thread_id, first_name, display_name)
    AppPy->>AppPy: Check for pending HITL interrupt
    AppPy->>Orchestrator: invoke(message, context)

    Orchestrator->>Orchestrator: Middleware: summarization,<br/>orchestrator_personalization,<br/>tool_monitor
    Orchestrator->>Orchestrator: Analyze intent<br/>Select specialist agent

    Orchestrator->>Worker: _create_worker_agent()<br/>ThreadID: parent:agent_name
    Orchestrator->>Worker: invoke(message, context)

    Worker->>Worker: Middleware: summarization,<br/>personalization, tool_monitor

    loop Tool Calling Loop
        Worker->>Tools: LLM selects tool to call
        Tools->>DataSrc: Execute tool<br/>(fetch data/compute)
        DataSrc-->>Tools: Return results
        Tools-->>Worker: Tool result
        Worker->>Worker: Process result<br/>Continue loop until done
    end

    Worker-->>Orchestrator: Return JSON<br/>(tool_calls + optional interrupts)

    Orchestrator->>Adapter: extract_tool_calls_from_messages()
    Adapter->>Adapter: Unwrap inner tool calls<br/>from orchestrator wrapper
    Adapter->>CardComponent: render_tool_elements()<br/>(JobCard, ProfileScore, etc.)
    CardComponent-->>Adapter: Component objects

    Adapter-->>Orchestrator: UI elements list

    Orchestrator-->>AppPy: Structured response

    AppPy->>ResponseUI: cl.Message.send()<br/>(with custom elements)
    ResponseUI->>UI: Render message + cards
    UI-->>User: Display response
```

## HITL Interrupt Flow

```mermaid
sequenceDiagram
    participant User as User
    participant AppPy as app.py
    participant Adapter as Chainlit Adapter
    participant Orch as OrchestratorAgent
    participant Worker as Worker Agent
    participant HITL as HumanInTheLoopMiddleware

    User->>AppPy: "Add skills to my profile"
    AppPy->>Orch: invoke(message)
    Orch->>Worker: call profile worker
    Worker->>HITL: update_profile intercepted
    HITL-->>Worker: Interrupt raised
    Worker-->>Orch: {interrupts: [...]}

    Orch-->>AppPy: Response with interrupts
    AppPy->>Adapter: extract_interrupts_from_messages()
    AppPy->>Adapter: render_interrupt_elements()
    Adapter-->>AppPy: ProfileUpdateConfirmation card

    AppPy->>User: Show confirmation card

    User->>AppPy: Clicks "Approve"
    AppPy->>AppPy: action_callback("approve_profile_update")
    AppPy->>Worker: agent.resume(decision="approve")
    Worker-->>AppPy: Updated result
    AppPy->>User: Show confirmation
```

## Process Steps

1. **User Input** → Chainlit UI receives message
2. **HITL Check** → app.py checks for pending interrupt from previous turn
3. **Session Context** → app.py builds AppContext (thread_id, first_name, display_name)
4. **Orchestration** → OrchestratorAgent applies middleware, analyzes intent, selects specialist
5. **Worker Agent Invocation** → Specialist agent wrapped as tool with namespaced ThreadID
6. **Specialist Middleware** → Personalization, profile warnings, HITL interception applied
7. **Tool Execution Loop** → Agent iteratively calls tools until task complete
8. **Data Fetching** → Tools query JSON files or compute results
9. **Result Extraction** → `extract_tool_calls_from_messages()` unwraps inner tool calls
10. **Interrupt Extraction** → `extract_interrupts_from_messages()` finds HITL interrupts
11. **UI Adaptation** → `render_tool_elements()` converts results to React components
12. **Response Rendering** → Chainlit displays message with custom UI elements

## Thread ID Namespacing

- Parent thread: `{session_id}`
- Child thread: `{parent_thread_id}:{agent_name}`
- Example: `abc123:profile` (ensures isolated histories per agent)
