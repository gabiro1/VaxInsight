# VaxInsight Implementation Gap Analysis

## Purpose

This analysis compares the requirements baseline in `requirements_specification.md` with the repository as inspected. It does not treat dependency declarations, empty directories, role enum values, or high-level architecture diagrams as implemented functionality.

The current implementation is an account-management and administrator foundation. It is not an implemented mobile application or end-to-end ML/XAI system.

The authorization layer now includes a static permission catalogue, explicit
role mappings, reusable permission dependencies, owner-scoped narrative checks,
and a provisional assignment/review permission boundary. Analysis, dataset, and
model permissions remain intentionally unavailable.

## Classification Summary

| Classification | Meaning | Count |
|---|---|---:|
| Implemented | Current code substantially satisfies the requirement. | 21 |
| Partially implemented | Some required behavior exists, but the requirement is incomplete or only account-level. | 9 |
| Proposed | Not implemented, but no specific external decision or missing dataset is the primary blocker. | 5 |
| Blocked | Not responsibly implementable until the stated dataset, supervisor, ethical, public-health, or policy dependency is resolved. | 25 |
| **Total** | Functional and non-functional requirements in the specification. | **60** |

| Requirement type | Total | Implemented | Partially implemented | Proposed | Blocked |
|---|---:|---:|---:|---:|---:|
| Functional requirements | 38 | 15 | 4 | 0 | 19 |
| Non-functional requirements | 22 | 5 | 6 | 5 | 6 |
| **Total** | **60** | **21** | **9** | **5** | **25** |

## Functional Requirement Gaps

