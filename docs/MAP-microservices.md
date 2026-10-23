# MAP: Python worker microservices

## Runtime topology

- `docker-compose.yml`: declares nine independently addressable worker containers.
- `Dockerfile`: common Python image and runtime.
- `src/video2storyboard/worker_api.py`: HTTP boundary, request validation, allowlisted worker dispatch, health endpoint.
- `src/video2storyboard/graph/nodes.py`: canonical processing logic; microservices wrap these functions instead of duplicating implementation.
- `src/video2storyboard/mcp_server.py`: existing local-only OpenCode MCP entry point; the HTTP workers are an additional deployment option.
- `tests/test_worker_api.py`: health and dispatch tests.

## Data flow

1. Call `ingest` (8001) with a state containing `source_video`.
2. Pass returned state fields to `frames` (8002).
3. Run pose (8003), composition (8004), meaning/VLM (8005), and STT (8006) on the state containing their required inputs.
4. Pass worker outputs into storyboard (8007), then render (8008) and validate (8009).

This is intentionally a worker-service layer, not an automatic distributed orchestrator. The caller must preserve and merge state between calls. Paths must exist in the container namespace. All containers mount `./input` read-only and share `./outputs`.

## Local-only boundary

The meaning worker calls the existing LM Studio adapter. It targets `LM_STUDIO_BASE_URL` and has no cloud fallback. Keep ports on a trusted local network; authentication is not included in this first cut.

## Verification status

Files and configuration have been committed on `feat/python-microservices`. The implementation has not been run in this assistant session; execute `PYTHONPATH=src python -m pytest -q` and `docker compose config` locally before treating the container stack as verified.
