# UI Component Architecture

React components in the frontend and their styling patterns.

## Component Hierarchy

```mermaid
graph TB
    subgraph Webapp["HR Assistant App<br/>Web Interface"]
        ChatWindow["Chat Window"]
        MessageList["Message List"]
        InputBox["Message Input"]
    end

    subgraph MessageComponent["cl.Message<br/>(Webapp)"]
        TextContent["Text content<br/>from agent"]
        CustomElement["Custom Element<br/>(React component)"]
    end

    subgraph ReactComponents["React Components<br/>(public/elements/) — 10 total"]
        JobCard["JobCard.jsx"]
        ProfileScore["ProfileScore.jsx"]
        DraftMessage["DraftMessage.jsx"]
        CandidateCard["CandidateCard.jsx"]
        SkillsCard["SkillsCard.jsx"]
        SendConfirmation["SendConfirmation.jsx"]
        ProfileUpdateConfirmation["ProfileUpdateConfirmation.jsx"]
        RequisitionCard["RequisitionCard.jsx"]
        JdQaCard["JdQaCard.jsx"]
        JdFinalizedCard["JdFinalizedCard.jsx"]
    end

    subgraph SidePanels["Side Panels (SSE-driven)"]
        ProfilePanel["Profile Editor Panel"]
        JDEditorPanel["JD Editor Panel"]
        JobDetailPanel["Job Detail Panel"]
    end

    subgraph Styling["Microsoft Teams Styling"]
        PrimaryBtn["Primary Button<br/>#6264A7"]
        OutlineBtn["Outline Button<br/>#6264A7 border"]
        GhostBtn["Ghost Button<br/>#6264A7 text"]
        DisabledBtn["Disabled<br/>#464775"]
    end

    ChatWindow --> MessageList
    MessageList --> MessageComponent
    MessageComponent --> TextContent
    MessageComponent --> CustomElement

    CustomElement --> JobCard
    CustomElement --> ProfileScore
    CustomElement --> DraftMessage
    CustomElement --> CandidateCard
    CustomElement --> SkillsCard
    CustomElement --> SendConfirmation
    CustomElement --> ProfileUpdateConfirmation
    CustomElement --> RequisitionCard
    CustomElement --> JdQaCard
    CustomElement --> JdFinalizedCard

    JobCard --> Styling
    ProfileScore --> Styling
    DraftMessage --> Styling
    CandidateCard --> Styling
    SkillsCard --> Styling
    SendConfirmation --> Styling
    ProfileUpdateConfirmation --> Styling
    RequisitionCard --> Styling
    JdQaCard --> Styling
    JdFinalizedCard --> Styling
```

## Component → Tool Mapping

| Component | Triggered By | Purpose |
|-----------|-------------|---------|
| `JobCard.jsx` | `get_matches` | Grid of job listing cards with View button |
| `ProfileScore.jsx` | `profile_analyzer` | Completion % gauge with section breakdown |
| `SkillsCard.jsx` | `infer_skills` | Interactive skill selection with evidence citations, save to profile |
| `DraftMessage.jsx` | `draft_message` | Message preview with recipient, body, send flow |
| `SendConfirmation.jsx` | `send_message` | Confirmation with recipient name, type, timestamp |
| `ProfileUpdateConfirmation.jsx` | `update_profile` / `rollback_profile` (HITL) | Before/after diff with Approve/Reject buttons |
| `JdQaCard.jsx` | `ask_jd_qa` | Q&A answer with citations and HM contact suggestion |
| `CandidateCard.jsx` | `search_candidates` | Candidate grid with skills and match info |
| `RequisitionCard.jsx` | `get_requisition` | Job requisition details for JD authoring |
| `JdFinalizedCard.jsx` | `jd_finalize` | Finalization summary with next steps |

## JobCard Component

```mermaid
graph TB
    JobCard["JobCard.jsx<br/>Job Listing Grid"]

    subgraph Data["Input Props"]
        Jobs["jobs: Array<br/>List of job matches"]
        TotalAvailable["totalAvailable: number"]
        HasMore["hasMore: boolean"]
    end

    subgraph PerJob["Per Job Card"]
        Title["title: string"]
        ID["id: string (e.g., 331525BR)"]
        Location["location: string"]
        OrgLine["orgLine: string"]
        MatchScore["matchScore: number"]
        MatchingSkills["matchingSkills: string[]"]
        DaysAgo["daysAgo: number"]
        IsNew["isNewToUser: boolean"]
    end

    subgraph Buttons["Action Buttons"]
        ViewBtn["View<br/>Primary button<br/>#6264A7"]
    end

    JobCard --> Data
    Data --> PerJob
    JobCard --> Buttons
```

