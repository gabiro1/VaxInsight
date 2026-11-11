# VaxInsight Requirements Specification

## Document Status

This is an evidence-based requirements baseline for the project titled **A Mobile Application Based on Explainable Artificial Intelligence for Intelligent Health Communication on Vaccine-Related Narratives**. It is a working specification, not a statement that all proposed functionality has been approved.

The repository was inspected before this document was written. The only substantive project document currently available is `README.md`. The referenced Secure AI Labs 60-day implementation plan, research proposal, supervisor-provided requirements, research report, dataset assessment, and detailed architecture document were not found. Those missing sources are recorded as limitations and decision dependencies below.

The authoritative dataset has not been received. No dataset attributes, labels, target variable, language distribution, class distribution, provenance, or model task are assumed in this document.

## Evidence Register

| ID | Evidence | Supported facts |
|---|---|---|
| E-001 | `README.md`, lines 3-16 | Project title, mobile/XAI/ML intent, and vaccine-related health communication purpose. |
| E-002 | `README.md`, lines 18-42 | Proposed technologies and high-level pipeline: dataset, assessment/preprocessing, ML model, SHAP, FastAPI, and mobile application. |
| E-003 | `README.md`, lines 55-77 | Dataset-first principle and development checklist. Requirements analysis, dataset assessment, ML task confirmation, model development, SHAP, mobile, integration, and final documentation are marked incomplete. |
| E-004 | `README.md`, lines 79-122 | Invitation-based account foundation, approved personnel, security controls, and research/decision-support disclaimer. |
| E-005 | `backend/app/main.py` | FastAPI application, health/auth/admin routers, OpenAPI configuration, security headers, CORS configuration, and rate-limit error handling. |
| E-006 | `backend/app/api/routes/auth.py` | Registration, login, invitations, invitation acceptance, refresh, logout, password, email verification, profile, token check, status, and role endpoints. |
| E-007 | `backend/app/api/routes/admin.py` | Administrator-only user directory, invitation management, dashboard summary, and audit-event search endpoints. |
| E-008 | `backend/app/models/user.py` | Implemented roles: `chw`, `reviewer`, and `administrator`; account lifecycle statuses. |
| E-009 | `backend/app/models/auth.py` | Implemented invitation, refresh-session, password-reset, email-verification, audit-event, and rate-limit entities. |
| E-010 | `backend/app/api/dependencies.py` | JWT bearer authentication, active-account checks, and server-side role authorization. |
| E-011 | `backend/app/services/auth.py` and `backend/app/services/sessions.py` | Invitation onboarding, password/email flows, account changes, session rotation/revocation, audit events, and last-administrator protection. |
| E-012 | `backend/app/services/admin_users.py`, `admin_invitations.py`, `audit.py`, and `dashboard.py` | Database-side account/invitation queries, sanitized audit details, and operational account statistics. |
| E-013 | `backend/app/core/config.py`, `backend/app/database/database.py`, and `.env.example` | PostgreSQL configuration, production security validation, token lifetimes, rate limits, SMTP settings, and a placeholder `MODEL_PATH`; no model integration. |
| E-014 | `requirements.txt` | Planned data/ML/XAI dependencies, including Pandas, scikit-learn, XGBoost, SHAP, LIME, and joblib. Dependencies are not evidence that those capabilities are implemented. |
| E-015 | `data/*/.gitkeep`, `models/.gitkeep`, and empty `mobile/` and `notebooks/` folders; source-document inspection before this deliverable | No dataset, trained model, notebook, mobile source, or dataset-assessment artifact is present. The requested requirements documents were created after the inspection. |
| E-016 | `tests/` and `pytest.ini` | Automated coverage exists for the implemented authentication, account administration, security, health, OpenAPI, and rate-limit foundation. An `integration` marker identifies tests requiring PostgreSQL. |
| E-017 | Repository-wide inspection | No Secure AI Labs 60-day implementation plan, proposal, supervisor requirements, research report, dataset-assessment report, or detailed architecture document was found. |
| E-018 | This requirements brief | The requested stakeholder, ethical, privacy, mobile, AI, traceability, and supervisor-decision coverage is treated as a requirements input, not as evidence that the corresponding feature exists. |

## Status and Priority Conventions

Priority describes the proposed importance of a requirement and does not mean that a supervisor has approved it.

| Priority | Meaning |
|---|---|
| Must | Required for the defined scope if the related scope decision is approved. |
| Should | Important, but can follow the first approved baseline. |
| Could | Useful optional capability that should not block the baseline. |

| Status | Meaning |
|---|---|
| Implemented | Evidence exists in the current implementation and the requirement is substantially satisfied. |
| Partially implemented | Some behavior exists, but a stated condition, interface, or domain capability is incomplete. |
| Proposed | A documented requirement for future work; it is not implemented. |
| Awaiting confirmation | The requirement depends on a supervisor, public-health, ethics, or product decision and must not be implemented as an assumption. |

# A. Project Overview

## Problem

Vaccine-related narratives require health communication that is understandable, accountable, and appropriate for the people using it. The repository describes a research and software project intended to interpret vaccine-related data through machine learning and explainability techniques (E-001). The available evidence does not define a specific misinformation category, prediction target, dataset, language, or clinical/public-health workflow. The problem is therefore stated at the communication and decision-support level, not as a confirmed disease-diagnosis or misinformation-verification task.

## Objectives

The requirements baseline supports these objectives:

1. Provide a controlled foundation for authorized personnel to use a future VaxInsight mobile application.
2. Support a clearly governed workflow for submitting, reviewing, interpreting, and communicating vaccine-related narratives.
3. Assess the authoritative dataset before selecting a machine-learning task, target variable, model, or explanation method.
4. Present model outputs and explanations transparently, with human oversight and clear separation from verified health information.
5. Protect account, participant, and health-related information through least privilege, privacy controls, auditability, and approved ethical procedures.
6. Provide administrators with the operational controls needed to manage authorized accounts without granting unapproved access to narrative or research data.

The first objective is partially supported by the current backend. Objectives 2-5 remain largely proposed or blocked by missing decisions, data, and policy approvals. Objective 6 is supported for account operations only.

