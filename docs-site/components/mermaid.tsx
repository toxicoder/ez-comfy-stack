"use client";

import { useTheme } from "next-themes";
import { useEffect, useId, useRef, useState } from "react";

/** The two schemes the Voltage token block in `app/global.css` defines. */
export type MermaidScheme = "light" | "dark";

/** Mermaid's `initialize()` options, narrowed to what this site sets. */
export interface MermaidConfig {
  startOnLoad: boolean;
  securityLevel: "strict";
  theme: "base";
  fontFamily: string;
  fontSize: number;
  themeVariables: Record<string, string>;
  themeCSS: string;
  flowchart: Record<string, unknown>;
  sequence: Record<string, unknown>;
}

/** Same sans stack the docs chrome falls back to, so a diagram is not set in a third face. */
const FONT_STACK = "ui-sans-serif, system-ui, sans-serif";

/**
 * Node, line and label colours for each scheme.
 *
 * The values are the `--color-fd-*` tokens read by eye rather than read at runtime: Mermaid
 * bakes `themeVariables` into the SVG at render time, so a `var()` reference would be
 * resolved against the SVG's own context and lost. Keeping them beside the token block in
 * `app/global.css` is what makes the two easy to keep in step.
 */
const THEME_VARIABLES: Record<MermaidScheme, Record<string, string>> = {
  light: {
    darkMode: "false",
    background: "#f5f2ee",
    primaryColor: "#faf8f5",
    primaryBorderColor: "#c46e16",
    primaryTextColor: "#161311",
    secondaryColor: "#f7f2ec",
    secondaryBorderColor: "#1b8a84",
    secondaryTextColor: "#161311",
    tertiaryColor: "#faf8f5",
    tertiaryBorderColor: "#d4cfc6",
    tertiaryTextColor: "#6b6157",
    lineColor: "#6b6157",
    textColor: "#161311",
    titleColor: "#161311",
    edgeLabelBackground: "#f5f2ee",
    edgeLabelColor: "#161311",
    clusterBkg: "rgba(196, 110, 22, 0.06)",
    clusterBorder: "#d4cfc6",
    noteBkgColor: "#e7e2db",
    noteBorderColor: "#c46e16",
    noteTextColor: "#161311",
    actorBkg: "#faf8f5",
    actorBorder: "#c46e16",
    actorTextColor: "#161311",
    actorLineColor: "#d4cfc6",
    activationBkgColor: "rgba(27, 138, 132, 0.14)",
    activationBorderColor: "#1b8a84",
    signalColor: "#6b6157",
    labelBoxBkgColor: "#faf8f5",
    labelBoxBorderColor: "#d4cfc6",
    loopTextColor: "#161311",
    errorBkgColor: "#e85d28",
    errorTextColor: "#faf8f5"
  },
  dark: {
    darkMode: "true",
    background: "#131211",
    // Nodes sit a step above the page and the frame, or the border is the only thing
    // separating a box from its background.
    primaryColor: "#241f1a",
    primaryBorderColor: "#e89424",
    primaryTextColor: "#f2eee8",
    secondaryColor: "#221d18",
    secondaryBorderColor: "#3ec4bb",
    secondaryTextColor: "#f2eee8",
    tertiaryColor: "#1d1916",
    tertiaryBorderColor: "#3b3630",
    tertiaryTextColor: "#a89d90",
    lineColor: "#a89d90",
    textColor: "#f2eee8",
    titleColor: "#f2eee8",
    edgeLabelBackground: "#131211",
    edgeLabelColor: "#f2eee8",
    clusterBkg: "rgba(232, 148, 36, 0.08)",
    clusterBorder: "#3b3630",
    noteBkgColor: "#201e1b",
    noteBorderColor: "#e89424",
    noteTextColor: "#f2eee8",
    actorBkg: "#241f1a",
    actorBorder: "#e89424",
    actorTextColor: "#f2eee8",
    actorLineColor: "#3b3630",
    activationBkgColor: "rgba(62, 196, 187, 0.16)",
    activationBorderColor: "#3ec4bb",
    signalColor: "#a89d90",
    labelBoxBkgColor: "#241f1a",
    labelBoxBorderColor: "#3b3630",
    loopTextColor: "#f2eee8",
    errorBkgColor: "#ff7a3d",
    errorTextColor: "#131211"
  }
};

/**
 * Rounded nodes, a hairline that matches the rest of the article's rules, and no shadow.
 *
 * Mermaid draws square corners, a hard 1px line, and a light-grey `drop-shadow` on every
 * node. The shadow is invisible on a white page and reads as a white halo on the dark one,
 * and the docs' own boxes are 0.25rem-0.5rem rounded with `--color-fd-border`-weight edges,
 * which is what this aligns.
 */
