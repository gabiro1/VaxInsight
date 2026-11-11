# VaxInsight Requirements Traceability Matrix

## Purpose

This matrix connects the project objectives to stakeholder needs, requirements, proposed modules, acceptance criteria, and verification methods. It is intentionally explicit about requirements that are not yet supported by the implementation. A traceability link does not mean that the linked feature is approved or complete.

## Objective Register

| ID | Project objective | Evidence |
|---|---|---|
| OBJ-001 | Support intelligent and understandable health communication around vaccine-related narratives in the approved Rwanda context. | `README.md` project title and overview; task brief; E-001 and E-018 in the requirements specification. |
| OBJ-002 | Provide controlled access for approved personnel and protect account/session information. | `README.md` account foundation; current FastAPI authentication and authorization implementation. |
| OBJ-003 | Assess approved data before selecting and operating an ML task. | `README.md` dataset-first principle and incomplete-status checklist. |
| OBJ-004 | Provide transparent, model-linked explanations without overstating what AI proves. | `README.md` SHAP pipeline; task brief; no current XAI implementation. |
| OBJ-005 | Keep qualified human reviewers responsible for interpretation, correction, escalation, and safe communication. | Task brief and proposed stakeholder/workflow requirements; current reviewer role has no domain workflow. |
| OBJ-006 | Protect participant/community confidentiality and comply with approved ethical and privacy procedures. | Task brief; current security foundation; no ethics or data-management plan in the repository. |
| OBJ-007 | Give administrators sufficient operational control without granting automatic access to research data. | Current administrator routes, account services, audit services, and task brief. |
| OBJ-008 | Deliver an Android-compatible mobile experience using an approved framework and measurable evaluation criteria. | `README.md` mobile framework-to-be-confirmed status; task brief; empty `mobile/` directory. |

## Traceability Matrix

| Objective | Stakeholder need | Requirement IDs | Proposed module | Acceptance criteria summary | Verification method |
|---|---|---|---|---|---|
| OBJ-001 | CHWs, reviewers, and approved users need understandable, appropriately sourced communication about vaccine-related narratives. | FR-013, FR-016, FR-017, FR-028, FR-029, FR-030; NFR-012, NFR-013, NFR-021 | Narrative submission; review; visualization; health communication; mobile UX | Authorized users can follow the approved workflow; model output, explanation, reviewer judgment, and approved source content are visibly separate; source and currency are shown; usability and language scope are approved. | API integration tests; representative usability/accessibility tests; language review; public-health review |
| OBJ-002 | CHWs, reviewers, and administrators need reliable, secure access to their approved accounts. | FR-001 to FR-011; NFR-001 to NFR-005, NFR-016 | Authentication and account management; role authorization | Valid invitation/login/session flows work; inactive or unauthorized accounts fail; secrets are protected; current account actions are audited; protected contracts are documented. | Unit tests; API security/integration tests; concurrency tests; OpenAPI contract tests; security review |
| OBJ-003 | The research team needs trustworthy data and reproducible analytical inputs before model selection. | FR-020 to FR-022; NFR-017, NFR-022 | Dataset and analytical data management | Dataset provenance, permissions, data dictionary, quality assessment, labels, language, missingness, duplicates, bias, preprocessing, and lineage are recorded before model work. | Dataset assessment report; data-governance review; reproducibility check; privacy/ethics review |
| OBJ-004 | Reviewers and authorized users need explanations that clarify model behavior without becoming false medical certainty. | FR-023 to FR-028; NFR-019 | ML inference; SHAP/XAI; visualization | Output identifies task/model/version; uncertainty semantics are defined; explanation is linked to the exact input/output; wording states limitations and does not claim causation or independent verification. | Model evaluation; calibration/uncertainty analysis; XAI faithfulness and stability evaluation; UI review |
| OBJ-005 | Qualified reviewers need authority and tools to inspect, correct, approve, reject, or escalate AI-assisted communication. | FR-016 to FR-019, FR-031, FR-032; NFR-020 | Review and human oversight | Reviewer qualification, assignment, state transitions, feedback, override, escalation, and attribution are approved and enforced; human and model contributions remain separate. | Workflow/API tests; role and resource authorization tests; reviewer acceptance testing; ethics/public-health review |
| OBJ-006 | Participants and community members need confidentiality, informed participation, appropriate withdrawal, and controlled data use. | FR-013 to FR-015, FR-038; NFR-006 to NFR-008, NFR-017, NFR-018, NFR-022 | Narrative data governance; authorization; audit; retention | Data collection has approved consent and ethical basis; access is least-privilege; identity is minimized; retention/deletion/withdrawal and incident procedures are documented; sensitive actions are auditable. | Privacy threat model; access-control tests; data-protection review; ethics approval; audit inspection |
| OBJ-007 | Administrators need account and operational visibility while research data remains purpose-limited. | FR-009 to FR-012, FR-034 to FR-038; NFR-002, NFR-006, NFR-018 | Role management; administrator dashboard; audit logs | Administrators can perform current account operations and view sanitized aggregates/logs; raw narratives, identifiers, datasets, and models require separately approved permissions. | API authorization tests; audit tests; negative-access tests; security review |
| OBJ-008 | Approved users need a usable and accessible Android client that can operate against stable APIs. | FR-028, FR-033; NFR-009 to NFR-016 | Mobile application; notifications; FastAPI integration | Framework, Android range, device/network assumptions, accessibility baseline, response targets, offline behavior, and evaluation criteria are approved; core journeys pass representative tests. | Android device matrix; API contract tests; performance tests against approved targets; usability/accessibility evaluation |

