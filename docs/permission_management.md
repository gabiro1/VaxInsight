# VaxInsight Permission Management

## Status

This document records the fine-grained authorization implementation for the
current backend scope. Health Expert assignment and human review are implemented as a
minimal workflow. Analysis, dataset, model, and health-communication workflows
remain outside the approved scope.

## Initial Assessment

Before implementation, the backend was inspected across routes, dependencies,
models, migrations, services, schemas, tests, and project requirements.

- Users had one nullable `users.role` value and four existing role identifiers.
- `get_current_user` validated JWTs and active account state.
- Administrator routes used a reusable administrator-only role dependency.
- Narrative routes required authentication and enforced owner scope in the
  narrative service, but had no action-level permission checks.
- No permission catalogue, role-permission mapping, assignment entity, Health Expert
  workflow, or custom-role API existed before the permission foundation was added.
- Account administration and audit access were separate from narrative content;
  administrator access to other users' narratives was already denied.
- Existing requirements leave CHW/Health Expert assignment, review authority, dataset
  access, model access, and administrator research-data access unresolved.

The implementation therefore uses a static role-to-permission configuration and
does not add database tables or mutable permission administration.

## Architecture

Permission definitions and the explicit role mapping are centralized in
`backend/app/core/permissions.py`.

- `Permission` is the stable identifier enum.
- `PERMISSION_DEFINITIONS` is the catalogue and records implementation and
  assignability status.
- `ROLE_PERMISSIONS` explicitly lists permissions for every current role.
- Unknown permission identifiers fail closed with `ValueError` during dependency
  construction or direct permission validation.
- Known but future permissions are listed for documentation, are not assigned to
  any role, and cannot be used to construct an API authorization dependency until
  they are marked implemented.
- `require_permissions` enforces all requested permissions.
- `require_any_permissions` supports an explicit any-permission policy for future
  routes.
- Review routes use `narrative.assign` for assignment managers and
  `narrative.read.assigned`/`narrative.review` for assigned Health Experts. Resource
  checks remain in the review service and do not rely on a role alone.
- Existing `require_roles` remains available for compatibility, but protected
  role-sensitive routes use permission dependencies.

Authentication remains unchanged. `get_current_user` still validates the access
token and reloads the current account, including its current lifecycle state,
before a permission dependency runs.

## Permission Catalogue

| Permission | Capability | Status | Assignable now |
|---|---|---|---|
| `user.read` | View permitted user information | Implemented | Yes |
| `user.manage` | Manage user account lifecycle state | Implemented | Yes |
| `role.read` | View role assignments and mappings | Implemented | Yes |
| `role.manage` | Assign an existing application role | Implemented | Yes |
| `invitation.manage` | Create, inspect, and revoke invitations | Implemented | Yes |
| `narrative.create` | Submit a narrative record | Implemented | Yes |
| `narrative.read.own` | Read narratives owned by the authenticated user | Implemented | Yes |
| `narrative.update.own` | Update narratives owned by the authenticated user | Implemented | Yes |
| `narrative.assign` | Create, reassign, and revoke narrative review assignments | Implemented | Yes |
| `narrative.read.assigned` | Read narratives explicitly assigned to the authenticated user | Implemented | Yes |
| `narrative.review` | Perform an authorized narrative review | Implemented | Yes |
| `vaccine_content.read` | Read published official vaccine content | Implemented | Yes |
| `vaccine_content.manage` | Create and publish official vaccine content | Implemented | Yes |
| `question.create` | Ask a vaccine question | Implemented | Yes |
| `question.read.own` | Read questions asked by the authenticated user | Implemented | Yes |
| `question.review` | Review questions and publish professional responses | Implemented | Yes |
| `vaccine_analysis.request` | Request a vaccine-question analysis run through the approved provider boundary | Implemented boundary; provider unavailable | Yes |
| `vaccine_analysis.read` | Read vaccine-question analysis runs | Implemented boundary; provider unavailable | Yes |
| `analysis.request` | Request an analysis when available | Reserved for future analysis capability | No |
| `analysis.read` | Read authorized analysis results | Reserved for future analysis capability | No |
| `dataset.manage` | Manage approved dataset metadata | Reserved for future dataset governance | No |
| `model.manage` | Manage approved model metadata | Reserved for future model governance | No |
| `audit.read` | Read authorized audit records | Implemented | Yes |

Future permissions have no role assignment and no route. Defining a permission
name does not create the corresponding business functionality.

## Role Matrix

