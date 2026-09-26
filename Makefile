# ez-comfy-stack - Bazel-primary with Make compatibility shims
#
# Preferred:
#   bazelisk run //:validate
#   bazelisk test //:test-fast
#   bazelisk test //:lint --test_tag_filters=manual
#   bazelisk run //:fix
#   bazelisk run //docs:docs
#   bazelisk run //:manage -- doctor
#
# This Makefile exists for people without bazelisk and for muscle memory.
# Most targets delegate to Bazel when bazelisk/bazel is on PATH.

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

BAZEL := $(shell command -v bazelisk 2>/dev/null || command -v bazel 2>/dev/null || echo "")

.PHONY: help test bats python coverage lint typecheck fmt docs doctor clean fix validate

# @target help - list available Make targets
help:
	@echo "ez-comfy-stack (Bazel primary)"
	@echo ""
	@echo "Preferred (bazelisk):"
	@echo "  bazelisk run //:validate"
	@echo "  bazelisk test //:test-fast"
	@echo "  bazelisk test //:lint --test_tag_filters=manual"
	@echo "  bazelisk run //:fix"
	@echo "  bazelisk run //docs:docs"
	@echo "  bazelisk run //:manage -- doctor"
	@echo ""
	@echo "Makefile shims:"
	@echo "  make test       (bazelisk test //:test-fast, else tests/run_all.sh)"
	@echo "  make coverage"
	@echo "  make lint"
	@echo "  make typecheck"
	@echo "  make fmt / make fix"
	@echo "  make docs"
	@echo "  make validate"
	@echo "  make doctor"

# @target test - full hermetic suite (BATS + pytest + Pyright + mypy)
test:
	@if [ -n "$(BAZEL)" ]; then \
	  echo "-> Bazel primary: bazelisk test //:test-fast"; \
	  $(BAZEL) test //:test-fast; \
	else \
	  bash tests/run_all.sh; \
	fi

# @target bats - shell behavior tests only
bats:
	@if [ -n "$(BAZEL)" ]; then \
	  $(BAZEL) test //tests:bats; \
	else \
	  jobs="$${BATS_JOBS:-}"; \
	  if [ -z "$$jobs" ]; then \
	    jobs=$$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4); \
	  fi; \
	  if bats --help 2>&1 | grep -q -- '--jobs' && command -v parallel >/dev/null 2>&1; then \
	    bats --jobs "$$jobs" --no-parallelize-within-files tests/bats; \
	  else \
	    bats tests/bats; \
	  fi; \
	fi

# @target python - patch module unit tests with 100% coverage fail-under
python:
	@if [ -n "$(BAZEL)" ]; then \
	  $(BAZEL) test //tests:pytest; \
	else \
	  bash tests/run_pytest.sh; \
	fi

# @target coverage - Python 100% + Pyright + mypy + shell function inventory + BATS
coverage:
	@if [ -n "$(BAZEL)" ]; then \
	  echo "-> Bazel primary: bazelisk test //:test-fast"; \
	  $(BAZEL) test //:test-fast; \
	else \
	  bash tests/coverage.sh; \
	fi

# @target typecheck - Pyright (Pylance) + mypy on first-party Python
typecheck:
	@if [ -n "$(BAZEL)" ]; then \
	  $(BAZEL) test //tests:typecheck; \
	else \
	  bash tests/typecheck.sh; \
	fi

# @target lint - ShellCheck + shfmt + Pyright + mypy
lint:
	@if [ -n "$(BAZEL)" ]; then \
	  echo "-> Bazel primary: bazelisk test //:lint --test_tag_filters=manual"; \
	  $(BAZEL) test //:lint --test_tag_filters=manual; \
	else \
	  shellcheck -x scripts/manage.sh scripts/lib/*.sh scripts/utilities/*.sh docker/*.sh docker/install-comfy/*.sh; \
	  shfmt -d -s -i 2 -ci scripts docker/install-comfy.sh docker/install-comfy docker/entrypoint.sh tests/coverage.sh tests/run_all.sh tests/typecheck.sh; \
	  bash tests/typecheck.sh; \
	fi

# @target fmt - apply shfmt -w (and buildifier when Bazel tools exist)
fmt: fix

# @target fix - trusted formatters
fix:
	@if [ -n "$(BAZEL)" ]; then \
	  echo "-> Bazel primary: bazelisk run //:fix"; \
	  $(BAZEL) run //:fix; \
	else \
	  shfmt -w -s -i 2 -ci scripts docker/install-comfy.sh docker/install-comfy docker/entrypoint.sh tests/coverage.sh tests/run_all.sh tests/typecheck.sh; \
	fi

# @target validate - git-aware core + docs slices
validate:
	@if [ -n "$(BAZEL)" ]; then \
	  $(BAZEL) run //:validate; \
	else \
	  echo "bazelisk required for validate target" >&2; \
	  exit 1; \
	fi

# @target docs - generate CLI + workflow references, then Fumadocs static export
docs:
	@if [ -n "$(BAZEL)" ]; then \
	  echo "-> Bazel primary: bazelisk run //docs:docs"; \
	  $(BAZEL) run //docs:docs; \
	else \
	  bash docs/manage-docs.sh build; \
	fi

# @target doctor - host preflight without starting the stack
doctor:
	@if [ -n "$(BAZEL)" ]; then \
	  $(BAZEL) run //:manage -- doctor; \
	else \
	  ./scripts/manage.sh doctor; \
	fi

# @target clean - remove local build/test artifacts (not models or git state)
clean:
	rm -rf site coverage .coverage htmlcov .pytest_cache .mypy_cache \
	  docs-site/.next docs-site/out docs-site/.source
	@if [ -n "$(BAZEL)" ]; then $(BAZEL) clean --expunge || true; fi
