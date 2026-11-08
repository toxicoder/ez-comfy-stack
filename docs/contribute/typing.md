---
title: Strong types
description: The typing policy for every language in the repo, the declared Any boundaries, and the gate that keeps broad types out.
tags: [conventions, python, typescript, typing, contributing]
---

# Strong types

Every value in this repo has a name. `Any` is a declaration that a boundary
exists, never a way to finish a signature, and the typecheck gate fails the
build when the two are confused.

**What's on this page**

- **The rule** - what the checkers enforce, per language
- **Choosing a type** - the ladder from precise to declared boundary
- **Declared boundaries** - the modules allowed to keep `Any`, and why
- **Recipes** - graph documents, tensors, optional imports, JSON records
- **Gates** - the command that proves a change holds
- **Related** - the pages this one expands

**What this enables**

- **Reviewing** a change without guessing what a dict can hold
- **Keeping** the hermetic lane honest: no torch, numpy, bpy, or Comfy install
- **Finding** a bug at the line that introduced it instead of at the node that
  consumed it
- **Refusing** a broad type that a later reader would have to re-derive

## The rule

| Language | Instruments | Gate |
| --- | --- | --- |
| Python (first-party) | PEP 613 `TypeAlias`, `TypedDict`, `Protocol`, `NewType`, `Literal`, `Enum`, `dataclass(frozen=True)` | `bazelisk test //tests:typecheck` |
| Python (myPy) | `disallow_untyped_defs`, `disallow_any_generics`, **`disallow_any_explicit`**, `warn_return_any`, `warn_unused_ignores`, `ignore-without-code` | `mypy.ini` over production (`bazelisk test //tests:typecheck`, zero errors); `mypy-tests.ini` over the pytest tree, ratcheted by `bazelisk test //lints:mypy_tests` (`lints/mypy_tests_baseline.json`) |
| Python (Pyright) | `standard` plus `reportMissingTypeArgument`, `reportUnreachable`, `reportUnnecessaryComparison`, `reportImplicitOverride` | `pyrightconfig.json` over production (zero errors); `pyrightconfig-tests.json` over the pytest tree, ratcheted by `bazelisk test //lints:pyright_tests` (`lints/pyright_tests_baseline.json`) |
| TypeScript (`docs-site/`) | `strict` plus `noUncheckedIndexedAccess`, `noImplicitOverride`, `noUnusedLocals`, `noUnusedParameters`, `exactOptionalPropertyTypes`; `zod` for data that enters at runtime | `bazelisk test //docs-site:typecheck` |
| JavaScript (`custom_nodes/*/js/`) | JSDoc with a **type expression** on every `@param` / `@returns`, `{object}` counted as debt, one `@typedef` vocabulary per pack | `bazelisk test //lints:js_types` (`tsc --checkJs`, ratcheted by `lints/js_types_baseline.json`) + `tests/python/test_jsdoc.py` |
| Shell | Google-style `Globals` / `Arguments` / `Outputs` / `Returns` header per function; `set -euo pipefail`; ShellCheck at warning level | `bazelisk test //:lint --test_tag_filters=manual` |
| YAML / JSON data | A record type in the reader that loads it, plus a schema file in `schemas/` when the file is authored by hand | `tests/python/test_strong_types.py` |

Python carries the most weight because it is the operational core (the in-canvas
packs, the MCP servers, the validators), so it is the language where the gate is
strictest.

## Choosing a type

Reach down this ladder and stop at the first rung that describes the value.

1. **A name you already have.** A `TypedDict` record, a frozen `dataclass`, an
   `Enum`, or a `Literal` union that exists in the owning pack. Reuse it.
2. **A record you can name.** JSON or YAML with known keys becomes a `TypedDict`
   in the pack that owns it (`ez_edit/protocol.py` is the house pattern). Keys a
   producer may omit are `NotRequired`; read those with `.get()` - Pyright
   rejects `td["optional"]` on a non-required key.
3. **A closed union.** `str | int` beats `object`, and `Literal["fast",
   "quality"]` beats both. An `Enum` when the members have behavior or travel
   across a process boundary.
