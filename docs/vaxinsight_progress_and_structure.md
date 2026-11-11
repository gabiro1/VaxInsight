# VaxInsight Progress Report and Project Structure

**Report date:** November 9, 2026  
**Project title:** A Mobile Application Based on Explainable Artificial Intelligence for Intelligent Health Communication on Vaccine-Related Narratives.

## Purpose

This report is a presentation-ready summary of the work completed in the VaxInsight repository. It explains what is implemented, where each feature is located, what was tested, and what remains unfinished or blocked.

The report is evidence-based. It does not claim that the mobile application,
dataset, machine-learning model, or SHAP explanations exist. The backend has a
provisional reviewer workflow, but it is not presented as formally approved for
production use.

## 1. Executive Summary

VaxInsight currently has a tested FastAPI and PostgreSQL backend foundation. The completed foundation includes secure authentication, invitation-based account management, role authorization, administrator operations, audit logs, health checks, rate limiting, OpenAPI documentation, and a neutral owner-scoped narrative record module.

The narrative module now supports validated submission, owner-only listing and retrieval, updates, immutable revision history, audit events, pagination, PostgreSQL row-lock concurrency protection, database integrity constraints, controlled persistence failures, and write rate limiting.

The mobile directory is empty and the authoritative dataset has not been received. No model, prediction endpoint, SHAP/LIME explanation service, notification module, or approved public-health content integration has been implemented. A minimal provisional human reviewer assignment and review workflow now exists in the backend; its formal qualification and governance decisions remain unresolved.

## 2. Progress At A Glance

| Area | Status | Evidence |
|---|---|---|
| Project structure and Python environment | Completed | `README.md`, `requirements.txt`, backend package structure |
| Authentication and account lifecycle | Completed | `backend/app/api/routes/auth.py`, `backend/app/services/auth.py`, authentication tests |
| Community self-registration | Completed | Full name, email, password confirmation, server-assigned `community_member`, email verification, and rate limiting |
| Fine-grained role and permission enforcement | Completed for current routes | `backend/app/core/permissions.py`, `backend/app/api/dependencies.py`, permission and administrator route tests |
| Administrator management | Completed | User directory, invitations, dashboard, audit search, account status and role management |
| Security hardening | Completed for current backend scope | JWT validation, Argon2, refresh rotation, rate limiting, headers, sanitized validation errors |
| Neutral narrative foundation | Partially complete by design | Narrative records and owner-only history exist; final workflow decisions remain open |
| Narrative concurrency and integrity hardening | Completed | PostgreSQL row-lock test, rollback test, unique revision constraint, integrity migration |
| Reviewer workflow | Provisional backend implementation | Assignment, active-reviewer access, structured review history, evidence, reassignment, revocation, and explicit escalation exist; formal qualification and production policy remain unresolved |
| In-app notifications | Not implemented | Notification channels and policy remain unresolved |
| Dataset assessment | Blocked | Dataset has not been received |
| Machine learning | Blocked | Task, labels, features, and target are unknown |
| SHAP/LIME explainability | Blocked | No model or approved task exists |
| Mobile application | Blocked by framework decision | `mobile/` is empty and framework is unconfirmed |
| Requirements documentation | Completed as a working baseline | `docs/requirements/` |

## 3. Completed Features

### 3.1 Authentication and Account Management

**What works:**

- Community self-registration with full name, email, password, and password confirmation.
- Public registration assigns only the server-controlled `community_member` role.
- Invitation-based onboarding for CHWs, reviewers, and administrators; staff roles are not selectable during public registration.
- Login with short-lived JWT access tokens.
- Rotating persisted refresh sessions.
- Logout and logout-all.
- Password change and password reset.
- Email verification and resend flow.
- Email change request and verification.
- Current profile and token-check endpoints.
- Account lifecycle states: pending, active, suspended, deactivated, and deleted.
- Argon2 password hashing.

**Main locations:**

