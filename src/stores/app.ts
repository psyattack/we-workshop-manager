import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type ThemeCode = "dark" | "light" | "nord" | "monokai" | "solarized";

export const THEME_CODES: ThemeCode[] = [
  "dark",
  "light",
  "nord",
  "monokai",
  "solarized",
];

interface AppState {
  ready: boolean;
  language: string;
  theme: ThemeCode;
  accent: string;
  weDirectory: string;
  availableLanguages: { code: string; label: string }[];
  accountIndex: number;
  accounts: { index: number; username: string; is_custom: boolean }[];
  sidebarCollapsed: boolean;
  setReady: (v: boolean) => void;
  setLanguage: (lang: string) => void;
  setTheme: (theme: ThemeCode) => void;
  setAccent: (accent: string) => void;
  setWeDirectory: (dir: string) => void;
  setAvailableLanguages: (list: { code: string; label: string }[]) => void;
  setAccountIndex: (index: number) => void;
  setAccounts: (
    accounts: { index: number; username: string; is_custom: boolean }[],
  ) => void;
  setSidebarCollapsed: (v: boolean) => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      ready: false,
      language: "en",
      theme: "dark",
      accent: "indigo",
      weDirectory: "",
      availableLanguages: [
        { code: "en", label: "English" },
        { code: "ru", label: "Русский" },
      ],
      accountIndex: 3,
      accounts: [],
      sidebarCollapsed: false,
      setReady: (v) => set({ ready: v }),
      setLanguage: (language) => set({ language }),
      setTheme: (theme) => {
        set({ theme });
        // Apply right now in addition to whatever React effects do.
        // The user reported many previous attempts still left the
        // theme not switching — going aggressive here as a "crutch":
        // every code path that mutates theme is forced to flip the
        // CSS class + dataset attribute synchronously.
        if (typeof document !== "undefined") {
          const root = document.documentElement;
          THEME_CODES.forEach((c) => {
            root.classList.remove(`theme-${c}`);
            document.body?.classList.remove(`theme-${c}`);
          });
          root.classList.add(`theme-${theme}`);
          document.body?.classList.add(`theme-${theme}`);
          if (theme === "light") {
            root.classList.remove("dark");
            document.body?.classList.remove("dark");
          } else {
            root.classList.add("dark");
            document.body?.classList.add("dark");
          }
          root.dataset.theme = theme;
          root.style.colorScheme = theme === "light" ? "light" : "dark";
        }
      },
      setAccent: (accent) => set({ accent }),
      setWeDirectory: (weDirectory) => set({ weDirectory }),
      setAvailableLanguages: (availableLanguages) => set({ availableLanguages }),
      setAccountIndex: (accountIndex) => set({ accountIndex }),
      setAccounts: (accounts) => set({ accounts }),
      setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
      toggleSidebar: () => set({ sidebarCollapsed: !get().sidebarCollapsed }),
    }),
    {
      name: "weave.ui",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        theme: state.theme,
        language: state.language,
        accent: state.accent,
      }),
    },
  ),
);
