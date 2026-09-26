"use client";

import { Check, Clipboard } from "lucide-react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode
} from "react";

import builderJson from "../../includes/command-builder.json";
import {
  commandById,
  defaultVarValues,
  FLAGS_PREFIX,
  flagValue,
  renderCommand,
  splitVarTemplate,
  substituteVars,
  templateHasVars,
  VARS_KEY,
  type BuilderCommand,
  type BuilderFlag,
  type CommandBuilder
} from "@/lib/command-vars";

const builder = builderJson as CommandBuilder;

interface CommandVarsContextValue {
  values: Record<string, string>;
  defaults: Record<string, string>;
  setValue: (id: string, value: string) => void;
  reset: () => void;
  builder: CommandBuilder;
}

const CommandVarsContext = createContext<CommandVarsContextValue | null>(null);

function loadStoredVars(defaults: Record<string, string>): Record<string, string> {
  const merged = { ...defaults };
  try {
    const raw = localStorage.getItem(VARS_KEY);
    if (!raw) return merged;
    const stored = JSON.parse(raw) as Record<string, unknown>;
    for (const id of Object.keys(merged)) {
      const value = stored[id];
      if (typeof value === "string" && value !== "") merged[id] = value;
    }
  } catch {
    return defaults;
  }
  return merged;
}

