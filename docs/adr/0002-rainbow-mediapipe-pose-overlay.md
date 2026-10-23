# ADR-0002: Rainbow MediaPipe Pose overlay for source video

- Status: Proposed
- Date: 2026-10-23
- Issue: https://github.com/bonsai/video2storyboard/issues/10

## Context

The project needs to draw MediaPipe Pose bones over the original video's frames using rainbow colors. The original media must remain untouched. Users also want to show or hide the pose layer during preview. An exported MP4 is a rendered artifact, so its overlay cannot be toggled after export; runtime toggling requires a preview/player that composites a separate layer.

## Decision

1. Use Python + OpenCV + MediaPipe for frame-by-frame pose inference and rendering.
2. Export a **new MP4** as the primary durable output. Never overwrite the input video.
3. Color pose connections with a rainbow palette by mapping connection order or normalized hue to HSV, then converting to OpenCV BGR.
4. Preserve original audio by muxing the rendered video stream with the source audio using FFmpeg. If FFmpeg is unavailable, fail clearly when audio preservation is requested; allow an explicit silent-output mode.
5. Treat transparent SVG/PNG overlays as optional editing artifacts, and GIF as an optional short preview only. Neither is the canonical output.
6. Implement runtime ON/OFF as a preview/player control over the separate pose-render layer. Keep it separate from offline MP4 export; a baked MP4 is not toggleable.
7. Use a visibility threshold to avoid drawing low-confidence landmarks. Keep the threshold configurable.

## Alternatives considered

| Option | Pros | Cons | Decision |
|---|---|---|---|
| Baked MP4 | Easy to share/play; preserves timing; one output file | Overlay cannot be toggled after export; needs audio muxing | Primary export |
| Transparent PNG/SVG sequence | Reusable as a separate editing layer; color can be changed later | Many files; frame/timestamp alignment needed | Optional |
| GIF | Simple short-loop preview | Palette and size limits; no audio; poor long-video format | Optional preview only |
| Runtime preview toggle | Interactive ON/OFF; supports iteration | Requires a player/preview UI and compositing every frame | Separate preview feature |

## Consequences

- The source video is read-only and output is written to a distinct path.
- Video dimensions and frame rate should follow the source metadata; audio is muxed from the original where requested.
- Exporting all frames costs more time than analyzing sampled storyboard frames.
- Runtime toggle applies only to the interactive preview, not to already-rendered MP4/GIF files.
- Tests should cover rainbow color mapping, threshold behavior, safe output paths, and export orchestration without requiring a webcam or downloading a model.

## Acceptance criteria

- [ ] New MP4 contains rainbow-colored pose bones across processed frames.
- [ ] Input video remains unchanged; output dimensions and FPS match the source.
- [ ] Original audio is preserved when enabled and FFmpeg is available.
- [ ] Preview exposes an explicit pose visibility toggle.
- [ ] GIF remains an optional preview, not the main output.
- [ ] README documents commands, dependencies, output locations, and audio limitations.