## Intended Operating Context in Rwanda

The requested project context is Rwanda, and the stakeholder brief identifies CHWs, qualified reviewers, public-health stakeholders, community members, and language experts as relevant parties. The repository contains no Rwanda-specific public-health source list, approved language list, connectivity requirement, device inventory, policy reference, or ethics approval. Accordingly, this specification does not assume a particular national health workflow, language, health authority, or deployment setting. Those facts must be supplied or confirmed before implementation.

The system should be designed for authorized health communication work in the approved Rwandan context, with consideration for the actual devices, connectivity, literacy, language, and public-health channels identified by the supervisor and relevant health stakeholders. These are requirements to investigate, not findings about the current system.

## Proposed Solution

The proposed solution is a mobile application backed by FastAPI. It would accept or present vaccine-related narratives, invoke a model selected after dataset assessment, attach explainability outputs, and support human-reviewed health communication. The current backend provides an account and administration foundation: invitation-based onboarding, JWT access tokens, rotating refresh sessions, account lifecycle controls, role authorization, audit events, health checks, and administrator views (E-004 to E-012).

The proposed narrative, review, dataset, ML, XAI, visualization, mobile, notification, and approved-health-information capabilities are not present in the repository. The requirements below keep them separate from implemented account functionality.

## Scope

The current and proposed scope includes:

- Authorized user authentication and account lifecycle management.
- Roles for CHWs, reviewers, and administrators.
- Narrative intake and review, subject to supervisor confirmation.
- Dataset assessment and governed data management after the dataset is supplied.
- Model inference and explainability after the ML task is confirmed.
- Human oversight and transparent communication of model outputs.
- A mobile client using the FastAPI backend, after the mobile framework is approved.
- Administrator account, audit, and operational controls.

The scope does not include an independently diagnosing medical system, autonomous treatment advice, a claim that the model can establish medical truth, or a claim that SHAP can verify misinformation. The repository also does not support a claim that the mobile application is implemented.

## Explicit Limitations

- The dataset has not been received or assessed.
- The ML prediction task, target variable, labels, features, and evaluation method are unknown.
- A neutral narrative API and provisional reviewer workflow exist; no ML inference endpoint, SHAP/LIME service, mobile source, or approved health-information integration exists in the repository.
- The final mobile framework is explicitly marked as to be confirmed in `README.md`.
- Community self-registration is enabled by default and creates only a `community_member`; CHW, reviewer, and administrator accounts remain invitation-only.
- The current administrator dashboard covers users, invitations, and refresh sessions, not narrative or model analytics.
- Ethical approval, consent language, data ownership, retention, deletion, and withdrawal procedures are not documented.

## Relationship Between Components

- **Mobile application:** Proposed user-facing client for authorized users. The `mobile/` directory is empty and the framework is unconfirmed.
- **FastAPI backend:** Implemented account/security/admin foundation, neutral narrative records, and a provisional review integration boundary; ML, XAI, and communication services remain proposed.
- **PostgreSQL:** Current persistence layer for account, invitation, session, audit, rate-limit, narrative, assignment, review, and evidence entities. Dataset schemas must not be invented before scope and data decisions.
- **Machine Learning:** Proposed component that would perform a confirmed task on approved data. No model or inference code exists.
- **Explainable AI:** Proposed component that would explain a model output, not determine whether a health statement is medically true. SHAP is named by the README; LIME is optional in the dependency plan and requires justification.
- **Human reviewers:** Provisional assigned-review functions exist for structured review, evidence, history, and explicit escalation. Qualified oversight for interpretation, correction, and health communication remains subject to approval.

# B. Stakeholder Identification

| Stakeholder | Interests | Expected interaction | Responsibilities | Application account? | Unresolved questions |
|---|---|---|---|---|---|
| Community Health Workers (CHWs) | Usable, understandable, locally appropriate communication support for vaccine-related narratives. | They may submit owner-scoped narratives; assigned-review access is limited to the reviewer role. Approved explanations and educational information do not exist yet. | Follow approved communication and privacy procedures; avoid treating model output as medical authority. | Likely yes if they are operational users; invitation-based onboarding supports the role. Confirmation required. | Are CHWs primary users? Can they submit, view, annotate, or only consume approved content? What data may they see? |
| Health reviewers or qualified health professionals | Human review, safe interpretation, correction, and escalation of narrative and model output. | Provisional assignment, inspection, structured assessment, evidence, history, and escalation endpoints exist. Feedback, approval, and model-output review remain absent. | Apply approved health criteria, document reasoning, identify unsafe or uncertain communication, and maintain confidentiality. | Likely yes; `reviewer` has provisional domain permissions subject to qualification confirmation. | What qualification is required? Who can approve a communication? Is reviewer approval mandatory? |
| System administrators | Secure operation of accounts, invitations, roles, status, audit records, and operational statistics. | Current administrator API supports account directory, invitations, dashboard summary, and audit search. | Manage authorized accounts, preserve least privilege, review operational audit records, and avoid unapproved research-data access. | Yes; administrator role and server-side authorization are implemented. | Can administrators access raw narratives, labels, model outputs, or participant identifiers? |
| Public-health stakeholders | Alignment with approved health messages, policy, sources, and evaluation priorities in Rwanda. | Governance, source approval, review of communication content, and evaluation; no current application endpoint is assigned. | Identify authoritative sources and approve communication policy. | Not automatically. A governance stakeholder is not assumed to be an application role. | Which institution or representative approves sources and content? |
| Research participants and community members | Confidential participation, understandable communication, and control over their data where applicable. | They may be narrative subjects or possible submitters; direct submission is not implemented and must be decided. | Provide informed consent where required and communicate only what the approved study permits. | Not automatically. Direct-submit users require an explicit decision. | Are narratives collected from participants, public channels, CHWs, or an existing dataset? Is direct submission allowed? |
| Linguists or language experts | Language quality, translation validity, terminology, and interpretation across approved languages. | Proposed dataset review, translation review, and usability testing; no current feature exists. | Validate language handling and identify language-specific risks. | Not necessarily. An expert may participate in research review without an application account. | Which languages and dialects are in scope? Is translation human, machine-assisted, or out of scope? |
| Project supervisor and research team | Academic scope, evidence quality, implementation priorities, and approval of unresolved decisions. | Requirements approval, dataset and method decisions, evaluation, and governance. | Confirm scope, approve requirements, coordinate data and ethics approvals, and prevent unsupported implementation assumptions. | Not necessarily; governance responsibility does not imply an application role. | Who is the named decision owner for each item in the decision register? |
| Ethics or institutional review authority | Protection of participants and responsible handling of sensitive data. | Review consent, collection, privacy, retention, withdrawal, and risk controls. | Approve or reject research procedures according to applicable institutional policy. | Not automatically. | What approval process and reference number apply? |

