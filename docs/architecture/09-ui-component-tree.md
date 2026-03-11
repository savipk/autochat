# UI Component Architecture

React components in the frontend and their styling patterns.

## Component Hierarchy

```mermaid
graph TB
    subgraph Chainlit["Chainlit UI<br/>Web Interface"]
        ChatWindow["Chat Window"]
        MessageList["Message List"]
        InputBox["Message Input"]
    end

    subgraph MessageComponent["cl.Message<br/>(Chainlit)"]
        TextContent["Text content<br/>from agent"]
        CustomElement["Custom Element<br/>(React component)"]
    end

    subgraph ReactComponents["React Components<br/>(public/elements/)"]
        JobCard["JobCard.jsx"]
        ProfileScore["ProfileScore.jsx"]
        DraftMessage["DraftMessage.jsx"]
        CandidateCard["CandidateCard.jsx"]
        SkillsCard["SkillsCard.jsx"]
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

    JobCard --> Styling
    ProfileScore --> Styling
    DraftMessage --> Styling
    CandidateCard --> Styling
    SkillsCard --> Styling
```

## JobCard Component

```mermaid
graph TB
    JobCard["JobCard.jsx<br/>Job Listing Card"]

    subgraph Data["Input Props"]
        Title["title: string<br/>Job title"]
        Company["company: string<br/>Company name"]
        Location["location: string<br/>Job location"]
        Description["description: string<br/>Job description"]
        Skills["requiredSkills: string[]<br/>Required skills"]
        Salary["salary: string<br/>Compensation"]
        Link["link: string<br/>Application URL"]
    end

    subgraph Layout["Card Layout"]
        Header["Header section<br/>Title + Company"]
        Details["Details section<br/>Location + Salary"]
        SkillBadges["Skill badges<br/>Visual list"]
        DescText["Description<br/>Rich text"]
    end

    subgraph Buttons["Action Buttons"]
        ViewBtn["View Full Job<br/>Primary button<br/>#6264A7"]
        ApplyBtn["Apply Now<br/>Primary button<br/>#6264A7"]
        SaveBtn["Save for Later<br/>Outline button"]
        ShareBtn["Share<br/>Ghost button"]
    end

    subgraph Handlers["Event Handlers"]
        OnView["onClick view<br/>Open job detail"]
        OnApply["onClick apply<br/>Submit application"]
        OnSave["onClick save<br/>Save to profile"]
        OnShare["onClick share<br/>Copy link"]
    end

    JobCard --> Data
    Data --> Title
    Data --> Company
    Data --> Location
    Data --> Description
    Data --> Skills
    Data --> Salary
    Data --> Link

    JobCard --> Layout
    Layout --> Header
    Layout --> Details
    Layout --> SkillBadges
    Layout --> DescText

    JobCard --> Buttons
    Buttons --> ViewBtn
    Buttons --> ApplyBtn
    Buttons --> SaveBtn
    Buttons --> ShareBtn

    Buttons --> Handlers
    Handlers --> OnView
    Handlers --> OnApply
    Handlers --> OnSave
    Handlers --> OnShare
```

## ProfileScore Component