| Role | Implemented permissions | Boundary rationale |
|---|---|---|
| `community_member` | `vaccine_content.read`, `narrative.create`, `narrative.read.own`, `narrative.update.own`, `question.create`, `question.read.own`, `vaccine_analysis.request`, `vaccine_analysis.read` | Own narrative/question workflows and published content only; analysis remains an explicit unavailable boundary when no provider is configured. |
| `chw` | `vaccine_content.read`, `narrative.create`, `narrative.read.own`, `narrative.update.own`, `question.create`, `question.read.own`, `vaccine_analysis.request`, `vaccine_analysis.read` | Own narrative/question workflows and published content only; no assigned-record, Health Expert, administrator, audit, or participant-data access is inferred. |
| `reviewer` | `vaccine_content.read`, `narrative.create`, `narrative.read.own`, `narrative.update.own`, `narrative.read.assigned`, `narrative.review`, `question.create`, `question.read.own`, `question.review`, `vaccine_analysis.request`, `vaccine_analysis.read` | Assigned-record access is still limited to active assignments; the role alone does not grant access to another user's narrative. |
| `administrator` | `user.read`, `user.manage`, `role.read`, `role.manage`, `invitation.manage`, `narrative.assign`, `narrative.create`, `narrative.read.own`, `narrative.update.own`, `vaccine_content.read`, `vaccine_content.manage`, `audit.read` | Can manage accounts, content, assignment metadata, and audit records but does not receive unrestricted narrative content through the review API. |

The owner permissions for staff and administrators are narrow permissions, not
administrator access to research content. An administrator cannot read or
update another user's narrative through the current API.

## Authorization Flow

1. FastAPI resolves `get_current_user`.
2. JWT claims are validated and the user is reloaded from PostgreSQL.
3. Inactive, suspended, deactivated, deleted, malformed, expired, or stale
   post-password-change credentials are rejected with `401` by the existing
   authentication boundary.
4. The route-specific permission dependency checks the current server-side role.
5. Missing permissions receive the consistent `403` response
   `{"detail": "Insufficient permissions"}`.
6. The handler applies resource-level authorization. Narrative services query by
   both narrative identifier and owner identifier, returning `404` when the
   caller is not the owner.

Permission checks never trust a role, permission list, or ownership value sent by
the client. Role and status request schemas reject unexpected fields, including
permission injection fields.

## Protected API Changes

Existing endpoints now use these permissions:

| Endpoint group | Permission |
|---|---|
| `POST /api/v1/auth/invitations` | `invitation.manage` |
| `PATCH /api/v1/auth/admin/users/{user_id}/status` | `user.manage` |
| `PATCH /api/v1/auth/admin/users/{user_id}/role` | `role.manage` |
| Administrator user directory and details | `user.read` |
| Administrator invitation list, details, and revoke | `invitation.manage` |
| Administrator dashboard summary | `user.read` |
| Administrator audit search | `audit.read` |
| Narrative create | `narrative.create` |
| Narrative list, detail, and history | `narrative.read.own` plus owner query scope |
| Narrative update | `narrative.update.own` plus owner query scope |
| Narrative assignment management | `narrative.assign` plus submitted-narrative and eligible-reviewer checks |
| Assigned narrative list/detail | `narrative.read.assigned` plus active Health Expert-assignment scope |
| Review status and history | `narrative.read.assigned` for Health Experts or `narrative.assign` for assignment managers |
| Review submission | `narrative.review` plus active reviewer-assignment scope |
| Personal dashboard summary (`GET /api/v1/dashboard/summary`) | `narrative.read.own` plus authenticated owner scope; returns only owned narrative counts and status-only recent records. |
| Published vaccine content (`GET /api/v1/vaccine-content`, `GET /api/v1/vaccine-content/{id}`) | `vaccine_content.read`; published records only. |
| Owned questions and analysis | `question.create`, `question.read.own`, `vaccine_analysis.request`, `vaccine_analysis.read`; owner scope and shared rate-limit boundary. |
| Question review queue and response | `question.review`; Health Expert-only queue and professional-response routes remain separate from owner access. |

New protected read-only administrator inspection endpoints are available:

- `GET /api/v1/admin/permissions`
- `GET /api/v1/admin/roles`
- `GET /api/v1/admin/roles/{role}`
- `GET /api/v1/admin/users/{user_id}/permissions`

The last endpoint requires both `user.read` and `role.read`, and returns no
credentials, tokens, narrative content, or future permissions. There is no API
for editing permission definitions, assigning individual permissions, or
creating custom roles.

Authenticated self-service operations such as the current profile, logout, and
password change retain the existing account-authentication boundary. The
permission catalogue is focused on role-sensitive and resource-sensitive
operations; it does not add artificial permissions to the authentication system.

## Ownership and Assignment Rules

- A narrative owner is `narratives.submitted_by_id`.
- `narrative.read.own` and `narrative.update.own` are valid only when that owner
  identifier equals the authenticated user's identifier.
- List queries are filtered by owner in SQL and cannot return another user's rows.
- Detail, update, and history queries return `404` for another user's identifier,
  avoiding disclosure of whether a private narrative exists.
