import { useEffect } from "react";

import { invoke, inTauri } from "@/lib/tauri";
import { useAppStore, ThemeCode, THEME_CODES } from "@/stores/app";

// hex → "r g b" triples consumed by Tailwind's `rgb(var(--primary) / X)`.
// Keeping both hex (for `--accent-color`) and triples (for `--primary`)
// so any place still reading `--accent-color` stays consistent.
const ACCENT_COLORS: Record<string, { hex: string; rgb: string; muted: string; fg: string }> = {
  indigo:  { hex: "#6366f1", rgb: "99 102 241",  muted: "67 56 202",   fg: "255 255 255" },
  blue:    { hex: "#3b82f6", rgb: "59 130 246",  muted: "29 78 216",   fg: "255 255 255" },
  purple:  { hex: "#a855f7", rgb: "168 85 247",  muted: "126 34 206",  fg: "255 255 255" },
  pink:    { hex: "#ec4899", rgb: "236 72 153",  muted: "190 24 93",   fg: "255 255 255" },
  rose:    { hex: "#f43f5e", rgb: "244 63 94",   muted: "190 18 60",   fg: "255 255 255" },
  orange:  { hex: "#f97316", rgb: "249 115 22",  muted: "194 65 12",   fg: "255 255 255" },
  amber:   { hex: "#f59e0b", rgb: "245 158 11",  muted: "180 83 9",    fg: "30 27 75" },
  emerald: { hex: "#10b981", rgb: "16 185 129",  muted: "4 120 87",    fg: "255 255 255" },
  teal:    { hex: "#14b8a6", rgb: "20 184 166",  muted: "15 118 110",  fg: "255 255 255" },
  cyan:    { hex: "#06b6d4", rgb: "6 182 212",   muted: "14 116 144",  fg: "255 255 255" },
};

// Per-theme inline palette. We apply these directly to <html> with
// !important so theme switching is instant and immune to:
//   • Tailwind preflight ordering,
//   • cached `:root` defaults from earlier paints,
//   • any `dark:` variants that previously won.
// (User reported "ничего не помогало" with the class-only approach.)
const THEME_PALETTES: Record<ThemeCode, Record<string, string>> = {
  dark: {
    "--bg": "15 17 26", "--surface": "26 29 46", "--surface-raised": "37 41 56",
    "--surface-sunken": "12 14 22", "--border": "42 47 66", "--border-strong": "58 63 82",
    "--fg": "255 255 255", "--fg-muted": "180 183 195", "--fg-subtle": "107 110 124",
    "--titlebar": "17 19 30", "--titlebar-fg": "236 238 246",
    "--success": "91 239 157", "--warning": "251 191 36", "--danger": "239 91 91", "--info": "99 165 250",
  },
  light: {
    "--bg": "255 255 255", "--surface": "248 250 252", "--surface-raised": "241 245 249",
    "--surface-sunken": "226 232 240", "--border": "226 232 240", "--border-strong": "203 213 225",
    "--fg": "30 41 59", "--fg-muted": "100 116 139", "--fg-subtle": "148 163 184",
    "--titlebar": "248 250 252", "--titlebar-fg": "30 41 59",
    "--success": "34 197 94", "--warning": "202 138 4", "--danger": "239 68 68", "--info": "59 130 246",
  },
  nord: {
    "--bg": "46 52 64", "--surface": "59 66 82", "--surface-raised": "67 76 94",
    "--surface-sunken": "41 46 56", "--border": "76 86 106", "--border-strong": "90 101 122",
    "--fg": "236 239 244", "--fg-muted": "216 222 233", "--fg-subtle": "107 123 141",
    "--titlebar": "36 42 54", "--titlebar-fg": "236 239 244",
    "--success": "163 190 140", "--warning": "235 203 139", "--danger": "191 97 106", "--info": "129 161 193",
  },
  monokai: {
    "--bg": "39 40 34", "--surface": "45 46 39", "--surface-raised": "62 61 50",
    "--surface-sunken": "30 31 25", "--border": "73 72 62", "--border-strong": "91 90 80",
    "--fg": "248 248 242", "--fg-muted": "207 207 194", "--fg-subtle": "117 113 94",
    "--titlebar": "30 31 25", "--titlebar-fg": "248 248 242",
    "--success": "166 226 46", "--warning": "253 151 31", "--danger": "249 38 114", "--info": "102 217 239",
  },
  solarized: {
    "--bg": "0 43 54", "--surface": "7 54 66", "--surface-raised": "10 63 78",
    "--surface-sunken": "0 33 42", "--border": "17 80 95", "--border-strong": "26 96 112",
    "--fg": "253 246 227", "--fg-muted": "147 161 161", "--fg-subtle": "88 110 117",
    "--titlebar": "0 33 42", "--titlebar-fg": "253 246 227",
    "--success": "133 153 0", "--warning": "181 137 0", "--danger": "220 50 47", "--info": "38 139 210",
  },
};