## Requirement-to-Evidence Check

| Requirement group | Current support | Traceability conclusion |
|---|---|---|
| FR-001 to FR-012 and FR-034 to FR-037 | Current FastAPI account/admin implementation and tests provide direct evidence. | These requirements have an implementation path and can be verified now; FR-001 is covered by community self-registration and staff invitation controls. |
| FR-013 to FR-015 | A neutral owner-scoped narrative record and revision foundation exists; approved submission, lifecycle, consent, and role/assignment rules do not. | These requirements are partially traceable to the new record foundation but remain incomplete pending supervisor and policy decisions. |
| FR-016 to FR-019, FR-027, FR-029 to FR-033, and FR-038 | Provisional reviewer assignment, structured review, evidence, history, and escalation implementation exists; health-information, notification, and research-resource implementations do not. | Review links have API/test evidence but remain provisional and depend on supervisor, qualification, public-health, privacy, and ethics decisions. |
| FR-020 to FR-026 and FR-028 | README establishes a proposed pipeline, but no data, model, XAI code, or mobile code exists. | These requirements are blocked by dataset/task availability and associated approvals; dependencies alone do not provide traceability evidence. |
| NFR-001 to NFR-005 | Current security/configuration code and tests provide evidence. | Account security requirements are substantially traceable to implementation. |
| NFR-006, NFR-010, NFR-014, NFR-016 to NFR-018 | Current code provides account-level evidence plus provisional narrative-review resource and audit evidence. | The foundation is traceable, but consent, retention, qualification, and production domain policies are absent. |
| NFR-007, NFR-009, NFR-011 to NFR-013 | No approved deployment, device, accessibility, scale, or performance targets exist. | These remain proposed and require measurable acceptance targets. |
| NFR-008, NFR-019 to NFR-022 | No ethics, data policy, ML/XAI, language, or retention evidence exists. | These are blocked by dataset, supervisor, or ethical/policy decisions. |

## Orphan and Missing Evidence Review

- No major objective is intentionally left without a requirement link.
- The account-management objectives have implementation evidence in the current backend.
- The narrative and provisional review objectives have implementation evidence; ML, XAI, mobile, language, health-source, and ethics objectives remain unsupported by implementation evidence.
- No dataset-specific requirement is allowed to claim a feature, label, task, language, or performance result before dataset delivery and assessment.
- The missing Secure AI Labs plan, proposal, supervisor requirements, and ethics/data documents prevent stronger source traceability. They should be added to the evidence register when supplied.