- Routes: `backend/app/api/routes/auth.py`
- Authentication service: `backend/app/services/auth.py`
- Session service: `backend/app/services/sessions.py`
- Auth schemas: `backend/app/schemas/auth.py`
- User model and roles: `backend/app/models/user.py`
- JWT validation: `backend/app/core/tokens.py`
- Password hashing: `backend/app/core/security.py`
- Auth tests: `tests/test_auth_api.py`, `tests/test_auth_integration.py`, `tests/test_auth_service.py`, `tests/test_login_api.py`, `tests/test_login_service.py`, `tests/test_registration_api.py`, `tests/test_security.py`, `tests/test_tokens.py`

### 3.2 Role and Permission Management

**Implemented roles:**

- `community_member`
- `administrator`
- `chw`
- `reviewer`

**What works:**

- JWT authentication and current account status are checked server-side.
- A centralized permission catalogue and explicit mapping cover current account,
  invitation, audit, and owner-scoped narrative actions.
- Administrator routes use permission dependencies rather than broad role checks.
- Permission inspection endpoints expose the catalogue, role mapping, and a user's
  effective permissions without allowing permission editing or custom roles.
- Unknown permissions and reserved future permissions fail closed.
- Narrative action permissions remain subject to owner queries. Reviewers can access
  only active assignments through the separate review resource, while assignment
  managers receive metadata/history without unrestricted narrative content.
- Administrator self-deactivation and self-demotion are prevented.
- The last active administrator cannot be removed or demoted.
- Concurrent administrator changes preserve the last-active-administrator invariant.

**Main locations:**

- Role model: `backend/app/models/user.py`
- Permission catalogue and mapping: `backend/app/core/permissions.py`
- Authorization dependencies: `backend/app/api/dependencies.py`
- Account changes: `backend/app/services/auth.py`
- Role/status routes: `backend/app/api/routes/auth.py`
- Authorization tests: `tests/test_account_authorization_api.py`, `tests/test_admin_account_management_api.py`, `tests/test_admin_account_management.py`, `tests/test_admin_account_management_concurrency.py`
- Permission tests: `tests/test_permission_management.py`

### 3.3 Administrator Management

**What works:**

- Searchable, sortable, paginated user directory.
- User detail retrieval without passwords or token fields.
- Invitation listing, detail, filtering, and revocation.
- Administrator dashboard summary for users, invitations, roles, and sessions.
- Filtered and paginated audit-event search.
- Role and account-status management.

**Main locations:**

- Routes: `backend/app/api/routes/admin.py`
- User queries: `backend/app/services/admin_users.py`
- Invitation queries: `backend/app/services/admin_invitations.py`
- Dashboard aggregation: `backend/app/services/dashboard.py`
- Audit queries: `backend/app/services/audit.py`
- Admin schemas: `backend/app/schemas/admin_users.py`, `backend/app/schemas/admin_invitations.py`, `backend/app/schemas/dashboard.py`, `backend/app/schemas/audit.py`
- Admin tests: `tests/test_admin_user_directory.py`, `tests/test_admin_invitation_management.py`, `tests/test_admin_audit_events.py`, `tests/test_dashboard_api.py`

Administrators do not automatically receive access to research narratives. The
provisional `narrative.assign` permission manages assignment metadata and review
history but does not return narrative content through assignment-management
responses.

The current administrator permission-inspection endpoints are:

- `GET /api/v1/admin/permissions`
- `GET /api/v1/admin/roles`
- `GET /api/v1/admin/roles/{role}`
- `GET /api/v1/admin/users/{user_id}/permissions`

### 3.4 Audit Logging

**What works:**

- Account, login, session, invitation, role, and status actions create audit events.
- Administrator audit search is newest-first and paginated.
- Audit detail values are sanitized.
- Passwords, raw tokens, and authentication secrets are not returned.
- Narrative submission and successful updates create audit events.
- Narrative audit events are part of the same transaction as the narrative change.

**Main locations:**

- Audit model: `backend/app/models/auth.py`, class `AuditEvent`
- Audit service: `backend/app/services/audit.py`
- Administrator audit route: `backend/app/api/routes/admin.py`
- Audit tests: `tests/test_admin_audit_events.py`, `tests/test_narrative_api.py`

### 3.5 Security and Rate Limiting

**What works:**

