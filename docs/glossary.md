---
title: Glossary
description: Terms used in the US-safe ComfyUI studio — click a dotted word anywhere in the docs for a short definition.
tags: [glossary, comfyui, klein, wan, ltx, learning]
---

# Glossary

**What's on this page**

- How dotted terms and the definition dialog work
- Every studio, model, and operator term in one place
- Links from each entry to the guide that teaches it

**What this enables**

- Looking up Klein, Wan, LTX, Queue, latent, headroom, and the rest without leaving the page
- Teaching vocabulary once so Create and Operate pages can stay task-focused

!!! tip "Dotted words open a definition"

    Across the docs, the **first** time a glossary term appears on a page it is underlined with dots.

    - **Hover** (or keyboard focus) to read the short definition
    - **Click** or press ++enter++ / ++space++ to open the dialog
    - **Open full glossary entry** jumps here
    - ++esc++ or the backdrop closes the dialog

    Terms inside code, headings, and links stay plain so copy-paste and navigation do not fight the modal.

```mermaid
flowchart LR
  Prose["Docs prose"] --> First["First match on the page"]
  First --> Hover["Hover: short definition"]
  First --> Click["Click: dialog"]
  Click --> Full["This page: long entry"]
```

Add or change a term in `includes/glossary.json` (unique `id` and aliases). Conventions: [Project conventions](project-conventions.md).

<!-- ez-glossary:render -->
