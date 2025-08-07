# quadtreefabric
# Improve nodes.py — Towards a **General‑Purpose Programming Language LAB**

> A clear, execution‑oriented plan to evolve `nodes.py` into an elite, polyglot systems lab: fast, composable, safe, and ergonomically sharp.

---

## 0) North star (non‑negotiables)

An **elite lab** delivers:
- **Latency**: edit→run loop under 100 ms for interpreted cells; bounded for compiled cells.
- **Composability**: cells can depend on each other’s artifacts, state, and logs.
- **Polyglot**: first‑class multi‑language with a uniform executor contract.
- **Reproducibility**: contexts are single‑file specs; runs are timestamped and diffable.
- **Ergonomics**: keyboard‑driven, modal‑free speed paths; power features discoverable.

---

## 1) What’s solid today (keep & extend)

- Visual quadtree canvas with contexts, JSON import/export, and PNG export.
- Modal **CodeEditor** and **Output** flows; **Explorer** lists and batch‑runs code cells.
- Dynamic plugin discovery under `runtime/plugins/`, plus a minimal plugin template.
- Stateful per‑language sessions for interpreters (via `ExecutorSession`).

These give us the essential substrate; the rest is polish, power, and discipline.

---

## 2) Immediate fixes (same week)

**2.1 Duplications & wiring**
- **De‑duplicate** repeated definitions for *Cell Explorer* button and its event handler calls.
- Make modal dispatch strictly topmost‑wins; exit early when handled.
- Ensure `runtime/plugins/` exists before saving new executor files (already partially addressed).

**2.2 Safety/robustness**
- Add try/except guards around all file dialogs and image loads; surface errors in the Output modal.
- Clamp depth/size inputs; validate JSON before load; guard against missing keys.
- Make TIMEOUT per‑language/per‑cell (fallback to default).

**2.3 UX paper cuts**
- Editor: Ctrl/Cmd+A/C/V work; add Ctrl/Cmd+F (find), Shift+Enter (run), Ctrl+S (save).
- Explorer: space toggles selection; A selects all; F filters by language/status.
- Right‑click on canvas: add quick “Run cell” and “Open code” actions.

---

## 3) Executor API v1 (uniform, inspectable, future‑proof)

**Current**: `_exec(code: str, g: dict | None) -> (ok: bool, out: str)`

**Proposed (back‑compat shimmed)**:
```python
@dataclass
class ExecMeta:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    wall_ms: float = 0.0
    artifacts: dict[str, str] = {}         # name -> absolute path (or data: URIs for small items)
    diagnostics: list[dict] = []           # e.g., {severity, line, col, message}
    session_changed: bool = False          # if plugin mutated its session state
    extras: dict[str, Any] = {}            # plugin-defined

def _exec(code: str, g: dict | None) -> tuple[bool, ExecMeta]
```

**Why/benefits**
- Standardizes stdout vs stderr; records timing consistently.
- Allows **artifacts** (files/images/plots) and **diagnostics** (lint, compile errors).
- Enables smarter **Explorer** filtering/sorting and richer Output rendering.

**Migration**
- Wrap legacy `(ok, str)` returns into `ExecMeta(stdout=out)`; deprecate in one release.

---

## 4) Execution engine 2.0 (non‑blocking, observable)

- **Job queue**: enqueue runs from Editor/Explorer; execute on a **ProcessPool** (per language) to avoid main‑thread stalls and to isolate failures.
- **Session lifecycle**: per‑language *Reset*, *Snapshot*, *Restore* (for Python workers); expose in UI.
- **Per‑cell policy**: timeout, max‑mem, env vars, argv; editable in Editor footer.
- **Structured status bus**: replace free‑form text with JSON events (start, log, artifact, done); Explorer renders events and keeps a rolling buffer.

---

## 5) Dataflow & artifacts (from “cells of code” → “cells of systems”)

- **Cell links**: optional `inputs: ["d:idx", ...]` and `outputs: ["name", ...]` metadata.
- **Artifact browser**: sidebar tab listing artifacts by cell; preview images/text; open in OS.
- **Run‑graph**: Explorer mode to run topologically by declared inputs; show critical path timing.

---

## 6) Editor & Explorer upgrades (power features)

**Editor**
- Monospace gutter diagnostics; inline error squiggles from `ExecMeta.diagnostics`.
- Command palette (Ctrl/Cmd+K): *Run*, *Save*, *New executor*, *Reset session(lang)*, *Find cell by id*.
- Optional syntax highlight (Pygame‑friendly tokenizer; keep fast/low‑GC).

**Explorer**
- Columns: d:idx, lang, lines, *status*, *last run*, *ms*, *artifacts* count.
- Tabs: *All*, *Failed*, *Changed*, *By language*.
- Actions: *Run selected*, *Run failed*, *Run by language*, *Run graph*.
- Log pane shows structured events; toggle raw/pretty view.

---

## 7) Plugins & discovery (scale beyond local files)

- Support **entry points** (installed executors) in addition to `runtime/plugins/` scans.
- Provide a **plugin starter** command that writes a scaffold with tests and `pyproject.toml`.
- A small “**Executor SDK**” package with helpers: `compile_and_run`, artifact emitters, event logging.

