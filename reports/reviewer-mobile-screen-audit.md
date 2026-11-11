# VaxInsight Health Expert Mobile Screen Audit

Audit date: 2026-11-11

## Scope And Boundary

The backend role remains `reviewer`. The mobile interface may display this role
as **Health Expert**, but no new `health_expert` RBAC value is introduced. The
backend remains the authorization source of truth.

The Health Expert may access only active assignments belonging to that Health
Expert. The Health Expert cannot assign/reassign work, browse unassigned narratives, access
administrator audit data, or access owner-only narrative history.

## Existing Architecture

- Mobile: Expo React Native JavaScript, React Navigation native stack,
  `AuthContext`, `LanguageContext`, `ThemeContext`, shared state components, and
  `mobile/src/theme/tokens.js`.
- Authenticated navigation: `mobile/src/navigation/RootNavigator.js`.
- Shared bottom navigation: `mobile/src/components/BottomTabBar.js`, limited to
  icon-only top-level items and a maximum of five.
- Health Expert screens already registered:
  `ReviewQueueScreen`, `ReviewDetailScreen`, `ReviewHistoryScreen`,
  `QuestionReviewQueueScreen`, and `QuestionReviewDetailScreen`.
- Backend authorization: `Permission.NARRATIVE_READ_ASSIGNED` and
  `Permission.NARRATIVE_REVIEW` in `backend/app/core/permissions.py`.
- Health Expert resource authorization: `backend/app/services/reviews.py` gates
  assignment content, status changes, review submission, and history by the
  active assignment and reviewer ID.

## API Contract

| Capability | Operation | Permission | Current mobile use |
|---|---|---|---|
| Assigned workload | `GET /api/v1/reviews/assignments?page=&page_size=` | `narrative.read.assigned` | `ReviewQueueScreen` |
| Assignment detail | `GET /api/v1/reviews/assignments/{assignment_id}` | `narrative.read.assigned` | `ReviewDetailScreen` |
| Assignment status | `GET /api/v1/reviews/assignments/{assignment_id}/status` | `narrative.read.assigned` | Client method exists; screen reloads detail instead |
| Start review/escalate | `POST /api/v1/reviews/assignments/{assignment_id}/status` | `narrative.review` or assignment manager permission | `ReviewDetailScreen` |
| Submit review | `POST /api/v1/reviews/assignments/{assignment_id}/review` | `narrative.review` | `ReviewDetailScreen` |
| Review history | `GET /api/v1/reviews/assignments/{assignment_id}/history` | `narrative.read.assigned` | `ReviewHistoryScreen` |
| Question review queue | `GET /api/v1/review/questions` | `question.review` | `QuestionReviewQueueScreen` |
| Question review detail | `GET /api/v1/review/questions/{question_id}` | `question.review` | `QuestionReviewDetailScreen` |
| Professional response | `POST /api/v1/review/questions/{question_id}/response` | `question.review` | `QuestionReviewDetailScreen` |
| Published resources | `GET /api/v1/vaccine-content`, `GET /api/v1/vaccine-content/{id}` | `vaccine_content.read` | Shared Resources screens |

`ReviewPageQuery` supports only `page` and `page_size`. There is no backend
search, status filter, sort parameter, reviewer dashboard summary, assignment
activity feed, or assigned-narrative revision-history endpoint.

## Capability Classification

