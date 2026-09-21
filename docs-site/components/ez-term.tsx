"use client";

import { useCallback, useEffect, useId, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

import { loadGlossaryTerms } from "@/lib/remark-glossary";

interface EzTermProps {
  termId: string;
  category: string;
  short: string;
  children: ReactNode;
}

/**
 * First-occurrence glossary trigger. Hover shows the short definition; click opens
 * the definition dialog via ``showModal()`` so the panel is top-layer and viewport-centered
 * (native ``<dialog>`` via ``showModal()``).
 */
export function EzTerm({ termId, category, short, children }: EzTermProps) {
  const [open, setOpen] = useState(false);
  const titleId = useId();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const triggerRef = useRef<HTMLSpanElement>(null);
  const term = loadGlossaryTerms().find((row) => row.id === termId);
  const href = `/glossary/#${termId}`;

  const onKey = useCallback((event: KeyboardEvent<HTMLSpanElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      setOpen(true);
    }
  }, []);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }
    if (open) {
      if (!dialog.open && typeof dialog.showModal === "function") {
        dialog.showModal();
      }
      closeRef.current?.focus();
      return;
    }
    if (dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }
    const onClose = () => {
      setOpen(false);
      triggerRef.current?.focus();
    };
    dialog.addEventListener("close", onClose);
    return () => dialog.removeEventListener("close", onClose);
  }, []);

  return (
    <>
      <span
        ref={triggerRef}
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
      <dialog
        ref={dialogRef}
        className="ez-glossary-dialog"
        aria-labelledby={titleId}
        aria-modal="true"
        onClick={(event) => event.currentTarget === event.target && setOpen(false)}
      >
        <div className="ez-glossary-dialog__panel">
          <button ref={closeRef} type="button" className="ez-glossary-dialog__close" onClick={() => setOpen(false)}>
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
    </>
  );
}
