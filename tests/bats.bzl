"""Helpers to declare one hermetic BATS sh_test per suite file."""

load("@rules_shell//shell:sh_test.bzl", "sh_test")

_MEDIUM = {
    "bats/manage.bats": True,
    "bats/workflow.bats": True,
    "bats/safety.bats": True,
    "bats/lib_unit.bats": True,
}

def bats_file_tests(srcs, common_data):
    """Declare `bats_<stem>_test` sh_test targets and a `bats` test_suite.

    Args:
        srcs: labels/paths of `bats/*.bats` files (typically from glob).
        common_data: shared runfiles (helper, scripts, docker, config, bats-core).
    """
    tests = []
    for src in srcs:
        base = src.split("/")[-1]
        stem = base.replace(".bats", "").replace("-", "_")
        name = "bats_" + stem + "_test"
        size = "medium" if src in _MEDIUM else "small"
        sh_test(
            name = name,
            size = size,
            timeout = "short",
            srcs = ["bats_runner.sh"],
            args = [base],
            data = common_data + [src],
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