```mermaid
graph TB
    ProfileScore["ProfileScore.jsx<br/>Profile Analysis Card"]

    subgraph Data["Input Props"]
        Name["name: string<br/>User name"]
        Score["overallScore: number<br/>0-100"]
        Scores["categoryScores: {<br/>  technical: 85,<br/>  experience: 90,<br/>  education: 75<br/>}"]
        Skills["skills: string[]<br/>Detected skills"]
        Summary["summary: string<br/>Analysis summary"]
    end

    subgraph Display["Display Elements"]
        Avatar["Avatar<br/>User image"]
        ScoreBar["Score bar<br/>Visual progress"]
        CategoryBreakdown["Category breakdown<br/>Sub-scores"]
        SkillTags["Skill tags<br/>Colored badges"]
        Analysis["Analysis text<br/>Key findings"]
    end

    subgraph Buttons["Action Buttons"]
        EditBtn["Edit Profile<br/>Primary button<br/>#6264A7"]
        ExportBtn["Export Profile<br/>Outline button"]
        UpdateBtn["Update Skills<br/>Primary button"]
        ViewDetailBtn["View Details<br/>Ghost button"]
    end

    subgraph TeamsStyling["Teams Styling"]
        PrimaryStyle["Primary:<br/>backgroundColor: #6264A7<br/>color: #fff<br/>className: font-medium rounded"]
        OutlineStyle["Outline:<br/>variant: outline<br/>borderColor: #6264A7<br/>color: #6264A7"]
        GhostStyle["Ghost:<br/>variant: ghost<br/>color: #6264A7"]
    end

    ProfileScore --> Data
    ProfileScore --> Display
    ProfileScore --> Buttons
    Buttons --> TeamsStyling
```

## DraftMessage Component

```mermaid
graph TB
    DraftMessage["DraftMessage.jsx<br/>Message Draft Card"]

    subgraph Data["Input Props"]
        Template["template: string<br/>Message template"]
        To["to: string<br/>Recipient email"]
        Subject["subject: string<br/>Email subject"]
        Body["body: string<br/>Message content"]
        Personalization["personalization: object<br/>Template variables"]
    end

    subgraph Preview["Preview Section"]
        Header["Subject line<br/>Recipient info"]
        Content["Message preview<br/>Full draft text"]
        Highlight["Highlighted<br/>personalized parts"]
    end

    subgraph EditTools["Edit Tools"]
        TextEditor["Text editor<br/>Rich editing"]
        Replace["Replace variable<br/>Re-personalize"]
        Template["Use template<br/>Change template"]
    end

    subgraph Buttons["Action Buttons"]
        SendBtn["Send Now<br/>Primary button<br/>#6264A7"]
        ScheduleBtn["Schedule Send<br/>Primary button"]
        SaveDraftBtn["Save Draft<br/>Outline button"]
        PreviewBtn["Preview Email<br/>Ghost button"]
        CancelBtn["Cancel<br/>Outline button"]
    end

    DraftMessage --> Data
    Data --> Template
    Data --> To
    Data --> Subject
    Data --> Body
    Data --> Personalization

    DraftMessage --> Preview
    DraftMessage --> EditTools
    DraftMessage --> Buttons
```

## CandidateCard Component

```mermaid
graph TB
    CandidateCard["CandidateCard.jsx<br/>Candidate Profile Card"]

    subgraph Data["Input Props"]
        Name["name: string<br/>Candidate name"]
        Title["currentRole: string<br/>Job title"]
        Experience["experience: number<br/>Years of experience"]
        Skills["skills: string[]<br/>Skill list"]
        Location["location: string<br/>Location"]
        SkillMatch["skillMatch: number<br/>% match to role"]
    end

    subgraph Layout["Card Layout"]
        Header["Header<br/>Name + Title"]
        Meta["Metadata<br/>Experience + Location"]
        SkillBadges["Skill badges<br/>Match highlighting"]
        Bio["Bio/Summary<br/>Brief background"]
    end

    subgraph Indicators["Match Indicators"]
        MatchScore["Match score<br/>Visual indicator"]
        GapAnalysis["Skill gaps<br/>Missing skills"]
        Strengths["Strengths<br/>Top matches"]
    end

    subgraph Buttons["Action Buttons"]
        ViewProfileBtn["View Profile<br/>Primary button<br/>#6264A7"]
        ContactBtn["Send Message<br/>Primary button"]
        ScheduleBtn["Schedule Call<br/>Outline button"]
        MoreBtn["More options<br/>Ghost button"]
    end

    CandidateCard --> Data
    Data --> Name
    Data --> Title
    Data --> Experience
    Data --> Skills
    Data --> Location
    Data --> SkillMatch

    CandidateCard --> Layout
    CandidateCard --> Indicators
    CandidateCard --> Buttons
```

