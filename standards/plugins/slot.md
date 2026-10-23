# Plugin 16: slot

## Status
Proposed; design only. This entry does not claim the plugin is implemented.

## Responsibility
Manage storyboard slots: define available positions/frames in a storyboard layout and assign scene, shot, keyframe, or annotation references to those slots. Keep layout/placement separate from canonical story meaning.

## Inputs
- `storyboard_json` or a storyboard draft
- optional `scenes`, `frames`, and `temporal_events`
- slot layout configuration

## Outputs
- `slot_layout`: ordered slot definitions and layout metadata
- `slot_assignments`: stable slot IDs mapped to storyboard item references
- structured diagnostics for unassigned, duplicated, or incompatible assignments

## Rules
- Preserve source-media timestamps and canonical storyboard IDs.
- Never copy or mutate source media; refer to artifacts by explicit paths/IDs.
- Keep layout geometry separate from narrative/storyboard content.
- Validate slot IDs and references; report unresolved assignments explicitly.
- Support deterministic output for the same input and configuration.

## Boundary
`slot` handles placement and assignment only. It does not generate the storyboard, render final exports, or validate the entire pipeline. Those responsibilities remain with `storyboard`, `export`, and `validation`.

## Open design questions
- Are slots only visual storyboard cells, or also time-range slots in the timeline?
- Should slot layout be represented in YAML configuration, canonical JSON, or both?
