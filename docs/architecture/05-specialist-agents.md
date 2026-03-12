# Specialist Agents Architecture

Detailed breakdown of each specialist agent and their tool sets.

## Specialist Agents Overview

```mermaid
graph TB
    subgraph Profile["ProfileAgent<br/>agents/profile/"]
        P1["profile_analyzer<br/>Profile scoring & analysis"]
        P2["infer_skills<br/>Auto-detect skills"]
        P3["update_profile<br/>CRUD on profile sections"]
        P4["list_profile_entries<br/>List section entries & IDs"]
        P5["open_profile_panel<br/>Open editor panel"]
        P6["rollback_profile<br/>Restore from backup"]
        PData["data/*_profile.json"]
    end

    subgraph JobD["JobDiscoveryAgent<br/>agents/job_discovery/"]
        J1["get_matches<br/>Search & filter job postings"]
        J2["view_job<br/>Display job details panel"]
        J3["ask_jd_qa<br/>Q&A on job descriptions"]
        JData["data/matching_jobs.json"]
    end

    subgraph Outreach["OutreachAgent<br/>agents/outreach/"]
        O1["draft_message<br/>Compose outreach message"]
        O2["send_message<br/>Send via Teams"]
        OData["data/*_profile.json"]
    end

    subgraph JDGen["JDGeneratorAgent<br/>agents/jd_generator/"]
        JG1["get_requisition<br/>Fetch requisition details"]
        JG2["jd_search<br/>Search role templates"]
        JG3["jd_compose<br/>Create job description"]
        JG4["section_editor<br/>Modify JD sections"]
        JG5["jd_finalize<br/>Complete & validate JD"]
        JG6["load_skill<br/>Fetch skill definitions"]
        JGData["data/job_requisitions.json<br/>data/skills_ontology.json<br/>agents/jd_generator/skills/"]
    end

    subgraph Candidate["CandidateSearchAgent<br/>agents/candidate_search/"]
        C1["search_candidates<br/>Find employees<br/>by skill/level/location"]
        C2["view_candidate<br/>Get candidate profile"]
        CData["data/employee_directory.json"]
    end

    P1 --> PData
    P2 --> PData
    P3 --> PData
    P4 --> PData
    P5 --> PData
    P6 --> PData

    J1 --> JData
    J2 --> JData
    J3 --> JData

    O1 --> OData
    O2 --> OData

    JG1 --> JGData
    JG2 --> JGData
    JG3 --> JGData
    JG4 --> JGData
    JG5 --> JGData
    JG6 --> JGData

    C1 --> CData
    C2 --> CData
```

## Agent Detail: ProfileAgent

```mermaid
graph TB
    ProfileAgent["ProfileAgent<br/>Profile Analysis & Management"]

    subgraph Tools6["6 Tools"]
        analyze["profile_analyzer<br/>Completion scoring & gap analysis"]
        infer["infer_skills<br/>Auto-detect from work history"]
        update["update_profile<br/>Add/edit/remove entries"]
        list_entries["list_profile_entries<br/>List entries with IDs"]
        open_panel["open_profile_panel<br/>Open editor side panel"]
        rollback["rollback_profile<br/>Restore from backup"]
    end

    subgraph Middleware["Middleware Stack"]
        MW1["SummarizationMiddleware"]
        MW2["first_touch_profile_middleware<br/>(auto-analyze on first touch)"]
        MW3["employee_personalization<br/>(inject user context)"]
        MW4["tool_monitor_middleware"]
        MW5["HumanInTheLoopMiddleware<br/>(intercepts update_profile,<br/>rollback_profile)"]
    end

    subgraph Process["Workflow"]
        load["Load profile JSON"]
        compute["Compute scores"]
        infer_proc["Infer missing skills"]
        persist["Persist changes via ProfileManager"]
        backup["Create backup before changes"]
    end

    ProfileAgent --> Tools6
    ProfileAgent --> Middleware
    Tools6 --> Process
```

## Agent Detail: JobDiscoveryAgent

```mermaid
graph TB
    JobAgent["JobDiscoveryAgent<br/>Job Search & Matching"]

    subgraph Tools3["3 Tools"]
        search["get_matches<br/>Search by keywords/filters<br/>with pagination"]
        details["view_job<br/>Open job details panel"]
        qa["ask_jd_qa<br/>Answer questions<br/>about job postings"]
    end

    subgraph Middleware["Middleware Stack"]
        MW1["SummarizationMiddleware"]
        MW2["employee_personalization<br/>(inject user context)"]
        MW3["profile_warning_middleware<br/>(warn if profile < 50%)"]
        MW4["tool_monitor_middleware"]
    end

    subgraph Process["Workflow"]
        parse["Parse search query & filters"]
        match["Match against job postings"]
        rank["Rank by match score (descending)"]
        paginate["Paginate results (default top_k=3)"]
    end

    JobAgent --> Tools3
    JobAgent --> Middleware
    Tools3 --> Process
```

