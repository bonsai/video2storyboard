# PRD: LangGraph-Driven Development Workflow

- **Status:** Draft for implementation
- **Date:** 2026-10-23
- **Repository:** `bonsai/video2storyboard`
- **Related workflow specification:** `dev.wf.yml`

## 1. Summary

Make the development process itself a LangGraph-orchestrated workflow instead of relying on the human to manually direct an LLM through each development step. The graph should interpret requirements, inspect the repository, survey existing libraries and projects, propose a plan, create/update GitHub Issues and design artifacts, implement small changes, run tests, inspect failures, and prepare a reviewable result.

The video-to-dance pipelines are the first target domain, but the workflow engine should be reusable for other units in this repository.

## 2. Problem

Today, development depends on a human manually prompting an LLM, coordinating research, writing design files, editing code, and checking results. This makes the process difficult to reproduce, resume, audit, and improve. A workflow YAML describes intended steps but does not itself execute them.

## 3. Goals

- Orchestrate the development lifecycle through LangGraph nodes and explicit conditional edges.
- Make repository inspection and survey/reuse evaluation mandatory before proposing new dependencies, plugins, or custom implementations.
- Use GitHub Issues as canonical work entry points and keep requirements/design decisions in versioned files.
- Support small, independently testable work units with explicit inputs, outputs, exit criteria, and error handling.
- Persist graph state so interrupted work can resume without losing completed steps.
- Keep humans in the loop for scope approval, destructive actions, credential-sensitive operations, and final merge/release decisions.
- Support Python by default while allowing Rust or other languages when survey evidence justifies them.
- Treat `dev.wf.yml` as declarative workflow configuration and validate it against an explicit schema.

## 4. Non-goals

- Fully autonomous merging or releasing without human approval.
- Replacing GitHub, the repository, tests, or code review as the source of truth.
- Building a custom plugin when a maintained library, CLI, API, or MCP server already meets requirements.
- Requiring every processing component to use Python.
- Starting with multi-agent complexity when a single graph with clear nodes is sufficient.
- Claiming work is complete merely because a node generated text or code; completion requires observable checks.

## 5. Primary users and use cases

### Primary user
A repository maintainer who directs development goals in natural language and wants the system to turn them into traceable, tested changes.

### Core use cases
1. Convert a natural-language request into a scoped PRD/Issue and acceptance criteria.
2. Inspect repository structure, existing code, dependencies, and open Issues before changing anything.
3. Survey candidate libraries/projects, including non-Python options, and record evidence and trade-offs.
4. Recommend a plan and pause for approval where required.
5. Implement one small unit at a time, using existing tools where possible.
6. Run relevant tests, validate schemas and artifacts, and route failures back to diagnosis/fix with a bounded retry budget.
7. Produce a summary with changed files, test evidence, unresolved risks, and next steps.

## 6. Proposed workflow

```text
Request
  -> Normalize requirements
  -> Inspect repository + related Issues
  -> Survey reusable libraries/projects
  -> Evaluate candidates and implementation options
  -> Draft plan / design / acceptance tests
  -> Human approval gate (scope, dependencies, risky actions)
  -> Create or update GitHub Issue
  -> Implement smallest work unit
  -> Run tests and artifact validation
       -> pass: review diff and evidence
       -> fail: diagnose -> bounded repair loop -> test again
  -> Human review gate
  -> Commit/PR preparation (never auto-merge by default)
  -> Report status and checkpoint
```

The graph should support conditional branches for: more research required, existing solution can be reused, custom implementation justified, human input required, tests failed, and task blocked.

## 7. Functional requirements

### FR-1: Request normalization
Convert a request into a structured record containing goal, context, constraints, expected artifacts, acceptance criteria, risk level, and unresolved questions.

### FR-2: Repository reconnaissance
Inspect relevant files, project structure, dependencies, tests, Issues, and existing workflows. Record the inspected commit/ref to make the result reproducible.

### FR-3: Survey-first decision
Before new code or dependencies are proposed, search existing libraries, projects, CLIs, APIs, and MCP servers. Compare fit, license, maintenance, security, platform compatibility, local/CPU support, performance, integration cost, and lifecycle cost. Save sources and rationale in a survey artifact. If evidence is insufficient, continue research or report a blocker.

### FR-4: Language selection
Choose implementation language per unit. Python is the default for orchestration/glue; Rust or another language is allowed when an existing solution or measured requirement justifies it. Do not rewrite working code merely to change language.

### FR-5: Issue and artifact management
Create or update a GitHub Issue as the canonical entry point for implementation work. Keep PRD/ADR/YAML schemas and architecture maps versioned in the repository. Avoid duplicate Issues by searching before creation.

### FR-6: Plan and approval
Create a step plan with dependencies, expected outputs, tests, cost/risk notes, and rollback approach. Require explicit human approval before destructive changes, adding sensitive permissions, publishing artifacts, or merging/releasing.

### FR-7: Bounded implementation
Implement one small unit at a time. Every implementation step must state its expected files and verify the resulting diff. Never treat generated output as successful without checking it.

