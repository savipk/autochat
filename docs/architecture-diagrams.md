# HR Agent Architecture Diagrams

## 1) System Context Diagram

```mermaid
flowchart LR
  U["Employee / Hiring Manager"] --> UI["Chainlit Web UI"]
  UI --> AC["HR Agent App Runtime (app.py)"]

  AC --> ORCH["Orchestrator Agent"]
  ORCH --> MC["MyCareer Agent"]
  ORCH --> JD["JD Generator Agent"]

  MC --> PF["Profile JSON Files (data/*.json)"]
  MC --> JOBS["Job Dataset (data/matching_jobs.json)"]
  JD --> SK["JD Standards Skill File (agents/jd_generator/skills/*.md)"]

  AC --> API["Profile API + SSE (/api/profile/*)"]
  API --> PF
  API --> DRAFTS["Draft Files (data/drafts/<user>)"]

  AC --> DB["SQLite Chat History (data/data.db)"]
  ORCH --> LLM["Azure OpenAI (via AzureChatOpenAI)"]
  MC --> LLM
  JD --> LLM
```

Notes:
- This shows where `HR Agent` sits between end users, AI models, and local persistence.
- The orchestrator is the single routing point that delegates to specialist agents.
- Profile APIs and SSE support side-panel UX for profile editing and refresh events.

## 2) Core Component Diagram

```mermaid
flowchart TB
  subgraph CoreService["HR Agent Core Service"]
    APP["Chainlit Entry + Session/Auth\n(app.py)"]
    ROUTER["Message Router\n(on_message)"]
    ORCH["OrchestratorAgent\n(routes to worker agents)"]
    REG["AgentRegistry\n(mycareer, jd_generator)"]
    ADAPT["Chainlit Adapter\n(render_tool_elements,\nrender_interrupt_elements)"]
    PR["Profile Routes API\n(core/profile_routes.py)"]
    PM["ProfileManager\n(load/save drafts/submit)"]
    DL["SQLiteCompatibleDataLayer\n(chat threads/users)"]
  end

  APP --> ROUTER
  ROUTER --> ORCH
  ORCH --> REG
  ORCH --> ADAPT
  APP --> PR
  PR --> PM
  APP --> DL

  REG --> MC["MyCareer Agent\n+ middleware + HITL"]
  REG --> JD["JD Generator Agent\n+ skill loader"]

  MC --> MT["MyCareer Tools\n(get_matches, update_profile,\ninfer_skills, ask_jd_qa, etc.)"]
  JD --> JT["JD Tools\n(jd_search, jd_compose,\nsection_editor, jd_finalize)"]

  MT --> FS["Local JSON Data Files"]
  JT --> FS
```

 notes:
- `app.py` is the runtime entry and wires auth, routing, and API mounting.
- The adapter layer turns tool outputs into rich UI elements (cards/panels).
- MyCareer includes human-in-the-loop approval for `update_profile` before persistence.

## 3) Regular Sequence Diagram (Normal Request, No HITL)

```mermaid
sequenceDiagram
  autonumber
  participant User
  participant UI as Chainlit UI
  participant App as app.py
  participant Orch as OrchestratorAgent
  participant MC as MyCareer Agent
  participant Tool as MyCareer Tool (e.g., get_matches)
  participant Data as Local Data Files

  User->>UI: "Find matching roles"
  UI->>App: on_message()
  App->>Orch: invoke(message, AppContext)
  Orch->>MC: delegate as worker agent

  MC->>Tool: call get_matches(filters, search_text)
  Tool->>Data: read matching_jobs.json (+ profile data)
  Data-->>Tool: jobs/profile payload
  Tool-->>MC: tool result (matches, scores)

  MC-->>Orch: worker response + inner tool summary
  Orch-->>App: final turn messages
  App-->>UI: text response + JobCard element(s)
```

 notes:
- This is the baseline flow for most requests: route, tool call, respond.
- No interrupt means the turn completes in one pass.
- The adapter renders structured UI elements from tool outputs.

## 4) Key Sequence Diagram (Profile Update with Approval)

```mermaid
sequenceDiagram
  autonumber
  participant User
  participant UI as Chainlit UI
  participant App as app.py
  participant Orch as OrchestratorAgent
  participant MC as MyCareer Agent
  participant HITL as HumanInTheLoop Middleware
  participant PM as ProfileManager
  participant SSE as /api/profile/events

  User->>UI: "Update my profile skills"
  UI->>App: on_message()
  App->>Orch: invoke(message, AppContext)
  Orch->>MC: delegate as worker agent

  MC->>HITL: proposes update_profile(section, updates)
  HITL-->>MC: interrupt (await approve/reject)
  MC-->>Orch: response + interrupt payload
  Orch-->>App: current turn messages
  App-->>UI: show ProfileUpdateConfirmation card

  User->>UI: clicks Approve
  UI->>App: action_callback("approve_profile_update")
  App->>MC: resume(decision=approve, thread_id=parent:mycareer)

  MC->>PM: submit(updated profile JSON)
  PM-->>MC: persisted (+ backup .bak)
  MC-->>App: resumed completion

  App->>SSE: set_profile_updated() + push refresh event
  SSE-->>UI: refresh side panel
  App-->>UI: "Profile updated"
```

 notes:
- This is the highest-value flow for trust and control.
- Profile changes are interrupt-gated: no write until user approves.
- After approval, the UI gets a refresh event via SSE to stay in sync.
