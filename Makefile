# ez-comfy-stack — thin operator / CI entry points
#
# Purpose:
#   Provide short, documented targets for the workflows contributors run most:
#   hermetic tests, coverage gate, shell format/lint, MkDocs build, and doctor.
#   Does not wrap Docker stack start/stop (use ./scripts/manage.sh for that).
#
# Requirements:
#   bash, bats, python3, shellcheck, shfmt; pytest+pytest-cov for coverage;
#   docs/requirements.txt (mkdocs-material + mike) for docs.

.PHONY: help test bats python coverage lint fmt docs doctor clean

# @target help — list available Make targets
help:
	@echo "Targets:"
	@echo "  make test       Run BATS + Python tests"
	@echo "  make coverage   100% coverage gate"
	@echo "  make lint       shellcheck + shfmt check"
	@echo "  make fmt        shfmt -w"
	@echo "  make docs       mkdocs build --strict"
	@echo "  make doctor     ./scripts/manage.sh doctor"

# @target test — full hermetic suite (see tests/run_all.sh)
test:
	bash tests/run_all.sh

# @target bats — shell behavior tests only (parallel across files when available)
bats:
	@jobs="$${BATS_JOBS:-}"; \
	if [ -z "$$jobs" ]; then \
	  jobs=$$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4); \
	fi; \
	if bats --help 2>&1 | grep -q -- '--jobs' && command -v parallel >/dev/null 2>&1; then \
	  bats --jobs "$$jobs" --no-parallelize-within-files tests/bats; \
	else \
	  bats tests/bats; \
	fi

# @target python — patch module unit tests with 100% coverage fail-under
python:
	PYTHONPATH=docker python3 -m pytest tests/python -q --cov=patch_get_free_memory --cov-fail-under=100

# @target coverage — Python 100% + shell function inventory + BATS
coverage:
	bash tests/coverage.sh

# @target lint — ShellCheck + shfmt diff (no write)
lint:
	shellcheck -x scripts/manage.sh scripts/lib/*.sh scripts/utilities/*.sh docker/*.sh docker/install-comfy/*.sh
	shfmt -d -s -i 2 -ci scripts docker/install-comfy.sh docker/install-comfy docker/entrypoint.sh tests/coverage.sh tests/run_all.sh

# @target fmt — apply shfmt -w to shell sources
fmt:
	shfmt -w -s -i 2 -ci scripts docker/install-comfy.sh docker/install-comfy docker/entrypoint.sh tests/coverage.sh tests/run_all.sh

# @target docs — strict MkDocs Material build into site/ (publish is Actions + mike)
# NO_MKDOCS_2_WARNING: suppress Material advisory; stack is pinned to mkdocs 1.x.
docs:
	NO_MKDOCS_2_WARNING=1 python3 -m mkdocs build --strict
	# Match deploy-docs.yml: mike copies from site/; skip Jekyll on Pages.
	touch site/.nojekyll

# @target doctor — host preflight without starting the stack
doctor:
	./scripts/manage.sh doctor

# @target clean — remove local build/test artifacts (not models or git state)
clean:
	rm -rf site coverage .coverage htmlcov .pytest_cache