- JWT issuer, audience, expiry, JTI, and token-type validation.
- Argon2 password hashing.
- Hashed opaque refresh, invitation, and reset tokens plus hashed email OTPs.
- Refresh rotation and replay detection.
- PostgreSQL-backed fixed-window rate limiting.
- Security headers.
- Production configuration checks.
- Sanitized validation errors.
- Narrative submission and update rate limiting through the existing rate-limit service.
- Narrative write limit configuration: `NARRATIVE_RATE_LIMIT=10` by default.

**Main locations:**

- Security settings: `backend/app/core/config.py`
- Example configuration: `.env.example`
- Rate limiting: `backend/app/services/rate_limit.py`
- Rate-limit cleanup: `backend/app/services/rate_limit_cleanup.py`
- Security middleware: `backend/app/main.py`
- Security tests: `tests/test_backend_security_audit.py`, `tests/test_rate_limit_cleanup.py`

The global rate-limit key construction, proxy handling, and cleanup behavior were not changed.

### 3.6 Health Checks and OpenAPI

**What works:**

- Application health endpoint.
- PostgreSQL database health endpoint.
- Generated OpenAPI document.
- Protected endpoint JWT security documentation.
- Documented request, response, and error schemas.
- Narrative routes included under the `Narratives` OpenAPI tag.

**Main locations:**

- FastAPI application: `backend/app/main.py`
- Health routes: `backend/app/api/routes/health.py`
- Documentation helpers: `backend/app/api/docs.py`
- OpenAPI tests: `tests/test_openapi_documentation.py`

### 3.7 Narrative Record Foundation

This is intentionally a neutral record-management layer. It does not classify narratives, fact-check them, generate predictions, or provide health conclusions.

**What works:**

- Authenticated account submits narrative text.
- Content is limited to 10,000 characters.
- Blank, whitespace-only, unexpected-field, and disallowed-control-character input is rejected.
- Narratives are owned by the submitting account.
- Owners can list only their own records.
- Owners can retrieve only their own records.
- Owners can update content without changing the neutral submitted state.
- Updates increment the version number.
- Every creation and update creates an immutable revision snapshot.
- History is returned in deterministic version order.
- Cross-user and administrator access return not found rather than exposing ownership.
- Pagination and date/status filters are available.
- Narrative write operations use the existing PostgreSQL rate limiter.

**API locations:**

- Routes: `backend/app/api/routes/narratives.py`
- Schemas: `backend/app/schemas/narrative.py`
- Service: `backend/app/services/narratives.py`
- Models: `backend/app/models/narrative.py`
- Tests: `tests/test_narrative_api.py`

**Available endpoints:**

| Method | Endpoint | Access |
|---|---|---|
| `POST` | `/api/v1/narratives` | Authenticated active account |
| `GET` | `/api/v1/narratives` | Authenticated active account; own records only |
| `GET` | `/api/v1/narratives/{narrative_id}` | Narrative owner only |
| `PATCH` | `/api/v1/narratives/{narrative_id}` | Narrative owner only |
| `GET` | `/api/v1/narratives/{narrative_id}/history` | Narrative owner only |

Narrative routes now require `narrative.create`, `narrative.read.own`, or
`narrative.update.own` before applying the existing owner query boundary.

### 3.8 Human Narrative Review Workflow

The backend now contains a minimal provisional human-review workflow. It remains
separate from the neutral narrative submission status and does not produce model
predictions, health conclusions, or automated escalation resolutions.

**What works:**

- Administrators with `narrative.assign` can assign, reassign, and revoke submitted narratives.
- Assignment targets must be active accounts with the `reviewer` role.
- A narrative has at most one active assignment, enforced by row locking and a partial unique index.
- Reviewers can list and retrieve only their active assigned narratives.
- Assignment managers can inspect assignment metadata and review history without narrative content.
- Reviewers can explicitly set `in_review` or `requires_escalation`.
- Submitted reviews are immutable API records with one of four neutral outcomes and optional evidence references.
- Review history, assignment changes, status changes, escalation, and submissions are audited without raw notes or evidence in audit details.
- Reassignment and revocation require a reason and preserve prior assignment history.