export function applyThemeClass(theme: ThemeCode) {
  const root = document.documentElement;
  const body = document.body;
  THEME_CODES.forEach((t) => {
    root.classList.remove(`theme-${t}`);
    body?.classList.remove(`theme-${t}`);
  });
  root.classList.add(`theme-${theme}`);
  body?.classList.add(`theme-${theme}`);
  if (theme === "light") {
    root.classList.remove("dark");
    body?.classList.remove("dark");
  } else {
    root.classList.add("dark");
    body?.classList.add("dark");
  }
  root.dataset.theme = theme;
  root.style.colorScheme = theme === "light" ? "light" : "dark";

  // Force-set every palette variable inline with !important. This is the
  // "crutch" path the user asked for: bypasses any cached/conflicting CSS
  // and guarantees the theme actually flips on screen.
  const palette = THEME_PALETTES[theme] ?? THEME_PALETTES.dark;
  for (const [name, value] of Object.entries(palette)) {
    root.style.setProperty(name, value, "important");
  }

  try {
    localStorage.setItem("weave.theme", theme);
  } catch {
    /* noop */
  }
}

export function applyAccent(accent: string) {
  const entry = ACCENT_COLORS[accent] ?? ACCENT_COLORS.indigo;
  const root = document.documentElement;
  // Use !important via setProperty's third arg so we override any
  // `:root.theme-…` palette set in CSS — the user wants accent to be
  // a global override that wins over theme defaults.
  root.style.setProperty("--accent-color", entry.hex, "important");
  root.style.setProperty("--primary", entry.rgb, "important");
  root.style.setProperty("--primary-muted", entry.muted, "important");
  root.style.setProperty("--primary-fg", entry.fg, "important");
  root.dataset.accent = accent;
}

// Subscribe directly to the store so any theme change is reflected on the
// <html> element synchronously, even if no React component re-renders.
let subscribed = false;
function ensureSubscribed() {
  if (subscribed) return;
  subscribed = true;
  let lastTheme = useAppStore.getState().theme;
  let lastAccent = useAppStore.getState().accent;
  useAppStore.subscribe((state) => {
    if (state.theme !== lastTheme) {
      lastTheme = state.theme;
      applyThemeClass(state.theme);
    }
    if (state.accent !== lastAccent) {
      lastAccent = state.accent;
      applyAccent(state.accent);
    }
  });
}

export function useApplyTheme() {
  const theme = useAppStore((s) => s.theme);
  const accent = useAppStore((s) => s.accent);
  useEffect(() => {
    ensureSubscribed();
    applyThemeClass(theme);
    applyAccent(accent);
  }, [theme, accent]);
}

export async function persistTheme(theme: ThemeCode) {
  applyThemeClass(theme);
  if (!inTauri) return;
  await invoke<void>("config_set", {
    path: "settings.general.appearance.theme",
    value: theme,
  }).catch(() => undefined);
}
