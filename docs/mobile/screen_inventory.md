# VaxInsight Mobile Screen Inventory

## Audit Scope

Audit date: 2026-11-11

The `mobile/` directory was empty before this implementation. There was no
existing mobile framework, route, screen, API client, component library, asset
registry, or mobile test suite to preserve. The app is now a JavaScript Expo
React Native client using the existing FastAPI contract.

Status meanings:

- **EXISTING**: implemented in the current mobile client and connected to a real API or local system state.
- **INCOMPLETE**: a route exists but one or more important states or interactions are still missing.
- **MISSING**: relevant to an existing supported backend workflow but not implemented in mobile.
- **OPTIONAL**: requires product approval before adding.
- **BLOCKED**: depends on a backend, dataset, policy, or external decision that is not available.
- **OUT OF SCOPE**: intentionally not part of the current mobile boundary.

## A. Entry And Onboarding

| Item | Status | Current evidence or dependency |
|---|---|---|
| Welcome screen | EXISTING | `WelcomeScreen`; plain branded layout, bilingual copy, entrance motion, slider. |
| Language selector | EXISTING | `LanguageSelector`; English/Kinyarwanda persisted with AsyncStorage. |
| Initial app loading | EXISTING | Font/session bootstrap loader in `RootNavigator`. |
| Authentication selection | EXISTING | `AuthChoiceScreen`. |
| First-launch onboarding | OPTIONAL | No approved onboarding content or completion policy exists. |
| Onboarding completion state | OPTIONAL | Depends on first-launch onboarding approval. |
| Welcome image-loading failure | INCOMPLETE | Local bundled image removes network failure, but a missing/corrupt asset fallback is not yet surfaced. |
| App initialization failure | INCOMPLETE | Session restore fails closed, but no dedicated initialization recovery screen exists. |
| Unsupported app version | OUT OF SCOPE | No version-enforcement endpoint or policy exists. |
| Maintenance screen | OUT OF SCOPE | No maintenance-mode configuration or endpoint exists. |

## B. Authentication And Account Access

| Item | Status | Current evidence or dependency |
|---|---|---|
| Registration | EXISTING | `RegisterScreen` uses `POST /api/v1/auth/register`; community role remains server-controlled. |
| Sign in | EXISTING | `LoginScreen` uses `POST /api/v1/auth/login`. |
| Forgot-password request | EXISTING | `PasswordResetScreen` uses the generic `POST /api/v1/auth/password-reset/request` response. |
| Password-reset confirmation | EXISTING | `PasswordResetConfirmScreen`; accepts `vaxinsight://reset-password/:token` and calls `POST /auth/password-reset/confirm`. |
| Email verification | EXISTING | `VerifyEmailScreen`; accepts the registered email and six-digit OTP, calls `POST /auth/email/verify`, and establishes the returned session. |
| Verification pending/success/failure/expired/invalid | EXISTING | OTP entry, resend, success, and API failure states are surfaced without exposing account state; successful verification opens Home. |
| Resend verification | EXISTING | `VerifyEmailScreen` and `AccountScreen` call `POST /auth/email/verify/resend`. |
| Registration success | EXISTING | Registration opens verification with the submitted email prefilled. |
| Duplicate email | EXISTING | API error is shown through `InlineNotice` without changing backend wording. |
| Invalid registration details | EXISTING | Required fields and password mismatch are validated locally; API validation is surfaced. |
| Incorrect password/account-not-found | EXISTING | Generic sign-in failure presentation avoids account enumeration. |
| Rate limit/account lock | EXISTING | 429 responses use localized retry guidance; backend remains authoritative for account lock policy. |
| Suspended/deactivated/deleted/pending account | INCOMPLETE | Backend rejects access; mobile needs dedicated status-specific copy only if the API exposes safe state detail. |
| Invitation acceptance | EXISTING | `InvitationAcceptScreen`; opens from `vaxinsight://invite/:token`, keeps the one-time token internal, asks only for password confirmation, and establishes the returned session. |
| Invalid/expired/used invitation | EXISTING | 400/409 API responses preserve the form and show localized recovery copy. |
| Authentication service unavailable | EXISTING | Network/API errors use localized recovery copy; retry is available through form submission. |
| Session expired/refresh failure | EXISTING | Authenticated 401 failures switch to `SessionExpiredScreen`; local sign-out returns to auth. |
| Logout confirmation | EXISTING | Home and Account use native confirmation before revoking the session. |
| Logout failure/retry | EXISTING | Local sign-out completes even if server revocation fails; failure is intentionally not shown as a blocking state. |

