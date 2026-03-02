/**
 * Profile Editor Side Panel
 *
 * Panel is hidden by default and slides in from the right when the server
 * pushes an SSE "open_panel" event (triggered by profile-related messages).
 * Appended to document.body as position:fixed — no React DOM nodes are moved.
 */
(function () {
  "use strict";

  // ---------------------------------------------------------------------------
  // Config & state
  // ---------------------------------------------------------------------------
  const PANEL_WIDTH = 400;
  const POLL_INTERVAL_MS = 5000;

  let _username = "";
  let _profilePath = "";
  let _originalProfile = null;
  let _currentProfile = null;
  let _drafts = [];
  let _draftIndex = -1;
  let _panelEl = null;
  let _pollTimer = null;
  let _panelOpen = false;
  let _eventSource = null;

  // ---------------------------------------------------------------------------
  // Bootstrap — polls /user until authenticated, then initialises panel + SSE.
  // This handles the case where custom.js loads on the login page before the
  // user has logged in.  After login Chainlit does a client-side navigation so
  // the IIFE doesn't re-run; the interval below keeps checking.
  // ---------------------------------------------------------------------------
  var _bootstrapped = false;

  function tryBootstrap() {
    if (_bootstrapped) return;

    fetch("/user", { credentials: "include" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data) return;
        _username = data.identifier || data.username || "";
        _profilePath = (data.metadata || {}).profile_path || "";
        if (!_username || !_profilePath) return;

        _bootstrapped = true;
        clearInterval(_bootstrapTimer);
        createPanel();
        connectSSE();
        startPolling();
      })
      .catch(function () {});
  }

  // Try immediately, then every 2 seconds until logged in
  var _bootstrapTimer = setInterval(tryBootstrap, 2000);
  tryBootstrap();

  // ---------------------------------------------------------------------------
  // Panel creation — appended to body, position:fixed, off-screen by default
  // ---------------------------------------------------------------------------
  function createPanel() {
    _panelEl = document.createElement("div");
    _panelEl.className = "autochat-profile-panel";
    _panelEl.innerHTML = '<div class="profile-panel-loading">Loading profile...</div>';
    document.body.appendChild(_panelEl);
  }

  // ---------------------------------------------------------------------------
  // Panel open / close
  // ---------------------------------------------------------------------------
  function openPanel() {
    if (_panelOpen) return;
    _panelOpen = true;
    _panelEl.classList.add("open");
    document.getElementById("root").classList.add("autochat-panel-open");
    // Load profile data on first open
    if (!_currentProfile) {
      loadProfile();
    }
  }

  function closePanel() {
    if (!_panelOpen) return;
    _panelOpen = false;
    _panelEl.classList.remove("open");
    document.getElementById("root").classList.remove("autochat-panel-open");
  }

  // ---------------------------------------------------------------------------
  // SSE connection — uses native EventSource with username as query param
  // ---------------------------------------------------------------------------
  function connectSSE() {
    if (!_username) return;
    if (_eventSource) _eventSource.close();

    var url = "/api/profile/events?username=" + encodeURIComponent(_username);
    _eventSource = new EventSource(url);

    _eventSource.onmessage = function (e) {
      try {
        var event = JSON.parse(e.data);
        handleSSEEvent(event);
      } catch (err) { /* ignore */ }
    };

    _eventSource.onerror = function () {
      // EventSource auto-reconnects
    };
  }

  function handleSSEEvent(event) {
    if (event.type === "open_panel") {
      closeJdPanel();
      try { openPanel(); } catch (e) { /* ensure loadProfile still runs */ }
      loadProfile();
    } else if (event.type === "refresh") {
      loadProfile();
    } else if (event.type === "open_jd_panel") {
      closePanel();
      openJdPanel(event.job_id);
    }
  }

  // ---------------------------------------------------------------------------
  // API helpers
  // ---------------------------------------------------------------------------
  function apiHeaders() {
    return {
      "Content-Type": "application/json",
      "X-Username": _username,
      "X-Profile-Path": _profilePath,
    };
  }

  function normalizeProfile(profile) {
    if (!profile) return;
    var core = profile.core = profile.core || {};
    var sections = [
      "experience", "qualification", "skills",
      "careerAspirationPreference", "careerLocationPreference",
      "careerRolePreference", "language",
    ];
    sections.forEach(function (s) {
      if (!core[s] && profile[s]) core[s] = profile[s];
    });
    if (typeof core.completionScore !== "number" && typeof profile.completionScore === "number") {
      core.completionScore = profile.completionScore;
    }
  }

  function loadProfile() {
    fetch("/api/profile/current", { headers: apiHeaders(), credentials: "include" })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        normalizeProfile(data);
        _originalProfile = JSON.parse(JSON.stringify(data));
        _currentProfile = JSON.parse(JSON.stringify(data));
        _draftIndex = -1;
        refreshDraftList(function () { renderPanel(); });
      })
      .catch(function () {
        if (_panelEl) _panelEl.innerHTML = '<div class="profile-panel-loading">Failed to load profile.</div>';
      });
  }

  function refreshDraftList(cb) {
    fetch("/api/profile/drafts", { headers: apiHeaders(), credentials: "include" })
      .then(function (r) { return r.json(); })
      .then(function (list) { _drafts = list || []; if (cb) cb(); })
      .catch(function () { _drafts = []; if (cb) cb(); });
  }

  function saveDraft() {
    fetch("/api/profile/drafts", {
      method: "POST",
      headers: apiHeaders(),
      credentials: "include",
      body: JSON.stringify({ profile_data: _currentProfile, label: "" }),
    })
      .then(function (r) { return r.json(); })
      .then(function () {
        refreshDraftList(function () {
          _draftIndex = _drafts.length - 1;
          _originalProfile = JSON.parse(JSON.stringify(_currentProfile));
          renderPanel();
          showToast("Draft saved");
        });
      });
  }

  function submitProfile() {
    fetch("/api/profile/submit", {
      method: "POST",
      headers: apiHeaders(),
      credentials: "include",
      body: JSON.stringify({ profile_data: _currentProfile }),
    })
      .then(function (r) { return r.json(); })
      .then(function () {
        showToast("Profile submitted!");
        loadProfile();
      });
  }

  function loadDraftById(draftId) {
    fetch("/api/profile/drafts/" + encodeURIComponent(draftId), {
      headers: apiHeaders(),
      credentials: "include",
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        _currentProfile = JSON.parse(JSON.stringify(data));
        _originalProfile = JSON.parse(JSON.stringify(data));
        renderPanel();
      });
  }

  // ---------------------------------------------------------------------------
  // Polling for agent-initiated updates
  // ---------------------------------------------------------------------------
  function startPolling() {
    _pollTimer = setInterval(function () {
      fetch("/api/profile/poll-update", { headers: apiHeaders(), credentials: "include" })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data && data.updated) loadProfile();
        })
        .catch(function () {});
    }, POLL_INTERVAL_MS);
  }

  // ---------------------------------------------------------------------------
  // Render the full panel
  // ---------------------------------------------------------------------------
  function renderPanel() {
    if (!_panelEl || !_currentProfile) return;

    var core = _currentProfile.core || {};
    var nameInfo = core.name || {};
    var fullName = ((nameInfo.businessFirstName || "") + " " + (nameInfo.businessLastName || "")).trim();
    var title = core.businessTitle || "";
    var rank = (core.rank || {}).description || "";
    var score = core.completionScore;

    var html = '';

    // Header with close button
    html += '<div class="profile-panel-header">';
    html += '  <div style="display:flex;justify-content:space-between;align-items:center">';
    html += '    <h2>Profile Editor</h2>';
    html += '    <button class="profile-panel-close" data-action="close-panel" title="Close">&times;</button>';
    html += '  </div>';
    if (typeof score === "number") {
      html += '  <div class="profile-score-badge">' + score + '% complete</div>';
    }
    html += '</div>';

    // Read-only name/title
    html += '<div class="profile-readonly-info">';
    html += '  <div class="info-name">' + esc(fullName || "\u2014") + '</div>';
    if (title) html += '  <div class="info-detail">' + esc(title) + '</div>';
    if (rank) html += '  <div class="info-detail">' + esc(rank) + '</div>';
    html += '</div>';

    // Scrollable body
    html += '<div class="profile-panel-body">';
    html += renderExperienceSection(core.experience);
    html += renderEducationSection(core.qualification);
    html += renderSkillsSection(core);
    html += renderAspirationsSection(core.careerAspirationPreference);
    html += renderLocationSection(core.careerLocationPreference);
    html += renderRolesSection(core.careerRolePreference);
    html += renderLanguagesSection(core.language);
    html += '</div>';

    // Footer
    html += renderFooter();

    _panelEl.innerHTML = html;
    attachEvents();
  }

  // ---------------------------------------------------------------------------
  // Section renderers
  // ---------------------------------------------------------------------------

  function renderExperienceSection(exp) {
    var experiences = (exp || {}).experiences || [];
    var h = '<div class="profile-section">';
    h += '<div class="profile-section-title">Experience</div>';
    experiences.forEach(function (e, i) {
      h += '<div class="profile-group-item">';
      h += '<div class="group-item-header">';
      h += '<span class="group-item-title">' + esc(e.jobTitle || "Untitled") + '</span>';
      h += '<button class="profile-group-remove" data-action="remove-experience" data-index="' + i + '" title="Remove">&times;</button>';
      h += '</div>';
      h += fieldInput("Job Title", "exp-title-" + i, e.jobTitle || "");
      h += fieldInput("Company", "exp-company-" + i, e.company || "");
      h += fieldInput("Start Date", "exp-start-" + i, e.startDate || "");
      h += fieldTextarea("Description", "exp-desc-" + i, e.description || "");
      h += '</div>';
    });
    h += '<button class="btn-save-draft" style="width:auto;padding:4px 12px;margin-top:4px" data-action="add-experience">+ Add Experience</button>';
    h += '</div>';
    return h;
  }

  function renderEducationSection(qual) {
    var educations = (qual || {}).educations || [];
    var h = '<div class="profile-section">';
    h += '<div class="profile-section-title">Education</div>';
    educations.forEach(function (e, i) {
      h += '<div class="profile-group-item">';
      h += '<div class="group-item-header">';
      h += '<span class="group-item-title">' + esc(e.institutionName || "Untitled") + '</span>';
      h += '<button class="profile-group-remove" data-action="remove-education" data-index="' + i + '" title="Remove">&times;</button>';
      h += '</div>';
      h += fieldInput("Institution", "edu-inst-" + i, e.institutionName || "");
      h += fieldInput("Degree", "edu-degree-" + i, e.degree || "");
      h += fieldInput("Area of Study", "edu-area-" + i, e.areaOfStudy || "");
      h += fieldInput("Year", "edu-year-" + i, e.completionYear || "");
      h += '</div>';
    });
    h += '<button class="btn-save-draft" style="width:auto;padding:4px 12px;margin-top:4px" data-action="add-education">+ Add Education</button>';
    h += '</div>';
    return h;
  }

  function renderSkillsSection(core) {
    var skills = core.skills || {};
    var top = skills.top || [];
    var additional = skills.additional || [];

    var h = '<div class="profile-section">';
    h += '<div class="profile-section-title">Skills</div>';

    h += '<label style="font-size:12px;font-weight:500;color:#374151;margin-bottom:4px;display:block">Top Skills</label>';
    h += '<div class="profile-tags" id="tags-top-skills">';
    top.forEach(function (s, i) {
      h += '<span class="profile-tag">' + esc(s) + '<span class="tag-remove" data-action="remove-top-skill" data-index="' + i + '">&times;</span></span>';
    });
    h += '</div>';
    h += '<div class="profile-add-row"><input id="add-top-skill-input" placeholder="Add skill..." /><button data-action="add-top-skill">Add</button></div>';

    h += '<label style="font-size:12px;font-weight:500;color:#374151;margin:10px 0 4px;display:block">Additional Skills</label>';
    h += '<div class="profile-tags" id="tags-additional-skills">';
    additional.forEach(function (s, i) {
      h += '<span class="profile-tag">' + esc(s) + '<span class="tag-remove" data-action="remove-additional-skill" data-index="' + i + '">&times;</span></span>';
    });
    h += '</div>';
    h += '<div class="profile-add-row"><input id="add-additional-skill-input" placeholder="Add skill..." /><button data-action="add-additional-skill">Add</button></div>';

    h += '<p class="profile-hint">You can ask the chat agent to infer skills from your profile</p>';
    h += '</div>';
    return h;
  }

  function renderAspirationsSection(pref) {
    var aspirations = (pref || {}).preferredAspirations || [];
    var h = '<div class="profile-section">';
    h += '<div class="profile-section-title">Career Aspirations</div>';
    h += '<div class="profile-tags" id="tags-aspirations">';
    aspirations.forEach(function (a, i) {
      h += '<span class="profile-tag">' + esc(a.description || "") + '<span class="tag-remove" data-action="remove-aspiration" data-index="' + i + '">&times;</span></span>';
    });
    h += '</div>';
    h += '<div class="profile-add-row"><input id="add-aspiration-input" placeholder="Add aspiration..." /><button data-action="add-aspiration">Add</button></div>';
    h += '</div>';
    return h;
  }

  function renderLocationSection(locPref) {
    if (!locPref) locPref = {};
    var timeline = (locPref.preferredRelocationTimeline || {}).description || "";
    var regions = locPref.preferredRelocationRegions || [];

    var h = '<div class="profile-section">';
    h += '<div class="profile-section-title">Location Preferences</div>';
    h += fieldInput("Relocation Timeline", "loc-timeline", timeline);
    h += '<label style="font-size:12px;font-weight:500;color:#374151;margin-bottom:4px;display:block">Preferred Regions</label>';
    h += '<div class="profile-tags" id="tags-regions">';
    regions.forEach(function (r, i) {
      h += '<span class="profile-tag">' + esc(r.description || "") + '<span class="tag-remove" data-action="remove-region" data-index="' + i + '">&times;</span></span>';
    });
    h += '</div>';
    h += '<div class="profile-add-row"><input id="add-region-input" placeholder="Add region..." /><button data-action="add-region">Add</button></div>';
    h += '</div>';
    return h;
  }

  function renderRolesSection(rolePref) {
    var roles = ((rolePref || {}).preferredRoles) || [];
    var h = '<div class="profile-section">';
    h += '<div class="profile-section-title">Role Preferences</div>';
    roles.forEach(function (r) {
      var rc = r.roleClassification || {};
      h += '<div class="profile-group-item">';
      h += '<div class="group-item-title">' + esc(rc.description || "\u2014") + '</div>';
      (rc.children || []).forEach(function (c) {
        h += '<div style="font-size:12px;color:#6b7280;margin-top:2px">' + esc(c.description || "") + '</div>';
      });
      h += '</div>';
    });
    h += '</div>';
    return h;
  }

  function renderLanguagesSection(lang) {
    var languages = (lang || {}).languages || [];
    var proficiencyOptions = ["Native", "Fluent", "Intermediate", "Basic"];

    var h = '<div class="profile-section">';
    h += '<div class="profile-section-title">Languages</div>';
    languages.forEach(function (l, i) {
      var langName = (l.language || {}).description || "";
      var profDesc = (l.proficiency || {}).description || "";
      h += '<div class="profile-group-item" style="display:flex;gap:8px;align-items:center">';
      h += '<div style="flex:1">' + fieldInput("Language", "lang-name-" + i, langName) + '</div>';
      h += '<div style="flex:1"><div class="profile-field"><label>Proficiency</label><select id="lang-prof-' + i + '">';
      proficiencyOptions.forEach(function (opt) {
        h += '<option value="' + opt.toUpperCase() + '"' + (profDesc === opt ? ' selected' : '') + '>' + opt + '</option>';
      });
      h += '</select></div></div>';
      h += '<button class="profile-group-remove" data-action="remove-language" data-index="' + i + '" title="Remove">&times;</button>';
      h += '</div>';
    });
    h += '<button class="btn-save-draft" style="width:auto;padding:4px 12px;margin-top:4px" data-action="add-language">+ Add Language</button>';
    h += '</div>';
    return h;
  }

  // ---------------------------------------------------------------------------
  // Footer
  // ---------------------------------------------------------------------------
  function renderFooter() {
    var h = '<div class="profile-panel-footer">';

    if (_drafts.length > 0) {
      var draftLabel = "";
      if (_draftIndex >= 0 && _draftIndex < _drafts.length) {
        var d = _drafts[_draftIndex];
        var ts = d.timestamp || "";
        draftLabel = "Draft " + (_draftIndex + 1) + " of " + _drafts.length;
        if (ts) draftLabel += " (" + formatTimestamp(ts) + ")";
      } else {
        draftLabel = "Live profile";
      }
      h += '<div class="draft-nav">';
      h += '<button data-action="draft-prev"' + (_draftIndex <= 0 ? ' disabled' : '') + '>&laquo;</button>';
      h += '<span>' + draftLabel + '</span>';
      h += '<button data-action="draft-next"' + (_draftIndex >= _drafts.length - 1 ? ' disabled' : '') + '>&raquo;</button>';
      h += '</div>';
    }

    h += '<div class="profile-panel-actions">';
    h += '<button class="btn-save-draft" data-action="save-draft">Save Draft</button>';
    h += '<button class="btn-submit" data-action="submit-profile">Submit</button>';
    h += '</div>';
    h += '</div>';
    return h;
  }

  // ---------------------------------------------------------------------------
  // Event attachment
  // ---------------------------------------------------------------------------
  function attachEvents() {
    if (!_panelEl) return;

    _panelEl.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-action]");
      if (!btn) return;
      var action = btn.getAttribute("data-action");
      var idx = parseInt(btn.getAttribute("data-index"), 10);

      switch (action) {
        case "close-panel": closePanel(); break;
        case "save-draft": saveDraft(); break;
        case "submit-profile":
          collectFormData();
          submitProfile();
          break;
        case "draft-prev":
          if (_draftIndex > 0) { _draftIndex--; loadDraftById(_drafts[_draftIndex].id); }
          break;
        case "draft-next":
          if (_draftIndex < _drafts.length - 1) { _draftIndex++; loadDraftById(_drafts[_draftIndex].id); }
          break;

        // Skills
        case "remove-top-skill":
          collectFormData();
          (_currentProfile.core.skills.top || []).splice(idx, 1);
          renderPanel();
          break;
        case "add-top-skill":
          collectFormData();
          var v1 = (document.getElementById("add-top-skill-input") || {}).value || "";
          if (v1.trim()) {
            _currentProfile.core = _currentProfile.core || {};
            _currentProfile.core.skills = _currentProfile.core.skills || {};
            _currentProfile.core.skills.top = _currentProfile.core.skills.top || [];
            _currentProfile.core.skills.top.push(v1.trim());
            renderPanel();
          }
          break;
        case "remove-additional-skill":
          collectFormData();
          (_currentProfile.core.skills.additional || []).splice(idx, 1);
          renderPanel();
          break;
        case "add-additional-skill":
          var v2 = (document.getElementById("add-additional-skill-input") || {}).value || "";
          if (v2.trim()) {
            collectFormData();
            _currentProfile.core = _currentProfile.core || {};
            _currentProfile.core.skills = _currentProfile.core.skills || {};
            _currentProfile.core.skills.additional = _currentProfile.core.skills.additional || [];
            _currentProfile.core.skills.additional.push(v2.trim());
            renderPanel();
          }
          break;

        // Aspirations
        case "remove-aspiration":
          collectFormData();
          var asp = ((_currentProfile.core || {}).careerAspirationPreference || {}).preferredAspirations || [];
          asp.splice(idx, 1);
          renderPanel();
          break;
        case "add-aspiration":
          var v3 = (document.getElementById("add-aspiration-input") || {}).value || "";
          if (v3.trim()) {
            collectFormData();
            _currentProfile.core = _currentProfile.core || {};
            _currentProfile.core.careerAspirationPreference = _currentProfile.core.careerAspirationPreference || {};
            _currentProfile.core.careerAspirationPreference.preferredAspirations = _currentProfile.core.careerAspirationPreference.preferredAspirations || [];
            _currentProfile.core.careerAspirationPreference.preferredAspirations.push({
              type: "SimpleReferenceDataDto", code: "", description: v3.trim(),
            });
            renderPanel();
          }
          break;

        // Regions
        case "remove-region":
          collectFormData();
          var regs = ((_currentProfile.core || {}).careerLocationPreference || {}).preferredRelocationRegions || [];
          regs.splice(idx, 1);
          renderPanel();
          break;
        case "add-region":
          var v4 = (document.getElementById("add-region-input") || {}).value || "";
          if (v4.trim()) {
            collectFormData();
            _currentProfile.core = _currentProfile.core || {};
            _currentProfile.core.careerLocationPreference = _currentProfile.core.careerLocationPreference || {};
            _currentProfile.core.careerLocationPreference.preferredRelocationRegions = _currentProfile.core.careerLocationPreference.preferredRelocationRegions || [];
            _currentProfile.core.careerLocationPreference.preferredRelocationRegions.push({
              type: "SimpleReferenceDataDto", code: "", description: v4.trim(),
            });
            renderPanel();
          }
          break;

        // Experience
        case "remove-experience":
          collectFormData();
          ((_currentProfile.core || {}).experience || {}).experiences.splice(idx, 1);
          renderPanel();
          break;
        case "add-experience":
          collectFormData();
          _currentProfile.core = _currentProfile.core || {};
          _currentProfile.core.experience = _currentProfile.core.experience || {};
          _currentProfile.core.experience.experiences = _currentProfile.core.experience.experiences || [];
          _currentProfile.core.experience.experiences.push({
            id: crypto.randomUUID(), jobTitle: "", company: "", startDate: "", description: "",
          });
          renderPanel();
          break;

        // Education
        case "remove-education":
          collectFormData();
          ((_currentProfile.core || {}).qualification || {}).educations.splice(idx, 1);
          renderPanel();
          break;
        case "add-education":
          collectFormData();
          _currentProfile.core = _currentProfile.core || {};
          _currentProfile.core.qualification = _currentProfile.core.qualification || {};
          _currentProfile.core.qualification.educations = _currentProfile.core.qualification.educations || [];
          _currentProfile.core.qualification.educations.push({
            id: crypto.randomUUID(), institutionName: "", degree: "", areaOfStudy: "", completionYear: 0,
          });
          renderPanel();
          break;

        // Languages
        case "remove-language":
          collectFormData();
          ((_currentProfile.core || {}).language || {}).languages.splice(idx, 1);
          renderPanel();
          break;
        case "add-language":
          collectFormData();
          _currentProfile.core = _currentProfile.core || {};
          _currentProfile.core.language = _currentProfile.core.language || {};
          _currentProfile.core.language.languages = _currentProfile.core.language.languages || [];
          _currentProfile.core.language.languages.push({
            id: crypto.randomUUID(),
            language: { type: "SimpleReferenceDataDto", code: "", description: "" },
            proficiency: { type: "SimpleReferenceDataDto", code: "BASIC", description: "Basic" },
          });
          renderPanel();
          break;
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Collect form data back into _currentProfile
  // ---------------------------------------------------------------------------
  function collectFormData() {
    if (!_currentProfile || !_panelEl) return;
    var core = _currentProfile.core || {};

    // Experience
    var exps = ((core.experience || {}).experiences) || [];
    exps.forEach(function (e, i) {
      e.jobTitle = val("exp-title-" + i) || e.jobTitle;
      e.company = val("exp-company-" + i) || e.company;
      e.startDate = val("exp-start-" + i) || e.startDate;
      e.description = val("exp-desc-" + i) || e.description;
    });

    // Education
    var edus = ((core.qualification || {}).educations) || [];
    edus.forEach(function (e, i) {
      e.institutionName = val("edu-inst-" + i) || e.institutionName;
      e.degree = val("edu-degree-" + i) || e.degree;
      e.areaOfStudy = val("edu-area-" + i) || e.areaOfStudy;
      var yr = val("edu-year-" + i);
      if (yr !== null) e.completionYear = parseInt(yr, 10) || 0;
    });

    // Languages
    var langs = ((core.language || {}).languages) || [];
    langs.forEach(function (l, i) {
      var n = val("lang-name-" + i);
      if (n !== null && l.language) l.language.description = n;
      var p = val("lang-prof-" + i);
      if (p !== null && l.proficiency) {
        l.proficiency.code = p;
        l.proficiency.description = p.charAt(0) + p.slice(1).toLowerCase();
      }
    });

    // Location timeline
    var tl = val("loc-timeline");
    if (tl !== null) {
      core.careerLocationPreference = core.careerLocationPreference || {};
      core.careerLocationPreference.preferredRelocationTimeline = core.careerLocationPreference.preferredRelocationTimeline || {};
      core.careerLocationPreference.preferredRelocationTimeline.description = tl;
    }
  }

  // ---------------------------------------------------------------------------
  // Utilities
  // ---------------------------------------------------------------------------
  function val(id) {
    var el = document.getElementById(id);
    return el ? el.value : null;
  }

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function fieldInput(label, id, value) {
    return '<div class="profile-field"><label>' + esc(label) + '</label><input id="' + id + '" value="' + esc(value) + '" /></div>';
  }

  function fieldTextarea(label, id, value) {
    return '<div class="profile-field"><label>' + esc(label) + '</label><textarea id="' + id + '">' + esc(value) + '</textarea></div>';
  }

  function formatTimestamp(ts) {
    if (!ts || ts.length < 13) return ts;
    var m = ts.substring(4, 6);
    var d = ts.substring(6, 8);
    var h = ts.substring(9, 11);
    var min = ts.substring(11, 13);
    return m + "/" + d + " " + h + ":" + min;
  }

  function showToast(msg) {
    var t = document.createElement("div");
    t.className = "profile-toast";
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 2600);
  }

  // ===========================================================================
  // JD (Job Description) Side Panel
  // ===========================================================================
  var _jdPanelEl = null;
  var _jdPanelOpen = false;
  var _currentJobId = "";

  function createJdPanel() {
    _jdPanelEl = document.createElement("div");
    _jdPanelEl.className = "autochat-jd-panel";
    _jdPanelEl.innerHTML = '<div class="profile-panel-loading">Loading job details...</div>';
    document.body.appendChild(_jdPanelEl);
  }

  function openJdPanel(jobId) {
    if (!_jdPanelEl) createJdPanel();
    var newId = jobId || "";
    // If already open for the same job, don't re-fetch
    if (_jdPanelOpen && newId === _currentJobId) return;
    _currentJobId = newId;
    _jdPanelOpen = true;
    _jdPanelEl.classList.add("open");
    document.getElementById("root").classList.add("autochat-jd-panel-open");
    if (_currentJobId) loadJobDetail(_currentJobId);
  }

  function closeJdPanel() {
    if (!_jdPanelOpen || !_jdPanelEl) return;
    _jdPanelOpen = false;
    _jdPanelEl.classList.remove("open");
    document.getElementById("root").classList.remove("autochat-jd-panel-open");
  }

  function loadJobDetail(jobId) {
    if (!_jdPanelEl) return;
    _jdPanelEl.innerHTML = '<div class="profile-panel-loading">Loading job details...</div>';
    fetch("/api/profile/jd-detail?job_id=" + encodeURIComponent(jobId), { credentials: "include" })
      .then(function (r) { return r.json(); })
      .then(function (job) {
        if (job.error) {
          _jdPanelEl.innerHTML = '<div class="profile-panel-loading">Job not found.</div>';
          return;
        }
        renderJdPanel(job);
      })
      .catch(function () {
        _jdPanelEl.innerHTML = '<div class="profile-panel-loading">Failed to load job details.</div>';
      });
  }

  function renderJdPanel(job) {
    if (!_jdPanelEl) return;

    var title = job.title || "Unknown Position";
    var corporateTitle = job.corporateTitle || "";
    var rank = job.rank || "";
    var hiringManager = job.hiringManager || "";
    var orgLine = job.orgLine || "";
    var country = job.country || "";
    var location = job.location || "";
    var businessArea = job.businessArea || "";
    var summary = job.summary || "";
    var yourRole = job.yourRole || "";
    var requirements = job.requirements || [];
    var matchingSkills = job.matchingSkills || [];
    var jobId = job.id || "";

    var html = '';

    // Header
    html += '<div class="profile-panel-header">';
    html += '  <div style="display:flex;justify-content:space-between;align-items:center">';
    html += '    <h2 style="margin:0;font-size:16px;font-weight:600;color:#1f2937">Job Details</h2>';
    html += '    <button class="profile-panel-close" data-jd-action="close-jd-panel" title="Close">&times;</button>';
    html += '  </div>';
    html += '  <div style="margin-top:4px;font-size:12px;color:#6b7280">ID: ' + esc(jobId) + '</div>';
    html += '</div>';

    // Title area
    html += '<div class="profile-readonly-info">';
    html += '  <div class="info-name">' + esc(title) + '</div>';
    if (corporateTitle) html += '  <div class="info-detail">' + esc(corporateTitle) + (rank ? ' — ' + esc(rank) : '') + '</div>';
    if (location) html += '  <div class="info-detail">' + esc(location) + ', ' + esc(country) + '</div>';
    html += '</div>';

    // Scrollable body
    html += '<div class="profile-panel-body">';

    // Summary
    if (summary) {
      html += '<div class="profile-section">';
      html += '<div class="profile-section-title">Summary</div>';
      html += '<p class="jd-text-block">' + esc(summary) + '</p>';
      html += '</div>';
    }

    // Your Role
    if (yourRole) {
      html += '<div class="profile-section">';
      html += '<div class="profile-section-title">Your Role</div>';
      html += '<p class="jd-text-block">' + esc(yourRole) + '</p>';
      html += '</div>';
    }

    // Requirements
    if (requirements.length > 0) {
      html += '<div class="profile-section">';
      html += '<div class="profile-section-title">Requirements</div>';
      html += '<ul class="jd-requirements-list">';
      requirements.forEach(function (req) {
        html += '<li>' + esc(req) + '</li>';
      });
      html += '</ul>';
      html += '</div>';
    }

    // Hiring Manager & Org
    html += '<div class="profile-section">';
    html += '<div class="profile-section-title">Team Details</div>';
    if (hiringManager) {
      html += '<div class="jd-detail-row"><span class="jd-detail-label">Hiring Manager</span><span>' + esc(hiringManager) + '</span></div>';
    }
    if (orgLine) {
      html += '<div class="jd-detail-row"><span class="jd-detail-label">Organization</span><span>' + esc(orgLine) + '</span></div>';
    }
    if (businessArea) {
      html += '<div class="jd-detail-row"><span class="jd-detail-label">Business Area</span><span>' + esc(businessArea) + '</span></div>';
    }
    html += '</div>';

    // Matching Skills
    if (matchingSkills.length > 0) {
      html += '<div class="profile-section">';
      html += '<div class="profile-section-title">Matching Skills</div>';
      html += '<div class="profile-tags">';
      matchingSkills.forEach(function (skill) {
        html += '<span class="profile-tag">' + esc(skill) + '</span>';
      });
      html += '</div>';
      html += '</div>';
    }

    html += '</div>'; // end body

    // Footer with action buttons
    html += '<div class="profile-panel-footer">';
    html += '<div class="profile-panel-actions jd-panel-actions">';
    html += '<button class="btn-submit" data-jd-action="draft-message" style="flex:1">Draft Message</button>';
    html += '<button class="btn-submit" data-jd-action="apply" style="flex:1">Apply</button>';
    html += '<button class="btn-save-draft" data-jd-action="ask-question" style="flex:1">Ask a Question</button>';
    html += '</div>';
    html += '</div>';

    _jdPanelEl.innerHTML = html;
    attachJdEvents();
  }

  function attachJdEvents() {
    if (!_jdPanelEl) return;
    _jdPanelEl.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-jd-action]");
      if (!btn) return;
      var action = btn.getAttribute("data-jd-action");
      var titleEl = _jdPanelEl.querySelector(".info-name");
      var jobTitle = titleEl ? titleEl.textContent : "";
      var jobId = _currentJobId;

      switch (action) {
        case "close-jd-panel":
          closeJdPanel();
          break;
        case "draft-message":
          if (window.sendUserMessage) {
            window.sendUserMessage("Draft a message to the hiring manager for " + jobTitle + " (" + jobId + ")");
          }
          break;
        case "apply":
          if (window.sendUserMessage) {
            window.sendUserMessage("Apply for the " + jobTitle + " role (" + jobId + ")");
          }
          break;
        case "ask-question":
          if (window.sendUserMessage) {
            window.sendUserMessage("I have a question about the " + jobTitle + " role (" + jobId + ")");
          }
          break;
      }
    });
  }

})();