4. **The real third-party class, behind `TYPE_CHECKING`.** A Comfy image is a
   `torch.Tensor`, not `Any`. Import the package under `if TYPE_CHECKING:` and
   alias it as a string: `ImageTensor: TypeAlias = "torch.Tensor"`. The checkers
   resolve it to real stubs where the package is installed and to an opaque
   imported value where it is not, so the hermetic lane needs no CUDA.
5. **`object`.** The value is opaque and only passes through. `object` is honest
   and it forces any consumer that inspects it to narrow first, which is the
   whole point.
6. **`Json`.** A parsed document whose shape is genuinely not known yet - see
   `ez_common/json_value.py`. Narrow it one level at a time.
7. **`Any`, declared.** Last rung, and only inside a module that
   `mypy.ini` lists as a boundary. A new boundary is a review conversation.

Bare generics are defects: `dict` and `list` without parameters fail
`disallow_any_generics`. So does a bare `# type: ignore` - name the code, and
`warn_unused_ignores` deletes the ones that stopped earning their keep.

## Three registers: law, boundary, debt

`mypy.ini` is the single registry, and `tests/python/test_strong_types.py`
reads it rather than duplicating it, so a module can only be loose where a human
wrote it down. The file holds three kinds of entry and they mean different
things.

**Law** is the default: every section at the top of `mypy.ini`, and every module
that appears nowhere. `disallow_any_explicit` is on, so a bare `Any` fails.

**Boundary** is a third-party edge this repo genuinely cannot type. It is a
section that sets `disallow_any_explicit = False`, it carries a written reason
in the file, and it needs a row in the table below. The inventory gate checks
both directions: a pattern in `mypy.ini` that is missing here fails, and a
pattern whose module no longer uses `Any` fails until you delete it.

| Module pattern | Why it is a boundary |
| --- | --- |
| `ez_common.protocols` | Comfy's `INPUT_TYPES` registry mixes `str` / `int` / `bool` / combo lists per widget, and tests index sections a node omits, so the payload stays an open map |
| `ez_common.tensors` | `np.ndarray` is generic in shape and dtype; spelling its parameters is the only way to keep the alias portable across hosts that do and do not install numpy |
| `sitecustomize` | An interpreter-start import hook (`docker/pythonpath/sitecustomize.py`) that receives third-party module objects and torch enum members it must not import eagerly |
| `blender.*` | `bpy` attribute chains are Blender-version dependent and `bpy` is not installed here, so a structural `Protocol` would assert more than the code can prove (the files are `tools/blender/*.py`, named from the `tools` mypy_path root) |

**Debt** is first-party code that should be tight and is not yet: mostly
`dict[str, Any]` where a `TypedDict` or the :mod:`ez_common.json_value`
vocabulary is the honest type. It is the block at the bottom of `mypy.ini`, each
section keyed on `disable_error_code = explicit-any` - a different option than a
boundary uses, on purpose, so a to-do cannot be laundered into a documented
exemption. Three ratchets in `tests/python/test_strong_types.py` keep the
ledger shrinking:

| Ratchet | What may not rise |
| --- | --- |
| `PRODUCTION_ANY_BUDGET` | total `Any` tokens across production code |
| `DEBT_MODULE_BUDGET` | number of modules listed as debt |
| `PRODUCTION_CAST_BUDGET` | number of `cast()` calls |

A debt section whose module has gone clean fails the build, which is how the
list empties: narrow one module, delete its section, and the budgets drop. New
code is never admitted to the ledger without a PR conversation, and a `fix:`
PR that adds an `Any` to a module already in the list still has to explain it.

The pytest tree is not a boundary and does not need one: `mypy-tests.ini`
checks it with the same flags minus `disallow_any_explicit`, because a fake that
says "I stand in for a torch tensor" is honest. mypy per-module patterns only
accept a wildcard as a whole dotted component, which is why that exemption
cannot live inside `mypy.ini`.

### Production is absolute; the pytest tree ratchets

