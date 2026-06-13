# Fortran Corpora (graphify)

How the kg-skill layer handles **any Fortran source** — `MODULE` / `SUBROUTINE` / `FUNCTION` / `USE` / `CALL` structure, the C-preprocessor step for capital-`F` files (and its **macOS limitation**), the verified node/edge model, and the dependency-graph workflow this unlocks. Applies to scientific-computing / HPC code broadly; WRF is used below only as one worked example.

> **Version gate.** Fortran extraction does **not** exist in graphify v0.5.x. Base extraction (MODULE/SUBROUTINE/FUNCTION/PROGRAM/USE/CALL) landed in **v0.7.2** (#694); **v0.8.24** added Fortran *type-reference* edges (#1071); v0.8.29 hardened the cpp step. This skill targets **`graphifyy>=0.8.24`** (recommended: latest, `0.8.39`) for the full edge model, but the basic graph works from `0.7.2`. On a v0.5.x install every `.f`/`.F` file is silently treated as a non-code blob. Verify with `graphify --version` (prints `graphify 0.8.39`) — note `graphify --help` does **not** print a version — or `python -c "import tree_sitter_fortran"`.

## When this applies

The corpus contains Fortran: `.f .F .f90 .F90 .f95 .F95 .f03 .F03 .f08 .F08`. Both upper- and lower-case extensions are recognized. (**`.inc` is NOT parsed as Fortran** — graphify dispatches `.inc` to the Pascal extractor (`extract.py` ext map), so an `.inc` include file yields only an opaque file node with zero module/subroutine/use/call structure. Put extractable Fortran in a `.f`/`.f90`-family file.) This covers essentially any Fortran codebase, e.g.:

- **Numerical / scientific libraries** — linear algebra, ODE/PDE solvers, special functions, symbolic regression (e.g. AI-Feynman), optimization.
- **HPC / simulation** — CFD, FEM, molecular dynamics, computational physics/chemistry, MPI/OpenMP codes.
- **Earth-system models** — weather/climate/ocean (WRF, MPAS, CESM, …), often with heavy `#ifdef` macro use (see the cpp limitation below).
- **Legacy Fortran 77/90+** being audited, documented, modernized, or **ported** to another language (the dependency map is valuable before/while porting).

## Install (Fortran-ready graphify)

```bash
uv tool install graphifyy            # tree-sitter-fortran is a CORE dependency (pyproject), so no extra is needed
```

`pip install` is discouraged on macOS/Windows (Python-env mismatch → `ModuleNotFoundError`); `uv tool install` puts `graphify` on PATH in an isolated venv. For capital-`F` (`.F`) preprocessing to actually work you need a **GNU `cpp`** on PATH — see the cpp section: macOS Apple-clang `cpp` does **not** work for graphify's invocation.

## What graphify extracts from Fortran

The Fortran extractor (`extract.py::extract_fortran`) is pure tree-sitter AST and makes **no LLM calls** — it derives these nodes/edges from source bytes alone. (Whether a given graphify *command* stays offline is separate — see § Offline vs LLM below.)

| Construct | Maps to (by label form) | Label form |
|---|---|---|
| Source file | file node | `solver.f90` |
| `program X` | program | `x` |
| `module X` | module | `x` |
| `subroutine X(...)` | subroutine | `x()` |
| `function X(...)` | function | `x()` |
| `type :: T ... end type` | derived type | `t` |

> These categories are **not** stored as a node-type field — every Fortran node carries the same keys (`id`, `label`, `file_type=code`, `source_file`, `source_location`). A node's role is inferred only from its **label form**: bare lower-cased name (program/module/derived-type), trailing `()` (subroutine/function), or filename-with-extension (file node).

| Relation | Direction | From | Notes |
|---|---|---|---|
| `defines` | scope → child | file→program/module, module→subroutine/function/type | structural containment |
| `imports` (context `use`) | scope → module | `USE mod` statement | the **dependency backbone** — most reliable signal |
| `calls` (context `call`) | scope → callee | `CALL foo(...)` | all CALL forms parsed; an edge survives only for **same-file** callees — see caveat |
| `references` (context `parameter_type` / `return_type`) | proc → derived type | typed args / result of derived type | type usage |

Names are **lower-cased** (Fortran is case-insensitive), so `FOO`, `Foo`, `foo` collapse to one node.

### C-preprocessor step (capital-`F` files) — and its macOS limitation

For capital-F extensions (`.F .F90 .F95 .F03 .F08`) graphify *tries* to run the file through `cpp -w -P -nostdinc -I /dev/null <abs-path>` before parsing, intending to resolve `#ifdef`/`#if`/`#define` macros to the active code path first. **This only works where a GNU `cpp` accepts that invocation (Linux/gcc, or Homebrew `gcc`'s `cpp-NN`).**

**macOS caveat (verified):** the default `/usr/bin/cpp` is Apple-clang, which **rejects** graphify's exact argv — `cpp -w -P -nostdinc -I /dev/null <file>` returns `rc=1` with empty stdout (`cc: error: no such file or directory: 'c'`). graphify then **silently falls back to raw bytes** (`extract.py`), so **no macro is resolved and every `#if`/`#else`/`#ifdef` branch is parsed at once**. Proof: the WRF example below contains both the `#if defined(mpas)` branch (`mpas_atmphys_*`) and its `#else` branch (`module_ra_gfdleta`, `module_wrf_error`) as simultaneous USE edges — impossible if cpp had resolved. To get real preprocessing on macOS you must make a binary **literally named `cpp`** resolve to GNU cpp ahead of `/usr/bin` — graphify calls the bare name via `shutil.which("cpp")` and never looks for `cpp-15`, so `brew install gcc` alone (it only installs a versioned `cpp-N`, e.g. `cpp-15`) does nothing. Symlink the newest installed one (version-agnostic):

```bash
mkdir -p ~/.local/bin
ln -sf "$(ls -1 "$(brew --prefix gcc)"/bin/cpp-* | sort -V | tail -1)" ~/.local/bin/cpp
# put ~/.local/bin before /usr/bin on PATH, then verify it resolves to the GNU path (not /usr/bin/cpp):
python -c "import shutil; print(shutil.which('cpp'))"
```

Lower-case `.f90` is parsed as-is (never preprocessed).

**Security note (untrusted corpora):** `-nostdinc -I /dev/null` only clears the standard system-header search path — it does **not** sandbox includes. Where graphify's cpp invocation actually runs (a GNU-cpp host), an absolute-path directive like `#include "/etc/passwd"` (and current-directory-relative quote includes) is still read and inlined — verified on GNU cpp (`cpp-15`): graphify's argv inlines an absolute-path include (a planted `SECRET_TOKEN` leaked into the output). On macOS Apple-clang the invocation fails (rc=1) so neither macro resolution **nor** the include-leak fires there — but **do not run capital-`F` extraction on a Fortran corpus you do not trust** on any GNU-cpp host. (Lower-case `.f90` is not preprocessed, so it is not subject to this.)

## Offline vs LLM (don't overclaim)

Extracting **code** — including all Fortran structure — is local tree-sitter AST with **no LLM call**, for *both* `graphify update` and `graphify extract`. (Verified: `graphify extract` on a code-only Fortran corpus did AST-only and made no model call even with an API key set; per graphify's own docs, "code is extracted locally with no API calls".) graphify calls a model only for:

- **Non-code files in the corpus** — docs, PDFs, images go through the model API. A pure Fortran corpus has none.
- **`graphify extract --mode deep`** (and `--dedup-llm`) — richer INFERRED-edge semantic extraction, which can send code to the model.
- **Community naming** — `cluster-only` / `GRAPH_REPORT.md` label communities via an LLM backend. Clustering itself (Leiden if the optional `graspologic` extra is installed — Python<3.13 only — else Louvain) is offline; with no backend the communities stay `Community N` placeholders (graph structure unaffected).

So a Fortran (code) graph builds with no LLM via `update` **or** `extract`; community *naming* and `--mode deep` are the only LLM touchpoints.

## Verified behavior (code-only corpus, no API key → 0 LLM calls)

**Free-form `.f90` — AI-Feynman `symbolic_regress1.f90` + `tools.f90`** → 13 nodes / 14 edges / 4 communities. The graph has exactly **3 `calls` edges** (only same-file callees survive):

```
symbolic_regress1.f90 --defines--> symbolic_regress (program)
symbolic_regress      --calls--> go()                       # the only program-level call edge
tools.f90             --defines--> f(), limit(), loadmatrixtranspose(), multiloop(),
                                   mymedian(), permutation(), ran1(), sort(), sort2()   # 9 procedures
mymedian()            --calls--> sort()                     # same-file calls captured
permutation()         --calls--> sort2()
```

Note: subroutine `go` *does* `CALL multiloop(...)` and `CALL LoadMatrixTranspose(...)`, but those callees are defined cross-file in `tools.f90`; the call edges are **dropped** during cross-file resolution (callee unresolved) and the procedures survive only as `defines` targets. This is the cross-file limitation, not a CALL-syntax issue (see Caveats).

**Capital-`F` (macOS, raw fallback) — WRF v4.7.0 `module_mp_wsm6.F` + `module_sf_noahdrv.F` (`noahdrv.F` alone has 73 cpp directive lines)** → 23 nodes / 23 edges / 3 communities:

```
module_mp_wsm6.F  --defines--> module_mp_wsm6 --imports[use]--> {ccpp_kind_types, mp_wsm6, mp_wsm6_effectrad}
module_mp_wsm6    --defines--> wsm6()
module_sf_noahdrv --imports[use]--> {module_sf_noahlsm, module_sf_urban,
                                     mpas_atmphys_utilities, module_ra_gfdleta, module_wrf_error, ...}
#  ^ BOTH the #if-defined(mpas) branch (mpas_atmphys_*) AND its #else branch (module_ra_gfdleta,
#    module_wrf_error) appear together — on macOS cpp failed, so #ifdef was NOT resolved and all
#    branches were parsed (see the cpp macOS caveat). On a GNU-cpp host only the active branch would remain.
```

## Typical workflow (any Fortran codebase)

```bash
# 1. Build the graph — local tree-sitter AST, no LLM call
graphify update /path/to/fortran/src
#    capital-F (.F) preprocessing fires only on a GNU-cpp host (no-ops on macOS Apple-clang).
#    `graphify extract` is equivalent for a code corpus (also AST-only / no LLM);
#    it calls a model only for non-code files or with --mode deep.

# 2. Dependency backbone — what a module USEs (filter to USE edges only)
graphify query "<module-name>" --context use --budget 800

# 3. Blast radius — what breaks if you change something (reverse traversal).
#    Module (USE backbone) → --relation imports ; derived type → --relation references
#    (the two use DIFFERENT relations — see the edge table above):
graphify affected "<module>" --relation imports --depth 3
graphify affected "<type>"   --relation references --depth 3
#    --relation is repeatable, so `--relation imports --relation references` covers both at once.

# 4. Communities / god nodes — which routine everything flows through
graphify cluster-only /path/to/fortran/src   # clustering offline; community *naming* in
#    GRAPH_REPORT.md needs an LLM backend (else `Community N` placeholders)
```

The `USE`/`defines` graph is the module dependency order; `affected` gives the change-impact set before a refactor; god-nodes identify the central routine. This is generically useful for understanding/auditing a Fortran codebase, and specifically helpful when **modernizing or porting** a scheme (oracle/parity-test the central routine first, follow the dependency order).

## Caveats (verified — be honest about these)

- **`calls` is partial across files.** CALL detection itself is robust — positional (`call go`), keyword-argument (`call run(t=t_hv, q=qv_hv, ...)`), and `&`-continuation calls are all parsed and emitted. But a `calls` edge **survives only when the callee is defined in the same file**; cross-file callees (WSM6's `mp_wsm6_run`/`refl10cm_wsm6` from `USE`d modules; AI-Feynman's `multiloop`/`LoadMatrixTranspose` defined in `tools.f90`) emit stem-local target ids that fail cross-file resolution and are dropped at dedup. External/library callees are likewise dropped. **Treat the call graph as best-effort** — the `USE`/`module`/`defines`/`references` structure is the reliable signal. Also note: procedure-level `affected "<sub>" --relation calls` needs a **unique** label — a common subroutine name (`go`, `init`, `run`) defined in several files returns `No unique node match` rather than a result; query at module/type granularity, or disambiguate with the file-qualified node id.
- **`tree-sitter-fortran` must be importable.** If absent, the extractor returns `{"error": "tree-sitter-fortran not installed"}` and the file yields no nodes. It is a core dependency of `graphifyy`, but a partial/old install may lack it.
- **macOS `.F` preprocessing does not work.** Apple-clang `cpp` fails graphify's invocation, so `.F` is parsed raw with all `#ifdef` branches present (see cpp section). Lower-case `.f90` is unaffected. Use a GNU `cpp` host for real macro resolution.
- **Cross-file `CALL`/`USE` resolution** happens in graphify's later dedup/ghost-merge pass (`USE`-target and `CALL`-callee nodes start file-local and are reconciled across files), so single-file extraction shows stem-local targets until the full corpus is built.

## kg-skill integration points

- **`/kg-update`** — bootstraps/refreshes a Fortran graph via `graphify update <src-dir>` (AST-only, no LLM). Use `--force` after a refactor that deletes routines so the node count is allowed to shrink.
- **`/kg-query`** — `--context use` for dependency questions; reverse impact via `affected` (see `/kg-query` Impact mode).
- **`/kg-lint`** — note: graphify's import-cycle detection does **not** cover Fortran. `find_import_cycles` (analyze.py) only considers `imports_from`/`re_exports` edges, but Fortran `USE` is relation `imports` (context `use`) — so circular Fortran `USE` chains are **not** surfaced. Detect them manually if needed.
- **`/kg-ingest`** — file modules as Artifact pages (`code_refs: ["solver.f90:42"]`), linking `[[wikilinks]]` along the `USE` backbone.
