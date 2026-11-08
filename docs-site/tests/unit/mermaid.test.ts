/**
 * Tests for Mermaid SVG render ids.
 *
 * Mermaid 12 rejects two `render()` calls that share an id, and React `useId()` values
 * contain colons (`:r1:`) that are not legal in the SVG id Mermaid emits.  The helper has
 * to turn those into distinct, CSS-safe ids so every diagram on a page (architecture has
 * five) actually draws on GitHub Pages.
 */

import { describe, expect, it } from "vitest";

import { mermaidConfig, mermaidRenderId } from "../../components/mermaid";

const CSS_ID = /^[A-Za-z][A-Za-z0-9_-]*$/u;

describe("mermaidRenderId", () => {
  it("sanitizes a React useId value into a CSS-safe id", () => {
    expect(mermaidRenderId(":r1:")).toBe("mmdr1");
    expect(mermaidRenderId(":r1:")).toMatch(CSS_ID);
  });

  it("keeps two React ids distinct after sanitizing", () => {
    expect(mermaidRenderId(":r1:")).not.toBe(mermaidRenderId(":r2:"));
  });

  it("always starts with a letter even when the React id is only punctuation", () => {
    expect(mermaidRenderId(":::")).toMatch(CSS_ID);
  });
});

/**
 * Pull the red, green and blue out of the two colour forms `themeVariables` accepts.
 *
 * The docs theme gate rejects the Material blue that Mermaid ships with, so the palette
 * here has to clear the same test without a browser: `#rrggbb` and `rgb()/rgba()`.
 */
function channels(value: string): [number, number, number] | null {
  const hex = value.match(/^#([0-9a-f]{6})$/iu);
  if (hex?.[1]) {
    const n = Number.parseInt(hex[1], 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  const rgb = value.match(/rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)/u);
  if (rgb) return [Number(rgb[1]), Number(rgb[2]), Number(rgb[3])];
  return null;
}

function isIndigo(value: string): boolean {
  const [r, g, b] = channels(value) ?? [];
  if (r === undefined || g === undefined || b === undefined) return false;
  return b > 120 && b > r + 25 && b > g + 25;
}

describe("mermaidConfig", () => {
  it("uses Mermaid's palette-receiving theme and never auto-runs", () => {
    const config = mermaidConfig("light");
    expect(config.theme).toBe("base");
    expect(config.startOnLoad).toBe(false);
  });

  it("keeps strict sanitisation, since a diagram body is markdown a contributor wrote", () => {
    expect(mermaidConfig("dark").securityLevel).toBe("strict");
  });

  it("paints both schemes in the Voltage palette with no Material blue left in it", () => {
    for (const scheme of ["light", "dark"] as const) {
      const variables = mermaidConfig(scheme).themeVariables;
      const offenders = Object.entries(variables).filter(([, value]) => isIndigo(value));
      expect(offenders, `${scheme} palette carries a blue: ${JSON.stringify(offenders)}`).toEqual(
        []
      );
    }
  });

  it("gives every colour a value the renderer can parse", () => {
    // `darkMode` is a Mermaid flag that lives in the same bag as the colours.
    const flags = new Set(["darkMode"]);
    for (const scheme of ["light", "dark"] as const) {
      for (const [key, value] of Object.entries(mermaidConfig(scheme).themeVariables)) {
        if (flags.has(key)) continue;
        expect(channels(value), `${scheme}.${key} is not a colour: ${value}`).not.toBeNull();
      }
    }
  });

  it("actually differs between schemes, so a dark page is not drawing light nodes", () => {
    const light = mermaidConfig("light").themeVariables;
    const dark = mermaidConfig("dark").themeVariables;
    expect(dark.primaryColor).not.toBe(light.primaryColor);
    expect(dark.primaryBorderColor).not.toBe(light.primaryBorderColor);
    expect(dark.lineColor).not.toBe(light.lineColor);
  });

  it("sets the site's sans face rather than Mermaid's default", () => {
    expect(mermaidConfig("light").fontFamily).toContain("system-ui");
  });

  it("keeps themeCSS markup-free, because Mermaid injects it into the page unescaped", () => {
    const css = mermaidConfig("light").themeCSS;
    expect(css.length).toBeGreaterThan(0);
    expect(css).not.toMatch(/[<>]/u);
  });
});
