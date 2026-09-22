/**
 * Component map handed to every compiled MDX page.
 */

import { createElement } from "react";
import Link from "fumadocs-core/link";
import defaultMdxComponents from "fumadocs-ui/mdx";
import { Banner } from "fumadocs-ui/components/banner";
import { Callout } from "fumadocs-ui/components/callout";
import { Tab, Tabs } from "fumadocs-ui/components/tabs";
import type { Page } from "fumadocs-core/source";

import { EzCommand, EzCmd } from "@/components/command-vars";
import { DocsH1, DocsH2, DocsH3, DocsH4, DocsH5, DocsH6 } from "@/components/docs-heading";
import { EzTerm } from "@/components/ez-term";
import { GlossaryBody } from "@/components/glossary-body";
import { Mermaid } from "@/components/mermaid";
import { PageBrief } from "@/components/page-brief";
import { resolveDocHref } from "@/lib/source";

/**
 * Build the component map for one page.
 *
 * @param page Page being rendered; links in its content resolve relative to it.
 * @returns The `components` object for the compiled MDX component.
 */
export function mdxComponentsFor(page: Page) {
  function ContentLink(props: { href?: string } & Record<string, unknown>) {
    const { href, ...rest } = props;
    const resolved = resolveDocHref(href, page);
    if (resolved.external) {
      return createElement("a", { href: resolved.href, rel: "noreferrer noopener", target: "_blank", ...rest });
    }
    return createElement(Link, { href: resolved.href, ...rest });
  }

  return {
    ...defaultMdxComponents,
    h1: DocsH1,
    h2: DocsH2,
    h3: DocsH3,
    h4: DocsH4,
    h5: DocsH5,
    h6: DocsH6,
    a: ContentLink,
    Banner,
    Callout,
    Tab,
    Tabs,
    Mermaid,
    EzCommand,
    EzCmd,
    EzTerm,
    GlossaryBody,
    PageBrief
  };
}