Both checkers run twice. Over production (`mypy.ini`, `pyrightconfig.json`) a
single diagnostic fails the build, and `bazelisk test //tests:typecheck` is the
gate. Over the pytest tree (`mypy-tests.ini`, `pyrightconfig-tests.json`) the
same rules apply but the residue is recorded in a committed per-file ledger, so
a test file may go down and never up:

| Lane | Ledger |
| --- | --- |
| `bazelisk test //lints:mypy_tests` | `lints/mypy_tests_baseline.json` |
| `bazelisk test //lints:pyright_tests` | `lints/pyright_tests_baseline.json` |
| `bazelisk test //lints:js_types` | `lints/js_types_baseline.json` |

The tree owes that backlog because a test hands a production signature a fake,
and every signature this policy narrowed turned one of those fakes into a
diagnostic. Deleting the lane or deleting the tests are both worse outcomes than
a number with a name on it. Lower a number by teaching the test to narrow what
it gets back (`assert isinstance`, or a typed helper), never by widening the
production signature to suit the fake. The `--write` flag on either script
regenerates its ledger; use it only inside a reviewed decrease.

One rule is left off Pyright on purpose: `reportUnnecessaryTypeIgnoreComment`.
It asks "was this ignore needed?", and Pyright answers from its own rule names,
so every mypy-coded ignore this repo writes (`# type: ignore[explicit-any]`)
reads as dead weight to it. mypy's `warn_unused_ignores` asks the same question
against the rule names the ignores actually cite, and it is on and clean in both
configs, so nothing is unwatched.

### When the checker cannot see what is true

`Callable[..., T]` is the one place the law and the checker disagree. mypy
models a `...` parameter list as `Any[]`, so `disallow_any_explicit` flags the
spelling even when the result type is `object`. `custom_nodes/ez_film/protocols.py`
carries the single sanctioned `# type: ignore[explicit-any]` for that alias:
ffmpeg runners must accept `subprocess.run`, and mypy rejects an overloaded
callable as a `Protocol` implementation, so no `Protocol` shape can be the only
arm. Any second occurrence of that ignore is a design question, not a fix.

## Recipes

### A Comfy graph document

The two graph shapes are distinct types, and `ez_common/comfy_graph.py` keeps
them apart. `ComfyUiGraph` is the shipped `workflows/_lab/<lane>/<id>.json`
document (`nodes` is a list, edges are rows in `links`). `ComfyApiGraph` is what
`POST /prompt` accepts (`nodes` keyed by id, an input is a literal widget value
or a `[node_id, slot]` link).

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ez_common import ComfyUiGraph, NodeId, WidgetsValues

def _widget(graph: ComfyUiGraph, node_id: NodeId, index: int) -> WidgetsValues:
    """Read one widget slot out of a shipped graph."""
    ...
```

Node ids are a `NewType`, so the `int` ids the builders carry and the `str`
keys the file uses cannot be mixed by accident. Coerce at the boundary with
`as_node_id()` and index a UI graph with `ui_nodes_by_id()`.

### A tensor

Annotate the real class through `ez_common/tensors.py` and never import torch
at runtime for an annotation. `ImageTensor`, `MaskTensor`, `LatentTensor`,
`PcmTensor`, `Tensor`, and `NdArray` are all there is; a pack that needs a
pack-specific tensor aliases it locally.

### A JSON or YAML record

`json.loads` returns `Json`, and the loader narrows it:

```python
def load_catalog(path: Path) -> DiskCatalog:
    """Read and validate a disk catalog."""
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise CatalogError("catalog must be a JSON object")
    return validate_catalog(parsed)
