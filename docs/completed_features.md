# Vaccine AI Completed Features

## Overview

Vaccine AI currently provides a tested FastAPI and PostgreSQL backend foundation for secure account management, administrator operations, and controlled vaccine-related narrative records. The completed features below are implemented in the repository and supported by automated tests.

## Completed Features

### 1. Backend Foundation

- FastAPI application with modular routes, services, schemas, and database models.
- PostgreSQL persistence through SQLAlchemy and Alembic migrations.
- Environment-based configuration for database, authentication, email, and rate limiting.
- Command-line operations for creating the first administrator and cleaning expired rate-limit records.

### 2. Registration and Account Lifecycle

- Community self-registration using full name, email, password, and password confirmation.
- Public registration assigns only the `community_member` role.
- Invitation-based onboarding for `chw`, `reviewer`, and `administrator` accounts.
- Email verification and verification-email resend flow.
- Email-change request and verification flow.
- Password change and password reset flows.
- Account states including pending, active, suspended, deactivated, and deleted.
- Current-profile and token-check endpoints.
- Authenticated self-service hard deletion removes dependent account, narrative,
  review, session, token, invitation, and audit rows in one transaction.
- Deleted email addresses can be used for a new registration; the last active
  administrator cannot delete their account.

### 3. Authentication and Session Security

- Argon2 password hashing.
- Short-lived JWT access tokens with issuer, audience, expiry, JTI, and token-type validation.
- Persisted refresh sessions with refresh-token rotation.
- Refresh-token replay detection and session revocation.
- Individual logout and logout-all functionality.
- Hashed opaque invitation, reset, verification, and refresh tokens.

### 4. Role and Permission Authorization

- Server-side authorization for protected endpoints.
- Implemented roles: `community_member`, `chw`, `reviewer`, and `administrator`.
- Account-status checks prevent inactive accounts from using protected routes.
- Current role-sensitive routes are protected by centralized permission dependencies.
- The permission catalogue and explicit role-to-permission mapping are static and
  fail closed for unknown or future permissions.
- Permission inspection endpoints expose definitions, role mappings, and effective
  user permissions without allowing custom role or permission editing.
- Narrative permissions are combined with owner-scoped database queries.
- Administrators cannot deactivate or demote themselves.
- The last active administrator cannot be removed or demoted.
- Concurrent administrator changes preserve the last-active-administrator safety rule.

Assigned narrative access and human review permissions are implemented for the
provisional workflow. Analysis, dataset, and model permissions remain reserved
and unusable because those workflows do not exist yet.

### 5. Administrator Management

- Searchable, sortable, paginated administrator user directory.
- Sanitized user-detail responses that exclude passwords and token fields.
- Invitation listing, filtering, detail retrieval, and revocation.
- Account role and status management.
- Dashboard summary for users, invitations, roles, and active sessions.
- Paginated, filtered audit-event search.

### 6. Audit Logging and Privacy Controls

- Audit events for account, login, session, invitation, role, and status actions.
- Audit events for narrative creation and successful updates.
- Audit events for assignment, review status, escalation, and review submission actions.
- Newest-first and paginated audit history.
- Sanitized audit details.
- Passwords, raw tokens, and authentication secrets are not exposed in API responses.
- Narrative changes and their audit events are persisted in the same transaction.

### 7. Rate Limiting and Security Hardening

- PostgreSQL-backed fixed-window rate limiting.
- Rate limiting for narrative creation and updates.
- Bounded cleanup for expired rate-limit buckets.
- Security headers and controlled exception handling.
- Sanitized validation errors.
- Production configuration checks, including secure database and SMTP settings.

### 8. Narrative Record Management

The current narrative module is intentionally a neutral record-management foundation. It does not classify narratives, fact-check them, generate predictions, or provide medical conclusions.

- Authenticated users can submit narrative text.
- Narrative content is validated and limited to 10,000 characters.
- Blank, whitespace-only, unexpected-field, and disallowed-control-character input is rejected.
- Narratives are owned by the submitting account.
- Users can list, retrieve, update, and view history for their own narratives only.
- Cross-user and administrator access does not reveal narrative ownership.
- Updates increment the narrative version.
- Every creation and update stores an immutable revision snapshot.
- Pagination and date/status filters are supported.
- Available endpoints:

| Method | Endpoint | Access |
|---|---|---|
| `POST` | `/api/v1/narratives` | Authenticated active account |
| `GET` | `/api/v1/narratives` | Authenticated account; own records only |
| `GET` | `/api/v1/narratives/{narrative_id}` | Narrative owner only |
| `PATCH` | `/api/v1/narratives/{narrative_id}` | Narrative owner only |
| `GET` | `/api/v1/narratives/{narrative_id}/history` | Narrative owner only |

### 9. Human Narrative Review Workflow

The review module is a minimal human-review workflow. It does not classify
narratives, produce model output, or provide medical conclusions.