## C. Community Member And CHW

| Workflow | Status | Current evidence or dependency |
|---|---|---|
| Authenticated account home | EXISTING | `HomeScreen` uses `GET /api/v1/auth/me`, shows role/status, refresh, and sign-out. |
| Dashboard loading/empty/failure | EXISTING | Home has session bootstrap, CHW personal activity loading/error states, pull-to-refresh, role-aware workflow actions, and refresh error. |
| Narrative submission | EXISTING | `NarrativeComposerScreen` uses `POST /api/v1/narratives` with the backend content constraints. |
| Submission confirmation/loading/success/failure/retry | EXISTING | Composer preserves content on failure and opens detail after success. |
| My narratives list/loading/empty/failure | EXISTING | `NarrativeListScreen` uses owner-scoped `GET /api/v1/narratives` with refresh, empty, and retry states. |
| Narrative details/history/revision details | EXISTING | `NarrativeDetailScreen` and `NarrativeHistoryScreen` use the owner-scoped routes. |
| Edit narrative | EXISTING | `NarrativeComposerScreen` uses `PATCH /api/v1/narratives/{id}` while content remains submitted; active review assignment conflicts return `409` and preserve the form. |
| Narrative not found/access denied/conflict | EXISTING | Detail/editor map API errors and preserve recoverable form content. |
| Under review/assigned/completed/escalated labels | EXISTING | CHW Home and owner narrative screens show status-only `pending`, `in_review`, `reviewed`, and `requires_escalation` metadata from the personal dashboard; internal review notes, outcomes, and evidence remain unavailable pending policy. |
| CHW-specific dashboard | EXISTING | `HomeScreen` uses `GET /api/v1/dashboard/summary` for owned narrative counts and recent status-only records. |
| CHW access-restricted state | EXISTING | Backend permissions remain authoritative; CHWs receive no Health Expert, assignment-manager, administrator, or audit access. |
| My questions | EXISTING | `QuestionListScreen` is reachable from CHW/community bottom navigation and uses owner-scoped `GET /api/v1/questions`. |
| Ask question and unavailable analysis | EXISTING | `QuestionComposerScreen` uses `POST /api/v1/questions`; the explicit unavailable-analysis state remains visible when no approved provider exists. |
| Question detail/professional response | EXISTING | `QuestionDetailScreen` renders owner-safe analysis and any published professional response. |
| Resources hub | EXISTING | `ResourcesScreen` links published vaccine information, CHW questions, and an honest empty learning-resource state. |
| Vaccine article detail/source link | EXISTING | `VaccineArticleDetailScreen` renders the published detail contract and opens the backend-provided original source URL. |

## D. Health Expert

| Workflow | Status | Current evidence or dependency |
|---|---|---|
| Health Expert dashboard | EXISTING | `ReviewQueueScreen` is role-gated to Health Experts and uses active assignments. |
| Assigned list/loading/empty/failure | EXISTING | Queue uses `GET /api/v1/reviews/assignments` with refresh, empty, and retry states. |
| Assigned narrative details | EXISTING | `ReviewDetailScreen` uses active-assignment detail and displays only returned narrative content. |
| Assignment information/revoked/unavailable | EXISTING | 404/403/409 responses remain recoverable through error/retry states. |
| Review details/evidence | EXISTING | Review detail includes notes and up to 20 backend-shaped evidence records. |
| Review decision/validation/submission | EXISTING | Status transition to `in_review` and review submission use the existing endpoints and enums. |
| Review success/failure/conflict | EXISTING | Form values remain in memory on failure; API status mapping handles recovery copy. |
| Review history/empty/loading failure | EXISTING | `ReviewHistoryScreen` uses the assignment history endpoint. |
| Escalation confirmation/success/failure | EXISTING | Health Experts can submit a required escalation reason from pending or in-review states. |
| Review access denied/service unavailable | EXISTING | Permission, stale assignment, and service failures use shared error recovery. |

## E. Administrator