**Main locations:**

- Routes: `backend/app/api/routes/reviews.py`
- Schemas: `backend/app/schemas/review.py`
- Service: `backend/app/services/reviews.py`
- Models: `backend/app/models/review.py`
- Migration: `backend/migrations/versions/a7b8c9d0e1f2_add_narrative_review_workflow.py`
- Tests: `tests/test_narrative_review_workflow.py`

### 3.9 Narrative Concurrency and Data Integrity Hardening

**What was verified or added:**

- Existing `SELECT ... FOR UPDATE` row locking serializes concurrent updates.
- Revision numbers remain sequential under simultaneous PostgreSQL updates.
- The unique `(narrative_id, version)` constraint prevents duplicate revisions.
- Failed updates roll back narrative, revision, and audit changes together.
- Persistence failures return a generic `503` response.
- Database checks reject invalid content, invalid versions, and invalid revision actions.
- History endpoints are read-only through the API.

**Migration locations:**

- Narrative tables: `backend/migrations/versions/e5f6a7b8c9d0_add_narrative_records.py`
- Integrity constraints: `backend/migrations/versions/e6f7a8b9c0d1_harden_narrative_integrity.py`

### 3.10 Requirements Documentation

**Documents completed:**

- `docs/requirements/requirements_specification.md`
- `docs/requirements/supervisor_decision_register.md`
- `docs/requirements/requirements_traceability_matrix.md`
- `docs/requirements/implementation_gap_analysis.md`

These documents separate implemented, partially implemented, proposed, dataset-blocked, supervisor-blocked, and ethics/policy-blocked work.

## 4. Requirements Status By Labeled Area

The requirements baseline contains 38 functional requirements and 22 non-functional requirements.

Current overall classification:

| Classification | Count |
|---|---:|
| Implemented | 21 |
| Partially implemented | 9 |
| Proposed | 5 |
| Blocked | 25 |
| Total | 60 |

### Requirement Area 1: Authentication and Account Management

**Requirement IDs:** FR-001 to FR-008  
**Status:** FR-001 to FR-008 implemented for the current account-management scope.

The backend supports community self-registration, staff invitations, login, token rotation, logout, password flows, email verification, and current-profile operations. Community registration requires a full name and matching password confirmation, while staff roles remain invitation-only.

### Requirement Area 2: Role, Permission, and Account Audit

**Requirement IDs:** FR-009 to FR-012  
**Status:** Implemented for the current account-management scope.

Administrator status/role changes, server-side authorization, last-active-administrator protection, and account audit search are implemented and tested.

### Requirement Area 3: Narrative Submission and Ownership

**Requirement IDs:** FR-013 to FR-015  
**Status:** Partially implemented.

The neutral owner-scoped foundation is implemented. Final approved submitter roles, consent/provenance metadata, lifecycle states, organizational scope, reviewer access, and administrator research-data access are not approved or implemented.

### Requirement Area 4: Reviewer Workflow and Investigation

**Requirement IDs:** FR-016 to FR-019  
**Status:** Provisional backend implementation; formal supervisor and reviewer-qualification decisions remain unresolved.

The backend provides active assignment listing, assignment-level content access,
four structured review outcomes, immutable evidence/history, reassignment,
revocation, and explicit escalation status. It does not implement owner feedback,
correction, approval of model output, notifications, or automatic escalation
resolution, and the workflow is not production-approved.

### Requirement Area 5: Dataset and Analytical Data Management

**Requirement IDs:** FR-020 to FR-022  
**Status:** Blocked by dataset availability.

The dataset has not been received. No dataset schema, data dictionary, provenance record, assessment notebook, preprocessing pipeline, or lineage service exists.

### Requirement Area 6: Machine Learning Inference

**Requirement IDs:** FR-023 to FR-024  
**Status:** Blocked by dataset availability.

The ML task, target, features, labels, model, uncertainty semantics, and inference contract are unknown. No prediction endpoint exists.

### Requirement Area 7: Explainable AI

