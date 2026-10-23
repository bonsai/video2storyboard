# MAP — video2storyboard

## Purpose
Make a visible MediaPipe Pose layer from local video/frames now; reconstruct dance motion from timestamped pose data next.

## Canonical contract chain
`wf/` defines topology → `aw/` defines agent responsibilities → `openapi/` defines I/O → `contracts/` validates artifacts → `units/` documents isolated units.

## Minimal scaffold
| Path | Responsibility |
|---|---|
| `wf/dev.wf.yml` | Small development cycle, roles, quality gates |
| `wf/pose.wf.yml` | Pose pipeline nodes, edges, input/output |
| `aw/pose.aw.yaml` | Agent tasks and separation of duties |
| `openapi/pose.yaml` | Pose request/response API contract |
| `contracts/pose-artifact.schema.json` | Saved Pose JSON schema |
| `units/pose/README.md` | Unit acceptance and reuse notes |
| `src/video2storyboard/pose_video.py` | Existing video overlay implementation to reuse |
| `src/video2storyboard/pose_render.py` | Existing frame PNG/SVG renderer to reuse |
| `tests/` | Regression and contract tests |
| `artifacts/pose/` | Local generated output; normally not committed |
| `docs/PLAN-TOMORROW.md` | Dance reconstruction handover |
| `dev.wf.yml` | Compatibility pointer to `wf/dev.wf.yml` |

## Topology
```text
read_frame -> estimate_pose -> render_overlay -> validate_artifact
```
Each node has one responsibility. This milestone excludes VLM, STT/audio, and 3D retargeting.

## Today’s pass condition
A real local input must produce a visible skeleton overlay PNG, landmark JSON with explicit `detected`/`no_pose`/`error` status, a JSONL run record, and passing focused tests/artifact checks. Scaffold alone is not a pass.

## Tomorrow
Use timestamped Pose data to render a synchronized 2D stick-figure animation, then compare it side-by-side with source frames before considering 3D.

## Stick-figure playback diagrams
Both diagram formats are maintained side by side:
- Structure (SVG): [animate-stick-figure-structure.svg](docs/diagrams/animate-stick-figure-structure.svg)
- Structure (PlantUML): [animate-stick-figure-structure.puml](docs/diagrams/animate-stick-figure-structure.puml)
- Event flow (SVG): [animate-stick-figure-events.svg](docs/diagrams/animate-stick-figure-events.svg)
- Event flow (PlantUML): [animate-stick-figure-events.puml](docs/diagrams/animate-stick-figure-events.puml)

The SVG files are directly viewable in GitHub; the PUML files are editable source diagrams. Keep each pair conceptually aligned when changing the script.

## Migration status
This commit adds simpler canonical entry points without deleting legacy graph/plugin code. Migrate legacy modules only when a tested replacement exists.

## Safety and reuse
Source media remains local and immutable. Prefer existing implementations/dependencies, never upload source media by default, and store generated outputs under `artifacts/`. Read CLI `--help` before running; audio preservation requires FFmpeg, so prefer silent rendering for the minimal Pose-layer milestone.
