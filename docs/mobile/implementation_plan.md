# VaxInsight Mobile Missing-Screen Implementation Plan

## Phase 1: Finish The Existing Core Journey

1. **Complete**: language controls now appear on all public and account headers.
2. **Complete**: authenticated 401 failures route to `SessionExpiredScreen`.
3. **Complete**: logout confirmation and shared loader/empty/error/offline primitives are available.
4. **Complete**: email OTP verification, resend, password-reset confirmation, and invitation deep-link routes use existing backend endpoints; successful verification opens Home.
5. **Complete**: `AccountScreen` covers supported email, password, and self-service deletion operations.
6. **Remaining**: add dedicated initialization-failure copy and device-level offline detection if product requires it.

## Phase 2: Narrative Workflows

1. **Complete**: owner-scoped list, empty, detail, history, submit, update, validation, and conflict states are implemented.
2. **Complete**: owner screens use only `narrative.create`, `narrative.read.own`, and `narrative.update.own` API paths.
3. **Complete**: composer content remains in memory across recoverable request failures.
4. **Complete**: role-aware Home actions expose owner workflows to community members, CHWs, and reviewers.
5. **Complete**: an active review assignment prevents owner edits from changing the version under review; the API returns a recoverable conflict.
6. **Remaining**: add mobile unit/integration coverage for API fixtures and navigation guards.

## Phase 3: Reviewer Workflow

1. **Complete**: assigned queue from `GET /api/v1/reviews/assignments`.
2. **Complete**: assigned narrative detail and review history with stale-resource states.
3. **Complete**: explicit `in_review`, `reviewed`, and `requires_escalation` interactions use existing endpoints.
4. **Complete**: evidence and notes are submitted only through the backend review contract; no ML or medical conclusions are fabricated.
5. **Remaining**: add mobile unit/integration coverage for status transitions, evidence validation, and 409 recovery.

## Phase 4: Administrator Account Workspace

1. **Complete**: administrator dashboard with user, invitation, role, and session metrics.
2. **Complete**: user directory with search, role/status/email-verification filters, pagination, and recoverable states.
3. **Complete**: sanitized user details, effective-permission inspection, role changes, and lifecycle status changes with confirmations and backend safeguards.
4. **Complete**: staff invitation creation, invitation directory/details, pending invitation revocation, and delivery-expiry feedback.
5. **Complete**: audit log search, expandable sanitized details, role mapping inspection, and permission catalogue screens.
6. **Complete**: administrator-owned narrative navigation and source-backed vaccine-content draft/publish screen.
7. **Remaining**: assignment-management screens remain separate and require explicit product approval; account/content administration privileges do not grant raw narrative or research-data access.

## Phase 5: Blocked Analysis/XAI

Do not create functional prediction, SHAP, LIME, confidence, or evidence screens
until the dataset, model, inference API, explanation contract, uncertainty wording,
and governance approvals exist. A future unavailable state is appropriate now.

## Phase 6: Vaccine Information And Questions

1. **Complete**: published, source-attributed vaccine information list/detail
   screens use the backend content contract and show empty/error states when no
   approved content has been published.
2. **Complete**: community members and CHWs can submit questions, view their own
   question history, and request an analysis attempt without receiving fabricated
   AI or medical output.
3. **Complete**: reviewers can inspect the question queue and publish a separate
   professional response that is shown on the question detail screen.
4. **Complete**: Home actions and English/Kinyarwanda translations expose the new
   workflows with role-aware visibility.
5. **Complete**: question creation and repeat analysis requests use the backend
   rate-limit boundary; the mobile client preserves the explicit unavailable state.
6. **Remaining**: add mobile tests for question ownership, unavailable analysis,
   reviewer publishing, stale responses, and navigation guards.

## Phase 7: CHW Personal Activity

1. **Complete**: CHW Home uses the owner-scoped `GET /api/v1/dashboard/summary`
   endpoint for submitted, under-review, reviewed, and recent narrative data.
2. **Complete**: the endpoint exposes status only and excludes reviewer notes,
   outcomes, evidence, and other users' records.
3. **Remaining**: confirm whether the status-only owner projection is approved
   as a final product contract; owner feedback and outcomes remain blocked.

The full research boundary, Phase 1 data requirements, and Phase 3 evaluation
plan are recorded in
`docs/research/phase_2_3_implementation_report.md`.