**Requirement IDs:** FR-025 to FR-027  
**Status:** FR-025 and FR-026 blocked by dataset/task; FR-027 awaits safety and supervisor confirmation.

SHAP and LIME appear in the dependency plan, but no model or explanation implementation exists. No feature contribution will be presented as causation, medical truth, or independent misinformation verification.

### Requirement Area 8: Visualization and Interpretation

**Requirement ID:** FR-028  
**Status:** Proposed and blocked by model/mobile decisions.

No prediction, explanation, or mobile visualization exists.

### Requirement Area 9: Health Communication and Educational Information

**Requirement IDs:** FR-029 to FR-030  
**Status:** Awaiting supervisor and public-health source approval.

No approved source registry, content store, or communication workflow exists. The application is not a medical diagnosis or treatment recommendation system.

### Requirement Area 10: Reviewer Feedback and Human Oversight

**Requirement IDs:** FR-031 to FR-032  
**Status:** Awaiting reviewer, ethics, and public-health decisions.

No reviewer feedback, human override, approval, or escalation endpoint exists.

### Requirement Area 11: Notifications

**Requirement ID:** FR-033  
**Status:** Awaiting confirmation.

No in-app notification table, route, delivery preference, or notification service exists. The existing email service is used for account actions only.

### Requirement Area 12: Administrator Dashboard and Audit Logs

**Requirement IDs:** FR-034 to FR-038  
**Status:** FR-034 to FR-037 implemented; FR-038 awaits explicit research-data permission approval.

The administrator can manage accounts, invitations, dashboard statistics, and audit records. Administrator research-narrative access is deliberately not granted.

### Requirement Area 13: Security and Privacy Non-Functional Requirements

**Requirement IDs:** NFR-001 to NFR-008  
**Status:** NFR-001 to NFR-005 implemented; NFR-006 partially implemented; NFR-007 proposed; NFR-008 blocked by ethics/policy approval.

The account/security foundation is strong. Narrative-specific privacy policy, consent, retention, and storage classification still require approval.

### Requirement Area 14: Performance, Availability, Usability, and Maintainability

**Requirement IDs:** NFR-009 to NFR-018  
**Status:** Mixed.

Health checks, API documentation, maintainable backend modules, data integrity for current entities, and account auditability exist. Approved performance targets, availability/recovery objectives, scalability assumptions, mobile usability, accessibility, and domain API contracts are not complete.

### Requirement Area 15: Explainability, Human Oversight, Language, and Retention

**Requirement IDs:** NFR-019 to NFR-022  
**Status:** Blocked.

These requirements depend on the dataset, ML task, ethics approval, language decisions, reviewer policy, data ownership, retention, deletion, and withdrawal procedures.

## 5. What Has Not Been Done Yet

### 5.1 Dataset and Data Work

- The authoritative dataset has not been received.
- Dataset provenance and permission have not been assessed.
- No dataset size, columns, labels, target, languages, or class distribution is known.
- No missing-value, duplicate, bias, representativeness, or privacy analysis exists.
- No preprocessing pipeline exists.

### 5.2 Machine Learning and Explainable AI

- The ML prediction task has not been selected.
- No model has been trained or evaluated.
- No inference endpoint exists.
- No prediction, confidence, or uncertainty field exists.
- SHAP has not been implemented.
- LIME has not been implemented or justified.
- No explanation quality, stability, calibration, bias, or subgroup evaluation exists.

### 5.3 Reviewer Workflow

- The provisional reviewer queue is limited to active assignments; no broader triage queue exists.
- Assignment, reassignment, revocation, status, review, evidence, and history endpoints exist.
- Owner feedback, correction, model approval, notification, and automatic escalation resolution do not exist.
- No formal reviewer qualification policy has been confirmed.

### 5.4 Notifications

- No notification model exists.
- No read/unread state exists.
- No in-app notification list exists.
- No notification preference or delivery policy exists.
- No push/SMS integration exists.

### 5.5 Mobile Application

- `mobile/` is empty.
- No mobile framework has been approved.
- No authentication screens exist.
- No navigation or API client exists.
- No Android build or mobile test exists.

### 5.6 Health Communication and Ethics