Stakeholders are not automatically application users. In particular, public-health stakeholders, linguists, ethics authorities, and research supervisors may be governance or research stakeholders without receiving a production account.

# C. Functional Requirements

The following requirements use the current implementation as evidence where available. Proposed requirements must not be treated as approved feature commitments until the associated decision is confirmed.

## C1. Authentication and Account Management

| ID | Requirement | Primary actor | Priority | Acceptance criteria | Source or justification | Status |
|---|---|---|---|---|---|---|
| FR-001 | The system shall allow community members to self-register with a full name, email, password, and password confirmation while keeping CHW, reviewer, and administrator accounts invitation-only. | Community member and administrator | Must | `POST /api/v1/auth/register` assigns only `community_member`, creates a pending account, requires matching passwords, and starts email verification; staff roles are created through invitations. | E-004, E-006, E-013 | Implemented |
| FR-002 | An administrator shall be able to invite an email address to an approved application role without returning the raw invitation token through the API. | Administrator | Must | A valid administrator request creates a single-use invitation, sends it through the configured email service, returns expiry metadata, records an audit event, and rejects unauthorized roles or duplicate accounts. | E-006, E-011 | Implemented |
| FR-003 | An invitee shall be able to accept a valid, unexpired, single-use invitation and establish the invited account. | Invitee | Must | Acceptance creates an active, verified account with the invited role, issues authenticated session tokens, rejects expired/revoked/used tokens, and records the event. | E-006, E-011 | Implemented |
| FR-004 | The system shall authenticate an active account and issue a short-lived access token with a refresh token. | CHW, reviewer, administrator | Must | Valid credentials produce the documented token response; invalid credentials do not disclose account details; account and login events are handled according to the current security policy. | E-006, E-010, E-011 | Implemented |
| FR-005 | An authenticated user shall be able to refresh, revoke the current session, or revoke all sessions. | CHW, reviewer, administrator | Must | Refresh tokens rotate and are persisted as hashes; logout revokes the supplied session; logout-all revokes all active sessions; replayed or invalid tokens fail. | E-006, E-009, E-011 | Implemented |
| FR-006 | A user shall be able to change a known password and request or confirm a password reset without account-existence disclosure. | Authenticated user or password-reset requester | Must | Password policies are enforced; reset responses are generic; valid reset tokens are single-use and expiring; old reset tokens are invalidated as implemented. | E-006, E-011, E-013 | Implemented |
| FR-007 | The system shall support six-digit email OTP verification and generic verification-message resend. | Pending or authenticated user | Must | A valid, short-lived OTP marks the email verified and establishes a session for active accounts; invalid or expired OTPs fail safely; resend responses do not reveal account state. | E-006, E-011 | Implemented |
| FR-008 | An authenticated user shall be able to retrieve the current profile and request an email change that requires verification. | Authenticated user | Should | The profile response excludes authentication secrets; a new email is normalized, checked for conflict, and does not become active before verification. | E-006, E-010, E-011 | Implemented |

## C2. Role and Permission Management

| ID | Requirement | Primary actor | Priority | Acceptance criteria | Source or justification | Status |
|---|---|---|---|---|---|---|
| FR-009 | An administrator shall be able to change another account's lifecycle status while preserving at least one active administrator. | Administrator | Must | Valid status changes are persisted and audited; self-deactivation is rejected; an operation that would remove the last active administrator is rejected; affected sessions are revoked when required. | E-006, E-008, E-011, E-016 | Implemented |
| FR-010 | An administrator shall be able to change another account's role while preserving at least one active administrator. | Administrator | Must | Valid role changes are persisted and audited; self-demotion is rejected; demotion of the last active administrator is rejected; concurrent attempts preserve the invariant. | E-006, E-008, E-011, E-016 | Implemented |
| FR-011 | Every protected operation shall authenticate the caller and enforce server-side role authorization using the current account state. | Any authenticated actor | Must | Missing, invalid, expired, or inactive credentials fail; a non-administrator cannot call administrator endpoints; role checks are not delegated to the mobile client. | E-005, E-010, E-016 | Implemented |
| FR-012 | The system shall record security-relevant account actions and provide sanitized audit search to authorized administrators. | System and administrator | Must | Account and invitation events include actor/target/action/outcome where applicable; administrator queries are paginated and filterable; raw tokens and unsafe details are not returned. | E-007, E-009, E-012, E-016 | Implemented |

## C3. Vaccine-Related Narrative Submission

| ID | Requirement | Primary actor | Priority | Acceptance criteria | Source or justification | Status |
|---|---|---|---|---|---|---|
| FR-013 | The system shall accept a vaccine-related narrative from an approved submission channel using a supervisor-approved narrative schema and consent/provenance fields. | CHW, reviewer, or approved submitter | Must | The final workflow will enforce approved actor/channel and consent rules. The current neutral foundation accepts validated content from an authenticated account only and does not claim that the account is an approved submitter. | E-001, E-018; neutral foundation is implemented while workflow is unresolved | Partially implemented |
| FR-014 | The system shall persist a submitted narrative with a controlled lifecycle state and an auditable version or change history. | System | Must | The current foundation stores owner, content, a neutral `submitted` state, timestamps, version numbers, and immutable content revisions. Final lifecycle, provenance, consent, deletion, and retention rules remain subject to approval. | E-002, E-003, E-015, E-018 | Partially implemented |
| FR-015 | The system shall restrict narrative access according to approved role, assignment, purpose, and least-privilege rules. | System | Must | Owner routes remain submitting-account scoped. The provisional review API exposes content only to the active assigned reviewer and exposes assignment metadata/history to assignment managers without unrestricted content. Final CHW/reviewer assignment, administrator, direct-submit, and organizational-scope policy still requires approval. | E-010, E-018 | Partially implemented |

