# VaxInsight CHW Role Completeness Audit

Audit date: 2026-11-11

## 1. Executive Summary

The repository contains a real `chw` account role, invitation-only onboarding,
server-side permission checks, and a working neutral owner-scoped narrative
workflow. A CHW can authenticate, submit and edit an owned narrative, view its
history, read published vaccine-content records, submit owned vaccine questions
through the API, and use profile/session controls.

The role is not complete across the product. A safe owner-scoped personal
dashboard, CHW question entry points, question rate limits, and narrative edit
locking during active review are now implemented. The current narrative model
still cannot distinguish a CHW's own experience from a community participant's
statement and has no consent or provenance fields. Those fields are policy and
ethics dependent under `SD-003`, `SD-004`, `SD-009`, `SD-012`, and `SD-015`; they
must not be invented. Owner-visible review feedback and outcomes also remain
blocked; the dashboard exposes status only and omits internal review data.

This audit treats a capability as `IMPLEMENTED` only when the relevant UI or
API, data model, authorization boundary, and tests support the complete flow.

## 2. Status Legend

- `IMPLEMENTED`: Complete and verified in the current repository.
- `PARTIALLY IMPLEMENTED`: Some layers work, but the complete workflow is missing.
- `MISSING`: No meaningful implementation exists and no external decision is required to build the safe baseline.
- `BLOCKED`: A safe implementation requires an approved policy, data source, governance decision, or external dependency.
- `NOT APPLICABLE`: The capability is not part of the approved repository scope.

## 3. Existing CHW Functionality

| Capability | Status | Evidence |
|---|---|---|
| Invitation-only CHW onboarding | `IMPLEMENTED` | `backend/app/models/user.py` defines `UserRole.CHW`; `backend/app/api/routes/auth.py` exposes invitation creation/acceptance; `backend/app/schemas/auth.py` limits staff invitations to approved staff roles. |
| Login, refresh, logout, and session restoration | `IMPLEMENTED` | `backend/app/api/routes/auth.py`, `backend/app/services/sessions.py`, `backend/app/api/dependencies.py`, and `mobile/src/context/AuthContext.js`. |
| Server-side CHW RBAC | `IMPLEMENTED` | `backend/app/core/permissions.py` and `require_permissions` in `backend/app/api/dependencies.py`; account state is reloaded before authorization. |
| Own narrative create/read/update/history | `IMPLEMENTED` as a neutral record workflow | `POST/GET/PATCH /api/v1/narratives`, `GET /api/v1/narratives/{id}/history`, owner predicates in `backend/app/services/narratives.py`, and `tests/test_narrative_api.py`. |
| Published vaccine-content read access | `PARTIALLY IMPLEMENTED` | `GET /api/v1/vaccine-content` and `GET /api/v1/vaccine-content/{id}` are permission protected and mobile-rendered, but there is no approved source allow-list or publication governance. |
| Owned question workflow | `IMPLEMENTED` at the provisional owner-scoped boundary | `backend/app/api/routes/questions.py` and `backend/app/services/questions.py` support create/list/detail, unavailable analysis, and published professional responses; `QuestionListScreen`, `QuestionComposerScreen`, and `QuestionDetailScreen` are reachable for CHWs. Real analysis remains unavailable. |
| Profile, password, email, language, theme, and logout | `IMPLEMENTED` | `mobile/src/screens/AccountScreen.js`, `mobile/src/context/AuthContext.js`, `LanguageContext.js`, and `ThemeContext.js`; account status labels are localized through `accountStatusLabel`. |
| Real AI/XAI output | `BLOCKED` | `get_analysis_provider()` in `backend/app/services/questions.py` returns `None`; the client correctly shows an unavailable state. No approved dataset, model, inference, or explanation contract exists. |

## 4. Responsibility Audit

### A. Community Engagement And Narrative Collection

