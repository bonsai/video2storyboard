# video2storyboard — Repository Structure Policy

## Root (allowed top-level entries)

- `src/video2storyboard/` — main Python package (source code)
- `tests/` — pytest suite
- `docs/` — documentation (adr, prd, colab-handoff, diagrams, arch)
- `config/` — runtime yaml config
- `schemas/` — JSON schemas (artifacts, job)
- `examples/` — example yaml
- `standards/` — standards docs
- `units/` — unit specs/requirements
- `backends/` — Blender/VTuber backends
- `wf/` — workflow definitions (yaml)
- `models/` — ML model binaries (.task, .pt)
- `mcp/` — MCP tool implementations
- `requirements.txt`, `Dockerfile`, `docker-compose.yml`
- `dev.wf.yml`, `topology.yaml`, `timelines.yaml`, `config.yaml`
- `MAP.md`, `HANDOVER.md`, `README.md`, `TODO.md`, `TODO_issues.md`, `issues.mmd`
- `pipeline1_video_to_dance.py`, `pipeline2_dance_to_3d.py`
- `.github/`

## Source package layout

```
src/video2storyboard/
├── graph/                 # LangGraph nodes + workflow + state
├── plugins/               # plugin registry/contract/scaffold
├── dance_ir.py            # canonical IR
├── dsl/                   # DSL yaml
├── dsl_ast/               # DSL parser
├── pose_tasks.py          # MediaPipe Tasks wrapper
├── pose_render.py         # overlay render (SVG/PNG)
├── pose_video.py          # rainbow overlay preview
├── pose_layer_image.py   # single-frame layer creation
├── mcp_server.py          # MCP server
├── worker_api.py          # FastAPI worker
└── __init__.py
```

## Naming conventions

- Workflow definitions: `wf/<name>.wf.yml`
- Backend modules: `backends/<name>.py`
- MCP implementations: `mcp/server.py`
- IR schemas: `src/video2storyboard/dance_ir.py` (v1.0)
- Tests: `tests/test_<module>.py`

## Cleanup notes

- No duplicate implementation folders at root.
- All scripts/ modules referenced via `src.video2storyboard` namespace (PYTHONPATH=src).

---

## Next actions

- Move `pipeline1_video_to_dance.py` and `pipeline2_dance_to_3d.py` into `src/video2storyboard/`? → decide (keep root as scripts, but confirm policy)
- Remove stale root-level TODO/notes if consolidated into docs/.
- Final test + push.

---

## 現在の整理対象

| Path | 整理アクション |
|---|---|
| `TODO_issues.md`, `issues.mmd` | ルート直下ノート → docs/issues-*.md に移行 or keep |
| `pipeline*.py` | root OK (standalone scripts) |
| `.github/` | keep |
| `backends/`, `mcp/`, `wf/`, `models/`, `docs/`, `tests/`, `config/`, `schemas/`, `standards/`, `units/` | keep |

---

## フォルダ整理の完了条件

1. `git status --short` が `src/`, `tests/`, `docs/`, `config/`, `schemas/`, `examples/`, `standards/`, `units/`, `backends/`, `wf/`, `models/`, `mcp/` の外に残っていない。
2. テスト 23件すべて通過。
3. main branch が最新。

---

## 今後の作業（推奨）

1. **Final folder audit** & cleanup.
2. **Commit** any final cleanup.
3. **Push**.
4. **Next**: Issue #21 — Semantic Cube.

Let me proceed with cleaning the structure and finalizing. I'll move the top-level notes into docs to keep root clean, and verify the rest.<tool_call>bash<arg_key>command</arg_key><arg_value>cd /mnt/c/Users/0501JP/video2storyboard && ls -la | grep -E "TODO|issues|HANDOVER|MAP|README" && ls -la *.yml *.yaml 2>/dev/null && ls -la *.json 2>/dev/null