## C4. Narrative Review and Investigation

| ID | Requirement | Primary actor | Priority | Acceptance criteria | Source or justification | Status |
|---|---|---|---|---|---|---|
| FR-016 | The system shall provide reviewers with a queue of narratives according to approved assignment and workflow rules. | Reviewer | Must | The provisional queue lists active assignments with stable pagination, limits content to the assigned reviewer, and records assignment changes; ordering, filtering, and production policy remain subject to confirmation. | E-001, E-008, E-018 | Awaiting confirmation |
| FR-017 | An authorized reviewer shall be able to inspect a narrative and its permitted provenance/context without unnecessary participant identifiers. | Reviewer | Must | The provisional assigned view returns narrative content and current status only to the active reviewer; assignment managers receive metadata without content. Final provenance, identity minimization, and access-logging policy remain subject to approval. | E-009, E-018 | Awaiting confirmation |
| FR-018 | A reviewer shall be able to record an assessment, evidence reference, uncertainty, and structured feedback using approved labels. | Reviewer | Must | The provisional API records one of four neutral outcomes, optional notes, evidence references, reviewer attribution, timestamps, and immutable history. Formal labels, uncertainty, feedback, and qualification policy remain subject to approval. | E-001, E-003, E-018 | Awaiting confirmation |
| FR-019 | The system shall record the narrative review workflow, including review, escalation, approval, rejection, correction, and history states selected by the supervisor. | Reviewer and system | Must | The provisional workflow authorizes assignment, `pending`, `in_review`, `reviewed`, and explicit `requires_escalation` transitions, with reassignment/revocation history and audit events. Approval, rejection, correction, notifications, and escalation resolution remain unimplemented pending confirmation. | E-018; provisional review implementation | Awaiting confirmation |

## C5. Dataset and Analytical Data Management

| ID | Requirement | Primary actor | Priority | Acceptance criteria | Source or justification | Status |
|---|---|---|---|---|---|---|
| FR-020 | The system or research workflow shall ingest only an approved dataset with documented provenance, permission, and version information. | Research/data steward | Must | Dataset intake records source, owner, permission, license, collection context, version, and integrity metadata; unapproved data cannot enter model development. | E-003, E-015, E-018 | Proposed |
| FR-021 | The research workflow shall assess and preprocess the supplied dataset using a reproducible, documented process. | Data/ML team | Must | A data assessment reports structure, quality, missingness, duplicates, labels, language, bias indicators, and exclusions; preprocessing is versioned and reproducible. | E-002, E-003, E-015 | Proposed |
| FR-022 | The system shall preserve data dictionary, provenance, quality findings, preprocessing version, and dataset lineage for every analytical dataset used. | Data/ML team | Should | A reviewer can identify the source and transformations for a model input; lineage records are access-controlled and do not expose sensitive raw data unnecessarily. | E-003, E-015, E-018 | Proposed |

## C6. Machine Learning Inference

| ID | Requirement | Primary actor | Priority | Acceptance criteria | Source or justification | Status |
|---|---|---|---|---|---|---|
| FR-023 | The system shall run inference only for the ML task, target, model, and input schema approved after dataset assessment. | FastAPI inference service | Must | The service rejects incompatible or unauthorized inputs; every output identifies model/version and task; no inference endpoint is exposed before validation and approval. | E-002, E-003, E-013, E-015 | Proposed |
| FR-024 | The system shall communicate model confidence or uncertainty only when the selected task and evaluation support a meaningful interpretation. | Mobile user or reviewer | Must | The output defines the meaning and limitations of any confidence/uncertainty value; unsupported certainty is not displayed; model evaluation evidence accompanies release approval. | E-003, E-018 | Proposed |

## C7. Explainable AI Outputs

| ID | Requirement | Primary actor | Priority | Acceptance criteria | Source or justification | Status |
|---|---|---|---|---|---|---|
| FR-025 | The system shall associate each explanation with the exact input, model version, prediction, and explanation method used. | Reviewer or authorized user | Must | A permitted user can see which model output is being explained; explanation generation is reproducible for the recorded version or the limitation is shown. | E-002, E-003, E-018 | Proposed |
| FR-026 | The system should provide validated global model-behavior summaries when they are useful for the confirmed task and safe to disclose. | Reviewer, supervisor, or authorized analyst | Should | Global summaries identify the population and model version, include validation limitations, and do not expose sensitive features without approval. | E-002, E-014, E-018 | Proposed |
| FR-027 | The system shall present explanations as model associations or feature contributions, not as causal proof, medical truth, or independent misinformation verification. | All users receiving an explanation | Must | UI and API wording separates prediction, explanation, verified health information, and human review; limitations are visible at the point of use. | E-004, E-018 | Awaiting confirmation |

## C8. Visualization and Interpretation

| ID | Requirement | Primary actor | Priority | Acceptance criteria | Source or justification | Status |
|---|---|---|---|---|---|---|
| FR-028 | The mobile application shall display authorized predictions, uncertainty, explanations, review state, and relevant provenance in an understandable and accessible form. | CHW, reviewer, or approved user | Must | A usability-reviewed screen distinguishes model output from verified information, works on the approved Android devices, handles unavailable explanations, and respects role visibility. | E-001, E-002, E-003, E-018 | Proposed |

## C9. Health Communication and Educational Information