| Audited capability | Status | Evidence and finding |
|---|---|---|
| Understand VaxInsight and CHW purpose | `IMPLEMENTED` | CHW role copy exists in `mobile/src/screens/HomeScreen.js` and `mobile/src/i18n/translations.js`; account role is rendered through `roleLabel`. |
| Capture a vaccine-related question or concern | `IMPLEMENTED` at the owner-scoped boundary | `VaccineQuestion` and question routes exist; CHWs can reach `QuestionListScreen` from bottom navigation and `QuestionComposerScreen` from Home. |
| Record a community experience or information need | `PARTIALLY IMPLEMENTED` | The neutral narrative composer stores text, but only `submitted_by_id`, content, status, version, and timestamps exist. No approved collection context exists. |
| Preserve original meaning | `IMPLEMENTED` for submitted text | Narrative content is stored and revisions are immutable through `NarrativeRevision`; the backend does not rewrite or classify it. |
| Distinguish CHW's own narrative from a participant narrative | `BLOCKED` | No source/provenance field or workflow exists. `SD-003`, `SD-004`, `SD-012`, and `SD-015` require an approved collection and consent protocol first. |
| Record source/channel/context | `BLOCKED` | The current `NarrativeCreate` schema only accepts `content`; adding participant, location, or health information without the approved protocol would violate data minimization. |
| Follow informed consent/data-collection procedure | `BLOCKED` | No consent form, ethics approval, withdrawal process, retention schedule, or data-management plan is present. See `docs/requirements/supervisor_decision_register.md`. |
| Access responsible-engagement guidance | `BLOCKED` | No approved educational/resource content exists. The vaccine-content registry is an infrastructure boundary, not evidence of approved guidance. |

### B. Narrative Submission And Management

| Audited capability | Status | Evidence and finding |
|---|---|---|
| Submit an owned narrative | `IMPLEMENTED` | `NarrativeComposerScreen.js` calls `POST /api/v1/narratives`; backend validates length/control characters, rate limits writes, creates a revision, and audits the action. |
| Submit an authorized community-collected narrative | `BLOCKED` | No approved provenance/consent model or actor/channel policy exists. Do not add an unrestricted boolean or participant fields. |
| Provide narrative context | `BLOCKED` | Context fields are not defined by an approved protocol. The current neutral record intentionally accepts only narrative text. |
| Validate before submission | `IMPLEMENTED` | Mobile validates required/maximum length; Pydantic and database constraints validate content server-side with `extra="forbid"`. |
| View owned narratives/details/history | `IMPLEMENTED` | `NarrativeListScreen`, `NarrativeDetailScreen`, `NarrativeHistoryScreen`, and owner-scoped API queries. |
| Edit owned narratives | `IMPLEMENTED` with active-review protection | `PATCH /narratives/{id}` appends revisions while status is `submitted`, but rejects edits once an active `NarrativeAssignment` exists with `409`; this prevents an assigned reviewer from reviewing a changed version. |
| Recover submission failure without losing text | `IMPLEMENTED` | `NarrativeComposerScreen` keeps `content` in component state and leaves the form available after API failure. Persistent offline drafts are not implemented. |
| Enforce ownership and deny private cross-user access | `IMPLEMENTED` | Narrative queries include both narrative ID and authenticated owner ID; cross-user access returns `404`. Coverage exists in `tests/test_narrative_api.py`. |
| Record required audit events | `PARTIALLY IMPLEMENTED` | Create/update events are recorded, but domain audit details do not include a resource ID/version, limiting reconstruction. |
| Unrestricted deletion | `NOT APPLICABLE` | No narrative deletion route exists; this is consistent with the explicit requirement not to add unrestricted narrative deletion. |

### C. Narrative Tracking And Review Feedback