- No approved public-health source list exists.
- No health-information content registry exists.
- No consent process or participant information sheet exists.
- No retention, deletion, withdrawal, or correction policy exists.
- No ethics approval document was found.
- No incident-response process for harmful AI-assisted communication exists.

## 6. Project Structure and Where to Find Each Feature

### 6.1 Repository Structure

```text
vaccine-ai/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |   |-- routes/
|   |   |   |   |-- auth.py
|   |   |   |   |-- admin.py
|   |   |   |   |-- health.py
|   |   |   |   |-- narratives.py
|   |   |   |   |-- reviews.py
|   |   |   |-- dependencies.py
|   |   |   |-- docs.py
|   |   |-- core/
|   |   |   |-- account.py
|   |   |   |-- config.py
|   |   |   |-- security.py
|   |   |   |-- tokens.py
|   |   |   |-- opaque_tokens.py
|   |   |-- database/
|   |   |   |-- database.py
|   |   |   |-- dependencies.py
|   |   |-- models/
|   |   |   |-- user.py
|   |   |   |-- auth.py
|   |   |   |-- narrative.py
|   |   |   |-- review.py
|   |   |-- schemas/
|   |   |   |-- auth.py
|   |   |   |-- admin_users.py
|   |   |   |-- admin_invitations.py
|   |   |   |-- audit.py
|   |   |   |-- dashboard.py
|   |   |   |-- narrative.py
|   |   |   |-- review.py
|   |   |-- services/
|   |   |   |-- auth.py
|   |   |   |-- sessions.py
|   |   |   |-- email.py
|   |   |   |-- audit.py
|   |   |   |-- dashboard.py
|   |   |   |-- admin_users.py
|   |   |   |-- admin_invitations.py
|   |   |   |-- narratives.py
|   |   |   |-- reviews.py
|   |   |   |-- rate_limit.py
|   |   |   |-- rate_limit_cleanup.py
|   |   |-- main.py
|   |-- migrations/
|       |-- versions/
|           |-- account and security migrations
|           |-- e5f6a7b8c9d0_add_narrative_records.py
|           |-- e6f7a8b9c0d1_harden_narrative_integrity.py
|           |-- f1a2b3c4d5e6_add_community_registration_profile.py
|           |-- a7b8c9d0e1f2_add_narrative_review_workflow.py
|-- data/
|   |-- raw/
|   |-- processed/
|   |-- external/
|-- docs/
|   |-- requirements/
|   |-- vaxinsight_progress_and_structure.md
|-- models/
|-- mobile/
|-- notebooks/
|-- reports/
|-- tests/
|-- README.md
|-- requirements.txt
|-- .env.example
|-- alembic.ini
|-- pytest.ini
|-- ruff.toml
```

### 6.2 Feature Location Map

