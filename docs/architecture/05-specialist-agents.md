# Specialist Agents Architecture

Detailed breakdown of each specialist agent and their tool sets.

## Specialist Agents Overview

```mermaid
graph TB
    subgraph Profile["ProfileAgent<br/>agents/profile/"]
        P1["analyze_profile<br/>Profile analysis & scoring"]
        P2["infer_skills<br/>Auto-detect skills"]
        P3["update_profile<br/>Modify profile data"]
        P4["list_skills<br/>View skills"]
        P5["export_profile<br/>Export to format"]
        P6["rollback_changes<br/>Undo updates"]
        PData["data/profiles.json"]
    end

    subgraph JobD["JobDiscoveryAgent<br/>agents/job_discovery/"]
        J1["search_jobs<br/>Query job postings"]
        J2["view_job_details<br/>Get full job info"]
        J3["ask_about_job<br/>Q&A on job"]
        JData["data/jobs.json"]
    end

    subgraph Outreach["OutreachAgent<br/>agents/outreach/"]
        O1["draft_message<br/>Compose outreach"]
        O2["send_message<br/>Send email/contact"]
        O3["apply_for_role<br/>Submit application"]
        OData["data/profiles.json"]
    end

    subgraph JDGen["JDGeneratorAgent<br/>agents/jd_generator/"]
        J4["search_roles<br/>Find role templates"]
        J5["compose_jd<br/>Create job desc"]
        J6["edit_section<br/>Modify JD section"]
        J7["finalize_jd<br/>Complete JD"]
        J8["load_skill<br/>Fetch skill info"]
        JGData["data/skills.json<br/>agents/jd_generator/skills/"]
    end

    subgraph Candidate["CandidateSearchAgent<br/>agents/candidate_search/"]
        C1["search_candidates<br/>Find employees<br/>by skill/level/loc"]
        C2["view_candidate<br/>Get candidate profile"]
        CData["data/employee_directory.json"]
    end

    subgraph Shared["MyCareer Shared Tools<br/>agents/mycareer/tools/"]
        S1["get_user_profile"]
        S2["search_opportunities"]
        S3["update_status"]
        S4["get_recommendations"]
        S5["get_industry_trends"]
        S6["analyze_skills_gap"]
        S7["get_career_path"]
        S8["get_job_market_insights"]
        S9["get_salary_benchmarks"]
        S10["track_applications"]
        S11["get_networking_suggestions"]
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
    O3 --> OData

    J4 --> JGData
    J5 --> JGData
    J6 --> JGData
    J7 --> JGData
    J8 --> JGData

    C1 --> CData
    C2 --> CData

    ProfileAgent -.->|uses| Shared
    JobD -.->|uses| Shared
    Outreach -.->|uses| Shared
```

## Agent Detail: ProfileAgent

```mermaid
graph TB
    ProfileAgent["ProfileAgent<br/>Profile Analysis & Management"]

    subgraph Tools6["6 Tools"]
        analyze["analyze_profile<br/>Profile scoring & analysis"]
        infer["infer_skills<br/>Auto-detect from history"]
        update["update_profile<br/>Modify data"]
        list_skills["list_skills<br/>View current skills"]
        export["export_profile<br/>Export data"]
        rollback["rollback_changes<br/>Revert updates"]
    end

    subgraph Process["Workflow"]
        load["Load profile JSON"]
        compute["Compute scores"]
        infer_proc["Infer missing skills"]
        persist["Persist changes"]
        history["Maintain history"]
    end

    ProfileAgent --> Tools6
    Tools6 --> analyze
    Tools6 --> infer
    Tools6 --> update
    Tools6 --> list_skills
    Tools6 --> export
    Tools6 --> rollback

    Tools6 --> Process
    Process --> load
    Process --> compute
    Process --> infer_proc
    Process --> persist
    Process --> history
```

## Agent Detail: JobDiscoveryAgent