| Audited capability | Status | Evidence and finding |
|---|---|---|
| View own narrative submission status | `PARTIALLY IMPLEMENTED` | `GET /api/v1/dashboard/summary` returns owned recent narratives with status-only active review metadata; reviewer assignment resources remain protected. |
| Identify awaiting/in-review/reviewed/escalated records | `PARTIALLY IMPLEMENTED` | The personal dashboard exposes `pending`, `in_review`, `reviewed`, and `requires_escalation` status labels without internal history; policy confirmation is still required before treating this as a final owner-feedback contract. |
| View permitted review outcomes | `BLOCKED` | `NarrativeReviewResponse` contains outcomes and confidential notes/evidence; no approved owner-safe subset is defined. |
| View submitter-facing feedback | `BLOCKED` | There is no separate feedback field or correction workflow. Reviewer notes are intentionally not exposed to narrative owners. |
| Respond to clarification requests | `BLOCKED` | No approved clarification state, response model, notification, or escalation-resolution policy exists. |
| Reviewer workflow integrity | `PARTIALLY IMPLEMENTED` | `reviews.py` and `services/reviews.py` provide assignment, status, review, evidence, escalation, and history for reviewers/managers. Owners are correctly denied, but narrative edits after assignment are not version-bound. |

### D. Trusted Vaccine Information And Educational Resources

| Audited capability | Status | Evidence and finding |
|---|---|---|
| Browse published vaccine information | `PARTIALLY IMPLEMENTED` | `OfficialVaccineInfoScreen.js` calls the published content API and displays title, summary, body, source, authority, and publication date. No approved content package is present. |
| Source attribution and publication date | `IMPLEMENTED` at API/UI field level | `VaccineContentResponse` includes source metadata and `published_at`; mobile renders source, authority, and date. The original source URL is not currently rendered as a link. |
| Official announcements and educational materials | `BLOCKED` | `SD-009` is unresolved; no approved RBC, WHO, WHO Africa, UNICEF, or other source allow-list/content integration is present. Do not fabricate content or citations. |
| Source currency, withdrawal, and approval governance | `BLOCKED` | Administrator publication exists, but independent public-health approval, review cadence, withdrawal, and version governance are not defined. |
| CHW resource entry point | `PARTIALLY IMPLEMENTED` | The existing `VaccineInfo` bottom-tab route is reusable, but Home does not explain resource use or distinguish official guidance from general information. |

### E. Community Communication And Education

| Audited capability | Status | Evidence and finding |
|---|---|---|
| Understand reviewed information | `BLOCKED` | Owner-safe review feedback is not defined and real analysis is unavailable. |
| Find approved educational materials | `BLOCKED` | No approved materials are stored or seeded; the content registry is empty/operational only. |
| Share authorized public-health resources | `BLOCKED` | Source governance, link policy, and sharing requirements are unresolved. |
| Communicate responsibly and refer medical concerns | `BLOCKED` | No approved guidance, referral channels, or safety wording exists. Do not add a medical chatbot or advice generator. |
| Vaccination scheduling, stock, household outreach, or adverse-event reporting | `NOT APPLICABLE` | No approved requirement, model, route, or data source exists in this repository. |

### F. Personal Activity And Contribution Monitoring

| Audited capability | Status | Evidence and finding |
|---|---|---|
| Total narratives submitted | `IMPLEMENTED` | `GET /api/v1/dashboard/summary` counts narratives using the authenticated owner ID; `HomeScreen.js` renders the CHW metric. |
| Narratives awaiting/under review | `IMPLEMENTED` as a status-only metric | The personal dashboard derives active `pending`, `in_review`, and `requires_escalation` assignments for owned narratives only. |
| Narratives reviewed | `IMPLEMENTED` as a status-only metric | The personal dashboard derives reviewed active assignments for owned narratives only; it never uses platform totals. |
| Recent personal submissions | `IMPLEMENTED` | CHW Home uses the personal dashboard's owned recent records; other supported roles continue to use owner-scoped `GET /api/v1/narratives`. |
| Submission history | `IMPLEMENTED` | Narrative list/detail/history screens and endpoints exist. |
| Personal trends or community reach | `NOT APPLICABLE` | No approved reliable data source for trends beyond simple counts or community reach measurement exists. |

