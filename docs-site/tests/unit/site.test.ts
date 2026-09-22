/**
 * Tests for the published-site base path.
 *
 * GitHub project Pages serves the repo at `/<repo>/`, so an alias build that bakes
 * `basePath=/latest` asks the browser for `https://<user>.github.io/latest/_next/...` and
 * every stylesheet 404s.  The helper must prefix the repo name; local `next dev` and the
 * unprefixed export used by render-check keep an empty path.
 */

import { afterEach, describe, expect, it } from "vitest";

import { basePath, docsAlias, REPO, searchIndexPath } from "../../lib/site";

const ENV_KEYS = ["NEXT_BASE_PATH", "DOCS_ALIAS", "EZ_DOCS_VERSION", "MIKE_DOCS_VERSION", "DGX_DOCS_VERSION"] as const;

const originalEnv: Record<string, string | undefined> = {};

afterEach(() => {
  for (const key of ENV_KEYS) {
    if (originalEnv[key] === undefined) {
      delete process.env[key];
    } else {
      process.env[key] = originalEnv[key];
    }
  }
});

for (const key of ENV_KEYS) {
  originalEnv[key] = process.env[key];
  delete process.env[key];
}

describe("basePath", () => {
  it("is empty for local dev and the unprefixed export", () => {
    expect(basePath()).toBe("");
  });

  it("prefixes the GitHub Pages repo path for the latest alias", () => {
    process.env.DOCS_ALIAS = "latest";
    expect(basePath()).toBe(`/${REPO.repo}/latest`);
  });

  it("prefixes the GitHub Pages repo path for the development alias", () => {
    process.env.DOCS_ALIAS = "development";
    expect(basePath()).toBe(`/${REPO.repo}/development`);
  });

  it("lets NEXT_BASE_PATH override the alias", () => {
    process.env.DOCS_ALIAS = "latest";
    process.env.NEXT_BASE_PATH = "/custom";
    expect(basePath()).toBe("/custom");
  });

  it("treats NEXT_BASE_PATH=/ as no prefix", () => {
    process.env.NEXT_BASE_PATH = "/";
    process.env.DOCS_ALIAS = "latest";
    expect(basePath()).toBe("");
  });
});

describe("docsAlias", () => {
  it("is local when no publish env is set", () => {
    delete process.env.EZ_DOCS_VERSION;
    delete process.env.MIKE_DOCS_VERSION;
    delete process.env.DGX_DOCS_VERSION;
    delete process.env.DOCS_ALIAS;
    expect(docsAlias()).toBe("local");
  });

  it("follows EZ_DOCS_VERSION for the development banner build", () => {
    process.env.EZ_DOCS_VERSION = "development";
    expect(docsAlias()).toBe("development");
  });

  it("follows DOCS_ALIAS=latest when the version env is empty", () => {
    delete process.env.EZ_DOCS_VERSION;
    delete process.env.MIKE_DOCS_VERSION;
    delete process.env.DGX_DOCS_VERSION;
    process.env.DOCS_ALIAS = "latest";
    expect(docsAlias()).toBe("latest");
  });
});

describe("searchIndexPath", () => {
  it("stays at the host root for a local preview", () => {
    delete process.env.DOCS_ALIAS;
    delete process.env.NEXT_BASE_PATH;
    expect(searchIndexPath("")).toBe("/api/search");
    expect(searchIndexPath()).toBe("/api/search");
  });

  it("prefixes the GitHub Pages alias so the static index is not a root 404", () => {
    expect(searchIndexPath(`/${REPO.repo}/development`)).toBe(
      `/${REPO.repo}/development/api/search`
    );
    expect(searchIndexPath(`/${REPO.repo}/latest/`)).toBe(`/${REPO.repo}/latest/api/search`);
  });
});