| Required capability | Status | Evidence, gap, or boundary |
|---|---|---|
| Health Expert Home | IMPLEMENTED AT CONTRACT BOUNDARY | `HomeScreen` shows the existing Health Expert workspace, assignment-backed workload counts, recent assignment activity, review actions, and refresh/error states. Counts are loaded from all pages of the existing assigned-workload API; no new summary endpoint is invented. |
| Assigned workload overview | IMPLEMENTED | `HomeScreen` loads all active assigned pages through `/reviews/assignments`; `ReviewQueueScreen` provides the paginated list and page progress. |
| Recent review activity | PARTIALLY IMPLEMENTED | Per-assignment `ReviewHistoryScreen` exists; no aggregate activity endpoint exists. |
| All assigned narratives | IMPLEMENTED | Active reviewer assignments load from `/reviews/assignments`, with owner-scope enforcement in `services/reviews.py`. |
| Pending/in-progress/completed/escalated views | IMPLEMENTED AT CONTRACT BOUNDARY | Dashboard cards count the exact backend statuses across loaded assigned pages. Separate filtered tabs remain unavailable because the backend exposes no status-filter query. |
| Search and sorting | BLOCKED BY BACKEND | The existing query contract exposes pagination only. No client-side search can safely represent all records. |
| Assignment pagination/load more | IMPLEMENTED | Queue refreshes on focus, exposes page progress, and loads subsequent backend pages without changing the authorization scope. |
| Assigned narrative detail | IMPLEMENTED | Content, version, assignment date, and current review status are shown from the assigned-detail response. |
| Review workspace | PARTIALLY IMPLEMENTED | Start-review, outcome, notes, evidence, submit, escalation, confirmation, success, and conflict states exist; save-progress/draft persistence remains unavailable because no draft API exists. |
| Approved outcome selection | IMPLEMENTED | Uses the exact backend enum: `needs_further_review`, `evidence_supports_claim`, `evidence_does_not_support_claim`, and `insufficient_evidence`. |
| Review submission confirmation | IMPLEMENTED | Submission is validated locally, confirmed, then sent once; the existing backend remains authoritative. |
| Duplicate submission prevention | IMPLEMENTED | Confirmation plus action loading prevents repeated taps; backend lifecycle conflicts still map to recovery copy. |
| Evidence reference list | PARTIALLY IMPLEMENTED | Evidence is entered during review and rendered in review history with title/publisher only. |
| Add evidence reference | IMPLEMENTED | `ReviewDetailScreen` maps the exact `ReviewEvidenceCreate` fields and validates required text locally and server-side. |
| Edit evidence reference | BLOCKED BY BACKEND | Evidence is immutable after review submission; no update/delete evidence operation exists. |
| Evidence source-link opening | IMPLEMENTED | Review history renders an action only for returned HTTP(S) URLs and checks `Linking.canOpenURL` before opening externally. |
| Review history | IMPLEMENTED | Immutable review records, outcomes, notes, timestamps, and evidence are rendered for an active assigned Health Expert. |
| Review activity details | PARTIALLY IMPLEMENTED | History cards show the available fields, but there is no separate detail route or activity grouping. |
| Narrative revision history | BLOCKED BY BACKEND | `/narratives/{id}/history` is owner-only and Health Expert access is intentionally denied; no assigned-Health-Expert revision endpoint exists. |
| Escalation details | PARTIALLY IMPLEMENTED | Required reason and `requires_escalation` transition are supported; no dedicated escalation detail/history endpoint exists. |
| Escalation confirmation | IMPLEMENTED | Escalation requires a reason and an explicit confirmation before the existing status endpoint is called. |
| Automatic escalation resolution | NOT APPLICABLE | Backend explicitly does not resolve escalations automatically. |
| Trusted vaccine resources | IMPLEMENTED AT BOUNDARY | Shared Resources and article screens use published source-backed content and honest empty states. |
| Health Expert guidance | IMPLEMENTED AT CLIENT WORKFLOW BOUNDARY | Resources now provide procedural review steps derived from the existing lifecycle. Clinical/public-health guidance still requires approved content and remains intentionally absent. |
| Health Expert profile/edit/profile security | IMPLEMENTED | Shared `AccountScreen`, `AuthContext`, appearance selector, password change, email verification, logout, and deletion are reused. |
| Notification preferences | BLOCKED BY BACKEND | No notification model, delivery channel, preference endpoint, or approved policy exists. |
| Help and support | BLOCKED BY BACKEND/PRODUCT | Resources shows an explicit unavailable state; no contact or support endpoint is fabricated. |
| About VaxInsight | IMPLEMENTED | Health Expert Resources includes static About copy using existing product positioning; no unsupported claims or external links are added. |
| Health Expert-only navigation | IMPLEMENTED | Health Experts receive Home, Assignments, Questions awaiting response, Resources, and Profile as five icon-only circular tabs; owner narrative navigation is guarded to assignments-only. |
| Light/dark/system themes | IMPLEMENTED | Existing token-based theme is shared by reviewer screens. |
| Loading/empty/error/refresh states | IMPLEMENTED AT CONTRACT BOUNDARY | Queue, dashboard, detail, history, confirmation, success, pagination, refresh, unauthorized, stale-assignment, conflict, timeout, and honest unavailable states are covered. |

## Existing Security Tests And Documentation

- `tests/test_narrative_review_workflow.py` covers assignment scope, unassigned
  reviewer denial, lifecycle transitions, immutable history, evidence, escalation,
  reassignment, and revocation.
- `tests/test_permission_management.py` covers reviewer permission boundaries.
- `tests/test_account_authorization_api.py` and administrator tests cover role and
  account authorization.
- `docs/permission_management.md` documents the reviewer permission matrix.
- `docs/mobile/role_navigation_matrix.md` and
  `docs/mobile/state_coverage_matrix.md` document the existing reviewer routes.

## Safe Implementation Sequence

1. Make the Health Expert primary tab `Assignments` and keep the professional question queue visible as the fifth icon-only tab.
2. Add queue pagination/load-more and explicit status summaries only from loaded
   assignment records; do not claim global status counts without a backend summary.
3. Add confirmation dialogs for review submission and escalation.
4. Add explicit success/recovery notices and safe external-link actions for
   returned evidence URLs.
5. Add Health Expert contract tests and update the implementation report.

## Backend Blockers

- Health Expert dashboard aggregate counts and recent activity require a new backend
  summary contract if global counts are required.
- Search, filtering, and sorting require query support in the review API.
- Evidence editing requires a new immutable-history-compatible backend policy and
  operation; it must not be simulated in the client.
- Health Expert access to narrative revisions requires an explicitly approved,
  assignment-scoped backend endpoint.
- Health Expert guidance, notifications, help/support content, and qualification policy
  require approved product/public-health decisions.
