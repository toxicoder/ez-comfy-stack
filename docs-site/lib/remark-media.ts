/**
 * Rewrite cinema asset URLs onto `/assets/cinema/…` (plus the published basePath).
 *
 * Generated pages use file-relative `../assets/cinema/` and `../../../assets/cinema/`
 * paths. The build copies `docs/assets` to `docs-site/public/assets`, so the browser
 * URL is `/assets/cinema/…` (or `/ez-comfy-stack/<alias>/assets/cinema/…`).
 */

import { visit } from "unist-util-visit";

import { basePath } from "./site";

const ASSET_RE = /(?:\.\.\/)+assets\/cinema\/([^"' )\s]+)/g;

function rewrite(url: string): string {
  const match = /(?:\.\.\/)+assets\/cinema\/(.+)$/.exec(url);
  if (!match?.[1]) return url;
  const prefix = basePath();
  return `${prefix}/assets/cinema/${match[1]}`.replace(/\/{2,}/g, "/");
}

/**
 * Rewrite image, HTML, and JSX src attributes that point at docs/assets/cinema.
 *
 * @returns A remark transformer.
 */
export function remarkCinemaAssets() {
  return (tree: Parameters<typeof visit>[0]) => {
    visit(tree, (node) => {
      const n = node as {
        type?: string;
        url?: string;
        value?: string;
        attributes?: { type?: string; name?: string; value?: unknown }[];
      };
      if (typeof n.url === "string" && n.url.includes("assets/cinema/")) {
        n.url = rewrite(n.url);
      }
      if (typeof n.value === "string" && n.value.includes("assets/cinema/")) {
        n.value = n.value.replace(ASSET_RE, (_all, rest: string) => {
          const prefix = basePath();
          return `${prefix}/assets/cinema/${rest}`.replace(/\/{2,}/g, "/");
        });
      }
      if (Array.isArray(n.attributes)) {
        for (const attr of n.attributes) {
          if ((attr.name === "src" || attr.name === "poster" || attr.name === "href") && typeof attr.value === "string") {
            if (attr.value.includes("assets/cinema/")) attr.value = rewrite(attr.value);
          }
        }
      }
    });
  };
}