| ID | Requirement | Primary actor | Priority | Acceptance criteria | Source or justification | Status |
|---|---|---|---|---|---|---|
| FR-029 | The system shall display health communication content only from a supervisor-approved set of public-health sources and shall show source and currency information. | CHW, reviewer, or approved user | Must | Each displayed item identifies its source and review/update date; content cannot be presented as approved before source governance is defined. | E-001, E-004, E-018 | Awaiting confirmation |
| FR-030 | The system shall clearly separate verified educational information from model predictions, explanations, and reviewer judgments, and shall provide an appropriate professional-care disclaimer. | All users | Must | The interface and API use distinct labels and provenance; uncertain or unsafe cases are escalated according to the approved workflow; the system does not provide diagnosis or treatment recommendations. | E-004, E-018 | Awaiting confirmation |

## C10. Reviewer Feedback and Human Oversight

| ID | Requirement | Primary actor | Priority | Acceptance criteria | Source or justification | Status |
|---|---|---|---|---|---|---|
| FR-031 | A reviewer shall be able to submit corrections, concerns, and feedback linked to the narrative, model output, or explanation. | Reviewer | Must | Feedback is attributable, versioned, access-controlled, auditable, and distinguishable from the model output; the feedback schema is approved before implementation. | E-001, E-003, E-018 | Awaiting confirmation |
| FR-032 | The system shall support an approved human decision, override, or escalation path without silently replacing the original model output. | Qualified reviewer | Must | The final communication state identifies human and model contributions separately, records the reason and reviewer, and prevents an unreviewed model output from being represented as verified fact. | E-004, E-018 | Awaiting confirmation |

## C11. Notifications and Communication

| ID | Requirement | Primary actor | Priority | Acceptance criteria | Source or justification | Status |
|---|---|---|---|---|---|---|
| FR-033 | The system should notify authorized users of approved assignments, review-state changes, and security/account actions through confirmed channels without leaking sensitive narrative content. | System and authorized user | Should | Notification channels and opt-out rules are approved; messages contain only the minimum necessary data; delivery and failure events are auditable. | E-004, E-018; email exists only for account actions | Awaiting confirmation |

## C12. Administrator Dashboard and Audit Logs

| ID | Requirement | Primary actor | Priority | Acceptance criteria | Source or justification | Status |
|---|---|---|---|---|---|---|
| FR-034 | An administrator shall be able to list and search user accounts using approved filters without receiving password, token, or secret fields. | Administrator | Must | Directory results support pagination/filtering/sorting and return only approved account fields; non-administrators receive a forbidden response. | E-007, E-012, E-016 | Implemented |
| FR-035 | An administrator shall be able to list, inspect, and revoke invitations using non-secret metadata. | Administrator | Must | Invitation results expose lifecycle metadata but not raw tokens or token hashes; only pending invitations can be revoked; actions are audited. | E-007, E-009, E-012, E-016 | Implemented |
| FR-036 | An administrator shall be able to view aggregate user, invitation, role, and session statistics. | Administrator | Should | The dashboard returns documented non-negative aggregates and does not expose raw credentials or tokens; access is administrator-only. | E-007, E-012, E-016 | Implemented |
| FR-037 | An administrator shall be able to search a sanitized, paginated audit log by approved action, outcome, actor, target, and date filters. | Administrator | Must | Results are newest-first, paginated, sanitized, and role-protected; sensitive detail values are not returned. | E-007, E-012, E-016 | Implemented |
| FR-038 | Administrator access to narratives, participant identifiers, datasets, model artifacts, and explanations shall be explicitly defined and enforced separately from account administration. | Administrator and system | Must | The permission matrix names every sensitive resource; tests prove allowed and denied paths; account-admin privileges do not automatically grant raw research-data access. | E-007, E-010, E-018 | Awaiting confirmation |

# D. Non-Functional Requirements

No numerical performance, availability, scale, usability, or evaluation target is treated as approved unless it is supported by repository evidence. Where a target is needed, acceptance requires a supervisor-approved value to be recorded before implementation.

