# Next session: dance reconstruction

## Today’s pass condition

The MediaPipe Pose layer is visible on a source frame or video preview, with an inspectable overlay artifact and pose JSON. A scaffold alone is not a pass; run the pipeline and verify the output.

## Tomorrow’s target

Reconstruct dance motion from a timestamped sequence of MediaPipe Pose landmarks.

1. Read timestamped frame/pose JSONL records.
2. Preserve source timestamps and stable frame IDs.
3. Normalize pose coordinates and handle missing landmarks explicitly.
4. Render a simple 2D stick-figure animation synchronized to source time.
5. Compare source frames and reconstructed motion side by side.
6. Only after this works, consider a richer avatar or 3D reconstruction.

## Do not expand scope yet

- No VLM, STT, audio processing, or 3D character retargeting in the Pose-layer milestone.
- No duplicate renderer or unnecessary dependency installation.
- No source-media upload.