| Feature | Main file or directory | What to look for |
|---|---|---|
| FastAPI application setup | `backend/app/main.py` | App creation, router registration, middleware, exception handlers, OpenAPI tags |
| Authentication routes | `backend/app/api/routes/auth.py` | Registration, login, invitations, password, email, tokens, profile, account changes |
| Administrator routes | `backend/app/api/routes/admin.py` | Users, invitations, dashboard, audit events |
| Health routes | `backend/app/api/routes/health.py` | Application and PostgreSQL health endpoints |
| Narrative routes | `backend/app/api/routes/narratives.py` | Submit, list, retrieve, update, and history endpoints |
| Review routes | `backend/app/api/routes/reviews.py` | Assignment, reviewer access, status, review, evidence, history, reassignment, and revocation endpoints |
| Authentication dependencies | `backend/app/api/dependencies.py` | JWT validation, active-account checks, role checks |
| Security settings | `backend/app/core/config.py` | Database, JWT, SMTP, rate-limit, and production settings |
- Permission catalogue | `backend/app/core/permissions.py` | Permission definitions, implemented/future split, and role mapping |
| Password security | `backend/app/core/security.py` | Argon2 hashing and verification |
| JWT implementation | `backend/app/core/tokens.py` | Access-token creation and verification |
| Account model | `backend/app/models/user.py` | User roles and account statuses |
| Auth and audit models | `backend/app/models/auth.py` | Sessions, invitations, tokens, audit events, rate-limit buckets |
| Narrative models | `backend/app/models/narrative.py` | Narratives, revisions, statuses, integrity constraints |
| Review models | `backend/app/models/review.py` | Assignments, review statuses/outcomes, immutable reviews, evidence references |
| Auth schemas | `backend/app/schemas/auth.py` | Login, registration, invitations, passwords, roles, statuses |
- Permission schemas | `backend/app/schemas/permissions.py` | Permission catalogue, role mapping, and effective-permission responses |
| Admin schemas | `backend/app/schemas/admin_users.py`, `admin_invitations.py` | Admin filters and responses |
| Narrative schemas | `backend/app/schemas/narrative.py` | Content validation, filters, responses, history |
| Review schemas | `backend/app/schemas/review.py` | Assignment, status, outcome, evidence, and history contracts |
| Authentication service | `backend/app/services/auth.py` | Account lifecycle and administrator protection |
| Session service | `backend/app/services/sessions.py` | Refresh-token rotation and revocation |
| Narrative service | `backend/app/services/narratives.py` | Ownership queries, row locking, revisions, rollback handling |
| Review service | `backend/app/services/reviews.py` | Assignment lifecycle, active-reviewer scope, status transitions, reviews, evidence, and audit staging |
| Audit service | `backend/app/services/audit.py` | Audit creation, sanitization, search |
| Rate limiting | `backend/app/services/rate_limit.py` | Shared PostgreSQL fixed-window rate limiter |
| Rate-limit cleanup | `backend/app/services/rate_limit_cleanup.py` | Bounded cleanup of expired buckets |
| Email delivery | `backend/app/services/email.py` | Account invitation, verification, and reset email delivery |
| Database engine | `backend/app/database/database.py` | PostgreSQL engine, sessions, SQLAlchemy metadata |
| Narrative table migration | `backend/migrations/versions/e5f6a7b8c9d0_add_narrative_records.py` | Narrative and revision table creation |
| Narrative hardening migration | `backend/migrations/versions/e6f7a8b9c0d1_harden_narrative_integrity.py` | Content, version, and action checks |
| Community registration migration | `backend/migrations/versions/f1a2b3c4d5e6_add_community_registration_profile.py` | Full name storage, community role constraint, and profile integrity checks |
| Review workflow migration | `backend/migrations/versions/a7b8c9d0e1f2_add_narrative_review_workflow.py` | Assignment, review, evidence, status constraints, and active-assignment uniqueness |
| Authentication tests | `tests/test_auth_api.py`, `test_auth_integration.py`, `test_auth_service.py` | Authentication and account lifecycle verification |
| Administrator tests | `tests/test_admin_*.py`, `test_dashboard_api.py` | Admin authorization and management verification |
| Admin concurrency tests | `tests/test_admin_account_management_concurrency.py` | Actual PostgreSQL advisory-lock contention |
| Narrative security tests | `tests/test_narrative_api.py` | Ownership, concurrency, rollback, rate limits, constraints, history |
| Review workflow tests | `tests/test_narrative_review_workflow.py` | Assignment privacy, lifecycle, evidence, escalation, reassignment, revocation, and audit |
| OpenAPI tests | `tests/test_openapi_documentation.py` | Route, method, response, schema, and security documentation |
| Requirements specification | `docs/requirements/requirements_specification.md` | Full evidence-based requirements baseline |
| Decision register | `docs/requirements/supervisor_decision_register.md` | Unresolved supervisor and policy decisions |
| Traceability matrix | `docs/requirements/requirements_traceability_matrix.md` | Objectives to requirements and verification methods |
| Gap analysis | `docs/requirements/implementation_gap_analysis.md` | Implemented, partial, proposed, and blocked work |
| Dataset placeholders | `data/raw/`, `data/processed/`, `data/external/` | Empty placeholder directories; no dataset received |
| Model placeholders | `models/` | Empty model-artifact directory |
| Mobile project | `mobile/` | Empty; no framework approved |

## 7. Database Migration History