| ID | Current implementation evidence | Classification | Gap, blocker, or next action |
|---|---|---|---|
| FR-001 | `POST /api/v1/auth/register` accepts full name, email, password, and password confirmation, assigns `community_member`, and leaves staff roles invitation-only. | Implemented | Preserve server-side role assignment, email verification, rate limiting, and confirmation validation. |
| FR-002 | Administrator invitation endpoint and invitation service exist; raw token is not returned. | Implemented | Continue integration verification with configured email delivery and operational procedures. |
| FR-003 | Invitation acceptance creates an active verified account and issues tokens. | Implemented | Maintain single-use, expiry, and revocation tests. |
| FR-004 | Login endpoint, JWT access token, refresh token issuance, account checks, and audit event exist. | Implemented | Keep contract and security tests current. |
| FR-005 | Refresh rotation, logout, logout-all, persisted sessions, and replay handling exist. | Implemented | Confirm final mobile token-storage behavior when the framework is selected. |
| FR-006 | Password change and reset request/confirm flows exist with generic reset response. | Implemented | Confirm user support and email-delivery operational process. |
| FR-007 | Email verification and generic resend endpoints/services exist. | Implemented | Confirm final email content and approved account-action domain. |
| FR-008 | Current profile, email-change request, and verification behavior exist. | Implemented | Confirm whether any additional profile fields are required; do not add them without a purpose. |
| FR-009 | Administrator status changes enforce self-protection, last-active-administrator protection, session revocation, and auditing. | Implemented | Preserve concurrent invariant tests. |
| FR-010 | Administrator role changes enforce self-protection, last-active-administrator protection, and auditing. | Implemented | Preserve concurrent invariant tests. |
| FR-011 | JWT validation, active-account checks, and server-side administrator authorization exist. | Implemented | Add resource-level rules when narrative/data resources are defined. |
| FR-012 | Account, invitation, login/session, and administrative events are stored and sanitized for administrator search. | Implemented | Extend only after the future domain audit event policy is approved. |
| FR-013 | Owner-scoped `POST /api/v1/narratives` validates content and stores an authenticated submitter; approved channels and consent/provenance fields are absent. | Partially implemented | Resolve submitter population, channel, schema, consent, and moderation decisions SD-001 to SD-004 before broadening submission. |
| FR-014 | `narratives` and `narrative_revisions` store a neutral submitted state, timestamps, version numbers, and immutable content revisions. | Partially implemented | Approve final lifecycle, provenance, consent, retention, deletion, and policy behavior before adding transitions. |
| FR-015 | Owner routes retain submitting-account scope; separate review routes provide active-assignment access to reviewers and metadata/history access to assignment managers. | Partially implemented | Confirm final CHW/reviewer/admin/direct-submit visibility, consent, and least-privilege policy. |
| FR-016 | Provisional assignment list/detail endpoints and `narrative_assignments` exist; the queue is limited to active assignments. | Blocked by supervisor decision | Confirm reviewer responsibility, qualification, ordering/filtering, and production assignment policy. |
| FR-017 | Assigned reviewer responses include narrative content; assignment managers receive metadata without content. | Blocked by supervisor decision | Approve permitted context, identity fields, and field-level minimization for each reviewer role. |
| FR-018 | Provisional review outcomes, notes, evidence references, and immutable history exist. | Blocked by supervisor decision | Confirm outcome definitions, reviewer qualifications, feedback scope, and audit requirements. |
| FR-019 | Provisional assignment/review statuses, reassignment, revocation, and explicit escalation transitions exist. | Blocked by supervisor decision | Approve lifecycle, escalation resolution, approval, correction, deletion, and notification transitions. |
| FR-020 | `data/` contains placeholders only; no approved dataset or intake service exists. | Blocked by dataset availability | Supply the authoritative dataset and provenance/permission package before intake implementation. |
| FR-021 | No data-assessment notebook, report, preprocessing pipeline, or schema exists. | Blocked by dataset availability | Assess the supplied dataset before selecting task, target, labels, or preprocessing. |
| FR-022 | No data dictionary, lineage store, version registry, or analytical-data service exists. | Blocked by dataset availability | Define data lineage after the dataset and permitted transformations are known. |
| FR-023 | No model artifact, training pipeline, input schema, or inference route exists; `MODEL_PATH` is only configuration. | Blocked by dataset availability | Confirm task and model after dataset assessment, then define a versioned inference contract. |
| FR-024 | No prediction, calibration, confidence, or uncertainty implementation exists. | Blocked by dataset availability | Select and validate uncertainty semantics for the approved task before UI/API design. |
| FR-025 | SHAP is named in README/dependencies, but no explanation service or model exists. | Blocked by dataset availability | Implement only after task, model, preprocessing, explanation method, and safety review are approved. |
| FR-026 | No global model behavior summary or analysis artifact exists. | Blocked by dataset availability | Determine whether global summaries are valid and safe for the selected model and population. |
| FR-027 | No explanation UI, API wording, or approved safety language exists. | Blocked by supervisor decision | Confirm explanation guardrails and distinguish contribution, causation, truth, and human judgment. |
| FR-028 | No mobile source, narrative visualization, prediction UI, or Android framework exists. | Blocked by dataset availability | Define model output first, then approve mobile framework/device/accessibility requirements. |
| FR-029 | No approved public-health source registry, content store, or educational information route exists. | Blocked by supervisor decision | Obtain source approval, content ownership, review cadence, and withdrawal policy. |
| FR-030 | README disclaimer exists, but no narrative communication workflow or UI separation exists. | Blocked by supervisor decision | Approve content policy, disclaimers, escalation, and separation of model output from verified information. |
| FR-031 | No reviewer feedback, correction, or concern entity/API exists. | Blocked by supervisor decision | Confirm feedback schema, ownership, access, and resolution process. |
| FR-032 | No human override, approval, escalation, or final-communication state exists. | Blocked by supervisor decision | Confirm qualified reviewer authority and ethics/public-health safeguards before implementation. |
| FR-033 | Email exists for account actions, but no narrative assignment/status notification exists. | Blocked by supervisor decision | Confirm channels, content minimization, opt-out, and notification lifecycle. |
| FR-034 | Administrator user directory supports filtering, sorting, pagination, and sanitized account fields. | Implemented | Continue access-control and API contract tests. |
| FR-035 | Administrator invitation list/detail/revoke endpoints expose lifecycle metadata without secrets. | Implemented | Continue testing around expiry, revocation, and email delivery. |
| FR-036 | Administrator dashboard returns user, invitation, role, and session aggregates. | Implemented | Do not describe it as a narrative or ML analytics dashboard until those modules exist. |
| FR-037 | Administrator audit search supports filters, pagination, newest-first ordering, and sanitized details. | Implemented | Define future domain event policy before extending audit scope. |
| FR-038 | Account and operational permissions are implemented separately from narrative access; assigned narrative, dataset, model-artifact, explanation, and participant-resource permissions remain unavailable. | Blocked by supervisor decision | Confirm administrator boundaries and implement separate resource-level permissions only after approval. |