### FR-8: Test and repair loop
Run targeted tests first, then broader checks when relevant. On failure, capture the error, diagnose, and retry repair only within a configurable budget. After the budget is exhausted, stop and report the blocker rather than looping indefinitely.

### FR-9: Persistence and resume
Use a LangGraph checkpointer with stable thread/run identifiers. Store concise workflow state and artifact references, not large video/audio/image payloads. Resume from the last valid checkpoint after interruption. Choose local SQLite for a lightweight local prototype unless a survey identifies a stronger need.

### FR-10: Safety and provenance
Default to local processing. Do not upload source videos, frames, audio, transcripts, credentials, or private artifacts without explicit approval. Do not print secrets. Record tool actions, commit/ref, tests, and citations/evidence for research claims.

### FR-11: Final report
Report status per acceptance criterion: passed, failed, blocked, or not run. Include changed files/links, commit/Issue/PR references, test commands and actual outcomes, risks, and the next actionable step.

## 8. Initial domain: dance pipeline

The first graph-managed project should coordinate two pipelines defined by the current design:

### Pipeline A: source video to pose JSON and layered animation
- Select source segment `[00:02:20, 00:03:45)`.
- Extract still PNG frames with source timestamps and stable IDs.
- Run MediaPipe Pose on still images and write versioned JSON.
- Render JSON to SVG and validate alignment in a browser.
- Capture composite frames and assemble a video only after alignment checks pass.

### Pipeline B: dance JSON to a different character
- Survey free/redistributable character models.
- Verify license, rig, skeleton, and file-format compatibility.
- Retarget the motion and test on a short clip.
- Render only after the model and mapping pass validation.

Do not assume all steps must be implemented in one language. Preserve JSON contracts across units.

## 9. State and artifacts

Minimum graph state:
- `request_id`, `thread_id`, repository/ref/commit
- normalized requirements and open questions
- repository findings and relevant Issue IDs
- survey candidates, sources, scores, and decision
- plan, approval status, and risk flags
- current step, expected artifacts, and actual artifact references
- test results, error summaries, retry count
- changed files/diff summary and final status

Persist large media and build outputs as files referenced by path/URI; do not embed binary data in graph state.

## 10. Non-functional requirements

- **Reproducibility:** same repository ref and configuration should yield traceable steps.
- **Observability:** node inputs/outputs, timing, tool actions, and failures should be inspectable without leaking secrets.
- **Resilience:** checkpoints and bounded retries prevent restarting all work after a transient failure.
- **Cost control:** avoid redundant LLM calls; use deterministic code for parsing, filtering, schema checks, and tests.
- **Modularity:** nodes have narrow contracts and can be tested independently.
- **Security:** least-privilege GitHub access, no implicit publishing, and human approval for high-impact actions.
- **Portability:** local-first execution, with optional services only when justified.
- **Maintainability:** pin or constrain dependencies and validate workflow/schema changes in CI.

## 11. Success metrics

- Every implementation run begins with repository inspection.
- No custom plugin/dependency is added without a recorded survey decision.
- Every task has a canonical Issue or a documented reason not to create one.
- Every claimed completed step has machine-verifiable evidence or a linked human review.
- Failed tests enter a bounded diagnosis/repair path and cannot silently pass.
- Interrupted runs can resume from a checkpoint.
- The dance pipeline can be advanced through the same graph without manually prompting each intermediate step.

## 12. Delivery phases

1. **Phase 0 — Contracts:** define schema for `dev.wf.yml`, request, graph state, survey report, and step result.
2. **Phase 1 — Minimal development graph:** request normalization, repository inspection, survey decision, plan, human approval, and Issue creation/update.
3. **Phase 2 — Safe implementation loop:** one-unit edits, test execution, failure diagnosis, bounded repair, evidence report.
4. **Phase 3 — Persistence and resume:** checkpointing, stable run IDs, resume tests, and cost/trace logging.
5. **Phase 4 — Dance pipeline integration:** use the graph to implement and verify Pipeline A, then Pipeline B.
6. **Phase 5 — Evaluation:** measure repeatability, unnecessary code/dependency additions, failure recovery, and human review burden.

## 13. Acceptance criteria for the first release

- A LangGraph entrypoint loads and validates `dev.wf.yml`.
- A run can accept a request and produce normalized requirements plus a proposed plan.
- Repository inspection occurs before survey/implementation.
- Survey-first routing is enforced before custom implementation or dependency additions.
- The workflow can create/update a GitHub Issue after checking for duplicates.
- A human approval checkpoint blocks risky implementation actions until approved.
- A small test task can run tests, capture real results, and produce a final status report.
- Repair retries are bounded and a failed task cannot be reported as passed.
- Checkpoint/resume is demonstrated with a test.
- No video/media payload or secret is sent to a cloud service by default.

## 14. Open decisions

- Which local LLM endpoint/model should drive planning and coding decisions?
- Which GitHub tool boundary is canonical: existing MCP server, GitHub API client, or both?
- Should the first checkpointer be SQLite, and what retention policy is required?
- Should the workflow write changes directly to a feature branch or only generate patches for review?
- Which schema validation tool should be used for `dev.wf.yml`?
