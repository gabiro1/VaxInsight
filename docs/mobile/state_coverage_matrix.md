# VaxInsight Mobile State Coverage Matrix

This matrix records what the current client handles and what remains required
before each supported workflow can be considered complete.

| Workflow | Loading | Empty | Success | Validation | Network/API | Authorization/conflict | Recovery | Current status |
|---|---|---|---|---|---|---|---|---|
| App/font/session bootstrap | Center loader | N/A | Routes to public/authenticated stack | N/A | Session restore fails closed | Invalid session clears local tokens | Restart/login path still needs dedicated messaging | Incomplete |
| Welcome | Entrance animation | N/A | Slider navigates once | N/A | Bundled plain layout has no image dependency | N/A | No image fallback required | Implemented |
| Language | Immediate local state | N/A | AsyncStorage persists `en`/`rw` | Supported languages only | Storage failure is not surfaced | N/A | Default English fallback | Implemented |
| Login | Button spinner | N/A | Session stores tokens and loads `/auth/me` | Required fields | Network/API message | 401 generic message | Retry by resubmitting; session refresh on restore | Implemented |
| Registration | Button spinner | N/A | Opens email-verification route with submitted email | Required fields/password mismatch | Network/API message | Duplicate email uses server message without local enumeration | Retry preserves form values | Implemented |
| Password reset request | Button spinner | N/A | Generic success notice | Required email | Generic API message | Backend intentionally avoids account disclosure | Retry form submission | Implemented |
| Password reset confirmation | Button spinner | N/A | Success notice then sign-in route | Required token/password/match | API message | Invalid/expired token remains on form | Deep-link token or manual entry | Implemented |
| Email verification/resend | Button spinner | N/A | Six-digit OTP verification establishes a session and opens Home; resend remains generic | Required OTP/email | API message | Invalid/expired OTP remains on form | Resend or retry OTP | Implemented |
| Invitation acceptance | Button spinner | N/A | API-issued session opens Home | Required token/password | API message | Invalid/expired/used invitation maps to 400/409 copy | Preserve token/password for retry | Implemented |
| Session expired | N/A | N/A | Reauthentication returns to authenticated stack | N/A | Authenticated 401 switches route | Sign-out clears local tokens | Sign in again | Implemented |
| Authenticated Home | Session loader/refresh; CHW activity loader | Empty narrative/activity states | Profile, role/status, CHW owned metrics, recent records render | N/A | Pull-to-refresh and dashboard API notices | Backend remains authoritative; internal review data stays hidden | Retry refresh/sign out | Implemented |
| Narrative submission | Button spinner | Empty composer is validated | Detail route after create | 1–10,000 chars; backend content rules | Localized API status mapping | 403/409 preserve content | Retry preserves entered content | Implemented |
| Narrative list/detail/history | Initial loader/refresh | Empty state | Owner content, status-only review metadata, and revision history render | N/A | 404/403/409 conflict mapped | Owner scope remains backend-authoritative; active review locks edits | Retry or return to list | Implemented |
| Personal CHW dashboard | Activity loader | No owned narratives/zero metrics | Owned counts and recent status-only records render | N/A | Dashboard 401/403/network notice | SQL owner scope; no Health Expert notes/outcomes/evidence | Pull to refresh | Implemented |
| Question list/detail | Initial loader/refresh | No owned questions | Owner questions, unavailable analysis, and published professional response render | N/A | 404/403/429/503 mapped | Question owner scope remains backend-authoritative | Retry or return to list | Implemented |
| Question submission/analysis | Button spinner | N/A | Question persists; unavailable analysis remains explicit | Content/language validation | 422/429/503 mapped | Only owned question analysis can be requested | Retry preserves question form | Implemented |
| Health Expert assignment list/detail | Initial loader/refresh | Empty queue | Active assigned narrative renders | N/A | 403/404/503 mapped | Revoked/stale assignments remain recoverable | Retry or return to queue | Implemented |
| Review submission/escalation | Action spinners | No evidence is valid | Review status/history updates | Outcome, escalation reason, evidence fields | 422/409 mapped | Only assigned Health Expert can submit | Input remains after failure | Implemented |
| Official vaccine content/article detail | Initial loader/refresh | Approved-content empty state | Source, authority, date, summary, body, and original source link render | N/A | 403/404/408/429/503 mapped | Published-content permission remains backend-authoritative | Retry, refresh, or return to resources | Implemented at API/UI boundary |
| Resources hub/learning library | Initial screen load | Honest empty state when approved learning content is absent | Official content and question entry points render | N/A | Network/API notice | Role-aware question entry point; no fabricated resources | Retry or return to Home | Implemented; learning content blocked |
| Profile/password/email/delete | Screen/form loading | N/A | Account updates show success notices; email change enters verification; deletion returns to guest flow | Required fields/password match; destructive confirmation | Localized API status mapping | 401 switches to session recovery; 409 preserves form | Retry preserves entered values; deletion clears local session after success | Implemented |
| Analysis/XAI | N/A | Unavailable state required | Blocked | N/A | Blocked by missing API/model | No permission/API exists | Explain limitation and return | Blocked |

## Shared State Components

- `FullScreenLoader` implemented
- `InlineNotice` implemented
- `EmptyState` implemented
- `ErrorState` implemented
- `OfflineState` implemented
- `SessionExpiredScreen` implemented
- Platform confirmation alert implemented for logout
