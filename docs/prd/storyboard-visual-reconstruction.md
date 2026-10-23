# PRD: YAML-First Visual Development and Storyboard Image Reconstruction

- **Status:** Draft for implementation
- **Canonical specification:** [`config/storyboard-visualization.yaml`](../../config/storyboard-visualization.yaml)
- **Repository:** `bonsai/video2storyboard`

## 1. Product goal

Build a LangGraph-orchestrated development workflow where visualization and sharing are mandatory development outputs, and where YAML defines the actual scope, worker contracts, workflow stages, artifacts, and acceptance criteria.

The current product focus is narrowly defined: **reconstruct the image content of storyboard panels**. This is not a general video-understanding or full multimedia pipeline project.

## 2. Active worker scope

Only these three worker families are in the active path:

- **MP / MediaPipe Pose:** human pose landmarks from PNG frames.
- **CV2 / OpenCV:** frame/image measurements and image-processing support.
- **VLM:** semantic description of visible content needed to reconstruct a panel image.

Audio/STT, unrelated workers, and 3D-character retargeting are out of scope for this iteration.

## 3. Development is itself a workflow

Development must not depend on a human manually prompting an LLM at each intermediate step. LangGraph coordinates:
1. Inspect repository, source, dependencies, existing artifacts, and Issues.
2. Survey existing libraries/projects before custom implementation.
3. Read the canonical YAML and define/validate input-output contracts.
4. Implement one small unit.
5. Run tests and validate actual outputs.
6. Generate visualization from current code, graph topology, plugin contracts, and run artifacts.
7. Save shareable artifacts and a human-readable MAP in the repository.
8. Report evidence, failures, blockers, and artifact links.

Human approval remains required for destructive changes, permission/credential changes, external publishing, and merge/release. Retry loops must be bounded.

## 4. Visualization and sharing are required, not optional polish

Every development unit must produce or update appropriate inspectable evidence. Depending on the change, this includes:
- PlantUML class/data diagrams generated with `py2puml` where supported.
- A separate graph topology diagram generated from the actual LangGraph definition.
- A plugin contract/worker mapping for MP, CV2, and VLM.
- A storyboard review HTML/SVG/PNG showing source frame, observations, and reconstructed panel together.
- `MAP.md` explaining what each artifact means and how to regenerate it.

Diagrams must be generated from actual code and runtime artifacts, not maintained as unsupported guesses. `py2puml` does not replace explicit visualization of LangGraph edges or function-based workers.

## 5. Data and execution constraints

- YAML is the canonical definition of workflow and policy.
- JSON is the interchange format; JSONL is the execution/event log.
- Preserve source timestamp, stable frame ID, dimensions, and coordinate conventions.
- Represent detected, not-detected, unreadable, and error states explicitly.
- Keep image coordinates distinct from 3D world coordinates.
- Local-first; no cloud fallback and no source media upload by default.
- Survey and reuse existing libraries before custom code; choose language per unit based on evidence.

## 6. Initial source segment

Use the existing `skeleton_dance` timeline: `[00:02:20, 00:03:45)`. Include the start boundary and exclude the end boundary. Frames outside the interval must not enter pose inference or panel reconstruction.

## 7. Acceptance criteria

- The active reconstruction path uses only MP, CV2, and VLM.
- The workflow loads its actual stage/worker/visualization definitions from the canonical YAML.
- Each stage can be tested independently against a defined contract.
- A reconstructed panel can be inspected alongside its source frame and evidence.
- Code structure, graph topology, and worker contracts are visualized with limitations clearly marked.
- Artifacts are saved in repository-tracked paths and linked in the run report.
- Tests and artifact checks run before a task is reported complete.
- Failure to generate a required visualization or shareable artifact is reported as blocked/failing, not silently ignored.
