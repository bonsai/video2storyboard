# video2storyboard — Issue-Driven TODO

Git state: `main` @ latest (commit *config: define worker separation, workflow topology and reusable visualization tools*). 40 working-tree files modified but uncommitted (see git stash if you need to pull).

Derived from GitHub issues https://github.com/bonsai/video2storyboard — sorted by priority & dependency.

## P0 — Today (current sprint)

- **#19 Make MediaPipe Pose overlay visible → pass condition**
  - Reuse `src/video2storyboard/pose_video.py` + `pose_render.py` (do not add new renderers).
  - Emit visible overlay PNG (+ optional silent overlay video).
  - Write per-frame JSON: `frame_id`, source `timestamp`, image dims, normalized landmarks, visibility, explicit `detected/no_pose/error` status.
  - Append execution events to JSONL.
  - Run focused tests; validate PNG/SVG/JSON outputs.
  - Never overwrite/upload source media.
  - Scope excludes: VLM, STT/audio, 3D retargeting.

- **#21 Visualize dance-pose similarity in a Semantic Cube**
  - Inspect-reuse https://github.com/bonsai/Japanese-Designers-Graph (`space.html`, Three.js 3D + p5.js 2D).
  - MVP: short dance intervals → MP Pose landmarks → normalized feature vectors → pairwise similarity JSON → 3D Semantic Cube (select/compare 2 samples, 2D projection fallback) + README.
  - Distinguish real-data vs seed data in UI.

## P1 — Next

- **#15 Build two standalone dance pipelines (no LangGraph yet)**
  - P1: source video [00:02:20,00:03:45) → PNG → Pose JSON → SVG overlay → browser sync composite → MP4. Validates ts alignment, dims, dropped frames.
  - P2: dance JSON → license-verified free 3D char → retarget → render test clip.
- **#18 YAML-first topology / separated workers / reusable viz tools**
  - Canonical: `dev.wf.yml`, `config/storyboard-visualization.yaml`, `docs/prd/storyboard-visual-reconstruction.md`.
  - Enforce topology invariant:
    `request_normalize -> inspect_repository -> survey_reuse -> define_contracts -> approval_gate -> implement_unit -> run_tests -> generate_visuals -> package_share -> publish_report`
  - Failure routing: `run_tests -> diagnose_failure -> implement_unit` (retry budget) else `blocked_report`.
- **#6 Run complete pipeline locally → Colab handoff**
  - Phase A: synthetic test video → deps/ffmpeg/LM Studio check → end-to-end graph (local VLM adapter) → inspect storyboard.json+HTML+SVG → pytest → reproducible report.
  - Phase C: version job.json + artifacts.json manifests for Colab target.
- **#17 LangGraph-driven dev workflow from PRD** → load+validate `dev.wf.yml`, inspect repo+issues, survey libs, create Issue, draft plan w/ human approval, bounded diagnose/repair, checkpoints+resume, evidence report.

## P2 — Follow / infrastructure

- **#12 MCP-first Python plugin services + OpenAPI contracts + dashboard** (foundational)
- **#2 Expose pipeline as OpenCode MCP server** (HANDOVER 2026-10-23) — `mcp_server.py` exposes `check_local`, `analyze`, `get_run`.
- **#1 Implement LangGraph video-to-storyboard workers** (Kaggle/Colab workbench) — root issue.
- **#13/#14 pylib survey + adopt survey-first policy** before adding deps.

## Dependency spine

```
#15 P1 pose overlay  ->  #19 done   (reuse pose_video/pose_render)
#15 dance pipelines   ->  #6 local run, #17 LangGraph dev
#18 YAML topology      ->  #21, #19
#17 dev workflow       ->  #15, #18
#12 plugin services    ->  #2 MCP, #1 workers
```

See `HANDOVER.md` (LM Studio local VLM + OpenCode MCP integration, issue #2) for the verification checklist.

---

## Open Issue list (state: open, latest 40 fetched)

| # | Title | Label |
|---|---|---|
| 21 | ダンス動作データの類似度をSemantic Cubeで可視化する | enhancement |
| 19 | Make MediaPipe Pose overlay visible; prepare timestamped dance reconstruction | |
| 18 | YAML-first: topology, separated workers, reusable visualization tools, and storyboard reconstruction | |
| 17 | Implement LangGraph-driven development workflow from PRD | |
| 16 | PoC: PNG → MediaPipe Pose JSON → SVG overlay in browser | |
| 15 | Build two standalone dance pipelines before LangGraph orchestration | |
| 14 | Establish survey-first policy: reuse libraries and projects before implementing plugins | |
| 13 | TODO: Python library (pylib) survey for the video-analysis pipeline | |
| 12 | Define MCP-first Python plugin services with OpenAPI contracts, LangGraph orchestration, and live visualization | enhancement |
| 10 | Add rainbow MediaPipe Pose bone layer to source video with runtime toggle | |
| 6 | Run the complete pipeline locally, then define a Colab execution handoff | documentation |
| 4 | Write handover: record the 2026-10-23 local LM Studio verification results and remaining gaps | documentation |
| 3 | Write handover: record the 2026-10-23 local LM Studio verification results and remaining gaps | documentation |
| 2 | Expose the local video-to-storyboard pipeline as an OpenCode MCP server | enhancement |
| 1 | Implement LangGraph video-to-storyboard workers with Kaggle/Colab workbench | |

---

## Local working-tree state (to commit after TODO decided)

- Modified (uncommitted): HANDOVER.md, MAP.md, README.md, config.yaml, config/*, dev.wf.yml, docs/*, examples/*, requirements.txt, schemas/*, src/video2storyboard/*, standards/*, tests/*, timelines.yaml, topology.yaml, units/pose/requirements.yaml
- Untracked: `src/video2storyboard/__pycache__/`, `src/video2storyboard/graph/__pycache__/`, `tests/__pycache__/` (ignore)
- Stashed (auto-pulled then popped): stash@{0}
