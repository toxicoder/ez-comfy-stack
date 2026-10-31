import Link from "next/link";
import { ChevronRight } from "lucide-react";

import type { NavTrail } from "@/lib/nav";

/**
 * Breadcrumb above the page title: tab, then each sidebar folder, then the page.
 *
 * fumadocs' own breadcrumb drops everything above a `root: true` folder, and a tab is one,
 * so a reader on a narrow screen (where the tab strip collapses into the sidebar) would see
 * only the folder and the page. This names the tab as well, and labels the last step with the
 * sidebar's own wording so the trail and the folder list agree. Folders stay plain text: a
 * trail link that jumped sideways through the sidebar would compete with the sidebar itself.
 */
export function DocsTrail({ trail, page, url }: { trail: NavTrail; page: string; url: string }) {
  const items: { name: string; url?: string }[] = [
    { name: trail.tab },
    ...trail.groups.map((name) => ({ name })),
    { name: page, url }
  ];
  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-sm text-fd-muted-foreground">
      {items.map((item, index) => (
        <span key={`${item.name}-${String(index)}`} className="flex items-center gap-1.5">
          {index > 0 ? <ChevronRight aria-hidden="true" className="size-3.5 shrink-0" /> : null}
          {item.url ? (
            <Link
              className="truncate text-fd-primary font-medium transition-opacity hover:opacity-80"
              href={item.url}
            >
              {item.name}
            </Link>
          ) : (
            <span className="truncate" title={item.name}>
              {item.name}
            </span>
          )}
        </span>
      ))}
    </nav>
  );
}
