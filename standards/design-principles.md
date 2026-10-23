# Canon: Video2Storyboard Design Principles

- **Status:** Draft for design review
- **Version:** 0.1.0
- **Scope:** Architecture and plugin design for `video2storyboard`
- **Authority:** This document is the canonical design proposal until reviewed and accepted.

## Purpose

Define stable boundaries and operating principles before adding more implementation. The goal is a maintainable video-to-storyboard pipeline with approximately 15 focused capabilities, orchestrated by LangGraph and configured through YAML.

## Principles

1. **Single source of truth.** Define one canonical storyboard data model; derived exports must not become competing sources of truth.
2. **One plugin, one responsibility.** A plugin owns a cohesive capability with a clear boundary and observable result.
3. **Contract first.** Define input, output, errors, and versioning before implementing or integrating a plugin.
4. **LangGraph orchestrates.** Workflow order, branching, retries, and state transitions belong to the orchestration layer, not individual plugins.
5. **YAML configures.** Pipeline composition and user-adjustable settings should be declarative where practical.
6. **JSON and JSONL have distinct roles.** JSON carries structured artifacts and contracts; JSONL is suitable for append-only run/event records.
7. **Reuse before rebuild.** Inspect and adapt existing code and external repositories before creating duplicate implementations.
8. **Optional dependencies stay optional.** Heavy or provider-specific packages are imported only by capabilities that need them.
9. **Providers are replaceable.** Do not let a single VLM, ASR provider, or pose model leak into the public plugin contract.
10. **Trace every artifact.** Preserve source identity, timestamps, configuration, plugin version, and run ID where applicable.
11. **Make reruns safe.** Use stable inputs and configuration fingerprints to detect reusable results; do not overwrite source media.
12. **Fail explicitly.** Report missing dependencies, invalid data, partial results, and failures distinctly; never silently label a failure as success.
13. **Test in isolation.** Each plugin must have contract-level tests that can run without invoking the entire pipeline or paid services.
14. **Keep humans in the loop.** AI-generated interpretations must be inspectable and correctable before approval or publication.
15. **Deliver incrementally.** Build and validate a thin vertical slice before enabling the whole plugin catalog.

## Architecture boundaries

- **Plugins:** focused processing capabilities; no hidden orchestration and no direct mutation of unrelated plugin outputs.
- **LangGraph:** sequencing, branching, retries, shared run state, and orchestration-level error handling.
- **YAML:** pipeline configuration and plugin settings; secrets must be supplied through environment or secret management, never committed.
- **JSON:** canonical storyboard and versioned structured artifacts.
- **JSONL:** run events, plugin outcomes, and evaluation records.
- **MCP / CLI / API:** adapters for invoking capabilities; they must reuse the same core contract rather than duplicate business logic.
- **Human review:** explicit approval/edit step where output quality or publication warrants it.

## Design review checklist

- [ ] Every plugin has one stated responsibility.
- [ ] Inputs, outputs, errors, and optional dependencies are documented.
- [ ] Time values refer to the source media timeline.
- [ ] Artifacts can be traced to a run and configuration.
- [ ] Existing implementations are mapped before replacement.
- [ ] Core tests work without network access or paid model calls.
- [ ] Pipeline and plugin contracts are versioned.
- [ ] No source video or canonical input is overwritten.

## Change control

Changes to these principles should be made through a reviewable GitHub change. Until approved, the status remains **Draft** and implementation should avoid irreversible architectural commitments.
