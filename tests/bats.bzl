"""Helpers to declare one hermetic BATS sh_test per suite file."""

load("@rules_shell//shell:sh_test.bzl", "sh_test")

_MEDIUM = {
    "bats/manage.bats": True,
    "bats/workflow.bats": True,
    "bats/safety.bats": True,
    "bats/lib_unit.bats": True,
}

# Extra runfiles only for suites that still need them after REPO_ROOT
# resolves to the checkout via manage.sh. Most suites read the tree via
# no-sandbox + readlink and do not need fat globs on every target.
_EXTRA_DATA = {
    "bats/workflow.bats": ["//workflows:lab_graphs"],
    "bats/safety.bats": [
        "//docker:sources",
        "//:ci_workflows",
        "//config:policy",
    ],
    "bats/comfy_scripts.bats": ["//docker:sources"],
    "bats/tooling.bats": [
        "//:ci_workflows",
        "//scripts:validate",
        "//scripts:ci_install_lint_tools",
        "//scripts:ci_publish_pages_tree",
    ],
    "bats/publish_pages_tree.bats": [
        "//scripts:ci_publish_pages_tree",
    ],
    "bats/devcontainer.bats": ["//:devcontainer"],
}

def bats_file_tests(srcs, common_data):
    """Declare `bats_<stem>_test` sh_test targets and a `bats` test_suite.

    Args:
        srcs: labels/paths of `bats/*.bats` files (typically from glob).
        common_data: shared runfiles (helper, scripts, bats-core).
    """
    tests = []
    for src in srcs:
        base = src.split("/")[-1]
        stem = base.replace(".bats", "").replace("-", "_")
        name = "bats_" + stem + "_test"
        size = "medium" if src in _MEDIUM else "small"
        extra = _EXTRA_DATA.get(src, [])
        sh_test(
            name = name,
            size = size,
            timeout = "moderate" if src in _MEDIUM else "short",
            srcs = ["bats_runner.sh"],
            args = [base],
            data = common_data + extra + [src],
            tags = [
                "local",
                "no-sandbox",
            ],
            visibility = ["//visibility:public"],
        )
        tests.append(":" + name)
    native.test_suite(
        name = "bats",
        tests = tests,
        visibility = ["//visibility:public"],
    )
