import { loadGlossaryTerms } from "@/lib/remark-glossary";

const CATEGORY_ORDER = [
  "Models",
  "Modalities",
  "Studio",
  "Downloads",
  "Hardware and safety",
  "Film",
  "Audio",
  "Licenses"
];

/**
 * Renders `includes/glossary.json` in place of `<!-- ez-glossary:render -->`.
 */
export function GlossaryBody() {
  const terms = loadGlossaryTerms();
  const grouped = new Map<string, typeof terms>();
  for (const term of terms) {
    const list = grouped.get(term.category) ?? [];
    list.push(term);
    grouped.set(term.category, list);
  }
  const categories = [...grouped.keys()].sort((a, b) => {
    const ia = CATEGORY_ORDER.indexOf(a);
    const ib = CATEGORY_ORDER.indexOf(b);
    const ka = ia === -1 ? CATEGORY_ORDER.length : ia;
    const kb = ib === -1 ? CATEGORY_ORDER.length : ib;
    return ka - kb || a.localeCompare(b);
  });

  return (
    <>
      {categories.map((category) => (
        <section key={category}>
          <h2 id={category.toLowerCase().replace(/\s+/g, "-")}>{category}</h2>
          {(grouped.get(category) ?? []).map((term) => (
            <article key={term.id}>
              <h3 id={term.id}>{term.title}</h3>
              <p>{term.short}</p>
            </article>
          ))}
        </section>
      ))}
    </>
  );
}
