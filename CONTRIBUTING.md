# Contributing

Thanks for improving **ez-comfy-stack**.

## Workflow

1. Branch from latest `development`  
2. Prefer TDD (`make test` / `make coverage`)  
3. **Commit tests with the production files they cover** (same commit)  
4. Run `make lint` and `make docs`  
5. Open a PR into `development`  

```mermaid
flowchart TB
  A["Branch from development"] --> B["TDD: red → green → refactor"]
  B --> C["Commit tests + production together"]
  C --> D["make lint · make docs · make coverage"]
  D --> E["PR into development"]
```

## Commit messages

```text
<type>: <imperative summary>
```

Types: `feat`, `fix`, `docs`, `test`, `chore`, `ci`, `refactor`.

## Tests ship with production code

```mermaid
flowchart LR
  P["scripts/lib/*.sh"] --> T1["tests/bats/lib_unit.bats"]
  U["scripts/utilities/name.sh"] --> T2["tests/bats/name.bats"]
  M["scripts/manage.sh"] --> T3["tests/bats/manage.bats"]
  D["docker/patch_*.py · safety"] --> T4["tests/python/* · safety.bats"]
```

## PR checklist

- [ ] Tests updated in the same commits as the code they exercise  
- [ ] `make coverage` passes (100% gate)  
- [ ] `make lint` clean  
- [ ] `make docs` (mkdocs strict)  
- [ ] Safety impact called out if Docker/resources/download-limit changed  
- [ ] Docs updated for operator-facing changes  

## Style

See [docs/project-conventions.md](docs/project-conventions.md) and [AGENTS.md](AGENTS.md).