The migration chain is linear. The current PostgreSQL head is `a7b8c9d0e1f2`.

| Migration | Purpose |
|---|---|
| `4ab5cfdb6e2d` | Initial users table |
| `9c3f4f7a1b22` | Account lifecycle and authentication records |
| `a4e8b6c2d901` | Remove redundant token indexes |
| `b7d2e9f4c613` | Normalize user emails |
| `c1d2e3f4a5b6` | Audit-event ordering index |
| `d4e5f6a7b8c9` | Rate-limit expiration index |
| `e5f6a7b8c9d0` | Narrative and revision tables |
| `e6f7a8b9c0d1` | Narrative integrity constraints |
| `f1a2b3c4d5e6` | Community registration profile and role constraints |
| `a7b8c9d0e1f2` | Narrative review assignments, reviews, evidence, statuses, and history constraints |

## 8. Verification Evidence

### Focused Narrative Tests

```text
python -m pytest tests/test_narrative_api.py -q
19 passed
```

### Focused Review Workflow Tests

```text
python -m pytest tests/test_narrative_review_workflow.py -q
5 passed
```

### Permission Tests

```text
python -m pytest tests/test_permission_management.py -q
16 passed
```

### Repeated Concurrency Test

The same PostgreSQL concurrency test was executed ten times. Every run passed with one test passed and no failures.

### Full Test Suite

```text
python -m pytest tests/ -q -ra
228 passed
```

### Code Quality and Migration Checks

```text
python -m ruff check backend tests
All checks passed

python -m ruff format --check backend/app tests/test_permission_management.py tests/test_openapi_documentation.py tests/test_narrative_api.py
All touched files already formatted

The repository-wide formatting check still reports one pre-existing formatting
issue in `tests/test_auth_api.py`; that unrelated file was not changed.

python -m alembic check
No new upgrade operations detected
```

The review workflow migration was upgraded against PostgreSQL successfully and
the database is at `a7b8c9d0e1f2 (head)`.

## 9. Recommended Demonstration Sequence

### Demonstration 1: Explain the Project Boundary

Show the project title and the README architecture. Explain that the dataset-first principle prevents inventing the ML task, labels, or predictions.

### Demonstration 2: Show Secure Account Foundation

Open the authentication and administrator route files, then show the account/security tests. Point out invitation onboarding, JWT authentication, server-side roles, refresh rotation, audit events, and last-administrator protection.

### Demonstration 3: Show Narrative Management

Open `backend/app/api/routes/narratives.py` and demonstrate that the current neutral module can submit, list, update, retrieve, and inspect history for the owner only.

Emphasize that the module intentionally does not produce a prediction or fact-checking result.

### Demonstration 4: Show Human Review Boundaries

Open `backend/app/api/routes/reviews.py` and
`tests/test_narrative_review_workflow.py`. Demonstrate assignment-manager
metadata access, reviewer-only assigned content, explicit review status, neutral
outcomes, evidence references, immutable history, reassignment, revocation, and
escalation without automatic resolution.

### Demonstration 5: Show Reliability Hardening

Open `tests/test_narrative_api.py` and point to the concurrent update, rollback, rate-limit, inactive-account, cross-user, revision constraint, and history immutability tests.

### Demonstration 6: Show Database Evidence

Show the narrative and review migrations and the current Alembic head. Explain the unique revision constraint, active-assignment uniqueness, and content/version/action checks.

### Demonstration 7: Show What Remains

Open the requirements gap analysis and decision register. Explain that formal
reviewer qualification, production escalation policy, mobile framework, dataset,
ML task, XAI, public-health sources, consent, and retention policies require
evidence or supervisor approval.

## 10. Honest Readiness Assessment

The dataset-independent backend foundation is ready for the next phase of dataset acquisition and assessment. It is also ready to receive a future approved ML integration contract after the task, labels, input schema, and safety requirements are known.

The application is not ready for operational ML/XAI deployment or production
human-review use. The dataset, model task, formal reviewer qualification,
approved health sources, ethics controls, language scope, and mobile framework
remain unresolved. No prediction or explanation should be demonstrated as if it
were already implemented.
