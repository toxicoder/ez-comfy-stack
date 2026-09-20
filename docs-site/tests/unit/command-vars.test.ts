import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import {
  defaultVarValues,
  renderCommand,
  splitVarTemplate,
  substituteVars,
  templateHasVars,
  VARS_KEY,
  type CommandBuilder
} from "../../lib/command-vars";

const builder = JSON.parse(
  readFileSync(resolve(__dirname, "../../../includes/command-builder.json"), "utf8")
) as CommandBuilder;

describe("command-vars", () => {
  it("keeps the session storage key", () => {
    expect(VARS_KEY).toBe("ez-comfy.cmdvars");
  });

  it("substitutes known ${VAR} tokens without recursion", () => {
    const values = { SPARK_HOST: "10.0.0.1", MODELS_DIR: "/mnt/models" };
    expect(substituteVars("ssh ${SPARK_HOST} ${MISSING}", values)).toBe("ssh 10.0.0.1 ${MISSING}");
    expect(substituteVars("x ${SPARK_HOST:-127.0.0.1}", values)).toBe("x 10.0.0.1");
  });

  it("splits templates into chips", () => {
    const parts = splitVarTemplate("a ${SPARK_HOST} b", { SPARK_HOST: "h" });
    expect(parts).toEqual([
      { text: "a ", id: null },
      { text: "h", id: "SPARK_HOST" },
      { text: " b", id: null }
    ]);
  });

  it("detects session vars", () => {
    expect(templateHasVars("export MODELS_DIR=${MODELS_DIR}", defaultVarValues(builder))).toBe(true);
    expect(templateHasVars("echo hi", defaultVarValues(builder))).toBe(false);
  });

  it("renders download-models with the bound limit flag", () => {
    const recipe = builder.commands.find((row) => row.id === "download-models");
    expect(recipe).toBeDefined();
    const line = renderCommand(recipe!, {}, defaultVarValues(builder));
    expect(line).toContain("./scripts/manage.sh");
    expect(line).toContain("download-models");
    expect(line).toContain("--limit");
    expect(line).toContain("auto");
  });
});