## SkillsCard Component

```mermaid
graph TB
    SkillsCard["SkillsCard.jsx<br/>Skills Display Card"]

    subgraph Data["Input Props"]
        Skills["skills: {<br/>  name: string,<br/>  level: string,<br/>  endorsements: number<br/>}[]"]
        Categories["categories: string[]<br/>Skill categories"]
    end

    subgraph Display["Skill Display"]
        SkillTag["Skill tag<br/>Name + Level"]
        LevelIndicator["Level indicator<br/>Beginner/Intermediate/Expert"]
        Endorsements["Endorsement count<br/>Social proof"]
        Category["Category group<br/>Organize by type"]
    end

    subgraph Buttons["Action Buttons"]
        AddSkillBtn["Add Skill<br/>Primary button<br/>#6264A7"]
        EditBtn["Edit Skills<br/>Primary button"]
        ValidateBtn["Get Endorsed<br/>Outline button"]
        SortBtn["Sort/Filter<br/>Ghost button"]
    end

    SkillsCard --> Data
    SkillsCard --> Display
    SkillsCard --> Buttons
```

## Teams Button Styling Guide

```mermaid
graph TB
    TeamsStyleGuide["Microsoft Teams Button Styles<br/>MUST apply to all cards"]

    subgraph Primary["Primary Button"]
        PrimaryCode["style={{<br/>  backgroundColor: '#6264A7',<br/>  color: '#fff'<br/>}}<br/>className='font-medium rounded'"]
        PrimaryUse["Use for:<br/>Main actions<br/>Apply, Send, Save"]
    end

    subgraph Outline["Outline Button"]
        OutlineCode["variant='outline'<br/>style={{<br/>  borderColor: '#6264A7',<br/>  color: '#6264A7'<br/>}}<br/>className='font-medium rounded'"]
        OutlineUse["Use for:<br/>Secondary actions<br/>Save for later<br/>Cancel"]
    end

    subgraph Ghost["Ghost Button"]
        GhostCode["variant='ghost'<br/>style={{<br/>  color: '#6264A7'<br/>}}<br/>className='rounded'"]
        GhostUse["Use for:<br/>Tertiary/minimal<br/>View details<br/>More options"]
    end

    subgraph Disabled["Disabled State"]
        DisabledCode["Disabled primary:<br/>backgroundColor: '#464775'<br/>color: '#fff'<br/>cursor: not-allowed"]
        DisabledUse["Use for:<br/>Saved state<br/>Already applied<br/>Unavailable action"]
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
    participant Adapter as Chainlit Adapter
    participant Component as React Component
    participant Handler as Event Handler
    participant Agent as Agent

    Adapter->>Adapter: Convert agent result<br/>to component props

    Adapter->>Component: Pass props<br/>(data + config)

    Component->>Component: Render with<br/>Teams styling

    Component-->>Adapter: Component instance

    Adapter->>Adapter: Wrap in<br/>cl.Element

    Component->>Handler: User clicks button

    Handler->>Agent: Trigger action<br/>(apply, send, etc.)

    Agent-->>Component: Update state<br/>or callback

    Component->>Component: Re-render<br/>Updated state
```

## Key Design Rules

1. **Teams Styling** — All buttons MUST follow Teams color scheme (#6264A7)
2. **Consistent Buttons** — Primary/Outline/Ghost pattern across all cards
3. **Disabled State** — Use #464775 for disabled/saved state
4. **Responsive Layout** — Cards adapt to mobile/tablet/desktop
5. **Rich Text** — Support markdown and formatted text in descriptions
6. **Action Handlers** — Button clicks trigger agent tools or callbacks
7. **Error States** — Show validation errors inline or as toast notifications
8. **Loading States** — Spinner/skeleton while data loads
9. **Empty States** — Show meaningful message when no data
10. **Accessibility** — ARIA labels, keyboard navigation, color contrast