| ID | Requirement | Priority | Acceptance criteria | Source or justification | Status |
|---|---|---|---|---|---|
| NFR-001 | Authentication shall protect protected API operations using validated bearer tokens and current active-account state. | Must | Invalid, expired, malformed, inactive-account, and post-password-change tokens are rejected consistently; protected endpoints require authentication. | E-010, E-016 | Implemented |
| NFR-002 | Authorization shall be enforced on the server using least privilege and explicit role/resource rules. | Must | Role-denial tests cover every protected module; client-supplied role claims cannot grant access; resource-level rules are documented before narrative features ship. | E-010, E-018 | Implemented |
| NFR-003 | Passwords shall be protected using the implemented Argon2 hashing policy and input validation. | Must | Password hashes are never returned; the configured minimum and maximum lengths are enforced; authentication tests cover valid and invalid credentials. | E-004, `backend/app/core/security.py`, E-016 | Implemented |
| NFR-004 | Access and refresh sessions shall limit token exposure and support rotation, revocation, replay detection, and account-wide logout. | Must | Refresh tokens are stored hashed; rotation and revocation are persisted; replay detection revokes the relevant family; logout-all invalidates active sessions. | E-009, E-011, E-016 | Implemented |
| NFR-005 | The API shall apply configured rate limits and baseline security protections to reduce abuse and accidental disclosure. | Must | Protected account flows enforce configured limits; rate-limit errors are controlled; security headers and production configuration checks are present; raw validation input is not echoed. | E-005, E-013, E-016 | Implemented |
| NFR-006 | The system shall minimize personal and health-related data and expose only fields required for the actor's approved purpose. | Must | Account APIs omit secrets; audit details are sanitized; future narrative views document field-level minimization and are tested against the approved policy. | E-007, E-012, E-018 | Partially implemented |
| NFR-007 | Data in transit and at rest shall use safeguards appropriate to the approved deployment and sensitivity classification. | Must | Production database SSL and email transport settings meet the approved policy; storage encryption and mobile storage handling are documented and tested before sensitive data is deployed. | E-013; storage policy absent | Proposed |
| NFR-008 | The project shall have approved consent, ethics, confidentiality, withdrawal, retention, and deletion procedures before collecting or using participant-related data. | Must | Ethics approval and consent artifacts identify data uses, risks, withdrawal limits, retention, deletion, and responsible parties; implementation is blocked until applicable approval exists. | E-018; E-017 missing documents | Blocked by ethical or policy approval |
| NFR-009 | The API and mobile client shall meet supervisor-approved response-time and resource-use targets for the selected deployment context. | Should | Approved targets exist for key user journeys; representative tests measure them on the approved network/device profile; failures are reported without hiding uncertainty. | No target in repository; E-018 | Proposed |
| NFR-010 | The service shall provide reliable failure handling and health visibility for the API and PostgreSQL dependency. | Must | Liveness and database health endpoints report controlled states; transient failures return documented responses; no sensitive error details are exposed. | E-005, `backend/app/api/routes/health.py`, E-016 | Partially implemented |
| NFR-011 | The architecture shall support growth in authorized users, narratives, reviews, and inference requests without weakening access control or auditability. | Should | A supervisor-approved scale model, capacity assumptions, indexes, retention strategy, and load-test plan exist before production scale claims are made. | No scale evidence; E-018 | Proposed |
| NFR-012 | The mobile user experience shall be understandable for the approved users and communication tasks. | Must | Task-based usability evaluation with representative users identifies comprehension, error recovery, uncertainty interpretation, and workflow completion results; target thresholds require approval. | E-001, E-018 | Proposed |
| NFR-013 | The mobile and API interfaces shall meet an approved accessibility baseline, including readable content, semantic labels, contrast, input feedback, and non-visual alternatives where needed. | Should | The selected framework and approved accessibility standard are recorded; automated and representative manual checks are completed for core screens. | No mobile implementation or standard in repository; E-018 | Proposed |
| NFR-014 | The codebase shall remain maintainable through modular boundaries, documented interfaces, automated tests, migration discipline, and reproducible development setup. | Should | Backend modules have focused responsibilities, public API schemas are documented, changes have tests, and future ML/mobile components have versioned interfaces; current account foundation partially satisfies this. | E-005, E-016, repository structure | Partially implemented |
| NFR-015 | The mobile client shall be compatible with the supervisor-approved Android framework, OS range, and device profile. | Must | Framework, minimum OS, supported devices, offline/online behavior, and release test matrix are approved and verified; no claim is made while the framework is unconfirmed. | E-002, E-003, E-015 | Blocked by supervisor decision |
| NFR-016 | The FastAPI interface shall provide stable, documented request/response contracts and controlled error behavior for the mobile client. | Must | OpenAPI documents implemented endpoints; schemas validate inputs/outputs; authentication, authorization, validation, rate-limit, and service-unavailable responses are documented; future domain contracts are versioned. | E-005, E-006, E-007, E-016 | Partially implemented |
| NFR-017 | Persisted data shall maintain integrity, consistency, lifecycle constraints, and transaction behavior appropriate to each domain. | Must | Current account invariants, foreign keys, unique emails, lifecycle controls, and concurrent administrator protections remain enforced; future narrative/data rules are approved and tested. | E-008, E-009, E-011, E-016 | Partially implemented |
| NFR-018 | Security, administrative, review, and model lifecycle actions shall be auditable with attributable, time-ordered records that do not contain secrets. | Must | Current account actions are audited and sanitized; future narrative/reviewer/model events identify actor, target/resource, action, outcome, and version according to policy. | E-007, E-009, E-012 | Partially implemented |
| NFR-019 | Explainability shall be faithful to the selected model and transparent about limits, scope, input data, and uncertainty. | Must | Explanation quality and stability are evaluated for the selected task; UI distinguishes contribution from causation; model/version/input are recorded; no explanation is presented before the model task is approved. | E-002, E-003, E-018 | Blocked by dataset availability |
| NFR-020 | AI-assisted communication shall include human oversight, safe escalation, and controls against overreliance or unsafe interpretation. | Must | A qualified reviewer workflow, override/escalation rules, disclaimer language, incident handling, and release approval exist before AI output is used operationally. | E-004, E-018 | Blocked by ethical or policy approval |
| NFR-021 | Language support shall match the approved user and dataset population and shall be validated for meaning, terminology, and explanation quality. | Must | Supported languages are explicitly listed; representative language review is completed; untranslated or low-confidence content is identified; no language is claimed from the project title alone. | E-015, E-018 | Blocked by supervisor decision |
| NFR-022 | Retention, deletion, correction, and withdrawal behavior shall be defined for account, narrative, review, dataset, model, explanation, and audit data. | Must | A policy maps each data class to owner, retention period, legal/ethical basis, deletion/withdrawal effect, and immutable-audit exceptions; implementation tests follow the policy. | E-009, E-018; policy absent | Blocked by ethical or policy approval |

# E. Role and Permission Requirements

## Current Role Evidence

`backend/app/models/user.py` defines four application roles: `community_member`,
`administrator`, `chw`, and `reviewer`. `backend/app/api/dependencies.py` enforces
active-account authentication and server-side permission checks. The current
administrator routes use explicit permissions derived from the administrator
role. Reviewer-specific assignment and review routes exist as a provisional
workflow; no CHW-specific assigned-record route exists.

### Permission-layer implementation update

The current backend now also defines a centralized static permission catalogue
and explicit mapping for all four roles, including `community_member`. Implemented
permissions cover account administration, invitations, audit search, and
owner-scoped narrative operations, and the provisional assigned-review workflow.
Analysis, dataset, and model permissions remain unassigned because those
workflows are not implemented. See `docs/permission_management.md` for the
implementation assessment and final matrix.

## Preliminary Role-Permission Matrix

Legend: **Implemented** means the current backend supports the permission; **Proposed** means the permission is a future requirement; **Confirm** means the permission must be decided before implementation; **No evidence** means no permission is currently granted by the application.