### G. Profile And Account Management

| Audited capability | Status | Evidence and finding |
|---|---|---|
| View profile, role, and account status | `IMPLEMENTED` | `AccountScreen.js` and `GET /api/v1/auth/me`; role and account status are localized. |
| Update permitted profile information | `IMPLEMENTED` | `PATCH /api/v1/auth/me` supports full name/email-change verification; no role/permission fields are accepted. |
| Change password | `IMPLEMENTED` | `POST /api/v1/auth/password/change` validates current credentials and revokes sessions. |
| Appearance and language preferences | `IMPLEMENTED` | `ThemeContext`, `AppearanceSelector`, `LanguageContext`, and persisted AsyncStorage preferences. |
| Notification settings | `NOT APPLICABLE` | No notification capability or approved delivery channel exists. |
| Secure logout and deletion | `IMPLEMENTED` | Auth context revokes the session when possible, clears local tokens, and confirms deletion before `DELETE /auth/me`. |
| Change own role or permissions | `IMPLEMENTED` denial | No self-service route exists; role/status management is administrator protected and backend authoritative. |

### H. Privacy, Consent, And Responsible Data Handling

| Audited capability | Status | Evidence and finding |
|---|---|---|
| Authentication and active-account enforcement | `IMPLEMENTED` | JWT validation, Argon2 passwords, rotating refresh sessions, account-state checks, and password-change invalidation are implemented. |
| Narrative ownership/private access | `IMPLEMENTED` | Owner predicates are applied in SQL for list/detail/update/history; reviewer/admin routes do not grant owner data implicitly. |
| Data minimization for participant information | `BLOCKED` | The current model avoids participant fields, but a CHW-mediated collection flow cannot be added until consent/ethics/retention decisions are approved. |
| Safe validation/error messages | `IMPLEMENTED` | Pydantic input validation, sanitized validation errors, generic login/reset responses, and localized mobile status mapping exist. |
| Audit logging | `PARTIALLY IMPLEMENTED` | Auth, narrative, question, assignment, review, and account actions are audited; narrative/question resource IDs and revision/version context are not consistently recorded. |
| Confidential review feedback | `IMPLEMENTED` denial | Review history is limited to active assigned reviewers and assignment managers; owners are denied by the current API. Owner-safe feedback remains blocked. |
| Unauthorized exports | `NOT APPLICABLE` | No export endpoint or mobile export control exists. This should be reassessed if export is introduced. |

## 5. Backend Findings

- Models and migrations cover users, narratives/revisions, assignments/reviews/evidence, vaccine content, questions/analysis/responses, sessions, rate limits, and audit events. No CHW-specific table is required for the safe dashboard/navigation work.
- `backend/app/core/permissions.py` gives CHWs `vaccine_content.read`, `narrative.create`, `narrative.read.own`, `narrative.update.own`, `question.create`, `question.read.own`, `vaccine_analysis.request`, and `vaccine_analysis.read`. CHWs do not receive reviewer, assignment, administrator, or audit permissions.
- Narrative ownership is enforced in `backend/app/services/narratives.py`, not only hidden in the mobile UI.
- `backend/app/api/routes/questions.py` exposes a complete provisional owned-question contract, applies the existing PostgreSQL-backed rate-limit infrastructure to question creation and repeat analysis requests, and still returns an unbounded owned-question list.
- `backend/app/services/questions.py` explicitly fails closed when no approved analysis provider exists. This must remain blocked rather than replaced with fabricated output.
- `backend/app/api/routes/vaccine_content.py` exposes source-attributed published content, but administrator publication is not an approved-source governance system.
- The existing administrator dashboard is not a CHW dashboard and must not be reused for personal metrics because it aggregates platform data.
- `backend/app/api/routes/dashboard.py` and `backend/app/services/dashboard.py` provide a status-only owner projection; reviewer notes, outcomes, evidence, and other users' records are excluded.