- Administrators with `narrative.assign` can assign, reassign, and revoke review assignments.
- Assignment targets must be active accounts with the `reviewer` role.
- At most one assignment is active for a narrative; prior assignments remain in history.
- Health Experts can list and retrieve only their active assignments.
- Assignment managers receive assignment metadata and review history without narrative content.
- Health Experts can explicitly move an assignment into review or escalation.
- Submitted reviews are append-only and support four provisional neutral outcomes.
- Evidence references store source title, publisher, URL, publication date, access time, and relevance.
- Narrative owners cannot access internal review notes or review history.
- Reassignment and revocation require reasons and preserve prior records.
- Review assignment, status, escalation, submission, and outcome actions are audited without raw notes or evidence in audit details.

**Review endpoints:**

| Method | Endpoint | Access |
|---|---|---|
| `POST` | `/api/v1/narratives/{narrative_id}/assignment` | Assignment manager |
| `POST` | `/api/v1/narratives/{narrative_id}/assignment/reassign` | Assignment manager |
| `POST` | `/api/v1/narratives/{narrative_id}/assignment/revoke` | Assignment manager |
| `GET` | `/api/v1/reviews/assignments` | Active reviewer or assignment manager |
| `GET` | `/api/v1/reviews/assignments/{assignment_id}` | Assigned reviewer or assignment manager |
| `GET` | `/api/v1/reviews/assignments/{assignment_id}/status` | Assigned reviewer or assignment manager |
| `POST` | `/api/v1/reviews/assignments/{assignment_id}/status` | Assigned reviewer or assignment manager |
| `POST` | `/api/v1/reviews/assignments/{assignment_id}/review` | Assigned reviewer |
| `GET` | `/api/v1/reviews/assignments/{assignment_id}/history` | Assigned reviewer or assignment manager |

### 10. Narrative Data Integrity and Reliability

- PostgreSQL row locking serializes concurrent narrative updates.
- Revision numbers remain sequential during simultaneous updates.
- A unique `(narrative_id, version)` constraint prevents duplicate revisions.
- Failed updates roll back narrative, revision, and audit changes together.
- Persistence failures return a controlled generic `503` response.
- Database constraints reject invalid narrative content, versions, and revision actions.
- Narrative history is read-only through the API.

### 11. Health Checks and API Documentation

- Application liveness health endpoint.
- PostgreSQL database health endpoint.
- Generated OpenAPI documentation.
- JWT security requirements documented for protected endpoints.
- Request, response, and error schemas documented.
- Narrative routes grouped under the `Narratives` OpenAPI tag.
- Review routes grouped under the `Narrative Reviews` OpenAPI tag.

## Verification Evidence

The documented verification results include:

- Full test suite: **228 tests passed**.
- Narrative API tests: **19 tests passed**.
- Permission management tests: **16 tests passed**.
- Narrative review workflow tests: **5 tests passed**.
- Ruff lint checks passed.
- Ruff formatting checks passed for all files touched by this change. The
  repository-wide check still reports one pre-existing issue in
  `tests/test_auth_api.py`.
- Alembic migration check reported no pending upgrade operations.
- Review migration `a7b8c9d0e1f2` was upgraded against PostgreSQL and the database is at head.

## Current System Boundary

The following features are not yet implemented and should not be presented as completed:

- Authoritative dataset intake and assessment.
- Machine-learning model training, inference, and evaluation.
- SHAP/LIME explainability services.
- Formal supervisor, privacy, and ethics confirmation for the provisional Health Expert workflow.
- Health Expert qualification policy, owner feedback, correction, and production escalation resolution.
- Approved public-health content and source registry.
- In-app notifications.
- Mobile application and Android client.

The system is currently a secure, tested backend foundation ready for the next phase after the dataset, workflow, ethical, public-health, and mobile decisions are approved.

## Key Implementation Locations

| Area | Location |
|---|---|
| Application setup and middleware | `backend/app/main.py` |
| Authentication routes | `backend/app/api/routes/auth.py` |
| Administrator routes | `backend/app/api/routes/admin.py` |
| Narrative routes | `backend/app/api/routes/narratives.py` |
| Review routes | `backend/app/api/routes/reviews.py` |
| Health routes | `backend/app/api/routes/health.py` |
| Permission catalogue and authorization | `backend/app/core/permissions.py`, `backend/app/api/dependencies.py` |
| Authentication and account service | `backend/app/services/auth.py` |
| Session management | `backend/app/services/sessions.py` |
| Narrative service | `backend/app/services/narratives.py` |
| Audit service | `backend/app/services/audit.py` |
| Rate limiting | `backend/app/services/rate_limit.py` |
| User and role models | `backend/app/models/user.py` |
| Narrative models | `backend/app/models/narrative.py` |
| Review models | `backend/app/models/review.py` |
| Review schemas | `backend/app/schemas/review.py` |
| Review service | `backend/app/services/reviews.py` |
| Automated tests | `tests/` |