- `narrative_assignments` preserves assignment history and enforces one active
  assignment per narrative. Reassignment and revocation retain the prior row and
  require a reason.
- `narrative_reviews` and `review_evidence_references` are append-only through the
   API. Review records are visible to the active assigned Health Expert and assignment
  managers, not narrative owners.
- Administrator assignment permission does not bypass narrative ownership or
  return narrative content through assignment-management responses.
- An active narrative assignment prevents the owner from editing the submitted
  content, preserving the version presented to the reviewer; the API returns a
  conflict rather than silently changing the review target.

## Database and Migration Decision

The static role-to-permission mapping remains configuration-backed, while the
approved review workflow uses a new migration for assignment, review, and
evidence records. No custom-role or permission-definition tables were added.

- Existing role identifiers and user rows remain unchanged.
- No user, narrative, or audit data is deleted or rewritten.
- `a7b8c9d0e1f2_add_narrative_review_workflow.py` creates the three review tables,
  constraints, indexes, and a reversible partial unique index for one active
  assignment per narrative.
- Future custom-role decisions must preserve the current fail-closed permission
  default and use a separately reviewed migration.

## Security Considerations

The implementation verifies:

- Anonymous callers receive `401` on protected permission and domain routes.
- Authenticated roles without a required permission receive `403`.
- Cross-user narrative access remains `404`, including for CHWs, Health Experts, and
  administrators without an assignment/ownership relationship.
- Inactive accounts have no effective permissions and cannot authenticate.
- Role changes remain administrator-controlled and retain self-demotion and
  last-administrator protections.
- Permission fields submitted in role, status, or invitation payloads are rejected.
- Future permissions cannot be assigned by the current role mapping or used to
  construct an authorization dependency.
- Permission inspection is itself protected by `role.read`, and user effective
  permission inspection additionally requires `user.read`.
- Responses continue to exclude passwords, token values, token hashes, secrets,
  and private narrative content. Permission inspection does not log or return
  sensitive data.
- Review audit events record assignment, status, escalation, and outcome metadata
  without storing narrative content, review notes, evidence text, or reassignment
  reasons in audit details.
- Health Expert access is checked against the current active assignment and current
  account state, so revocation or role/status changes take effect at request time.
- Personal dashboard responses are marked `no-store` and return status-only
  review metadata; Health Expert notes, outcomes, evidence, and other users' records
  are not serialized.
- Question creation and repeat analysis requests use account-bound shared rate
  limits; the question API has no fabricated analysis fallback.

The existing JWT contract remains short-lived. Logout and session revocation
invalidate refresh sessions; an already-issued access token continues to follow
the existing short lifetime unless account state or password-change invalidation
also rejects it.

## Verification

The permission implementation adds unit and API coverage for catalogue
consistency, explicit role mappings, unknown and future permissions, all/any
checks, administrator inspection, inactive effective permissions, anonymous and
non-administrator denial, ownership boundaries, and permission-payload injection.
Existing authentication, account, invitation, administrator, narrative, audit,
OpenAPI, concurrency, and security tests remain in the suite.

Current CHW-extension verification:

- `python -m pytest tests/test_dashboard_api.py tests/test_supervisor_workflow.py tests/test_narrative_review_workflow.py tests/test_openapi_documentation.py tests/test_database_isolation.py -q`: `28 passed`.
- `python -m ruff check backend tests`: all checks passed.
- `python -m alembic check`: no new upgrade operations detected.
- Mobile Node contract/theme tests: `9 passed`; Android Expo export passed.
- A full `python -m pytest tests/ -q -ra` run against the isolated `vaccine_ai_test` database passed: `268 passed`. The development database `vaccine_ai` was not modified.
- Repository-wide Ruff formatting still reports pre-existing drift in unrelated files; the touched dashboard schema/service were formatted, while the existing `tests/test_supervisor_workflow.py` drift remains.

## Known Limitations and Unresolved Decisions

- The current workflow implements the supervisor-approved provisional assignment
  decisions recorded in the decision register; those decisions still require
  formal confirmation by the named authority before production use.
- `requires_escalation` is an explicit hold state and has no automatic resolution
  transition. A future approved escalation policy may define the next human action.
- Administrator access to raw narratives, participant identifiers, datasets,
  model artifacts, and explanations remains unapproved and is not granted.
- Analysis, dataset, model, notification, public-health content, and ML/XAI
  capabilities remain unavailable.
- The static mapping cannot represent per-user exceptions or custom roles. That is
  intentional until governance requirements justify a database-backed design.
- The existing access-token revocation contract is unchanged; immediate access
  token blacklisting would be a separate authentication decision.

## Recommended Next Implementation

Obtain and record formal supervisor, privacy, and ethics confirmation for the
provisional review decisions before production use. Keep analysis, dataset,
model, notification, and health-communication permissions reserved until their
separate requirements and authorities are approved.
