# Vaccine AI

## Project Title

A Mobile Application Based on Explainable Artificial Intelligence
for Intelligent Health Communication on Vaccine-Related Narratives.

## Overview

Vaccine AI is a research and software development project that aims
to develop a mobile application integrated with Machine Learning
and Explainable Artificial Intelligence (XAI).

The system will support the interpretation and communication of
vaccine-related data through machine learning analysis and
explainability techniques.

## Main Technologies

- Python
- Pandas and NumPy
- Scikit-learn
- XGBoost (if justified by the dataset)
- SHAP
- LIME (optional)
- FastAPI
- PostgreSQL or SQLite
- Mobile application framework (to be confirmed)

## Project Architecture

Dataset
   |
Data Assessment and Preprocessing
   |
Machine Learning Model
   |
Explainable AI (SHAP)
   |
FastAPI Backend
   |
Mobile Application

## Project Structure

- backend/: Backend application
- mobile/: Mobile application
- data/: Dataset storage and processing
- notebooks/: Exploratory analysis and experiments
- models/: Trained machine learning models
- reports/: Research reports and figures
- docs/: Requirements, architecture, and research documentation
- tests/: Automated tests

## Important Research Principle

The authoritative project dataset must be assessed before selecting
the final machine learning task, target variable, or model.

No dataset columns, labels, or findings should be assumed before
the dataset is received and examined.

## Current Development Status

- [x] Python environment established
- [x] Core project dependencies installed
- [x] Initial project structure created
- [ ] Requirements analysis completed
- [ ] Authoritative dataset received and assessed
- [ ] Machine learning task confirmed
- [ ] Model development
- [ ] SHAP explainability
- [x] Initial backend authentication and account foundation
- [x] Provisional backend narrative review workflow
- [ ] Mobile application development
- [ ] Integration and testing
- [ ] Final documentation

## Backend Account Management

The backend supports self-registration for community members and invitation-based
onboarding for staff. Public registration never grants a staff role: CHWs,
Health Experts, and administrators must be invited by an administrator.

- Community self-registration with full name, email, password confirmation, and email verification
- Invitation-based onboarding for CHWs, Health Experts, and administrators
- Account states and server-side role authorization
- Argon2 password hashing
- Short-lived JWT access tokens and rotating persisted refresh sessions
- Password change and reset flows
- Email verification and account status administration
- Self-service hard account deletion with dependent-data cleanup and email reuse
- PostgreSQL-backed audit events and authentication rate limits

Apply migrations before starting the API:

```text
alembic upgrade head
```

## Backend Test Database

Pytest never uses the development database. `tests/conftest.py` sets
`APP_ENV=test`, selects `vaccine_ai_test` by default, creates it if necessary,
resets only its `public` schema, and runs `alembic upgrade head` before the test
session. The database name must contain a separate `test` segment and must not
match the configured development or production database. No test fixture can
connect to a protected database name.

The configured `DB_USER` must be able to connect to the PostgreSQL maintenance
database and create databases. To use another isolated database, set the
test-only variable before running pytest:

```text
VAXINSIGHT_TEST_DB_NAME=vaccine_ai_test_local
```

If automatic provisioning is not permitted, create the database once as a
PostgreSQL administrator, owned by the configured `DB_USER`, then rerun pytest:

```sql
CREATE DATABASE vaccine_ai_test OWNER postgres;
```

The test bootstrap will reset and migrate that database on each test session.
It never drops the test database or modifies development/production accounts.

Provision the first administrator from the backend directory. The command
prompts for the password instead of accepting it on the command line:

```text
python -m app.cli create-admin --email admin@example.com
```

For local or emergency provisioning without email delivery, create an active,
verified staff account directly from the backend directory. The command prompts
for the password twice and refuses to overwrite an existing email:

```text
python -m app.cli create-staff --email chw@example.com --role chw --full-name "CHW Name"
```

The supported direct-provisioning roles are `chw` and `reviewer`. Use the normal
administrator invitation workflow for production staff onboarding.

Run bounded rate-limit cleanup from the backend directory through an external
scheduler. The defaults remove up to 5,000 expired buckets per invocation:

```text
python -m app.cli cleanup-rate-limits
```

Use `--batch-size` and `--max-batches` to adjust the per-invocation bound.

Configure SMTP settings before using invitations, email verification, or
password reset. Production configuration also requires `DEBUG=false`,
`DB_SSL_MODE=require`, and a secret key of at least 32 characters.
Set `ACCOUNT_ACTION_BASE_URL` to the real hosted browser client when one exists;
otherwise leave it empty and use the native `vaxinsight://` action links for the
mobile app.

## Fine-Grained Permissions

The backend uses a centralized static permission catalogue and explicit
role-to-permission mapping. Current permissions protect account administration,
invitations, audit search, owner-scoped narrative operations, and a provisional
human narrative-review workflow. Analysis, dataset, and model permissions remain
reserved future capabilities.

See [`docs/permission_management.md`](docs/permission_management.md) for the
assessment, matrix, authorization flow, security boundaries, API changes, and
known limitations.

## Disclaimer

Vaccine AI is intended as a research and decision-support system.
It is not a medical diagnostic tool and does not replace qualified
healthcare professionals.
