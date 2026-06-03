# Implementation Order

## Current status

Implementation should not begin yet. The repository does not currently contain the requested canonical planning documents, so this implementation order is a documentation-readiness sequence rather than a backend or frontend build sequence.

This document intentionally avoids prescribing concrete application code tasks because the product requirements, data model, permissions, workflows, API contracts, UI designs, architecture, and development plan are not present in the repository.

## Phase 0: Documentation baseline recovery

**Goal:** Add or recover the missing canonical documentation set.

### Tasks

1. Add `docs/PRD.md`.
2. Add `docs/DATABASE_SCHEMA.md`.
3. Add `docs/PERMISSION_SYSTEM.md`.
4. Add `docs/WORKFLOW_ENGINE.md`.
5. Add `docs/API_SPEC.md`.
6. Add `docs/UI_UX.md`.
7. Add `docs/UI_UX_WIREFRAME.md`.
8. Add `docs/SYSTEM_ARCHITECTURE.md`.
9. Add `docs/DEVELOPMENT_PLAN.md`.

### Exit criteria

- All source documents exist.
- Each document has an owner and review status.
- All domain terms are defined in one shared glossary or consistently defined in the PRD.
- Each document uses the same names for entities, roles, workflows, and screens.

## Phase 1: Product and domain model alignment

**Goal:** Establish the product scope and canonical business vocabulary before technical design starts.

### Tasks

1. Review the PRD for personas, business goals, feature scope, and acceptance criteria.
2. Extract the full entity inventory from the PRD.
3. Extract all user actions and business events.
4. Extract all lifecycle objects that require workflow states.
5. Identify non-functional requirements such as auditability, performance, availability, compliance, and retention.

### Exit criteria

- Every feature has acceptance criteria.
- Every entity has an owner and definition.
- Every business event has an expected actor and outcome.
- Open product questions are resolved or explicitly deferred.

## Phase 2: Data model and workflow design

**Goal:** Define persistence and lifecycle behavior before API and UI contracts are finalized.

### Tasks

1. Map each PRD entity to the database schema.
2. Define relationships, constraints, indexes, uniqueness rules, and deletion/archive behavior.
3. Define workflow state machines for lifecycle entities.
4. Define audit requirements for entity changes and workflow transitions.
5. Identify background jobs, notifications, and side effects.

### Exit criteria

- Every persistent entity has a table or documented non-persistence rationale.
- Every workflow state and transition is documented.
- Every transition has guards, side effects, and audit requirements.
- Schema terminology matches PRD terminology.

## Phase 3: Permission model

**Goal:** Define authorization rules before exposing APIs or UI actions.

### Tasks

1. Define roles and permission names.
2. Map every PRD user action to one or more permissions.
3. Map every workflow transition to required permissions.
4. Define organization, team, ownership, and record-scope access rules.
5. Define administrative override and impersonation/support behavior if applicable.
6. Define field-level restrictions if required.

### Exit criteria

- Every protected action has an explicit permission.
- Every API endpoint planned in the API spec has a permission rule.
- Every UI action has a visibility and disabled-state rule.
- Permission edge cases are documented.

## Phase 4: API contract design

**Goal:** Finalize service contracts after entities, workflows, and permissions are stable.

### Tasks

1. Define authentication/session endpoints.
2. Define CRUD, search, filtering, sorting, pagination, and bulk-action endpoints for entities.
3. Define workflow transition endpoints.
4. Define permission and role administration endpoints.
5. Define reporting and dashboard endpoints.
6. Define integration endpoints if applicable.
7. Define request/response schemas, validation errors, authorization errors, and rate limits.

### Exit criteria

- Every PRD feature has API coverage or an explicit no-API rationale.
- Every endpoint identifies authentication and authorization requirements.
- Every endpoint response uses documented schemas.
- API terminology matches PRD, schema, workflow, and permission terminology.

## Phase 5: UI/UX and wireframe completion

**Goal:** Finalize user journeys and screens after API capabilities are known.

### Tasks

1. Define navigation and information architecture.
2. Define screens for all core entities.
3. Define workflow action screens and confirmation states.
4. Define administration screens for users, roles, and permissions.
5. Define empty, loading, error, access-denied, and success states.
6. Align wireframes with the UI/UX document and API capabilities.

### Exit criteria

- Every user journey in the PRD has a UI flow.
- Every workflow requiring human action has a visible UI affordance.
- Every screen has required data dependencies mapped to API endpoints.
- Permission-driven visibility is documented for each protected action.

## Phase 6: Architecture validation

**Goal:** Confirm that the architecture can support the agreed product, data, permission, workflow, API, and UI requirements.

### Tasks

1. Define system components and service boundaries.
2. Define database, cache, queue, storage, and integration dependencies.
3. Define authentication and authorization architecture.
4. Define audit logging, observability, deployment, and rollback strategies.
5. Define security, privacy, compliance, and data retention behavior.
6. Identify technical risks and mitigation plans.

### Exit criteria

- Architecture supports all documented workflows and permission requirements.
- Operational requirements are documented.
- Major risks have mitigations.
- Implementation milestones can be sequenced safely.

## Phase 7: Development plan finalization

**Goal:** Convert the validated documentation set into an executable implementation plan.

### Tasks

1. Break implementation into milestones.
2. Sequence backend foundations before dependent API and UI work.
3. Sequence UI work after relevant API contracts are stable.
4. Include tests, fixtures, migrations, seed data, and release checks in each milestone.
5. Identify parallelizable workstreams.
6. Define review gates for each milestone.

### Exit criteria

- Every milestone has prerequisites, deliverables, tests, and acceptance criteria.
- Work is ordered by dependency rather than by document order alone.
- No milestone depends on unresolved product or architecture decisions.

## Phase 8: Implementation readiness gate

**Goal:** Decide whether backend and frontend implementation may begin.

### Required checks

1. Re-run the gap analysis against the completed documentation set.
2. Resolve all critical and high-severity gaps.
3. Confirm database migrations can be derived from the schema.
4. Confirm API tests can be derived from the API spec.
5. Confirm UI tests can be derived from UI/UX flows and wireframes.
6. Confirm permission tests can be derived from the permission matrix.
7. Confirm workflow tests can be derived from workflow state machines.

### Exit criteria

- Critical gaps: 0.
- High-severity gaps: 0 or explicitly accepted by the project owner.
- Implementation milestones are approved.
- Backend and frontend work can start without inventing undocumented product behavior.

## Recommended first build sequence after documentation approval

After the documentation set is complete and approved, the likely implementation order should be:

1. Project scaffolding and quality gates.
2. Database migrations and seed data.
3. Authentication and organization/user foundation.
4. Permission enforcement foundation.
5. Core entity models and repository/data-access layer.
6. Workflow engine/state transition foundation.
7. API endpoints for core entities.
8. API endpoints for workflow transitions.
9. Audit logging and notification side effects.
10. UI application shell and navigation.
11. Core entity list/detail/create/edit screens.
12. Workflow UI actions and status views.
13. Administration screens.
14. Reporting/dashboard screens.
15. End-to-end tests and release hardening.

This sequence is provisional and must be revised after the missing documentation is added.
