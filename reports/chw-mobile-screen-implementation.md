# VaxInsight CHW Mobile Screen Implementation

Implementation date: 2026-11-11

## Scope

This report covers the CHW experience in the existing Expo React Native client.
It uses the current FastAPI/OpenAPI contract, preserves owner-scoped access, and
does not add participant data, reviewer-confidential data, fabricated content, or
unavailable AI output.

## Screen Classification

| Screen or workflow | Classification | Evidence and boundary |
|---|---|---|
| Home dashboard | IMPLEMENTED | `HomeScreen` loads `GET /api/v1/auth/me`, `GET /api/v1/dashboard/summary`, and published vaccine content. It renders CHW welcome copy, actual submitted/under-review/reviewed counts, recent owned narratives, loading, empty, refresh, and error states. |
| Main CHW navigation | IMPLEMENTED | `BottomTabBar` exposes Home, My Narratives, Resources, and Profile/Account for CHWs. Navigation remains discoverability only; backend authorization is authoritative. |
| My Narratives list | IMPLEMENTED | Uses owner-scoped `GET /api/v1/narratives`, status-only review metadata, pagination, refresh, empty, loading, and retry states. |
| Narrative composer | IMPLEMENTED | Uses `POST /api/v1/narratives` and `PATCH /api/v1/narratives/{id}` with client/server validation, rate limiting, recoverable errors, and preserved form content. |
| Narrative detail | IMPLEMENTED | Shows submitted/review status, version, timestamps, active-review edit lock, and owner-safe revision-history access. |
| Narrative history | IMPLEMENTED | Shows immutable owner-visible revisions only. Health Expert notes, outcomes, evidence, and internal review history are not exposed. |
| Questions list/composer/detail | IMPLEMENTED at the provisional boundary | Uses owner-scoped question APIs, localized validation and rate-limit handling, published professional responses, and an explicit unavailable-analysis state. |
| Official vaccine information | IMPLEMENTED at the API/UI boundary | Lists published source-attributed content with category, source, authority, publication date, summary, detail view, original source link, empty, loading, refresh, and error states. Source governance remains unresolved. |
| Resources hub | IMPLEMENTED | Provides official vaccine information, CHW question entry points, and a learning-resource section. Learning resources intentionally render an honest empty state until approved content exists. |
| Profile and account | IMPLEMENTED | Supports profile fields, role/status display, language, light/dark/system appearance, password change, email verification resend, logout, and confirmed account deletion. Email changes transition into an explicit verification route after server session invalidation. |
| Health Expert/admin screens | NOT CHW-ACCESSIBLE | Existing routes remain role/permission protected and are not presented as CHW capabilities. |
| Participant collection/provenance/consent | BLOCKED | No approved provenance, consent, withdrawal, retention, or participant-data contract exists. |
| Owner review feedback/outcomes | BLOCKED | No approved owner-safe review-feedback schema exists; only status metadata is shown. |
| AI/XAI analysis | BLOCKED | No approved provider, model, dataset, inference, confidence, explanation, or medical-advice contract exists. |

## Backend Contract Map

| Mobile capability | Endpoint | CHW permission/boundary |
|---|---|---|
| Personal dashboard | `GET /api/v1/dashboard/summary` | `narrative.read.own`; owner counts and recent records only |
| Narratives | `POST/GET/PATCH /api/v1/narratives` | `narrative.create`, `narrative.read.own`, `narrative.update.own`; SQL owner scope |
| Narrative history | `GET /api/v1/narratives/{id}/history` | Owner-only immutable revisions |
| Vaccine content | `GET /api/v1/vaccine-content`, `GET /api/v1/vaccine-content/{id}` | `vaccine_content.read`; published records only |
| Questions | `POST/GET /api/v1/questions`, `GET /api/v1/questions/{id}` | `question.create`, `question.read.own`; owner scope and rate limits |
| Analysis boundary | `POST /api/v1/questions/{id}/analysis` | Permission exists, provider is unavailable, client shows no fabricated result |
| Account | `GET/PATCH/DELETE /api/v1/auth/me` | Authenticated account only |

The owner-safe narrative response includes `review_status` only when an active
assignment exists. It excludes reviewer notes, outcomes, evidence, and review
history. The response contract is covered by OpenAPI and API tests.

## Component And Theme Coverage

- Shared primitives: `AppText`, `PrimaryButton`, `SecondaryButton`, `StatusPill`, `FullScreenLoader`, `EmptyState`, `ErrorState`, `InlineNotice`, `LanguageSelector`, and `BrandMark`.
- Shared request handling: `ApiError`, 15-second abort timeout, localized `400/401/403/404/408/409/422/429/503` mapping, and authenticated refresh/recovery.
- Theme source of truth: `mobile/src/theme/tokens.js` with warm light/dark backgrounds, orange accent, semantic text/button colors, rounded cards, shadows, DM Sans body text, and Space Grotesk headings.
- Device appearance: `userInterfaceStyle` is `automatic`; manual light, dark, and system preferences remain persisted.
- English and Kinyarwanda translations cover the new resources, article, narrative status, timeout, validation, and CHW hero copy.

## Verification

- `python -m pytest -q`: `268 passed`
- Focused CHW/backend/API isolation tests: `28 passed`
- `python -m ruff check backend tests`: passed
- `node --test mobile/tests/theme-preference.test.cjs mobile/tests/chw-contract.test.cjs`: `9 passed`
- `npx expo export --platform android --output-dir ...`: passed; Android bundle generated successfully
- `python -m alembic check`: passed; no new upgrade operations detected and no migration was added for the owner-safe response metadata

The mobile tests currently provide contract and preference coverage. Component,
navigation-rendering, API-mock, accessibility, and device-flow tests remain a
follow-up once the repository adopts a React Native test harness.

## Remaining Decisions And Risks

- Confirm that status-only owner review metadata is approved for production use.
- Define an approved source allow-list, publication workflow, withdrawal policy, and update cadence for public-health content.
- Define consent/provenance/retention requirements before adding participant context or community-collected narrative fields.
- Define an owner-safe feedback and clarification contract before exposing review outcomes.
- Add approved analysis infrastructure before implementing any AI/XAI display.
- Add mobile component/device tests and question pagination if larger histories are required.
