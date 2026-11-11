# VaxInsight Mobile

The mobile app is a JavaScript Expo/React Native client for the existing VaxInsight API.

## Development

1. Copy `.env.example` to `.env` and set `EXPO_PUBLIC_API_URL` for the device or emulator.
2. Install dependencies with `npm install`.
3. Start the API from the repository root. Use `0.0.0.0` when testing on a physical device:

```text
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

4. Start Expo with `npm start`.

Android emulator API example:

```text
EXPO_PUBLIC_API_URL=http://10.0.2.2:8000/api/v1
```

### Invitation links with Expo Go

Installed builds use `vaxinsight://` links. Expo Go uses an `exp://` link. For a
physical phone, start Expo with `npx expo start --lan`, then set this backend
environment value using the LAN address shown by Expo:

```text
MOBILE_DEEP_LINK_BASE_URL=exp://<your-computer-lan-ip>:8081/--
ACCOUNT_ACTION_BASE_URL=http://<your-computer-lan-ip>:8000/api/v1/auth
```

Keep the phone and computer on the same network, restart the backend, and send a
new invitation. The email will contain a normal clickable HTTP link to the
backend landing page; that page contains the Expo Go handoff link. Revoke and
resend invitations created with the old configuration.

The welcome photograph is currently loaded from Unsplash as
`assets/welcome-clinic-hero.jpg`. Replace it with
approved/licensed project photography before production release; attribution is
recorded in `assets/ATTRIBUTION.md`.

The app does not invent ML output, medical conclusions, Health Expert data, or role
capabilities. Authenticated content is gated by the backend session and role.

## Supported Workflows

- Public auth: registration, sign-in, password reset, email verification, and invitation acceptance.
- Account: email-change request, verification resend, password change, session expiry recovery, and confirmed logout.
- Owner narratives: create, list, detail, edit, and revision history for `community_member` and `chw` accounts; Health Experts remain assignment-scoped.
- Health Expert workflow: assigned queue, `in_review` transition, evidence-backed review submission, escalation, and review history.
- Administrator workspace: dashboard, user directory, account role/status changes, staff invitations, invitation revocation, audit log, role permissions, permission catalogue, own narrative workspace, and source-backed vaccine-content publishing.

Password-reset and invitation links use the `vaxinsight://` scheme. The invitation
token is consumed internally by the deep link; invitees only see the acceptance
page and password fields, not a token input:

- `vaxinsight://reset-password/:token`
- `vaxinsight://invite/:token`

Email verification uses a six-digit OTP sent to the registered email address.
After a successful OTP verification, the API returns a session and the app
opens Home without a separate sign-in step.

The mobile client does not expose administrator narrative assignment management
or ML/XAI screens because those boundaries require separate product approval and
backend contracts.
