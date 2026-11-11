# VaxInsight Phase 2/3 Implementation Report

## Executive Status

The repository now contains a working application foundation for the two
vaccine workflows requested for the Rwanda-focused research direction:

1. Official, source-attributed vaccine information.
2. Community/CHW vaccine questions with a separate analysis record and
   professional response workflow.

The application foundation is implemented, but the ML/XAI portion is not
claimed as complete. No Phase 1 dataset, approved model, explanation contract,
linguist validation, or authoritative vaccine-content package is present in the
repository. Until those inputs are approved and supplied, the backend returns a
truthful unavailable analysis state and never fabricates a medical answer.

## Research Alignment

The implementation supports the working primary question:

> How can an integrated ML and explainable-AI solution bridge the gap between
> expert expectations and community awareness in Rwanda's childhood-vaccine and
> pandemic-preparedness context?

The product boundary is deliberately narrower than a clinical assistant. The
system can display approved educational content, collect a question, record an
analysis attempt, and display a qualified professional's response. It does not
diagnose, triage, prescribe, or present an unreviewed model output as medical
truth.

## Implemented Application Foundation

### Official Vaccine Information

- `VaccineSource` stores attribution and source metadata.
- `VaccineContent` stores language-specific title, summary, body, topic, status,
  publication metadata, and source linkage.
- Readers can access published content through:
  - `GET /api/v1/vaccine-content`
  - `GET /api/v1/vaccine-content/{content_id}`
- Administrators can create content through:
  - `POST /api/v1/admin/vaccine-content`
- Content is not seeded with invented medical material. A real deployment needs
  an approved, versioned source allow-list and content review process.

### Community Question and Professional Review

- `VaccineQuestion` stores the question, language, owner, status, and timestamps.
- `QuestionAnalysis` stores immutable analysis attempts, provider/model metadata,
  structured output, limitation text, and status.
- `ProfessionalResponse` stores the separately authored reviewer response and
  publication state.
- Question owners use:
  - `POST /api/v1/questions`
  - `GET /api/v1/questions`
  - `GET /api/v1/questions/{question_id}`
  - `POST /api/v1/questions/{question_id}/analysis`
- Reviewers use:
  - `GET /api/v1/review/questions`
  - `GET /api/v1/review/questions/{question_id}`
  - `POST /api/v1/review/questions/{question_id}/response`
- The question owner can see their own record; reviewer access is separate from
  owner access. A newer published professional response supersedes an older
  published response without deleting history.
- Deleting an account removes owned questions and dependent analysis/response
  records while preserving source attribution and reviewer references safely via
  nullable foreign keys where appropriate.

### Explicit ML/XAI Safety Boundary

The service layer exposes a provider seam but does not select or invent a model.
When no approved provider is configured, the analysis record is persisted as
`unavailable` with the limitation:

> An approved Phase 1 model/dataset is not configured; no AI or medical output
> was generated.

This prevents the UI from implying that a placeholder, generic LLM, or invented
classification is a research result.

## Mobile Implementation

The Expo client now includes:

- Kinyarwanda as the default language for fresh installations, while honoring a
  stored user preference.
- Official vaccine information list/detail screens.
- Question composer, owner question list, and question detail screens.
- Reviewer question queue and professional-response publishing screens.
- Home actions for official information, asking a question, viewing owned
  questions, and reviewer question review.
- English and Kinyarwanda feature copy, status labels, loading, empty, and error
  states.

The mobile client does not contain a fake AI answer state. If the backend marks
analysis unavailable, the limitation is shown as a limitation.

## Phase 1 Inputs Still Required

Before implementing real ML/XAI behavior, the supervisor/data custodian must
provide and approve a dataset package containing, at minimum:

- Provenance, ownership, license, consent/legal basis, and permitted uses.
- Data dictionary, schema, language fields, and source collection context.
- Approved prediction/interpretation task and label definitions.
- Annotation instructions, annotator qualifications, and agreement procedure.
- Privacy/de-identification rules, retention period, deletion/withdrawal process,
  and access controls.
- Language distribution, Kinyarwanda quality assessment, missingness, imbalance,
  and representativeness analysis.
- Train/validation/test split policy with leakage controls.
- Approved public-health sources for any educational recommendation or citation.

The task must not be selected merely because SHAP or LIME is present in the
dependency list. The task, model family, explanation method, uncertainty wording,
and permitted interpretation must follow the dataset assessment and supervisor
approval.

## Phase 2 Completion Criteria

The following work remains after the current application foundation:

1. Complete the dataset assessment and record its decision in the supervisor
   decision register.
2. Approve the prediction/interpretation task, labels, and evaluation split.
3. Implement a versioned inference provider behind the existing analysis seam.
4. Implement model-linked explanations with visible uncertainty and limitations.
5. Add linguist/public-health review for Kinyarwanda labels, explanations, and
   educational wording.
6. Add model and explanation evaluation tests before exposing outputs to users.
7. Add approved source content and a controlled update/withdrawal process.

## Phase 3 Evaluation Plan

The requested deployment/evaluation should compare the integrated application
with the existing teaching or information workflow, subject to supervisor and
ethics approval. The exact design, sample size, randomization, and participant
eligibility are intentionally not invented here.

Candidate participant strata requiring confirmation are:

- Community members who need vaccine information.
- CHWs who support community communication.
- Qualified reviewers or public-health professionals.

Candidate outcome groups are:

- Knowledge: understanding of vaccine purpose, schedule, and reliable sources.
- Trust: perceived source credibility, transparency, and confidence in the
  human-review boundary.
- Behavioral intention: stated intention to seek vaccination information,
  discuss vaccination with a trusted provider, or follow an approved schedule.
- Usability and accessibility: task completion, comprehension, language fit, and
  navigation burden.
- Safety and review quality: unsafe-output rate, reviewer agreement, escalation,
  correction, and response timeliness.
- Technical reliability: API errors, stale-resource handling, authorization
  failures, and mobile performance.

The study protocol must define instruments, baseline/follow-up timing, analysis
methods, privacy protections, adverse-event handling, and what claims are allowed
in the final report. The application should not be presented as effective based
only on successful API or bundle tests.

## Security and Governance Notes

- Question reads are owner-scoped unless the caller is an authorized reviewer.
- Reviewer publishing is separate from question submission and analysis request.
- Administrator content management does not grant unrestricted access to private
  questions or research data.
- Account deletion includes the new question workflow and keeps the existing
  last-administrator protection.
- No LLM assistant, diagnosis, confidence score, SHAP/LIME chart, or automated
  medical recommendation is implemented.
- Ethics approval, consent, retention, withdrawal, source governance, and named
  data ownership remain unresolved decisions.

## Verification

The current implementation was verified with:

- Backend workflow suite: `245 passed`.
- Ruff checks for `backend` and `tests`.
- `python -m alembic check`.
- Expo Android export: successful.
- `npx expo-doctor`: `20/20 checks passed`.

The database migration for the workflow is:

`backend/migrations/versions/b8c9d0e1f2a3_add_vaccine_content_question_workflow.py`

## Next Approved Sequence

1. Obtain and assess the Phase 1 dataset and public-health source package.
2. Record supervisor, linguist, ethics, and data-custodian decisions.
3. Implement and evaluate the approved provider behind the existing unavailable
   boundary.
4. Validate Kinyarwanda wording and explanations with qualified reviewers.
5. Run the approved Phase 3 comparison study and publish only supported claims.
