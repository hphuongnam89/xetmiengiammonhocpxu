# Product Scope

## Purpose

This system supports Vietnamese university staff in reviewing course-exemption requests. Sales users upload student degree, transcript, certificate, and supporting documents. AI extracts structured academic data and proposes course-recognition results using versioned rules and curriculum data. Teachers review the proposal and make the final decision. Administrators manage users, rules, curriculum versions, audit records, and AI usage costs.

## Scope

The system covers:

- Upload and private storage of academic documents for six sales accounts.
- AI-assisted OCR and extraction of courses, grades, credits, and document metadata.
- Versioned rules and curriculum data for course-recognition proposals.
- Teacher review, per-course correction, approval, rejection, and requests for more documents.
- Notifications to sales users after teacher decisions.
- Administration of users, roles, rules, curriculum versions, audit logs, and AI token/cost usage.
- Search, filtering, and status tracking across submissions and decisions.

## Roles

- **Sales user:** Creates submissions, uploads documents, answers requests for additional evidence, and receives final results.
- **Teacher reviewer:** Reviews source documents and AI proposals, edits individual course results, records reasons, and makes the final decision.
- **Administrator:** Manages users, permissions, assignments, rules, curriculum versions, audit logs, and AI cost controls.
- **AI service:** Extracts data and generates proposals only. It never makes the final decision.

## Core Workflow

1. A sales user creates a submission and uploads one or more documents.
2. The system validates the files and queues extraction.
3. AI extracts structured academic data and records confidence and source pages.
4. The rule engine applies the active rule and curriculum versions.
5. AI may assist with course matching and explanation; uncertain results are marked for review.
6. The assigned teacher reviews the documents, extracted data, and per-course proposals.
7. The teacher keeps, edits, adds, or removes course results and records the final decision.
8. The system records the decision and notifies the responsible sales user.
9. Administrators can audit every change and monitor AI usage and cost.

## Non-goals

- The system does not replace the university's legal or academic authority.
- The system does not invent rules, thresholds, percentages, or curriculum mappings.
- The AI does not override a teacher's final decision.
- Public student self-service and external-party access are outside the initial release.
- Automatic model training from unreviewed historical data is outside the initial release.

## Acceptance Criteria

- A sales user can create a submission, upload documents, and see processing status.
- The system preserves original files and shows extracted values with source evidence.
- A teacher can inspect, modify, and finalize each course result.
- The final result is distinguishable from the AI proposal.
- Administrators can manage users, rules, curriculum versions, and permissions.
- Audit records identify who changed what and when.
- AI provider, model, token usage, cost, and operation are recorded.
- No AI operation can finalize a submission without teacher authorization.