| Capability | Administrator | CHW | Reviewer | Evidence and decision note |
|---|---|---|---|---|
| Register as a community member | Self-registration with full name, email, password, and password confirmation | Self-registration with server-assigned `community_member` role | Invitation-only onboarding with `chw`, `reviewer`, or `administrator` role | FR-001; public registration cannot select or obtain a staff role. |
| Receive and accept invitation | Implemented | Implemented as supported role value | Implemented as supported role value | FR-002 and FR-003; invitation acceptance creates the invited role. |
| Login, refresh, logout, password, email verification, own profile | Implemented | Implemented for any active account | Implemented for any active account | FR-004 to FR-008; access is account-based, not domain-role based. |
| Change user status | Implemented for administrator callers | No evidence | No evidence | FR-009; endpoint is administrator-only. |
| Change user role | Implemented for administrator callers | No evidence | No evidence | FR-010; endpoint is administrator-only. |
| View user directory/details | Implemented for administrator callers | No evidence | No evidence | FR-034; returned fields exclude secrets. |
| Manage invitations | Implemented for administrator callers | No evidence | No evidence | FR-035; invitation metadata only. |
| View account dashboard | Implemented for administrator callers | No evidence | No evidence | FR-036; counts cover users, invitations, and sessions. |
| Search audit events | Implemented for administrator callers | No evidence | No evidence | FR-037; audit details are sanitized. |
| Submit narratives | Confirm | Confirm | Confirm | FR-013; direct/public submission and role scope are unresolved. Do not infer access from the role enum. |
| View assigned narratives | Metadata only | No evidence | Provisional active-assignment access | FR-015 and FR-016; formal assignment, minimization, and qualification policy remains unresolved. |
| Review/investigate narratives | Assignment metadata/history only | No evidence | Provisional structured review access | FR-017 to FR-019; outcomes and status transitions are implemented provisionally and do not imply approval of health communication. |
| View model output and explanations | Confirm | Confirm | Confirm | FR-023 to FR-028; blocked by ML task, model, data, and visibility decisions. |
| View approved health information | Confirm | Confirm | Confirm | FR-029 and FR-030; approved sources and audiences are unknown. |
| Override or approve communication | Confirm | No evidence | Confirm | FR-032; must require qualified human oversight and explicit policy. |
| Access raw participant identifiers | Confirm and least privilege | Confirm and least privilege | Confirm and least privilege | FR-015 and FR-038; no role receives this access automatically. |
| Access raw datasets or model artifacts | Confirm and least privilege | No evidence | No evidence | FR-020 to FR-022 and FR-038; research/data-steward permissions are not application permissions yet. |

This matrix is intentionally conservative. Administrator account management does not
imply access to all narratives, datasets, model artifacts, or participant
information. The provisional reviewer workflow is not formal qualification or
production approval.

# F. System Architecture Requirements

## Proposed Component Flow

```text
Approved data sources
        |
Data assessment and preprocessing
        |
ML model selected after assessment
        |
SHAP/XAI explanation component
        |
Python FastAPI backend
        |
Mobile application
        |
Authorized users
```

This flow is the high-level architecture recorded in `README.md` (E-002). It is a proposed architecture, not evidence of an implemented end-to-end pipeline.

## Component Responsibilities

| Component | Required responsibility | Current evidence and boundary |
|---|---|---|
| Approved data sources | Supply data with provenance, permission, licensing, consent/legal basis, and an identified owner. | No dataset or source approval is present. The source must be confirmed before ingestion. |
| Data assessment and preprocessing | Describe the data, identify quality and representation risks, define preprocessing, and create reproducible inputs. | No notebooks, pipeline, schema, or assessment report exists. This is blocked by dataset availability. |
| ML model | Perform the supervisor-approved task on approved inputs and expose versioned predictions with appropriate uncertainty. | No model artifact, training code, target, feature schema, or inference route exists. |
| SHAP/XAI | Produce a model-linked explanation and expose limits; never present contribution as causation or truth. | SHAP is named in the README and dependency plan, but no implementation exists. |
| FastAPI backend | Authenticate users, enforce permissions, persist approved domain records, expose versioned APIs, mediate inference, audit actions, and handle failures. | Account/security/admin foundation is implemented; narrative, ML, XAI, and communication APIs are absent. |
| PostgreSQL | Persist authorized account and future approved domain data with integrity, transaction, access, and audit controls. | Current account-related entities use PostgreSQL. Future domain schema is unknown and must not be invented. |
| Mobile application | Provide role-appropriate submission, review, explanation, visualization, health communication, and account journeys. | `mobile/` is empty and the framework is unconfirmed. |
| Authorized users | Use outputs within role, purpose, consent, and human-oversight boundaries. | Account roles exist, but CHW/reviewer permissions for domain workflows are unresolved. |

## Integration Requirements

| Interface | Requirement | Status |
|---|---|---|
| Mobile to FastAPI | Use versioned authenticated contracts, explicit error states, pagination where needed, secure token handling, and role/resource authorization enforced by the backend. | Account/API boundary exists; mobile client and domain contracts are not implemented. |
| FastAPI to PostgreSQL | Use transactions, migrations, constraints, least-privilege database configuration, connection health checks, and no secret leakage in logs or responses. | Account persistence, migrations, database health, and security configuration exist; narrative schema is unknown. |
| FastAPI to ML inference | Define a versioned input/output contract containing task, model version, prediction, uncertainty semantics, and failure behavior. | No inference service or approved task exists; blocked by dataset and supervisor decisions. |
| ML to SHAP/XAI | Bind the explanation to the exact model, input, preprocessing version, output, and explanation method; evaluate faithfulness and stability. | No model or explanation implementation exists; blocked by dataset/task and safety approval. |
| Health communication to approved sources | Store source identity, review date, content version, approval status, and update/withdrawal behavior. | No approved source list or content integration exists; blocked by public-health governance. |

# G. Data Requirements

## Known Data Facts

The authoritative dataset has not been received. The repository contains only placeholder files in data directories and no data schema or assessment. Therefore, this specification does **not** state a dataset size, feature list, label set, target variable, source, language distribution, class distribution, collection period, or representativeness finding. The presence of Pandas, scikit-learn, XGBoost, SHAP, LIME, and joblib in `requirements.txt` is a planned dependency signal only (E-014).

## Information Required Before Dataset Assessment

The project supervisor or data custodian must provide or confirm:

- The dataset file or authorized access mechanism and a data dictionary.
- Data owner, source, collection method, collection period, geographic context, and provenance.
- Permission, license, consent basis, ethics approval, and restrictions on secondary use.
- Unit of observation and whether records are narratives, messages, survey responses, labels, or another form.
- Candidate features, labels, target variable, annotation instructions, labeler qualifications, and inter-rater process.
- Language and dialect fields, translation history, and language-specific annotation quality.
- Sample size, class distribution, duplicate policy, missingness, invalid records, outliers, and inconsistent values.
- Personally identifiable, sensitive health, location, contact, or free-text fields and the required minimization/de-identification approach.
- Population represented, sampling method, inclusion/exclusion criteria, temporal drift, and known coverage gaps.
- Data split policy that prevents leakage between training, validation, and test sets.
- Ownership of derived datasets, features, model artifacts, explanations, labels, and audit records.
- Retention, deletion, correction, withdrawal, export, and incident-response requirements.
- Whether the dataset may be used for model training, testing, demonstrations, or production inference.

## Data Quality and Governance Requirements

Data assessment must be evidence-based and must report provenance, permissions, licensing, quality, missing values, duplicates, labels, representativeness, bias, privacy risks, and limitations. A data assessment must precede selection of the target and model. No model-development milestone should be recorded as complete merely because the ML dependencies are installed.

# H. AI and Explainability Requirements

## Responsibility Separation

| Component or actor | Responsibility | Explicit non-responsibility |
|---|---|---|
| Machine Learning | Produce a prediction for a confirmed task using approved data and a versioned model. | It must not be described as diagnosing a person, recommending treatment, or independently verifying public-health truth. |
| SHAP | Attribute model output to input features according to the selected model/explainer assumptions and provide a model-linked explanation. | SHAP does not prove causation, medical truth, or that a narrative is misinformation. |
| LIME | May be evaluated only if a supervisor-approved justification shows that it adds value for the selected model/task and is communicated with its limitations. | The dependency declaration does not approve LIME or require it in the final system. |
| Human reviewers | Assess context, source, safety, uncertainty, and communication; correct, approve, reject, or escalate according to policy. | Reviewers must not be replaced by a model, and their judgments must remain distinguishable from model output. |
| Health communication components | Present approved public-health information with source, date, audience, and safe wording. | They must not convert a prediction or explanation into diagnosis, treatment advice, or an unsupported claim of truth. |

## AI Risks Requiring Controls

- Incorrect predictions can misclassify narratives and cause harmful communication.
- An explanation can be technically consistent with a model while still being misleading, unstable, or misunderstood.
- Feature contribution is not evidence that a feature caused a health belief or outcome.
- Bias in collection, labels, language, sampling, or annotation can produce unequal errors.
- Language-related tokenization, translation, dialect, and terminology errors can distort both prediction and explanation.
- Users may over-trust a visual score or explanation; uncertainty, limits, and human review must be visible.
- The system cannot independently verify vaccine misinformation merely by producing a prediction or SHAP output.
- Model output must not be presented as public-health guidance unless it is separately supported by an approved source and workflow.

## Minimum AI Release Conditions

Before any operational ML feature is released, the project must have an approved task and label definition, assessed dataset, documented preprocessing, model evaluation, error and bias analysis, explanation evaluation, human-review procedure, safety wording, rollback/versioning plan, and ethics/privacy approval where applicable. None of these conditions can be claimed as satisfied by the current repository.

# I. Ethical and Privacy Requirements

| Topic | Requirement | Current evidence/status |
|---|---|---|
| Informed consent | Collection and use of participant or community narratives shall use approved consent language and record the applicable consent basis. | No consent procedure or form is present; supervisor/ethics approval required. |
| Confidentiality | Access, display, logging, exports, and notifications shall minimize identity and sensitive health information. | Account APIs omit secrets and audit details are sanitized; narrative confidentiality is not implemented. |
| Data minimization | Collect and retain only fields necessary for the approved research and communication purpose. | Current account endpoints select limited fields; future narrative fields are unknown. |
| Access control | Role and resource rules shall be enforced server-side and reviewed for CHW, reviewer, administrator, data steward, and direct-submit paths. | Account authorization exists; domain permissions are unresolved. |
| Right to withdraw | Where applicable, participants shall be able to withdraw according to an approved procedure, with clear limits for derived data and immutable audit obligations. | No policy exists; ethics and data-owner decision required. |
| Retention and deletion | Each data class shall have an approved owner, retention period, deletion behavior, and legal/ethical basis. | No policy exists; blocked. |
| Ethical approval | Data collection, secondary use, sensitive health information, model use, and user evaluation shall follow the applicable institutional approval process. | No approval document is present; blocked. |
| Human oversight | High-impact or uncertain communication shall be reviewed or escalated by an appropriately qualified person. | Reviewer role exists only as an account value; workflow is absent. |
| Transparency | Users shall be told when they see a model output, explanation, verified source content, or human judgment. | Required by this specification; no domain UI exists. |
| Incident handling | The project shall define how harmful output, privacy incidents, incorrect source content, and model failures are reported, triaged, corrected, and audited. | No incident procedure is present; supervisor/policy approval required. |

The project must not collect new participant narratives, deploy AI communication, or claim ethical compliance until the relevant approvals and procedures are confirmed.

# J. Verification Approach

| Verification method | Use |
|---|---|
| Unit test | Pure validation, permission, transformation, sanitization, and lifecycle rules. |
| API integration test | Authentication, authorization, persistence, error contracts, audit behavior, and transaction boundaries against PostgreSQL. |
| Concurrency/invariant test | Administrator protection and any future state transition that must remain safe under concurrent requests. |
| Data assessment report | Dataset provenance, quality, labels, bias, missingness, privacy, and representativeness. |
| Model evaluation | Task-appropriate predictive performance, calibration/uncertainty, subgroup/language error, robustness, and leakage checks. |
| XAI evaluation | Explanation faithfulness, stability, comprehensibility, version linkage, and non-causal wording. |
| Security/privacy review | Threat modeling, access control, secrets, transport/storage, retention, consent, and auditability. |
| Usability/accessibility evaluation | Representative user tasks, comprehension of uncertainty, accessibility checks, language review, and Android device testing. |
| Human/ethics review | Reviewer qualification, consent, public-health source approval, safe communication, and withdrawal/incident procedures. |
