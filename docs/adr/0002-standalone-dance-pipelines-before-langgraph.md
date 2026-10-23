# ADR-0002: Validate two standalone dance pipelines before LangGraph

- **Status:** Accepted
- **Date:** 2026-10-23
- **Related issue:** https://github.com/bonsai/video2storyboard/issues/15

## Context

The project is currently exploring video-to-storyboard and dance motion extraction. Building orchestration first would couple uncertain processing steps together and make it harder to inspect failures. The pipeline should first be proven as small, independently runnable tools with explicit data contracts.

## Decision

Defer LangGraph until both initial pipelines work independently. Use JSON as the interchange format between stages. Prefer surveying and reusing existing libraries and projects over building plugins. Python is permitted but not mandatory; Rust and other languages may be selected per component when research demonstrates a better fit.

## Pipeline 1: source video to layered animation

1. Identify the source video and source-time interval.
2. Extract still PNG frames, preserving source timestamp and stable frame ID.
3. Run MediaPipe Pose on PNG stills and save landmark results as versioned JSON.
4. Render the pose JSON to SVG so the skeleton overlay can be inspected independently.
5. Synchronize the video and overlay in a browser and capture composited frames.
6. Assemble the captured frames into an animation/video such as an MP4.
7. Validate timing, dimensions, dropped frames, and output appearance.

Initial example:
- Source: https://www.youtube.com/watch?v=U6dnieqgYvI
- Target segment: `skeleton_dance`, `[00:02:20, 00:03:45)`
- Appearance and performance segments are excluded.

## Pipeline 2: dance JSON to another character

1. Consume the same versioned dance JSON from Pipeline 1.
2. Survey for a free-to-use 3D character model; do not create a model as the first response.
3. Verify license, attribution requirements, redistribution rights, rig, skeleton, and supported formats.
4. Map pose landmarks to the character rig and retarget the motion.
5. Preview a short clip and render the animated character.

A model being downloadable for free does not automatically mean it permits unrestricted reuse or redistribution. Record the exact license and its conditions.

## JSON contract requirements

The pose JSON should include:
- schema version and coordinate convention;
- source video identifier and source timestamp;
- stable frame ID and image dimensions;
- landmark names/indices, coordinates, visibility/presence or confidence where available;
- pose detection status, including no-pose and processing-error cases.

Use normalized coordinates only when their meaning is explicit. Keep image/pixel coordinates or 3D world landmarks separate rather than mixing coordinate spaces. Preserve timestamps through every stage.

## Survey and implementation policy

Before implementing each stage, inspect this repository and survey existing libraries, CLIs, MCP servers, and projects. Compare maintenance, license, correctness, local/CPU support, language/platform compatibility, integration effort, and lifecycle cost. Choose a language per unit based on evidence, not preference. Add a custom implementation only when the survey identifies a documented gap.

## Deferred decision: LangGraph

After standalone steps have stable contracts, reproducible samples, and tests, they may be wrapped as LangGraph nodes. LangGraph is a future orchestration layer, not a prerequisite for validating the media pipeline.

## Consequences

- Intermediate artifacts are inspectable and debuggable.
- Pipeline 1 can be validated independently from character rigging in Pipeline 2.
- Versioned JSON allows implementations in different languages.
- Separate tools and runtimes may add packaging overhead; keep interfaces simple and introduce cross-language boundaries only when justified.

## Acceptance criteria

- Pipeline map and JSON schema are documented.
- Pipeline 1 produces timestamped pose JSON and SVG overlays, then composited frames/video.
- Pipeline 2 animates one model whose license has been verified.
- Each stage has a small repeatable sample/test.
- LangGraph integration is deferred until these conditions are met.