## 6. Database And Migration Findings

The current migration chain ends at `b8c9d0e1f2_add_vaccine_content_question_workflow.py`.
Existing tables are sufficient for an owner-scoped personal dashboard and question
navigation. No migration is justified for the safe implementation identified in
this audit.

A future CHW-mediated participant workflow would require an approved data model
for provenance, consent, retention, withdrawal, and ownership before any migration
is written. It must not be represented by an ad-hoc `is_community_collected` flag.

## 7. API And Authorization Matrix

| Capability | Expected CHW access | Current status | Backend boundary |
|---|---|---|---|
| Home dashboard | Allowed | `IMPLEMENTED` | `GET /api/v1/dashboard/summary` is authenticated and owner-scoped; the administrator summary remains separate. |
| Submit own narrative | Allowed | `IMPLEMENTED` | `narrative.create`; actor becomes `submitted_by_id`. |
| Submit community-collected narrative | Policy dependent | `BLOCKED` | No provenance/consent contract. |
| View/edit own narratives/history | Allowed | `IMPLEMENTED` | `narrative.read.own` and `narrative.update.own` plus owner predicates. |
| Track own review status | Allowed if approved | `PARTIALLY IMPLEMENTED` | The personal dashboard exposes status-only review metadata; internal review history and feedback remain blocked. |
| View permitted review feedback | Allowed if approved | `BLOCKED` in current baseline | Internal review notes/evidence are not owner-visible. |
| Browse published vaccine content | Allowed | `PARTIALLY IMPLEMENTED` | `vaccine_content.read`; content governance is unresolved. |
| Ask/read own questions | Allowed | `IMPLEMENTED` at the provisional boundary | `question.create` and `question.read.own`; CHW Home and bottom navigation expose the existing mobile workflow. |
| Request/read unavailable analysis boundary | Allowed | `IMPLEMENTED` boundary | `vaccine_analysis.request/read`; no real provider. |
| View other users' private narratives | Denied | `IMPLEMENTED` denial | No CHW permission and owner query scope. |
| Assign reviewers | Denied | `IMPLEMENTED` denial | `narrative.assign` is administrator-only. |
| Review assigned narratives | Denied by default | `IMPLEMENTED` denial | `narrative.read.assigned` and `narrative.review` are reviewer-only. |
| Manage users/audit/roles | Denied | `IMPLEMENTED` denial | Administrator-only permissions. |
| Change own role/permissions | Denied | `IMPLEMENTED` denial | No client-controlled role or permission fields/routes. |

## 8. Mobile UI/UX Findings

- `HomeScreen.js` has a CHW-specific hero, narrative action, recent narratives,
  published vaccine-content preview, pull-to-refresh, loading, empty, and error
  states.
- `NarrativeListScreen.js`, `NarrativeComposerScreen.js`,
  `NarrativeDetailScreen.js`, and `NarrativeHistoryScreen.js` are connected to
  owner-scoped APIs and preserve form content after recoverable failures.
- `QuestionListScreen.js`, `QuestionComposerScreen.js`, and
  `QuestionDetailScreen.js` are registered in `RootNavigator.js`; CHWs can reach
  the list from bottom navigation and the composer from Home.
- `OfficialVaccineInfoScreen.js` renders published content and source metadata but
  does not render the original source URL as an external link.
- `AccountScreen.js` supports profile, password, email verification, appearance,
  deletion, and logout. Account status uses the localized `accountStatusLabel`
  helper.
- `OfflineState` exists, but the API client has no timeout/abort behavior and the
  narrative/question forms do not persist drafts across app termination.
- The app has only the existing theme-preference Node tests; no mobile component,
  navigation, CHW, API-mock, accessibility, or device-flow tests exist.