const THEME_CSS = [
  // `!important` because Mermaid puts `themeCSS` above the diagram's own stylesheet, so a
  // plain rule loses to the `drop-shadow` its flowchart styles set on every node.
  ".node rect,.node polygon,.node path{stroke-width:1.2px;filter:none !important}",
  ".node rect{rx:6;ry:6}",
  ".edgePath .path,.edgeLabel .edgeLabel{stroke-width:1.2px}",
  ".edgeLabel{background-color:transparent}",
  ".label text,.nodeLabel,.edgeLabel,.label {font-size:13px}",
  ".cluster rect{rx:8;ry:8;stroke-width:1px}",
  "text .text-outer-tspan tspan{dominant-baseline:central}"
].join("");

/**
 * Mermaid options for one scheme.
 *
 * `theme: "base"` is the only Mermaid theme that accepts a full palette, which is how the
 * diagrams follow the Voltage tokens instead of Mermaid's default indigo set.
 *
 * @param scheme The resolved colour scheme of the page.
 * @returns Options to hand to `mermaid.initialize()`.
 */
export function mermaidConfig(scheme: MermaidScheme): MermaidConfig {
  return {
    startOnLoad: false,
    // Strict keeps Mermaid from injecting raw HTML from a diagram's labels into the page.
    securityLevel: "strict",
    theme: "base",
    fontFamily: FONT_STACK,
    fontSize: 13,
    themeVariables: THEME_VARIABLES[scheme],
    themeCSS: THEME_CSS,
    flowchart: {
      curve: "basis",
      htmlLabels: true,
      padding: 10,
      nodeSpacing: 32,
      rankSpacing: 46,
      useMaxWidth: true
    },
    sequence: {
      actorMargin: 44,
      boxMargin: 8,
      messageMargin: 32,
      noteMargin: 10,
      mirrorActors: false,
      useMaxWidth: true
    }
  };
}

/**
 * Turn a React `useId()` value into a Mermaid `render()` id.
 *
 * Mermaid 12 rejects two `render()` calls that share an id, and `useId()` emits colons
 * (`:r1:`) that are not legal in the SVG id Mermaid writes. Prefixing `mmd` keeps the
 * result a CSS identifier even when the React id is only punctuation.
 *
 * @param reactId Value from `useId()`.
 * @returns A distinct, CSS-safe id.
 */
export function mermaidRenderId(reactId: string): string {
  return `mmd${reactId.replace(/[^A-Za-z0-9_-]/g, "")}`;
}

/**
 * Renders a ```mermaid fence.
 *
 * `remarkMdxMermaid` (registered in `source.config.ts`) rewrites `mermaid` code fences into
 * `<Mermaid chart="..." />`, so this component only has to draw the diagram.  It re-renders
 * when the colour scheme flips so diagrams follow the Voltage theme instead of staying stuck
 * on Mermaid's default palette.
 */
export function Mermaid({ chart }: { chart: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const reactId = useId();
  const [error, setError] = useState<string>();
  // `useTheme` returns an object; `resolvedTheme` is the scheme after `system` is
  // evaluated, which is what the diagram palette has to follow.
  const { resolvedTheme } = useTheme();
  const scheme: MermaidScheme = resolvedTheme === "dark" ? "dark" : "light";

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    let cancelled = false;

    void (async () => {
      const [{ default: mermaid }] = await Promise.all([import("mermaid"), Promise.resolve()]);
      if (cancelled) return;
      mermaid.initialize(mermaidConfig(scheme));
      try {
        const { svg } = await mermaid.render(mermaidRenderId(reactId), chart);
        if (cancelled) return;
        node.innerHTML = svg;
        setError(undefined);
      } catch (cause) {
        if (!cancelled) setError(cause instanceof Error ? cause.message : String(cause));
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [chart, scheme, reactId]);

  if (error) {
    return (
      <div className="rounded-md border border-fd-error/40 bg-fd-error/5 p-3 text-0.875rem text-fd-error">
        <p className="font-semibold">Mermaid diagram failed to render</p>
        <pre className="mt-2 overflow-auto whitespace-pre-wrap">{error}</pre>
        <pre className="mt-2 overflow-auto text-0.75rem opacity-70">{chart}</pre>
      </div>
    );
  }

  return (
    <div
      ref={ref}
      className="ez-mermaid"
      data-ez-mermaid-scheme={scheme}
      role="img"
      aria-label="Mermaid diagram"
    />
  );
}
