/**
 * Command-builder substitution spec.
 *
 * Keep in sync with `docs/commands.py` (`split_var_template`, `substitute_vars`,
 * `render_command`). Vitest asserts the TypeScript port against the same fixtures.
 */

export const VAR_TOKEN = /\$\{([A-Z][A-Z0-9_]*)(?::-([^}]*))?\}/g;

export const SESSION_VAR_IDS = [
  "SPARK_HOST",
  "SPARK_USER",
  "MODELS_DIR",
  "COMFY_OUTPUT_DIR",
  "COMFY_PORT",
  "DOWNLOAD_LIMIT"
] as const;

export const VARS_KEY = "ez-comfy.cmdvars";
export const FLAGS_PREFIX = "ez-comfy.cmdflags.";

export interface BuilderVariable {
  id: string;
  label: string;
  default: string;
}

export interface BuilderFlagChoice {
  value: string;
  label: string;
}

export interface BuilderFlag {
  name: string;
  kind: "bool" | "choice" | "choice-or-int";
  required?: boolean;
  default?: unknown;
  bind_var?: string;
  label?: string;
  int_label?: string;
  choices?: BuilderFlagChoice[];
}

export interface BuilderCommand {
  id: string;
  title: string;
  description?: string;
  argv: string[];
  flags?: BuilderFlag[];
}

export interface CommandBuilder {
  variables: BuilderVariable[];
  commands: BuilderCommand[];
}

export function defaultVarValues(builder: CommandBuilder): Record<string, string> {
  const out: Record<string, string> = {};
  for (const row of builder.variables) {
    out[row.id] = row.default;
  }
  return out;
}

export function splitVarTemplate(
  template: string,
  values: Record<string, string>
): { text: string; id: string | null }[] {
  const parts: { text: string; id: string | null }[] = [];
  let last = 0;
  const re = new RegExp(VAR_TOKEN.source, "g");
  let match: RegExpExecArray | null;
  while ((match = re.exec(template)) !== null) {
    const name = match[1];
    if (!name || !Object.prototype.hasOwnProperty.call(values, name)) continue;
    if (match.index > last) parts.push({ text: template.slice(last, match.index), id: null });
    parts.push({ text: values[name] ?? "", id: name });
    last = match.index + match[0].length;
  }
  const tail = template.slice(last);
  if (tail) parts.push({ text: tail, id: null });
  else if (parts.length === 0) parts.push({ text: template, id: null });
  return parts;
}

export function substituteVars(template: string, values: Record<string, string>): string {
  return splitVarTemplate(template, values)
    .map((part) => part.text)
    .join("");
}

export function templateHasVars(template: string, values: Record<string, string>): boolean {
  return splitVarTemplate(template, values).some((part) => part.id !== null);
}

const UNSAFE_SHELL = /[^\w./:=@+-]/;

export function shellQuote(token: string): string {
  if (token === "") return "''";
  if (UNSAFE_SHELL.test(token)) return `'${token.replace(/'/g, `'\\''`)}'`;
  return token;
}

export function flagValue(
  flag: BuilderFlag,
  flags: Record<string, unknown>,
  values: Record<string, string>
): unknown {
  if (Object.prototype.hasOwnProperty.call(flags, flag.name)) return flags[flag.name];
  if (flag.bind_var && Object.prototype.hasOwnProperty.call(values, flag.bind_var)) {
    return values[flag.bind_var];
  }
  return flag.default;
}

export function renderCommand(
  recipe: BuilderCommand,
  flags: Record<string, unknown> | undefined,
  values: Record<string, string>
): string {
  const selected = flags ?? {};
  const parts = (recipe.argv || []).map((item) => substituteVars(String(item), values));
  for (const flag of recipe.flags || []) {
    let current = flagValue(flag, selected, values);
    if (flag.kind === "bool") {
      if (current === true) parts.push(`--${flag.name}`);
      continue;
    }
    if (current === null || current === false || current === "" || current === undefined) {
      if (flag.required) current = flag.default;
      else continue;
    }
    const token = String(current);
    if (!token) continue;
    parts.push(`--${flag.name}`);
    parts.push(token);
  }
  return parts.map(shellQuote).join(" ");
}

export function commandById(builder: CommandBuilder, id: string): BuilderCommand | undefined {
  return builder.commands.find((row) => row.id === id);
}