## 9. Testing Gaps

Existing coverage is strong for authentication, owner narrative isolation,
reviewer assignment integrity, administrator authorization, and security
constraints. The new CHW backend boundaries are covered by
`tests/test_supervisor_workflow.py`, `tests/test_narrative_review_workflow.py`,
`tests/test_dashboard_api.py`, and `tests/test_openapi_documentation.py`. The
remaining gaps are:

1. No mobile component, navigation, or rendering tests.
2. No question pagination contract; owned question listing remains unbounded.
3. No dedicated analysis-rate-limit integration assertion; creation rate limiting is covered.
4. No owner-visible review feedback test because that contract is unresolved.
5. No approved-source governance or seeded public-health content test.
6. No resource/version identifiers in all narrative audit details.

Focused verification for this implementation passed:

- `python -m pytest tests/test_dashboard_api.py tests/test_supervisor_workflow.py tests/test_narrative_review_workflow.py tests/test_openapi_documentation.py -q`: `28 passed`.
- `python -m ruff check backend tests`: passed.
- `python -m alembic check`: no new upgrade operations detected.
- Mobile theme tests: `4 passed`; Babel compilation passed for six changed modules; Android Expo export passed.

A full suite run reached `255 passed` and six failures in existing last-active-
administrator tests because the configured development database contains one
real active administrator in addition to the temporary test accounts. Those
tests should be rerun against an isolated test database.

## 10. Documentation Gaps

- `docs/mobile/implementation_plan.md` needs to record the completed CHW
  dashboard, question entry points, and question rate-limit boundary.
- `docs/mobile/role_navigation_matrix.md` needs current question routes, the
  personal dashboard route, and CHW permission dependencies.
- `docs/mobile/screen_inventory.md` needs current CHW dashboard/question status
  and the active-review edit restriction.
- `docs/mobile/state_coverage_matrix.md` needs question, personal-dashboard,
  and active-review conflict rows.
- `docs/permission_management.md` needs question, vaccine-content,
  vaccine-analysis, personal-dashboard, and narrative-lock coverage.
- Historical reports still describe `mobile/` as empty and must not be treated as
  current implementation evidence.

## 11. Safe Implementation Priorities

### Safe in this task

1. Completed: add a personal dashboard summary endpoint using only the
   authenticated user's own narratives and existing assignment status; counts
   and recent records omit reviewer notes, outcomes, and evidence.
2. Completed: add CHW/community question navigation using the existing question
   API and unavailable-analysis boundary.
3. Completed: add backend tests for CHW question/content/dashboard access,
   reviewer/administrator denials, rate limiting, and active-review edit locking.
4. Completed: localize account status labels and align Home content with real
   dashboard data.
5. Complete the current mobile role/navigation/state/permission documentation.

### Blocked until policy or external inputs exist

- Community-participant provenance, consent, withdrawal, retention, or sensitive
  context fields.
- Owner-visible review outcomes, reviewer notes, evidence, clarification, or
  escalation resolution.
- Real ML/XAI output, confidence, SHAP/LIME, model-linked explanations, or medical
  recommendations.
- Approved RBC/WHO/WHO Africa/UNICEF source integration, seeded content, source
  allow-list, update cadence, or external-link governance.
- Push/SMS notifications, offline synchronization, referrals, scheduling, stock,
  household outreach, or adverse-event reporting.

## 12. Recommended Order Of Work

1. Validate the current mobile dashboard/question flows with component or device
   tests when the mobile test harness is approved.
2. Add pagination to the owned question list if the product requires larger
   histories.
3. Update current navigation/state/permission documentation and retain unresolved
   decisions in the supervisor decision register.
4. Obtain decisions `SD-001` through `SD-005`, `SD-009`, `SD-012`, and `SD-015`
   before expanding data collection, review feedback, or public-health content.
5. Add mobile component/device testing after the route contracts stabilize.