---

## 8) Security (be explicit)

- Default to **process isolation** for all languages; Python in a worker, compiled in fresh temp dirs.
- Sandboxed execution: temp directories, stripped env, optional `seccomp`/JobObjects where available.
- Confirm before running files that touch the network or filesystem outside the temp dir (policy flag).

---

## 9) Performance

- **UI**: dirty‑rect redraw; static grid caching; font render cache for line numbers.
- **I/O**: memory‑map large JSON; stream PNG export; debounce `REG.tick()` scans.
- **Exec**: re‑use workers; pre‑compile often‑used snippets where languages allow.

---

## 10) Persistence & versioning

- **Context schema v2**: add `version`, per‑cell metadata (policy, inputs/outputs), and per‑run history (last N). Provide migration from v1.
- **Deterministic export**: stable key orders; optional content hashes in a footer block.
- **Diff‑friendly save**: split large payloads into sidecar files on export (opt‑in).

---

## 11) Testing & release discipline

- Unit tests for: registry discovery, session lifecycle, `compile_and_run`, JSON I/O, Explorer filters.
- Golden‑file tests for PNG export and code rendering.
- Headless CI run + smoke scripts for two sample plugins (python, c/cpp).
- Release train: `0.4.0` (engine/UX), `0.5.0` (dataflow/artifacts), `0.6.0` (plugin SDK + security).

---

## 12) Milestones (with “Definition of Done”)

**M1 — *Core hygiene* (week 1)**
- [ ] Remove duplicated Explorer button/handler; modal dispatch audit.
- [ ] Per‑cell timeout UI; safe file dialogs.
- [ ] Editor shortcuts; Explorer keyboarding.

**DoD**: zero duplicate UI hooks; keyboard cheatsheet shows in‑app; tests pass.

**M2 — *Exec API & engine* (weeks 2–3)**
- [ ] ExecMeta introduced & shims; structured status events.
- [ ] Process workers per language; session Reset/Snapshot/Restore.
- [ ] Policy footer (timeout/mem/env/argv).

**DoD**: two built‑in plugins (python, c/cpp) emit ExecMeta; Explorer renders diagnostics & artifacts; main loop never blocks during runs.

**M3 — *Artifacts & dataflow* (weeks 4–5)**
- [ ] Cell `inputs/outputs`; Run‑graph mode; artifact browser.
- [ ] PNG/text previewers in Output; open‑in‑OS.

**DoD**: topological batch runs succeed on sample LLM/OS canvases; artifacts list view stable.

**M4 — *Plugins at scale* (week 6)**
- [ ] Entry‑point discovery; executor starter; SDK docs.
- [ ] Security policy switches and defaults.

**DoD**: external plugin installed via pip is auto‑discovered; sandbox on by default; example plugin passes CI.

---

## 13) Appendix — Suggested data contracts

**Per‑cell payload (v2)**
```json
{
  "type": "code | text | image",
  "code": "…",
  "language": "python",
  "policy": {"timeout": 5, "max_mem_mb": 512, "env": {}, "argv": []},
  "inputs": ["1:0", "1:1"],
  "outputs": ["logits", "loss"],
  "last_run": "2025-08-06T12:00:00Z",
  "last_ok": true,
  "exec_ms": 12.7
}
```

**Status event**
```json
{"type":"start","cell":"1:3","lang":"python","ts":...}
{"type":"log","cell":"1:3","msg":"epoch=1 loss=1.23"}
{"type":"artifact","cell":"1:3","name":"plot.png","path":"/tmp/…/plot.png"}
{"type":"done","cell":"1:3","ok":true,"ms":12.7}
```

---

All set! Create a tiny, pip-installable external executor package that proves entry-point discovery end-to-end.

**Download the package:**

* ZIP: [fabric-exec-echo.zip](sandbox:/mnt/data/fabric-exec-echo.zip)
* Folder (if you prefer): `/mnt/data/fabric-exec-echo/`

### What it does

Registers a new language: **`echo`**. Running a cell with `lang: "echo"` will return the cell’s code as `stdout`. If your app has the **ExecMeta** shim from the patch, it uses `ExecMeta(stdout=...)`; otherwise it falls back to legacy `(ok, str)` and will be wrapped automatically.

### How to install locally

```bash
# Option A: from the unzipped folder
pip install ./fabric-exec-echo

# Option B: from the zip (unzip first)
unzip fabric-exec-echo.zip
pip install ./fabric-exec-echo
```

### How to try it in your LAB

1. Make sure the patch for entry-point discovery is applied and `ENTRYPOINT_GROUP` is `fabric_nodes.executors`.
2. Start the app.
3. Create a code cell with **language**: `echo` and put any text in the code area.
4. Run it — the output should mirror your input, proving the plugin was discovered via entry points.

If you want, I can also generate a second sample (e.g., `upper` that uppercases output, or a `sh` shell runner with a time/line cap) to demonstrate multiple entry points in the same package.


### Closing

Keep the canvas simple, but make **execution** world‑class. With the above, `nodes.py` becomes the go‑to bench for programmers who move between interpreters, compilers, and systems sketches daily.