```mermaid
graph TB
    JobAgent["JobDiscoveryAgent<br/>Job Search & Matching"]

    subgraph Tools3["3 Tools"]
        search["search_jobs<br/>Query by keywords/<br/>location/level"]
        details["view_job_details<br/>Full job information"]
        qa["ask_about_job<br/>Answer questions<br/>about posting"]
    end

    subgraph Process["Workflow"]
        parse["Parse search query"]
        match["Match against postings"]
        rank["Rank by relevance"]
        annotate["Add context/insights"]
    end

    JobAgent --> Tools3
    Tools3 --> search
    Tools3 --> details
    Tools3 --> qa
    Tools3 --> Process
```

## Agent Detail: OutreachAgent

```mermaid
graph TB
    OutAgent["OutreachAgent<br/>Communication & Outreach"]

    subgraph Tools3b["3 Tools"]
        draft["draft_message<br/>Compose email/<br/>message"]
        send["send_message<br/>Send via contact<br/>channel"]
        apply["apply_for_role<br/>Submit application<br/>to job posting"]
    end

    subgraph Process["Workflow"]
        template["Use message templates"]
        personalize["Personalize for role"]
        validate["Validate before send"]
        track["Track outreach"]
    end

    OutAgent --> Tools3b
    Tools3b --> draft
    Tools3b --> send
    Tools3b --> apply
    Tools3b --> Process
```

## Agent Detail: JDGeneratorAgent

```mermaid
graph TB
    JDAgent["JDGeneratorAgent<br/>Job Description Authoring"]

    subgraph Tools5["5 Tools + Skill Loader"]
        search_roles["search_roles<br/>Find role templates"]
        compose["compose_jd<br/>Create JD from scratch"]
        edit_sec["edit_section<br/>Modify specific section"]
        finalize["finalize_jd<br/>Complete & validate"]
        load_skill["load_skill<br/>Fetch skill definitions"]
    end

    subgraph SkillLoader["Skill Loader"]
        skill_reg["SkillRegistry<br/>Dynamic loading"]
        skill_files["Skill files in<br/>agents/jd_generator/skills/"]
    end

    subgraph Process["Workflow"]
        template["Start with template"]
        define_req["Define requirements"]
        add_skills["Add skill details"]
        finalize_step["Final review"]
    end

    JDAgent --> Tools5
    Tools5 --> search_roles
    Tools5 --> compose
    Tools5 --> edit_sec
    Tools5 --> finalize
    Tools5 --> load_skill

    load_skill --> SkillLoader
    SkillLoader --> skill_reg
    SkillLoader --> skill_files

    Tools5 --> Process
```

## Agent Detail: CandidateSearchAgent

```mermaid
graph TB
    CandAgent["CandidateSearchAgent<br/>Employee Directory Search"]

    subgraph Tools2["2 Tools"]
        search_cand["search_candidates<br/>Find by skills/<br/>level/location"]
        view_cand["view_candidate<br/>Get profile details"]
    end

    subgraph Process["Workflow"]
        parse_query["Parse search criteria"]
        query_dir["Query employee directory"]
        filter["Filter & rank results"]
        enrich["Enrich profiles"]
    end

    CandAgent --> Tools2
    Tools2 --> search_cand
    Tools2 --> view_cand
    Tools2 --> Process
```

## MyCareer Shared Tools (11 tools)

Used by Profile, Job Discovery, and Outreach agents:

1. `get_user_profile` — Fetch user profile
2. `search_opportunities` — Search jobs/roles
3. `update_status` — Update career status
4. `get_recommendations` — Career recommendations
5. `get_industry_trends` — Industry data
6. `analyze_skills_gap` — Skills gap analysis
7. `get_career_path` — Career progression paths
8. `get_job_market_insights` — Market intelligence
9. `get_salary_benchmarks` — Salary data
10. `track_applications` — Application tracking
11. `get_networking_suggestions` — Networking tips
