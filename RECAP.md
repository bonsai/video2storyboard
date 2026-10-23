# RECAP — video2storyboard

**Updated:** 2026-10-23  
**Purpose:** Fast handover for the next session. GitHub is canonical.

## Current direction

Restructure the work around verified, small deliverables. Keep Pipeline 1 (video → Pose data) and Pipeline 2 (dance data → 3D character) independently runnable. Do not expand LangGraph orchestration until the data contract and standalone paths are verified.

## Next execution order

1. **Issue #19 — Pose artifact gate**  
   Produce and inspect a visible Pose overlay PNG; emit timestamped landmark data with frame ID, dimensions, visibility, and explicit detection/error status; preserve failed/missing frames; append JSONL events; run focused tests. Existing scaffold/code alone does not pass this gate.
2. **Issue #25 — DSL → AST → versioned IR**  
   Validate YAML DSL into typed AST, compile deterministic IR, and explicitly adapt Pipeline 1 output to the canonical contract. Test schema and serialization without Blender.
3. **Issue #24 — Blender retargeting**  
   Make Pipeline 2 consume IR and generate actual armature animation keyframes for a small rig. Copying overlay images is not animation.
4. **Issue #21 — Semantic Cube**  
   Start after there are at least two comparable motion samples, documented features/distance, and a clear distinction between measured and demo data.
5. **Issue #6 — local synthetic end-to-end run**  
   Verify the whole local path, inspect JSON/HTML/SVG/assets/errors, and record exact commands and outcomes.
6. **Issue #3 — HANDOVER**  
   Update only from observed results; document remaining blockers.

## Scope held back until gates pass

- **#1 / #2 / #12 / #17 / #18:** broad LangGraph orchestration, MCP/service architecture, and development-workflow automation.
- **#16:** narrow PNG → Pose JSON → SVG/browser PoC.
- **#10:** separate rainbow Pose overlay export/runtime-toggle feature.
- **#13 / #14:** survey existing libraries/projects before adding dependencies or implementing new tools.
- **#15:** umbrella issue for the two standalone dance pipelines and their integration order.

## Latest repository evidence

- Commit `da90845b30eab07fda75dfe014e09fcf0a110d99` added `src/video2storyboard/dance_ir.py` and changes to the two dance pipelines.
- `src/video2storyboard/pose_video.py` and `pose_render.py` exist on the default branch.
- `dance_ir.py` documents a versioned `video2storyboard-dance-ir-v1.0` contract.
- The available combined commit-status response did not provide CI status checks. **Do not claim the latest changes passed CI or local tests based on that response.**
- Earlier local evidence recorded in Issue #3 (2026-10-23): Python 3.13.14; `pytest` 5 passed in 4.58s; FFmpeg available; `faster_whisper` missing; LM Studio endpoint reachable; a synthetic single-image VLM probe returned valid JSON; OpenCode MCP config not registered; full end-to-end graph run not yet executed. This evidence is recorded in the issue and has not been independently rerun in this session.

## GitHub issue housekeeping completed

- **#4 closed as duplicate of #3**; a comment points to the canonical handover issue.
- Execution order and acceptance notes added as comments to **#15, #19, #25, and #3**.
- Issues #19, #24, and #25 remain open until acceptance criteria are supported by tests or inspectable artifacts.

## Completion rules

- Do not close issues based on scaffold presence alone.
- Report changed files, exact commands, test outcomes, artifact paths, and remaining blockers.
- Keep source media local and immutable; no automatic upload or cloud fallback.
- Do not claim Blender animation until actual keyframes are generated and previewed.
- Keep `MAP.md` and architecture diagrams aligned with the actual implementation.
- Avoid committing videos, secrets, or large generated artifacts.

## Start here next session

1. Read this file and [Issue #19](https://github.com/bonsai/video2storyboard/issues/19).
2. Inspect current implementation/tests and run the smallest focused Pose artifact check using a synthetic/local test input.
3. Capture the exact command, exit code, and output artifact paths.
4. Fix the first failing gate; only then proceed to Issue #25.

## Navigation

- [README](README.md)
- [MAP](MAP.md)
- [HANDOVER](HANDOVER.md)
- [Issue #19 — Pose gate](https://github.com/bonsai/video2storyboard/issues/19)
- [Issue #25 — DSL/AST/IR](https://github.com/bonsai/video2storyboard/issues/25)
- [Issue #24 — Blender retargeting](https://github.com/bonsai/video2storyboard/issues/24)
- [Issue #6 — local E2E verification](https://github.com/bonsai/video2storyboard/issues/6)
- [Issue #3 — handover](https://github.com/bonsai/video2storyboard/issues/3)
