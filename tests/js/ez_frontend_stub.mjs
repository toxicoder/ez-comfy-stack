/**
 * @file ComfyUI frontend shim the JS harness swaps in for ../../scripts/app.js.
 *
 * The EZQuality overlay only needs registerExtension / graph / canvas /
 * extensionManager. Unknown properties resolve to a no-op so an additive
 * frontend call in the extension never fails the module load.
 */

const noop = () => undefined;

const extensions = [];
let storage = new Map();

function installLocalStorage() {
  storage = new Map();
  const shim = {
    getItem: (key) => (storage.has(String(key)) ? storage.get(String(key)) : null),
    setItem: (key, value) => {
      storage.set(String(key), String(value));
    },
    removeItem: (key) => {
      storage.delete(String(key));
    },
    clear: () => storage.clear(),
    key: (index) => Array.from(storage.keys())[index] ?? null,
    get length() {
      return storage.size;
    },
  };
  Object.defineProperty(globalThis, "localStorage", {
    value: shim,
    configurable: true,
    writable: true,
  });
  return shim;
}

export const app = {
  graph: null,
  canvas: {
    draw: noop,
    setDirtyCanvas: noop,
    requestGraphFrame: noop,
    boundingBox: [0, 0, 100, 100],
  },
  ui: {
    registerExtensionSettings: noop,
    dialog: { show: noop },
  },
  extensionManager: new Proxy(
    {
      registerCommand: noop,
      registerSettings: noop,
      registerSidebarTab: noop,
      getSidebarTab: () => undefined,
      bottomCanvasUISlots: { add: () => ({ remove: noop }) },
      menuCommands: [],
    },
    {
      get(target, prop) {
        if (prop in target || prop === "then") {
          return target[prop];
        }
        return noop;
      },
    },
  ),
  registerExtension(extension) {
    extensions.push(extension);
    return extension;
  },
};

/** Drop every registered extension, the live graph, and stored settings. */
export function resetFrontend() {
  extensions.length = 0;
  app.graph = null;
  installLocalStorage();
}

/** Extensions captured since the last resetFrontend(), in registration order. */
export function getExtensions() {
  return extensions.slice();
}

installLocalStorage();
