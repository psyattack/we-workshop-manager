import { create } from "zustand";

/**
 * Ephemeral navigation state for views that accept a payload (author profile
 * URL, collection id). The primary nav (workshop / collections / installed)
 * still lives in App.tsx as `view`; this store only tracks an optional
 * "sub view" rendered on top of the main one.
 *
 * The flow mirrors the original Python app:
 *   - Clicking a collection anywhere in the UI calls `openCollection(id)`
 *     which routes to the in-app Collection details view.
 *   - Clicking an author name/avatar calls `openAuthor(profile_url)` which
 *     routes to the in-app Author view (wallpapers + collections tabs).
 */

export type SubView =
  | { kind: "none" }
  | { kind: "author"; profileUrl: string; displayName: string }
  | { kind: "collection"; collectionId: string; title?: string };

interface NavState {
  sub: SubView;
  stack: SubView[];
  openAuthor: (profileUrl: string, displayName: string) => void;
  openCollection: (collectionId: string, title?: string) => void;
  back: () => void;
  reset: () => void;
}

export const useNavStore = create<NavState>((set, get) => ({
  sub: { kind: "none" },
  stack: [],
  openAuthor: (profileUrl, displayName) => {
    const prev = get().sub;
    set((s) => ({
      sub: { kind: "author", profileUrl, displayName },
      stack: prev.kind === "none" ? s.stack : [...s.stack, prev],
    }));
    // Reset page to 1 when navigating to author view
    const { useFiltersStore } = require("./filters");
    useFiltersStore.getState().setPage(1);
  },
  openCollection: (collectionId, title) => {
    const prev = get().sub;
    set((s) => ({
      sub: { kind: "collection", collectionId, title },
      stack: prev.kind === "none" ? s.stack : [...s.stack, prev],
    }));
    // Reset page to 1 when navigating to collection view
    const { useFiltersStore } = require("./filters");
    useFiltersStore.getState().setPage(1);
  },
  back: () => {
    const stack = get().stack;
    if (stack.length === 0) {
      set({ sub: { kind: "none" } });
      return;
    }
    const next = stack[stack.length - 1];
    set({ sub: next, stack: stack.slice(0, -1) });
  },
  reset: () => set({ sub: { kind: "none" }, stack: [] }),
}));
