"use client";

import { List } from "lucide-react";
import { useItems } from "fumadocs-ui/components/toc";
import { useEffect, useMemo, useRef, isValidElement, type ReactNode } from "react";

/** The part of a Fumadocs TOC item this bar reads, kept structural so it is testable. */
export interface TocBarSourceItem {
  id: string;
  title: string;
  depth: number;
  active: boolean;
}

/** One chip in the bar. */
export interface TocBarChip {
  id: string;
  title: string;
  /** 2 or 3: headings below the third level fold into the third level's styling. */
  depth: number;
}

/**
 * Flatten a TOC title to the text a chip can show.
 *
 * Fumadocs types a heading title as a `ReactNode` because an authored heading may carry
 * inline markup. The row is a plain link, so it needs the string the reader sees, the same
 * flattening the heading's own bug-report control does.
 *
 * @param node A TOC item title.
 * @returns The concatenated text, empty for anything that is not text.
 */
export function tocBarTitle(node: unknown): string {
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map((child) => tocBarTitle(child)).join("");
  if (isValidElement<{ children?: ReactNode }>(node)) return tocBarTitle(node.props.children);
  return "";
}

/**
 * Fold raw TOC items into the chips the bar renders.
 *
 * The bar is one horizontal row, so every heading stays in it and the row scrolls sideways
 * instead of growing taller. Blank titles would render an unlabelled link, and a duplicated
 * anchor (two headings with the same generated id) would give two chips that both claim to
 * be the reader's position, so both are dropped here rather than in the component.
 *
 * @param items TOC items in document order.
 * @returns Chips in document order, with depth clamped to 2 or 3.
 */
export function tocBarChips(items: readonly TocBarSourceItem[]): TocBarChip[] {
  const seen = new Set<string>();
  const chips: TocBarChip[] = [];
  for (const item of items) {
    const title = item.title.replace(/\s+/gu, " ").trim();
    if (!item.id || !title || seen.has(item.id)) continue;
    seen.add(item.id);
    chips.push({ id: item.id, title, depth: item.depth <= 2 ? 2 : 3 });
  }
  return chips;
}

/**
 * Id of the chip that says where the reader is.
 *
 * Fumadocs marks every heading currently intersecting the viewport, which is two during a
 * scroll between nested headings. The deepest/latest one is the section being read, so the
 * bar lights exactly one chip.
 *
 * @param items TOC items in document order.
 * @returns The active heading id, or `undefined` when the reader is above the first heading.
 */
export function tocBarActiveId(items: readonly TocBarSourceItem[]): string | undefined {
  for (let index = items.length - 1; index >= 0; index -= 1) {
    const item = items[index];
    if (item?.active && item.id) return item.id;
  }
  return undefined;
}

/**
 * Horizontal sub navigation: the page's own headings as a clickable row.
 *
 * It replaces Fumadocs' narrow-screen TOC popover, which showed a progress ring and the
 * page title and hid the headings behind a click, so the reader could not see where they
 * were without opening it. This row is present at every width: the heading being read is
 * filled, the rest are reachable in one click, and the row stays a single line tall.
 *
 * The right-hand `On this page` column is untouched; this is the top-of-page companion to
 * it, not a replacement. Renders nothing on a page with no headings, so it costs no space
 * there.
 */
export function DocsTocBar() {
  const items = useItems();
  // Fumadocs keeps the reader-facing fields on `original` and the scroll state beside it.
  const sources = useMemo<TocBarSourceItem[]>(
    () =>
      items.map((item) => ({
        id: item.id,
        title: tocBarTitle(item.original?.title),
        depth: item.original?.depth ?? 2,
        active: item.active
      })),
    [items]
  );
  const chips = useMemo(() => tocBarChips(sources), [sources]);
  const activeId = tocBarActiveId(sources);
  const listRef = useRef<HTMLOListElement>(null);

  const activeIndex = activeId ? chips.findIndex((chip) => chip.id === activeId) : -1;

  // A long page pushes the active chip out of the visible slice of the row; bring it back
  // without touching the vertical scroll, which `scrollIntoView` would move.
  useEffect(() => {
    const list = listRef.current;
    if (!list || !activeId) return;
    const chip = list.querySelector<HTMLElement>(`[data-ez-tocbar-anchor="${CSS.escape(activeId)}"]`);
    if (!chip) return;
    const pad = 16;
    const listBox = list.getBoundingClientRect();
    const chipBox = chip.getBoundingClientRect();
    if (chipBox.left < listBox.left + pad) {
      list.scrollLeft -= listBox.left + pad - chipBox.left;
    } else if (chipBox.right > listBox.right - pad) {
      list.scrollLeft += chipBox.right - listBox.right + pad;
    }
  }, [activeId]);

  if (chips.length === 0) return null;

  return (
    <nav aria-label="On this page" className="ez-tocbar not-prose" data-ez-tocbar="">
      <span className="ez-tocbar__label">
        <List aria-hidden="true" />
        On this page
      </span>
      <ol ref={listRef} className="ez-tocbar__list">
        {chips.map((chip) => (
          <li key={chip.id} className="ez-tocbar__item" data-depth={chip.depth}>
            <a
              className="ez-tocbar__link"
              data-ez-tocbar-anchor={chip.id}
              href={`#${chip.id}`}
              aria-current={chip.id === activeId ? "location" : undefined}
            >
              {chip.title}
            </a>
          </li>
        ))}
      </ol>
      {activeIndex >= 0 ? (
        <span className="ez-tocbar__count" aria-hidden="true">
          {activeIndex + 1}/{chips.length}
        </span>
      ) : null}
    </nav>
  );
}