## Non-Functional Requirement Gaps

| ID | Current implementation evidence | Classification | Gap, blocker, or next action |
|---|---|---|---|
| NFR-001 | JWT bearer validation and active-account checks exist in `backend/app/api/dependencies.py`. | Implemented | Preserve negative authentication tests for all future protected routes. |
| NFR-002 | Centralized server-side permission dependencies and narrative owner checks exist; current administrator routes use explicit permissions. | Implemented | Extend with assignment-level rules only after domain resources and policy are approved. |
| NFR-003 | Argon2 password hashing and password length validation exist. | Implemented | Keep hashing and secret-redaction tests. |
| NFR-004 | Rotating persisted refresh sessions, revocation, replay handling, and logout-all exist. | Implemented | Confirm secure storage and lifecycle behavior in the approved mobile client. |
| NFR-005 | Rate limits, security headers, sanitized validation errors, production settings, and CORS configuration exist. | Implemented | Review deployment configuration and apply the same protections to future domain routes. |
| NFR-006 | Account APIs select limited fields and audit details are sanitized; no narrative minimization policy exists. | Partially implemented | Define and test field-level minimization for narratives, datasets, explanations, logs, and notifications. |
| NFR-007 | Production configuration requires database SSL and SMTP TLS, but storage/mobile sensitive-data handling is not documented. | Proposed | Approve data classification and transport/storage controls before sensitive domain data is deployed. |
| NFR-008 | No consent, ethics, withdrawal, retention, or participant procedure exists. | Blocked by ethical or policy approval | Obtain applicable ethics/institutional approval and attach the approved procedures. |
| NFR-009 | No approved performance or resource targets, mobile client, or representative deployment profile exists. | Proposed | Approve measurable targets and test environment before performance claims. |
| NFR-010 | Liveness and PostgreSQL health endpoints plus controlled exception handlers exist; no availability target or recovery procedure exists. | Partially implemented | Define availability, backup, recovery, monitoring, and incident targets. |
| NFR-011 | No scale assumptions, capacity plan, load test, or narrative/inference workload exists. | Proposed | Define expected users, records, inference volume, retention, and scale tests. |
| NFR-012 | No mobile UX, task study, representative-user test, or comprehension evaluation exists. | Proposed | Conduct approved usability work with the actual user population after scope decisions. |
| NFR-013 | No mobile client, accessibility standard, or Android screen exists. | Proposed | Select the framework and accessibility baseline, then test core journeys. |
| NFR-014 | Backend modules, schemas, migrations, tests, OpenAPI documentation, and environment configuration provide a maintainable foundation; mobile/ML boundaries are absent. | Partially implemented | Add versioned domain interfaces, mobile source, ML pipeline, and reproducible evaluation artifacts. |
| NFR-015 | `README.md` explicitly says the mobile framework is to be confirmed; `mobile/` is empty. | Blocked by supervisor decision | Approve framework, Android range, device profile, online/offline behavior, and release matrix. |
| NFR-016 | FastAPI OpenAPI, request/response schemas, controlled errors, and current route contracts exist; domain contracts do not. | Partially implemented | Version and test narrative, review, ML, XAI, communication, and mobile integration contracts. |
| NFR-017 | Account models, constraints, migrations, transactions, last-administrator locks, and tests exist; no domain data rules exist. | Partially implemented | Define and test narrative, dataset, label, model, and retention integrity rules. |
| NFR-018 | Account, administrator, narrative, assignment, review status, escalation, and review-submission events are audited with sanitized details; model lifecycle events are absent. | Partially implemented | Approve the final event taxonomy and retain the no-secrets/no-unnecessary-content boundary. |
| NFR-019 | SHAP is only a planned dependency/name; no model, explanation, evaluation, or explanation API exists. | Blocked by dataset availability | Assess data, select task/model, evaluate explanation quality, and approve transparent wording. |
| NFR-020 | README provides a research/decision-support disclaimer and the backend has a provisional human-review/escalation workflow, but no formal qualification, incident plan, or operational AI exists. | Blocked by ethical or policy approval | Approve reviewer qualifications, safe-use controls, incident handling, escalation resolution, and release governance. |
| NFR-021 | Roles contain CHW/reviewer labels, but no supported language list or language pipeline exists. | Blocked by supervisor decision | Decide language scope from the approved population/dataset and perform linguistic validation. |
| NFR-022 | Current migrations cover account data; no retention/deletion/withdrawal policy exists for account or future research data. | Blocked by ethical or policy approval | Define data-class ownership, retention, deletion, correction, withdrawal, and audit exceptions. |

