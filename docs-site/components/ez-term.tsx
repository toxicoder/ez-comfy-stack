"use client";

import { useCallback, useEffect, useId, useState, type KeyboardEvent, type ReactNode } from "react";

import { loadGlossaryTerms } from "@/lib/remark-glossary";

interface EzTermProps {
  termId: string;
  category: string;
  short: string;
  children: ReactNode;
}

/**
 * First-occurrence glossary trigger. Hover shows the short definition; click opens
 * the definition dialog (same contract as `docs/javascripts/glossary.js`).
 */
export function EzTerm({ termId, category, short, children }: EzTermProps) {
  const [open, setOpen] = useState(false);
  const titleId = useId();
  const term = loadGlossaryTerms().find((row) => row.id === termId);
  const href = `/glossary/#${termId}`;

  const onKey = useCallback((event: KeyboardEvent<HTMLSpanElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      setOpen(true);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    const onEsc = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onEsc);
    return () => document.removeEventListener("keydown", onEsc);
  }, [open]);

  return (
    <>
      <span
        className="ez-term"
        tabIndex={0}
        role="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        data-term={termId}
        data-href={href}
        data-short={short}
        data-category={category}
        title={short}
        onClick={() => setOpen(true)}
        onKeyDown={onKey}
      >
        {children}
      </span>
      {open ? (
        <dialog className="ez-glossary-dialog" open onClick={(event) => event.currentTarget === event.target && setOpen(false)}>
          <div className="ez-glossary-dialog__panel">
            <button type="button" className="ez-glossary-dialog__close" onClick={() => setOpen(false)}>
              Close
            </button>
            <h2 className="ez-glossary-dialog__title" id={titleId}>
              {term?.title ?? termId}
            </h2>
            <p className="ez-glossary-dialog__category">{category}</p>
            <p className="ez-glossary-dialog__body">{short}</p>
            <p className="ez-glossary-dialog__more">
              <a href={href}>Open full glossary entry</a>
            </p>
          </div>
        </dialog>
      ) : null}
    </>
  );
}
