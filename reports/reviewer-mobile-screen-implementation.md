# VaxInsight Health Expert Mobile Screen Implementation

Implementation date: 2026-11-11

## Role Boundary

The backend role remains `reviewer`. The mobile UI displays this role as **Health
Expert** in English and **Inzobere mu buzima** in Kinyarwanda. No
`health_expert` role or permission was introduced.

The mobile client only exposes assigned review work. Backend authorization still
controls assignment visibility, narrative content, status transitions, review
submission, evidence, and review history.

## Implemented Experience

### Navigation

- Health Expert navigation uses five icon-only circular tabs: Home, Assignments,
  Questions awaiting response, Resources, and Profile.
- Other roles retain the shared four-tab structure with their existing primary
  workspace.
- Review queue and professional question queue are wrapped in the authenticated
  shell so both crucial Health Expert workflows remain available from the navbar.
- Health Expert access to the owner-scoped narrative list is guarded in the client;
  the backend remains the final authorization boundary.

### Home

- Existing Health Expert workspace hero is retained.
- Assigned workload is loaded from all pages of the existing
  `GET /reviews/assignments` contract with `page_size=100`.
- Dashboard cards show actual assigned-page counts for:
  - Assigned
  - Pending
  - In progress
  - Completed
  - Escalated
- Recent activity uses assignment `updated_at` values and links to the assigned
  review workspace.
- Dashboard refresh and API errors use existing shared state and error mapping.

### Assignments

- Queue refreshes whenever it receives focus and on pull-to-refresh.
- Existing backend pagination is exposed through page progress and Load more.
- Cards show the exact review status, assigned date, updated date, narrative
  content, and assignment detail route.
- Empty, loading, retry, unauthorized, stale-resource, and API failure states
  remain explicit.

### Review Workspace

- Existing start-review, outcome, notes, evidence, submit, escalation, and
  history actions remain backed by the existing API methods.
- Review submission requires local validation and explicit confirmation.
- Escalation requires a reason and explicit confirmation.
- Successful start, submission, and escalation actions show a success notice.
- Existing backend `409` lifecycle conflicts remain mapped to refresh/recovery
  copy.
- No draft-save UI was added because the backend exposes no draft operation.

### Evidence And History

- History evidence records now expose a safe source-link action only for returned
  HTTP(S) URLs.
- The device checks `Linking.canOpenURL` before opening the external source.
- Evidence remains immutable after submission because no backend edit/delete
  contract exists.

### Resources And Profile

- Official vaccine content continues to use the existing published,
  source-backed resource routes and honest empty state.
- Health Expert Resources includes procedural workflow guidance derived from the
  existing review lifecycle, without clinical claims or automated medical
  output.
- Health Expert Resources includes a clear unavailable state for support contact
  information because no approved support endpoint or contact content exists.
- Health Expert Resources includes static About VaxInsight copy using existing product
  positioning.
- Profile, password, email verification, logout, deletion, and theme settings
  continue to use the shared authenticated Account screen.

## Files Changed

- `mobile/src/components/BottomTabBar.js`
- `mobile/src/navigation/RootNavigator.js`
- `mobile/src/screens/HomeScreen.js`
- `mobile/src/screens/NarrativeListScreen.js`
- `mobile/src/screens/ResourcesScreen.js`
- `mobile/src/screens/ReviewDetailScreen.js`
- `mobile/src/screens/ReviewHistoryScreen.js`
- `mobile/src/screens/ReviewQueueScreen.js`
- `mobile/src/utils/reviewer.js`
- `mobile/src/i18n/translations.js`
- `mobile/tests/reviewer-contract.test.cjs`
- `reports/reviewer-mobile-screen-audit.md`

## Deliberate Backend Blockers

- Aggregate review-history activity is not claimed; the dashboard uses assigned
  record updates because no aggregate activity endpoint exists.
- Search, sorting, and server-side status filters remain unavailable because the
  assignment query accepts only `page` and `page_size`.
- Evidence editing remains unavailable because review evidence is immutable.
- Health Expert narrative revision history remains unavailable because the existing
  narrative history route is owner-scoped.
- Support contact content, notifications, and clinical Health Expert guidance require
  approved product and public-health contracts.

## Verification

- `node --test tests/*.test.cjs` from `mobile`: 15 passed.
- `npx expo export --platform android` from `mobile`: passed.
- `git diff --check`: passed; only existing line-ending warnings were reported by
  Git.
