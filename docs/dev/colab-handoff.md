# Local-first execution and Colab handoff

## Principle
Local execution is the default. Colab is an explicit, optional execution target for stages that benefit from a GPU or hosted notebook runtime. Never upload a source video automatically. Never put API keys, LM Studio credentials, personal paths, or secrets in a job manifest or bundle.

## Execution stages
1. Preflight locally: check Python packages, FFmpeg, local LM Studio /v1/models, input readability, disk space, and selected model.
2. Synthetic smoke test locally: generate a short test pattern using FFmpeg; run without private media.
3. Full local run: analyze a short user-selected clip; inspect errors and artifacts.
4. Worker-service smoke test: validate Compose config and call each API; document state merge and path requirements.
5. Optional Colab run: package an explicitly selected clip and job manifest, upload only after user confirmation, execute requested stages, download result bundle.
6. Local acceptance: verify hashes, schema version, relative paths, and run status before accepting remote results.

## Stable job contract
A job is a portable description of work, not a Python pickle and not a copy of runtime state.
- schema_version: version of this manifest contract.
- job_id: stable identifier for one requested run.
- execution_target: local or colab.
- input: relative path within the bundle plus SHA-256 and media type.
- config: deterministic settings such as frame interval and optional model identifiers. No credentials.
- requested_workers: explicit allowlist of stages.
- outputs: expected artifacts and contract version.
- privacy: remote execution requires deliberate user action.

Bundle layout:

    job-bundle/
      job.json
      input/source-video.mp4
      outputs/
      artifacts.json

Paths in manifests are relative to the bundle root. Runtime paths are resolved by the executor; do not hard-code Windows or Colab paths.

## Artifact contract
Each artifact records bundle-relative path, media type, byte size, SHA-256, and status. A successful full run should return storyboard.json, storyboard.html, storyboard.svg, and referenced frame PNGs.
The receiver verifies hashes before parsing JSON, validates the storyboard schema, and confirms every referenced image exists. A hash match proves byte integrity, not semantic correctness; visual review remains necessary.

## Local vs Colab responsibilities
| Concern | Local default | Optional Colab |
|---|---|---|
| Input | Local file path | User explicitly uploads a bundle |
| VLM | LM Studio on localhost | Notebook-configured model, only if separately approved |
| Pose / image processing | CPU or available local runtime | GPU/runtime when useful |
| Audio transcription | Local faster-whisper if installed | Optional notebook dependency |
| Results | Local output folder | Download ZIP, then validate locally |
| Credentials | Local environment only | Notebook secrets, never in job files |

## Current implementation boundary
The existing LangGraph nodes remain canonical. FastAPI services wrap those nodes; they do not yet provide an automatic distributed coordinator. Before building a Colab executor, make VLM adapter injection consistent between direct graph invocation and MCP invocation, and make missing optional workers report capability status clearly.

## First local commands (PowerShell)

    python --version
    ffmpeg -version
    $env:PYTHONPATH = "src"
    python -m pytest -q
    python -m video2storyboard.interfaces.mcp

Run the MCP server in a dedicated terminal; it uses stdio, not HTTP. Add it to OpenCode only after local dependency and model checks succeed.

## Acceptance gate
Do not call the pipeline verified until a short synthetic clip completes through graph invocation, output JSON/HTML/SVG and image paths are inspected, tests pass, and unavailable workers are reported explicitly. Do not call Colab verified until a bundle is uploaded intentionally, run remotely, downloaded, hash-checked, and validated locally.
