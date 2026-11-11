# VaxInsight Mobile Role And Navigation Matrix

The backend remains the authorization source of truth. Mobile visibility is a
discoverability layer only and must never replace API authorization.

| Screen/route | Allowed roles | Permission/API dependency | Entry point | Back destination | State coverage | Status |
|---|---|---|---|---|---|---|
| `Welcome` | Public | None | App launch | None | Entrance, slider reset, plain branded layout | Implemented |
| `AuthChoice` | Public | None | Completed welcome slider | `Welcome` | Normal, back | Implemented |
| `Login` | Public | `POST /auth/login` | Auth choice, reset, register success | Previous auth route | Form validation, submitting, API error | Implemented |
| `Register` | Public | `POST /auth/register` | Auth choice/login | Previous auth route | Form validation, submitting, generic/API error | Implemented |
| `PasswordReset` | Public | `POST /auth/password-reset/request` | Login | `Login` | Generic success, validation, API error | Implemented |
| `PasswordResetConfirm` | Public deep link | `POST /auth/password-reset/confirm` | `vaxinsight://reset-password/:token` | Login | Token/password validation, success, expired token | Implemented |
| `VerifyEmail` | Public registration flow | `POST /auth/email/verify`, `/auth/email/verify/resend` | Registration with six-digit email OTP | Home after session establishment | Pending, success, invalid/expired OTP, resend | Implemented |
| `InvitationAccept` | Public deep link | `POST /auth/invitations/accept` | `vaxinsight://invite/:token` | Home after session | Internal token handling, password confirmation, invalid/expired/used invitation | Implemented |
| `Home` | Active authenticated account | `GET /auth/me`; CHW activity uses `GET /dashboard/summary` | Successful login/session restore | Logout | Profile load, personal metrics, refresh failure, role/status | Implemented |
| `Account` | Active authenticated account | `PATCH/DELETE /auth/me`, `POST /auth/password/change` | Home profile action | Home | Email update, password change, verification resend, logout and deletion confirmation | Implemented |
| `SessionExpired` | Active session with 401 | Refresh/authenticated API failure | Auth context | Sign in after local sign-out | Reauthentication recovery | Implemented |
| My narratives | `community_member`, `chw`, `reviewer` | `narrative.read.own` and `GET /narratives` | Home workflow action | Home | Loading, empty, errors | Implemented |
| Narrative submit | Roles with `narrative.create` | `POST /narratives` | My narratives | My narratives | Validation, submit, retry | Implemented |
| Narrative detail/edit/history | Owner roles with own permissions | Narrative detail/history/update endpoints | My narratives | My narratives | Loading, conflict, not found, revision history | Implemented |
| Personal CHW activity | `chw` | `narrative.read.own`; `GET /dashboard/summary` | CHW Home | Home | Loading, status-only metrics, recent records, API failure | Implemented |
| My questions | `community_member`, `chw` | `question.create`, `question.read.own`; `GET /questions` | Bottom navigation or Home question action | Home | Loading, empty, errors, owner scope | Implemented |
| Ask question | `community_member`, `chw` | `question.create`; `POST /questions` | My questions or CHW Home | My questions | Validation, submitting, unavailable analysis, rate limit | Implemented |
| Question detail/history | `community_member`, `chw` | `question.read.own`, `vaccine_analysis.read`; `GET /questions/{id}` | My questions | My questions | Loading, unavailable analysis, professional response, not found | Implemented |
| Reviewer queue | Active `reviewer` with `narrative.read.assigned` | `GET /reviews/assignments` | Home workflow action | Home | Loading, empty, errors | Implemented |
| Reviewer detail/history | Active assigned reviewer | Review assignment/history endpoints | Reviewer queue | Reviewer queue | Access, revoked, conflict, errors | Implemented |
| Review submission | Active assigned reviewer with `narrative.review` | Review status/review endpoints | Reviewer detail | Reviewer detail | Validation, submit, success, failure | Implemented |
| Administrator dashboard | Active administrator | `GET /admin/dashboard/summary` | Home administrator card or administrator tab | Home | Loading, refresh, unauthorized, retry | Implemented |
| Administrator user directory | Active administrator with `user.read` | `GET /admin/users` | Administrator dashboard | Administrator dashboard | Search, filters, pagination, empty, errors | Implemented |
| Administrator user details | Active administrator with `user.read` and `role.read` | `GET /admin/users/{id}`, `GET /admin/users/{id}/permissions` | User directory | User directory | Loading, not found, unauthorized, retry | Implemented |
| Administrator role/status actions | Active administrator with `role.manage` or `user.manage` | `PATCH /auth/admin/users/{id}/role`, `/status` | User details | User details | Confirmation, self-protection, conflict, success, failure | Implemented |
| Staff invitation | Active administrator with `invitation.manage` | `POST /auth/invitations` | Administrator dashboard or invitation directory | Administrator dashboard | Validation, delivery success, expiry, API failure | Implemented |
| Invitation directory/details | Active administrator with `invitation.manage` | `GET /admin/invitations`, `/admin/invitations/{id}` | Administrator dashboard | Administrator dashboard | Filters, pagination, empty, not found, errors | Implemented |
| Invitation revocation | Active administrator with `invitation.manage` | `POST /admin/invitations/{id}/revoke` | Invitation directory/details | Invitation details | Confirmation, pending-only conflict, success, failure | Implemented |
| Administrator audit log | Active administrator with `audit.read` | `GET /admin/audit-events` | Administrator dashboard | Administrator dashboard | Filters, pagination, expandable details, empty, errors | Implemented |
| Role and permission inspection | Active administrator with `role.read` | `GET /admin/roles`, `/admin/roles/{role}`, `/admin/permissions` | Administrator dashboard | Administrator dashboard | Loading, reserved capabilities, empty, errors | Implemented |
| Vaccine-content management | Active administrator with `vaccine_content.manage` | `POST /admin/vaccine-content`, published `GET /vaccine-content` | Administrator dashboard or Home administration card | Administrator dashboard | Source/content validation, draft/published choice, success, empty, errors | Implemented |
| Professional question queue | Active reviewer with `question.review` | `GET /review/questions` | Reviewer Home workflow action | Home | Loading, empty, errors | Implemented |
| Professional question response | Active reviewer with `question.review` | `POST /review/questions/{id}/response` | Professional question queue | Question queue | Validation, publish, supersede, failure | Implemented |
| Administrator assignment | Active administrator with `narrative.assign` | Assignment endpoints | Optional approved admin navigation | Admin home | Eligibility, conflict, success, failure | Optional/not approved |
| Profile/settings | Active authenticated account | `GET/PATCH/DELETE /auth/me`, password endpoint | Home profile action | Home | Loading, validation, deletion confirmation, failure | Implemented |
| Analysis/XAI | None currently | No model/inference/XAI endpoint exists | None | None | Unavailable state only | Blocked |

## Current Role Mapping

| Role | Mobile-accessible screen today | Backend boundary |
|---|---|---|
| `community_member` | Welcome, auth, Home, My narratives, narrative workflows | Own narrative permissions only; no ML output. |
| `chw` | Welcome, auth, Home with personal activity, My narratives, narrative workflows, My questions, question workflows, published vaccine information | `vaccine_content.read`, `narrative.create`, `narrative.read.own`, `narrative.update.own`, `question.create`, `question.read.own`, `vaccine_analysis.request`, and `vaccine_analysis.read`; no assigned-review access inferred. |
| `reviewer` | Welcome, auth, Home, My narratives, Review queue, review workflows | Assigned-review permissions remain backend-authoritative. |
| `administrator` | Welcome, auth, Home, own narratives, Administrator dashboard, user/invitation/audit/role/permission/content screens | Account/content administration remains separate from raw narrative and research-data access. |
