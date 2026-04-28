import { create } from "zustand";

import { useInstalledStore } from "@/stores/installed";

/**
 * Lightweight bus for the global "refresh current view" button in the
 * TopBar. Each view (Workshop, Installed, Author, Collections, …) can
 * subscribe via `useRefreshSubscriber(fn)`; clicking the TopBar refresh
 * button bumps the counter and any subscriber re-runs its loader.
 *
 * We use a counter so identical clicks still trigger re-renders even
 * if the previous fetch completed instantly.
 */
interface RefreshState {
  counter: number;
  trigger: () => void;
}

export const useRefreshStore = create<RefreshState>((set, get) => ({
  counter: 0,
  trigger: () => set({ counter: get().counter + 1 }),
}));

export function triggerGlobalRefresh() {
  useRefreshStore.getState().trigger();
  // Always re-pull the installed list so cards' installed indicators
  // stay accurate after a manual refresh.
  void useInstalledStore.getState().refresh();
}