| Workflow | Status | Current evidence or dependency |
|---|---|---|
| Administrator home | EXISTING | `AdminDashboardScreen` uses the administrator summary endpoint and exposes the management workspace from Home and the administrator tab. |
| Administrator dashboard metrics | EXISTING | User, invitation, role, and active-session counts include loading, refresh, empty, unauthorized, and retry states. |
| Mobile user administration | EXISTING | `AdminUsersScreen` supports email search, role/status/email-verification filters, pagination, empty state, and retry state. |
| User account details | EXISTING | `AdminUserDetailScreen` displays sanitized account metadata and effective permissions without credentials. |
| User role management | EXISTING | Role changes use the protected backend route, confirmation, self-demotion protection, success, conflict, and retry states. |
| User status management | EXISTING | Status changes use the protected backend route, confirmation, self-deactivation protection, session-revocation feedback, and retry states. |
| Staff invitation creation | EXISTING | `AdminInviteScreen` sends CHW, Health Expert, or administrator invitations with validation and delivery-expiry feedback. |
| Invitation directory/details/revocation | EXISTING | `AdminInvitationsScreen` and `AdminInvitationDetailScreen` support filters, pagination, sanitized metadata, pending-only revoke confirmation, and recovery states. |
| Audit log | EXISTING | `AdminAuditScreen` supports action/outcome filters, pagination, expandable sanitized details, empty state, and retry state. |
| Role and permission inspection | EXISTING | `AdminRolesScreen`, `AdminRoleDetailScreen`, and `AdminPermissionsScreen` display static role mappings and reserved capabilities. |
| Vaccine-content management | EXISTING | `AdminVaccineContentScreen` creates draft or published source-backed content and lists published content; validation, success, empty, and retry states are included. |
| Administrator-owned narratives | EXISTING | Administrator accounts now see the owner-scoped narrative workspace granted by the backend role mapping. |
| Mobile narrative assignment management | OPTIONAL | Backend supports `narrative.assign`; mobile administration requires explicit product approval. |
| Assignment/Health Expert selection/conflict/revocation | OPTIONAL | Do not add until mobile administration is approved. |
| Administrator access denied | EXISTING | `AdminAccessDeniedScreen` and per-screen guards provide a recoverable error state; backend permission checks remain authoritative. |

## F. ML And Explainable AI

All analysis, prediction, SHAP, LIME, evidence, model metadata, and explanation
screens are **BLOCKED**. The dataset, model, inference endpoints, explanation
contract, uncertainty semantics, and approved safety wording do not exist.
The mobile client must show an unavailable state rather than fabricated output
when this area is eventually reached.

## G. Profile And Account Management

| Workflow | Status | Current evidence or dependency |
|---|---|---|
| Profile display | EXISTING | `AccountScreen` displays name, email, role, and lifecycle status. |
| Edit profile/email change | EXISTING | `AccountScreen` edits the full name without ending the session and calls `PATCH /auth/me`; email changes enter the explicit verification route after the server invalidates the old session. |
| Change password | EXISTING | `AccountScreen` calls `POST /auth/password/change` and clears fields after success. |
| Language settings | EXISTING | Welcome selector persists the selected language. A dedicated settings route is not needed yet. |
| Account status | EXISTING | Home displays current status from the authenticated profile. |
| Account deletion | EXISTING | `AccountScreen` confirms the destructive action, calls `DELETE /auth/me`, clears the local session, and permits re-registration with the same email. |

## H. Global And Form States

| State family | Status | Current evidence or dependency |
|---|---|---|
| Network/offline/timeout/server failure | EXISTING | Shared API error mapping, a 15-second request abort timeout, and reusable `OfflineState`/`ErrorState` primitives are available. |
| Unauthorized/forbidden/not found/conflict | EXISTING | `ApiError` status mapping provides localized 403/404/409/429/503 copy; authenticated 401s use session recovery. |
| Loading/submitting/duplicate prevention | EXISTING | Auth forms disable actions and show activity indicators; broader workflow coverage is pending. |
| Success/empty/error/retry primitives | EXISTING | `InlineNotice`, `FullScreenLoader`, `EmptyState`, `ErrorState`, and `OfflineState` are implemented. |
| Input focus/filled/invalid/password toggle | EXISTING | Shared input primitives implement labels, focus-compatible native inputs, password visibility, and inline errors. |
| Unsaved changes/recovery after failure | INCOMPLETE | Narrative/question forms preserve in-memory content after recoverable failures; persistent drafts and a global unsaved-change guard are not implemented. |
| Confirmation dialogs/bottom sheets | EXISTING | Logout confirmation uses the platform alert; review confirmations remain pending with Health Expert screens. |
