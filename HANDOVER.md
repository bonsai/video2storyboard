# Handover — video2storyboard

Updated: 2026-10-23 (Asia/Tokyo)

## Canonical decisions

- Repository: `bonsai/video2storyboard`.
- `main` is the canonical branch. Treat its current package/folder structure as authoritative.
- Do not merge or copy whole older branches over `main`; adapt only the implementation files that are still needed.
- The user will test and debug after integration. **Do not run tests or debug proactively** unless asked.
- Keep changes small and reviewable. Do not claim validation or successful execution unless actually verified.
- This repository is the specialized storyboard engine. `bonsai/anime-factory-tps` is the higher-level YAML/LangGraph orchestration layer; do not assume a stable CLI/API contract unless it is implemented and documented.

## Tracking issue

- [Issue #30 — Record current branch HEADs and restart development plan](https://github.com/bonsai/video2storyboard/issues/30)

## Branch HEAD snapshot

These are the HEADs recorded in Issue #30; re-check live refs before using them as current HEADs.

| Branch | Recorded HEAD | Summary |
|---|---|---|
| `main` | `b1da4e4dd153fb08cde1228facd572f06e38423e` | Canonical split structure; pose worker delegates to `tasks_nodes.py`. |
| `feat/mediapipe-tasks-api` | `ac1c358e7fc5d849376bbc182c6d334e4f2e7c65` | MediaPipe Tasks API work; graph routes through nodes adapter. |
| `fix/main-pose-tasks-api` | `3f2b77694645ac62259307ff0380ef01e1570685` | CI runtime-library changes for MediaPipe (EGL/GL/GLES/GLib). |
| `fix/pose-tasks-api` | `69b8c076617457a8f0ebb0825d44449dbe01a2e8` | CI adds `libgles2`. |

## Current implementation landmarks on main

- `src/storyboard/graph/tasks_nodes.py`: MediaPipe Tasks pose worker. Reads sampled frames, records landmarks/status, and attempts PNG/SVG overlays.
- `src/storyboard/graph/nodes.py`: delegates `eye_pose_mp` to the dedicated tasks worker.
- `src/work/pose/pose_tasks.py`: MediaPipe Tasks helpers including landmarker creation, pose connections, and landmark normalization.
- The current worker imports `render_pose_artifacts` from `src/work/pose/pose_render.py`; inspect this implementation before porting any older branch changes.

## Next steps

1. Re-check the live `main` tree and branch refs; the table above is a recorded snapshot, not a live status report.
2. Compare implementation-only diffs from the older branches against `main`, especially pose rendering. Translate old package paths into the current split layout rather than restoring `src/video2storyboard/`.
3. Inspect import/package consistency. The README currently contains older `src/video2storyboard` paths in some examples, while newer implementation files live under `src/storyboard` and `src/work`; reconcile docs with the actual package layout as a separate small change.
4. Integrate only necessary files in small commits. Keep CI/runtime dependency edits separate from Python implementation edits where practical.
5. Stop after integration and report the exact changed files/commit. Do not run tests or debug until the user requests it.

## Known cautions

- No successful test result is confirmed in this handover.
- A previous PR workflow was reported failing due to a `video2storyboard` import/package mismatch; verify the current run status before relying on that report.
- VLM semantics require a configured provider adapter; do not imply semantic descriptions work by default.
- Pose overlay rendering errors are intended to be recorded per frame without discarding landmark results.
