# ADR-0001: Survey-first, reuse-first, polyglot implementation

- **Status:** Accepted
- **Date:** 2026-10-23
- **Decision owners:** video2storyboard maintainers

## Context

The pipeline should avoid implementing plugins or utilities that already exist as suitable libraries or reusable projects. Python is the current orchestration and integration language, but it must not be treated as the only permitted implementation language. Some components may have mature Rust, C/C++, Java, or other-language implementations with better performance, reliability, packaging, or existing ecosystem support.

## Decision

1. **Survey before implementation.** Before creating a plugin, adapter, utility, or custom algorithm, survey existing libraries, MCP servers, frameworks, and GitHub projects.
2. **Reuse before custom code.** Prefer a suitable maintained solution over a new implementation. Inspect this repository and its current dependencies first to avoid duplication.
3. **Polyglot is allowed.** Python is the default for orchestration and glue, not a hard language restriction. Rust and other languages are allowed when evidence shows a meaningful benefit and integration is practical.
4. **Choose per unit, not by ideology.** Evaluate candidates by requirement fit, correctness, maintenance, license, security, platform and Python-version compatibility, CPU/local execution, performance, binary/wheel availability, integration complexity, debugging, deployment, and total lifecycle cost.
5. **Prefer simple integration boundaries.** Consider an existing CLI, library binding, HTTP/OpenAPI service, or MCP server before writing a new plugin. Use a subprocess or service boundary only when its operational cost is justified.
6. **Do not rewrite working code just to change languages.** A language change requires a documented benefit, migration plan, and tests demonstrating contract compatibility.
7. **Record the decision.** Store the survey, authoritative links, comparison, recommendation, known trade-offs, and rejected alternatives in a durable artifact such as `survey/pylib.md` or `papers.md`, and reference it from the related Issue/ADR.
8. **Fail closed on insufficient evidence.** If no candidate has been adequately evaluated, continue research or report the unknowns; do not silently assume a new implementation is required.
9. **Separate policy from enforcement.** This ADR is a design decision, not proof that LangGraph currently enforces survey-first routing. Runtime enforcement must be implemented and tested separately.

## Decision workflow

```text
Requirement / Unit Contract
        |
        v
Inspect repository and existing dependencies
        |
        v
Survey libraries, projects, CLIs, APIs, MCP servers
        |
        v
Compare against contract and operational constraints
        |
        +---- suitable candidate ----> reuse / integrate / test
        |
        +---- no suitable candidate -> document gap -> smallest viable implementation
        |
        +---- evidence incomplete ---> research further; do not implement yet
```

## Initial application: POSE unit

For the POSE unit, survey MediaPipe and relevant alternatives and existing projects before adding a plugin or custom pose-estimation implementation. Keep the current still-PNG input contract and the selected timeline interval intact. Compare Python APIs and, where relevant, Rust libraries or command-line tools; do not assume a Rust alternative is automatically better. Verify licensing, maintenance, platform support, output quality, and integration cost.

## Consequences

### Positive
- Reduces duplicate code and unnecessary plugins.
- Allows mature Rust or other-language components where they provide demonstrated value.
- Makes dependency and lifecycle-cost decisions explicit.

### Trade-offs
- Surveying adds upfront work.
- Polyglot systems can increase build, packaging, debugging, and deployment complexity.
- A candidate that is fast in isolation may still be a poor fit if its integration boundary is expensive.

## Acceptance criteria

- Related workflow design places a survey/reuse decision before implementation.
- Surveys include authoritative sources and explicit trade-offs.
- Language selection is made per component using evidence.
- New dependencies and custom implementations have documented justification.
- Runtime behavior is claimed only after implementation and tests verify it.