## ProfileScore Component

```mermaid
graph TB
    ProfileScore["ProfileScore.jsx<br/>Profile Analysis Card"]

    subgraph Data["Input Props"]
        Score["completionScore: number<br/>0-100"]
        SectionScores["sectionScores: {<br/>  experience: number,<br/>  skills: number,<br/>  education: number,<br/>  ...<br/>}"]
        Missing["missingSections: string[]"]
    end

    subgraph Display["Display Elements"]
        ScoreGauge["Completion gauge<br/>Visual progress"]
        SectionBreakdown["Section breakdown<br/>Individual scores"]
        MissingSections["Missing sections<br/>Improvement suggestions"]
    end

    ProfileScore --> Data
    ProfileScore --> Display
```

## SkillsCard Component

```mermaid
graph TB
    SkillsCard["SkillsCard.jsx<br/>Interactive Skills Card"]

    subgraph Data["Input Props"]
        TopSkills["topSkills: string[]<br/>Top 3 inferred skills"]
        AddSkills["additionalSkills: string[]<br/>Additional inferred skills"]
        Evidence["evidence: Array<{<br/>  skill, source, detail<br/>}>"]
        Confidence["confidence: number (0-1)"]
        CurrentTop["currentTopSkills: string[]"]
        CurrentAdd["currentAdditionalSkills: string[]"]
    end

    subgraph Features["Features"]
        Select["Select/deselect skills"]
        AddCustom["Add custom skills via text field"]
        ViewEvidence["View evidence for each skill"]
        SaveToProfile["Save selected → update_profile"]
    end

    SkillsCard --> Data
    SkillsCard --> Features
```

## ProfileUpdateConfirmation Component

```mermaid
graph TB
    PUC["ProfileUpdateConfirmation.jsx<br/>HITL Approval Card"]

    subgraph Data["Input Props"]
        Section["section: string<br/>(skills, experience, rollback)"]
        UpdatedFields["updated_fields: object<br/>Proposed changes"]
        CurrentValues["current_values: object<br/>Current state"]
        PrevScore["previous_completion_score: number"]
        NewScore["estimated_new_score: number"]
        Payload["payload: string (JSON)<br/>For action callback"]
    end

    subgraph Display["Display"]
        BeforeAfter["Before/After diff<br/>Current → Proposed"]
        ScoreChange["Score change<br/>e.g., 65% → 78%"]
    end

    subgraph Actions["Action Buttons"]
        Approve["Approve<br/>Primary button #6264A7"]
        Reject["Reject<br/>Outline button"]
    end

    PUC --> Data
    PUC --> Display
    PUC --> Actions
```

## DraftMessage Component

```mermaid
graph TB
    DraftMessage["DraftMessage.jsx<br/>Message Draft Card"]

    subgraph Data["Input Props"]
        RecipientName["recipient_name: string"]
        SenderName["sender_name: string"]
        MessageBody["message_body: string"]
        JobTitle["job_title: string"]
        MessageType["message_type: string<br/>(teams)"]
    end

    subgraph Display["Display"]
        Header["Recipient + sender info"]
        Body["Message body preview"]
        Context["Job context"]
    end

    subgraph Buttons["Action Buttons"]
        SendBtn["Send<br/>Primary button<br/>#6264A7"]
    end

    DraftMessage --> Data
    DraftMessage --> Display
    DraftMessage --> Buttons
```

## CandidateCard Component

```mermaid
graph TB
    CandidateCard["CandidateCard.jsx<br/>Candidate Grid"]

    subgraph Data["Input Props"]
        Candidates["candidates: Array"]
        TotalAvailable["totalAvailable: number"]
        HasMore["hasMore: boolean"]
    end

    subgraph PerCandidate["Per Candidate"]
        Name["name: string"]
        Title["currentRole: string"]
        Skills["skills: string[]"]
        Location["location: string"]
    end

    subgraph Buttons["Action Buttons"]
        ViewProfileBtn["View Profile<br/>Primary button<br/>#6264A7"]
    end

    CandidateCard --> Data
    Data --> PerCandidate
    CandidateCard --> Buttons
```