```

Validation stays hand-written and stdlib-only: the hermetic pytest lane does not
install PyYAML, pydantic, or jsonschema, and the container image does not gain a
dependency to save typing. A validator is a function that takes `object` and
returns the record, so the type system sees the narrowing.

### A behavioral seam

Small capability interfaces are `typing.Protocol` and classes satisfy them
structurally - do not inherit, and do not use `abc.ABC`. `Callable[..., Any]`
is banned outright: name the parameters and the return, or write a `Protocol`.

### A frontend extension

The ComfyUI frontends under `custom_nodes/*/js/` are plain JavaScript, so their
types live in JSDoc. Every `@param` / `@returns` carries a type expression, and
`{object}` is debt: the parameter is used as a record, so `tsc --checkJs`
reports every property read against it as an error. Name the payload with
`@typedef` and the reads check out:

```js
/**
 * @typedef {object} PresetRow
 * @property {string} id Preset id shown in the picker.
 * @property {string} label Human label.
 * @property {number} steps Sampler steps the preset pins.
 */

/**
 * Render one preset row.
 * @param {PresetRow} row The preset to render.
 * @returns {string} Markup for the row.
 */
function renderRow(row) { ... }
```

The checker runs with `--noResolve`: the extensions import ComfyUI's own
frontend at runtime-only relative paths (`../../scripts/app.js`) that do not
exist in this repo, so module resolution is skipped and the ComfyUI objects
arrive untyped, exactly as they do in the browser. `lints/js_types_baseline.json`
records what each file still owes - a number may fall, never rise.

The compiler is the one the docs-site lockfile pins, which is why the gate looks
for `docs-site/node_modules/.bin/tsc` first and a `tsc` on the `PATH` only after
that: one TypeScript checks both trees, so a version bump moves the site build
and this ledger together. Provision it with `bazelisk run //docs-site:install`;
the CI core job runs that step before `//:lint`, because `//:lint` sets
`REQUIRE_LINT_TOOLS=1` and a lane that could not find its tool has to fail.

### When a cast is the honest answer

`cast()` asserts a type instead of proving one, so it is ratcheted
(`PRODUCTION_CAST_BUDGET`) exactly like `Any` is. It is the right tool at one
place: a value that enters from outside the type system - `json.load`, a
dependency injected by a test, an `object()` coming back from a registry - where
the shape was already validated somewhere else, and where the `isinstance` guard
that would prove it here is a branch no test reaches. The 100% line-coverage
floor rules that guard out, which is why the repo trades it for a budgeted cast
rather than an uncovered `raise`.

```python
ShotList: TypeAlias = list[int]

def _size(data: JsonObject) -> ShotList:
    return cast(ShotList, data.get("size") or [PACK_WIDTH, PACK_HEIGHT])
```

Everywhere else, prove it: a `TypedDict` for a record, an `isinstance` chain on a
value the caller already has to supply, or a `Protocol` for an injected callable.
A cast in a function body that only touches first-party values is a defect with a
number on it.

## Gates

```bash
bazelisk test //tests:typecheck          # Pyright + mypy over production Python (zero errors)
bazelisk test //lints:mypy_tests         # pytest-tree mypy, against its committed ledger
bazelisk test //lints:pyright_tests      # pytest-tree Pyright, against its committed ledger
bazelisk test //lints:js_types           # JSDoc frontends, against their committed ledger
bazelisk test //tests:pytest             # pytest lane; inventory gate (no per-file target)
bazelisk test //docs-site:typecheck      # tsc --noEmit over the docs site
bazelisk test //:validate                # everything a PR has to satisfy
```

`tests/python/test_strong_types.py` is the inventory gate. It walks
`custom_nodes`, `docker`, `docs`, `scripts/lib`, `studio-ui`, and `tools` and
fails when a file outside the declared boundaries and the debt ledger mentions
`Any`, when `Callable[..., Any]` appears anywhere, when a `# type: ignore` has
no code, when a boundary or a debt module stops carrying `Any`, or when the
production `Any`, `cast()`, or debt-module count climbs above its recorded
budget. All three budgets only move down.

When the typecheck lane is red, fix the type at the line that produced the
value. Widening a signature to accept what a caller already passes, or adding a
`# type: ignore`, moves the defect instead of removing it.

## Related

| Need | Page |
| --- | --- |
| The eight principles and the gate table | [Conventions](../project-conventions.md) |
| Which lane to run after which edit | [Building with Bazel](building-with-bazel.md) |
| The coverage and docstring inventories | [Testing docs](testing-docs.md) |
