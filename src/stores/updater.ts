import { create } from "zustand";

interface UpdateInfo {
  current_version: string;
  latest_version: string;
  update_available: boolean;
  release_notes: string;
  html_url: string;
  error?: string | null;
}

interface UpdaterState {
  info: UpdateInfo | null;
  bannerVisible: boolean;
  show: (info: UpdateInfo) => void;
  dismiss: () => void;
}

/**
 * Lightweight cache of the most recent update-check result. Used so that
 * (1) the auto-check on bootstrap can surface a banner without opening the
 * dialog, and (2) reopening the dialog reuses the cached payload.
 */
export const useUpdaterStore = create<UpdaterState>((set) => ({
  info: null,
  bannerVisible: false,
  show: (info) =>
    set({ info, bannerVisible: Boolean(info.update_available && !info.error) }),
  dismiss: () => set({ bannerVisible: false }),
}));