## Teams Button Styling Guide

```mermaid
graph TB
    TeamsStyleGuide["Microsoft Teams Button Styles<br/>MUST apply to all cards"]

    subgraph Primary["Primary Button"]
        PrimaryCode["style={{<br/>  backgroundColor: '#6264A7',<br/>  color: '#fff'<br/>}}<br/>className='font-medium rounded'"]
        PrimaryUse["Use for:<br/>Main actions<br/>View, Send, Approve, Save"]
    end

    subgraph Outline["Outline Button"]
        OutlineCode["variant='outline'<br/>style={{<br/>  borderColor: '#6264A7',<br/>  color: '#6264A7'<br/>}}<br/>className='font-medium rounded'"]
        OutlineUse["Use for:<br/>Secondary actions<br/>Reject, Cancel"]
    end

    subgraph Ghost["Ghost Button"]
        GhostCode["variant='ghost'<br/>style={{<br/>  color: '#6264A7'<br/>}}<br/>className='rounded'"]
        GhostUse["Use for:<br/>Tertiary/minimal<br/>View details, More"]
    end

    subgraph Disabled["Disabled State"]
        DisabledCode["Disabled primary:<br/>backgroundColor: '#464775'<br/>color: '#fff'<br/>cursor: not-allowed"]
        DisabledUse["Use for:<br/>Saved state<br/>Already actioned<br/>Unavailable"]
    end

    TeamsStyleGuide --> Primary
    TeamsStyleGuide --> Outline
    TeamsStyleGuide --> Ghost
    TeamsStyleGuide --> Disabled

    Primary --> PrimaryCode
    Primary --> PrimaryUse

    Outline --> OutlineCode
    Outline --> OutlineUse

    Ghost --> GhostCode
    Ghost --> GhostUse

    Disabled --> DisabledCode
    Disabled --> DisabledUse
```

## Color Palette

```mermaid
graph TB
    Colors["Microsoft Teams Color Palette"]

    Primary["Primary Color<br/>#6264A7<br/>Buttons, links<br/>hover effects"]

    PrimaryDark["Primary Dark<br/>#464775<br/>Disabled state<br/>Active state"]

    White["White<br/>#ffffff<br/>Button text<br/>Backgrounds"]

    Light["Light Gray<br/>#f3f2f1<br/>Card backgrounds<br/>Borders"]

    Dark["Dark Gray<br/>#3c3c3c<br/>Body text<br/>Headers"]

    Colors --> Primary
    Colors --> PrimaryDark
    Colors --> White
    Colors --> Light
    Colors --> Dark
```

## Component Data Flow

```mermaid
sequenceDiagram
    participant Worker as Worker Agent
    participant Adapter as UI Adapter
    participant Component as React Component
    participant User as User
    participant App as app.py

    Worker-->>Adapter: JSON result via<br/>extract_tool_calls_from_messages()

    Adapter->>Adapter: render_tool_elements()<br/>Map tool name → component

    Adapter->>Component: Pass props<br/>(data from tool result)

    Component->>Component: Render with<br/>Teams styling

    Component-->>User: Display in chat

    User->>Component: Clicks button<br/>(e.g., Approve)

    Component->>App: action_callback<br/>(e.g., approve_profile_update)

    App->>Worker: Resume agent<br/>with decision
```

## Key Design Rules

1. **Teams Styling** — All buttons MUST follow Teams color scheme (#6264A7)
2. **Consistent Buttons** — Primary/Outline/Ghost pattern across all 10 cards
3. **Disabled State** — Use #464775 for disabled/saved state
4. **HITL Cards** — ProfileUpdateConfirmation uses Approve/Reject action callbacks
5. **Side Panels** — Profile editor, JD editor, and job details use SSE-driven panels (not card components)
6. **No Duplicate Data** — LLM prompt instructs agent NOT to repeat data shown in cards
7. **Action Handlers** — Button clicks trigger action callbacks → agent resume
8. **Pagination** — JobCard and CandidateCard support `hasMore` / `totalAvailable` for pagination
9. **Evidence Display** — SkillsCard shows citation evidence for each inferred skill
10. **Score Visualization** — ProfileScore and ProfileUpdateConfirmation show before/after completion scores