## Agent Detail: OutreachAgent

```mermaid
graph TB
    OutAgent["OutreachAgent<br/>Communication & Outreach"]

    subgraph Tools2["2 Tools"]
        draft["draft_message<br/>Compose Teams message<br/>to hiring manager"]
        send["send_message<br/>Send via Teams"]
    end

    subgraph Middleware["Middleware Stack"]
        MW1["SummarizationMiddleware"]
        MW2["employee_personalization<br/>(inject user context)"]
        MW3["tool_monitor_middleware"]
    end

    subgraph Process["Workflow"]
        template["Draft from context"]
        personalize["Personalize for role"]
        validate["Validate before send"]
        confirm["Confirm with user before sending"]
    end

    OutAgent --> Tools2
    OutAgent --> Middleware
    Tools2 --> Process
```

## Agent Detail: JDGeneratorAgent

```mermaid
graph TB
    JDAgent["JDGeneratorAgent<br/>Job Description Authoring"]

    subgraph Tools6["6 Tools"]
        get_req["get_requisition<br/>Fetch requisition details"]
        search["jd_search<br/>Search role templates"]
        compose["jd_compose<br/>Create JD from scratch"]
        edit_sec["section_editor<br/>Modify specific section"]
        finalize["jd_finalize<br/>Complete & validate"]
        load_skill["load_skill<br/>Fetch skill definitions<br/>(dynamic from SkillRegistry)"]
    end

    subgraph SkillLoader["Skill Registry"]
        skill_reg["SkillRegistry<br/>Dynamic loading"]
        skill_files["jd_standards.md<br/>agents/jd_generator/skills/"]
    end

    subgraph Middleware["Middleware Stack"]
        MW1["SummarizationMiddleware"]
        MW2["hiring_manager_personalization<br/>(inject HM context)"]
        MW3["tool_monitor_middleware"]
    end

    subgraph Process["Workflow"]
        template["Start from requisition"]
        define_req["Define requirements"]
        add_skills["Add skill details"]
        finalize_step["Final review & validation"]
    end

    JDAgent --> Tools6
    JDAgent --> Middleware
    load_skill --> SkillLoader
    SkillLoader --> skill_reg
    SkillLoader --> skill_files
    Tools6 --> Process
```

## Agent Detail: CandidateSearchAgent

```mermaid
graph TB
    CandAgent["CandidateSearchAgent<br/>Employee Directory Search"]

    subgraph Tools2["2 Tools"]
        search_cand["search_candidates<br/>Find by skills/<br/>level/location"]
        view_cand["view_candidate<br/>Get candidate profile details"]
    end

    subgraph Middleware["Middleware Stack"]
        MW1["SummarizationMiddleware"]
        MW2["hiring_manager_personalization<br/>(inject HM context)"]
        MW3["tool_monitor_middleware"]
    end

    subgraph Process["Workflow"]
        parse_query["Parse search criteria"]
        query_dir["Query employee directory"]
        filter["Filter & rank results"]
        enrich["Enrich profiles"]
    end

    CandAgent --> Tools2
    CandAgent --> Middleware
    Tools2 --> Process
```

## Shared Tools (11 tools in agents/shared/tools/)

Used by Profile, Job Discovery, and Outreach agents:

| # | Tool | File | Used By |
|---|------|------|---------|
| 1 | `profile_analyzer` | `profile_analyzer.py` | Profile |
| 2 | `update_profile` | `update_profile.py` | Profile |
| 3 | `infer_skills` | `infer_skills.py` | Profile |
| 4 | `list_profile_entries` | `list_profile_entries.py` | Profile |
| 5 | `open_profile_panel` | `open_profile_panel.py` | Profile |
| 6 | `rollback_profile` | `rollback_profile.py` | Profile |
| 7 | `get_matches` | `get_matches.py` | Job Discovery |
| 8 | `view_job` | `view_job.py` | Job Discovery |
| 9 | `ask_jd_qa` | `ask_jd_qa.py` | Job Discovery |
| 10 | `draft_message` | `draft_message.py` | Outreach |
| 11 | `send_message` | `send_message.py` | Outreach |

## Tool Distribution Summary

| Agent | Tool Count | Tools |
|-------|-----------|-------|
| **Profile** | 6 | profile_analyzer, update_profile, infer_skills, list_profile_entries, open_profile_panel, rollback_profile |
| **Job Discovery** | 3 | get_matches, view_job, ask_jd_qa |
| **Outreach** | 2 | draft_message, send_message |
| **Candidate Search** | 2 | search_candidates, view_candidate |
| **JD Generator** | 6 | get_requisition, jd_search, jd_compose, section_editor, jd_finalize, load_skill |
| **Total** | **19** | |
