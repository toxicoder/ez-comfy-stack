/**
 * Stamp `__DOCS_GIT_REF__` and this-repo GitHub blob/tree URLs to the active docs ref.
 *
 * Ports `docs/hooks.py` `stamp_git_ref` / `stamp_docs_git_ref_placeholder` so operator
 * clone commands and source links match the published alias (`main` vs `development`).
 */

import { visit } from "unist-util-visit";

import { gitRef, REPO } from "./site";

const PLACEHOLDER = "__DOCS_GIT_REF__";

function githubRefRe(): RegExp {
  return new RegExp(
    `(https://github\\.com/${REPO.user}/${REPO.repo}/(?:blob|tree)/)(main|master|development)(/)`,
    "g"
  );
}

function stamp(text: string, ref: string): string {
  return text.replaceAll(PLACEHOLDER, ref).replace(githubRefRe(), `$1${ref}$3`);
}

/**
 * Walk text, code, and inline-code nodes and stamp the active git ref.
 *
 * @returns A remark transformer.
 */
export function remarkGitRef() {
  const ref = gitRef();
  return (tree: Parameters<typeof visit>[0]) => {
    visit(tree, (node) => {
      const n = node as { type?: string; value?: string; url?: string };
      if (typeof n.value === "string" && (n.value.includes(PLACEHOLDER) || n.value.includes("github.com"))) {
        n.value = stamp(n.value, ref);
      }
      if (typeof n.url === "string" && (n.url.includes(PLACEHOLDER) || n.url.includes("github.com"))) {
        n.url = stamp(n.url, ref);
      }
    });
  };
}