function loadFlags(cmdId: string): Record<string, unknown> {
  try {
    const raw = localStorage.getItem(FLAGS_PREFIX + cmdId);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function saveFlags(cmdId: string, flags: Record<string, unknown>): void {
  try {
    localStorage.setItem(FLAGS_PREFIX + cmdId, JSON.stringify(flags));
  } catch {
    /* private mode */
  }
}

/** Session-variable store plus the Your Spark panel. */
export function CommandVarsProvider({ children }: { children: ReactNode }) {
  const defaults = useMemo(() => defaultVarValues(builder), []);
  const [values, setValues] = useState<Record<string, string>>(defaults);

  useEffect(() => {
    setValues(loadStoredVars(defaults));
  }, [defaults]);

  const persist = useCallback((next: Record<string, string>) => {
    setValues(next);
    try {
      localStorage.setItem(VARS_KEY, JSON.stringify(next));
    } catch {
      /* private mode */
    }
  }, []);

  const setValue = useCallback(
    (id: string, value: string) => {
      persist({ ...values, [id]: value });
    },
    [persist, values]
  );

  const reset = useCallback(() => persist({ ...defaults }), [defaults, persist]);

  const ctx = useMemo(
    () => ({ values, defaults, setValue, reset, builder }),
    [values, defaults, setValue, reset]
  );

  return (
    <CommandVarsContext.Provider value={ctx}>
      <SparkPanel />
      <CodeVarBinder />
      {children}
    </CommandVarsContext.Provider>
  );
}

function useCommandVars(): CommandVarsContextValue {
  const ctx = useContext(CommandVarsContext);
  if (!ctx) throw new Error("CommandVarsProvider is missing");
  return ctx;
}

function SparkPanel() {
  const { values, setValue, reset, builder: data } = useCommandVars();
  const [open, setOpen] = useState(false);
  return (
    <details className="ez-spark-panel" open={open} onToggle={(event) => setOpen(event.currentTarget.open)}>
      <summary className="ez-spark-panel__summary">Your Spark</summary>
      <p className="ez-spark-panel__hint">
        Values stay in this browser only. Copy buttons and highlighted chips use them.
      </p>
      <div className="ez-spark-panel__grid">
        {data.variables.map((row) => (
          <label key={row.id} className="ez-spark-panel__field">
            <span className="ez-spark-panel__label">{row.label}</span>
            <input
              name={row.id}
              value={values[row.id] ?? row.default}
              onChange={(event) => setValue(row.id, event.target.value)}
              spellCheck={false}
              autoComplete="off"
            />
          </label>
        ))}
      </div>
      <div className="ez-spark-panel__actions">
        <button type="button" className="ez-spark-panel__reset" onClick={reset}>
          Reset to defaults
        </button>
      </div>
    </details>
  );
}

function CodeVarBinder() {
  const { values } = useCommandVars();
  useEffect(() => {
    const root = document.querySelector("article") ?? document;
    const nodes = root.querySelectorAll("code");
    for (const code of nodes) {
      if (code.closest(".ez-cmd-builder, .ez-spark-panel, .ez-glossary-dialog, .mermaid")) continue;
      let template = code.getAttribute("data-ez-src");
      if (!template) {
        template = code.textContent ?? "";
        if (!templateHasVars(template, values)) continue;
        code.setAttribute("data-ez-src", template);
      }
      const parts = splitVarTemplate(template, values);
      const frag = document.createDocumentFragment();
      for (const part of parts) {
        if (part.id) {
          const span = document.createElement("span");
          span.className = "ez-var";
          span.dataset.ezVar = part.id;
          span.contentEditable = "true";
          span.spellcheck = false;
          span.setAttribute("role", "textbox");
          span.setAttribute("aria-label", `${part.id}, session variable, click to edit`);
          span.title = `${part.id} - session variable, click to edit`;
          span.textContent = part.text;
          frag.appendChild(span);
        } else if (part.text) {
          frag.appendChild(document.createTextNode(part.text));
        }
      }
      code.replaceChildren(frag);
    }
  }, [values]);

  useEffect(() => {
    const onInput = (event: Event) => {
      const chip = (event.target as HTMLElement | null)?.closest?.("span.ez-var[data-ez-var]");
      if (!chip) return;
      const name = chip.getAttribute("data-ez-var");
      if (!name) return;
      const text = (chip.textContent ?? "").replace(/\n/g, "");
      if (chip.textContent !== text) chip.textContent = text;
      const next = { ...values, [name]: text };
      try {
        localStorage.setItem(VARS_KEY, JSON.stringify(next));
      } catch {
        /* private mode */
      }
    };
    document.addEventListener("input", onInput);
    return () => document.removeEventListener("input", onInput);
  }, [values]);

  return null;
}

function FlagControl({
  flag,
  flags,
  values,
  onChange
}: {
  flag: BuilderFlag;
  flags: Record<string, unknown>;
  values: Record<string, string>;
  onChange: (name: string, value: unknown) => void;
}) {
  const current = flagValue(flag, flags, values);
  if (flag.kind === "bool") {
    return (
      <label className="ez-cmd-builder__flag">
        <input
          type="checkbox"
          checked={current === true}
          onChange={(event) => onChange(flag.name, event.target.checked)}
        />
        {flag.label ?? flag.name}
      </label>
    );
  }
  const choices = flag.choices ?? [];
  return (
    <label className="ez-cmd-builder__flag">
      <span>{flag.label ?? flag.name}</span>
      <select value={String(current ?? "")} onChange={(event) => onChange(flag.name, event.target.value)}>
        {!flag.required && <option value="">(omit)</option>}
        {choices.map((choice) => (
          <option key={choice.value} value={choice.value}>
            {choice.label}
          </option>
        ))}
      </select>
    </label>
  );
}

/** Interactive recipe widget for a command-builder id. */
export function EzCommand({ id }: { id: string }) {
  const { values, builder: data } = useCommandVars();
  const recipe = commandById(data, id);
  const [flags, setFlags] = useState<Record<string, unknown>>({});

  useEffect(() => {
    setFlags(loadFlags(id));
  }, [id]);

  const setFlag = (name: string, value: unknown) => {
    const next = { ...flags, [name]: value };
    setFlags(next);
    saveFlags(id, next);
  };

  if (!recipe) {
    return <p className="ez-cmd-builder">Unknown command id: {id}</p>;
  }

  const line = renderCommand(recipe, flags, values);
  return (
    <div className="ez-cmd-builder" data-ez-cmd={id}>
      <p className="ez-cmd-builder__title">{recipe.title}</p>
      {recipe.description ? <p className="ez-cmd-builder__desc">{recipe.description}</p> : null}
      {(recipe.flags ?? []).length > 0 ? (
        <div className="ez-cmd-builder__controls">
          {(recipe.flags ?? []).map((flag) => (
            <FlagControl key={flag.name} flag={flag} flags={flags} values={values} onChange={setFlag} />
          ))}
        </div>
      ) : null}
      <div className="ez-cmd-builder__code not-prose">
        <pre>
          <code>{line}</code>
          <CopyCommandButton line={line} />
        </pre>
      </div>
    </div>
  );
}

/** Clipboard icon overlay for one rendered command line. */
function CopyCommandButton({ line }: { line: string }) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return undefined;
    const timer = window.setTimeout(() => setCopied(false), 1500);
    return () => window.clearTimeout(timer);
  }, [copied]);

  const label = copied ? "Copied" : "Copy command";
  return (
    <button
      type="button"
      className="ez-cmd-builder__copy"
      title={label}
      aria-label={label}
      onClick={() => {
        void navigator.clipboard.writeText(line).then(() => {
          setCopied(true);
        });
      }}
    >
      {copied ? <Check aria-hidden /> : <Clipboard aria-hidden />}
    </button>
  );
}

/** Used by MDX after the ezcmd fence is rewritten. */
export function EzCmd(props: { id: string }): ReactNode {
  return <EzCommand id={props.id} />;
}