## Major Implementation Gaps

### 1. No Mobile Application

The `mobile/` directory is empty. There is no approved framework, Android target, screen, client token storage, offline behavior, accessibility baseline, or device test matrix. The backend's reference to a mobile audience does not establish a mobile implementation.

### 2. Partial Narrative Domain

The neutral foundation now includes owner-scoped narrative models, migrations, validated submission/update/list/detail routes, pagination, and immutable content revision history. A separate provisional review module adds assignment, active-reviewer access, review outcomes, evidence, history, reassignment, revocation, and explicit escalation status. Approved submission channels, consent/provenance metadata, organizational scope, administrator research-data access, formal reviewer qualification, and final retention/deletion policy remain unresolved.

### 3. Dataset and ML Work Is Blocked

No dataset, data dictionary, model artifact, notebook, preprocessing pipeline, target, label, feature schema, inference route, or model evaluation exists. Dataset assessment must remain explicitly blocked until the authoritative dataset and permission package are supplied.

### 4. No Explainability Implementation

SHAP and LIME appear in `requirements.txt`, and SHAP appears in the README architecture, but no code imports or invokes them. No explanation contract, explanation quality evaluation, user wording, or explanation safety review exists.

### 5. No Approved Health-Information Workflow

There is no public-health source registry, content approval process, health education content store, reviewer approval policy, or update/withdrawal process. The system must not manufacture health guidance from model output.

### 6. Governance and Ethics Evidence Is Missing

No proposal, supervisor requirements, ethics approval, consent process, data-management plan, retention policy, withdrawal procedure, incident process, or named decision owners were found. These gaps prevent responsible collection and use of participant or community narratives.

### 7. Administrator Scope Is Incomplete by Design

The administrator API currently manages accounts, invitations, audit events, and account/session statistics. It does not provide narrative or ML analytics. Administrator access to research data must be explicitly approved and separately authorized rather than inherited from the administrator role.

## Requirements That Prevent Further Implementation

Further workflow and domain-scope expansion should pause until the following are resolved:

- Primary users, access model, direct submission, narrative workflow, and reviewer authority: SD-001 to SD-005.
- Dataset delivery, permissions, data assessment, ML task, and target: SD-006 and SD-007.
- Language scope: SD-008.
- Approved public-health sources and communication policy: SD-009.
- Administrator resource boundaries: SD-011.
- Ethics, consent, ownership, retention, deletion, and withdrawal: SD-012 and SD-015.
- Mobile framework and Android target: SD-013.
- Evaluation criteria, explanation wording, uncertainty, override, and escalation: SD-014 and SD-016.

## Recommended Next Sequence After Approval

1. Add the missing proposal, 60-day plan, supervisor requirements, ethics/data-management documents, and decision records to the evidence set.
2. Obtain the authoritative dataset and complete the dataset assessment without selecting an ML task in advance.
3. Confirm stakeholder roles, narrative workflow, data permissions, languages, public-health sources, and mobile framework.
4. Produce approved domain/data schemas and threat/privacy analysis before adding migrations.
5. Define and test narrative/reviewer API contracts and resource-level permissions.
6. Select and evaluate the ML task/model; then design model-linked SHAP/XAI outputs and human-review safeguards.
7. Implement the mobile client only after the framework, Android profile, accessibility baseline, and API contracts are approved.
8. Evaluate the integrated system using supervisor-approved technical, usability, safety, privacy, and research criteria.
