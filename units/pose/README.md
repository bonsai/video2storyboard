# Pose unit

**Milestone 1:** make the MediaPipe Pose layer visible and save inspectable output.

## Contract

- Workflow: [`wf/pose.wf.yml`](../../wf/pose.wf.yml)
- Agent workflow: [`aw/pose.aw.yaml`](../../aw/pose.aw.yaml)
- API contract: [`openapi/pose.yaml`](../../openapi/pose.yaml)
- Artifact schema: [`contracts/pose-artifact.schema.json`](../../contracts/pose-artifact.schema.json)

## Reuse first

The repository already has `src/video2storyboard/pose_render.py` and `pose_video.py`. Extend or call those implementations rather than introducing another renderer.

## Acceptance

Given one local frame, produce:
- an overlay PNG that visibly shows the pose skeleton;
- a JSON record with source frame ID/timestamp, dimensions, landmark coordinates, visibility, and explicit status;
- a JSONL run log.

Do not overwrite or upload source media.

## Next milestone

Tomorrow: use the timestamped Pose JSON sequence to reconstruct the dance motion. This is out of scope for the current scaffold.
