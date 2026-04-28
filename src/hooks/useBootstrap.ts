import { useEffect } from "react";
import { listen } from "@tauri-apps/api/event";

import { loadTranslations } from "@/lib/i18n";
import { invoke, inTauri, tryInvoke, tryInvokeOk } from "@/lib/tauri";
import { useAppStore, ThemeCode } from "@/stores/app";
import { useTasksStore } from "@/stores/tasks";
import { useInstalledStore } from "@/stores/installed";
import { triggerGlobalRefresh } from "@/stores/refresh";
import i18n from "@/lib/i18n";
import { maybeMinimize } from "@/lib/window";

export function useBootstrap() {
  useEffect(() => {
    void (async () => {
      if (!inTauri) {
        useAppStore.setState({ ready: true });
        return;
      }

      const translations = await tryInvoke<Record<string, unknown>>(
        "i18n_get_translations",
        undefined,
        {},
      );
      const config = await tryInvoke<Record<string, unknown>>(
        "config_get_all",
      );
      const availableLanguages = await tryInvoke<{ code: string; label: string }[]>(
        "i18n_get_available_languages",
        undefined,
        [],
      );
      const weDirectory = await tryInvoke<string | null>(
        "we_get_directory",
        undefined,
        null,
      );
      const accountIndex = await tryInvoke<number>(
        "config_get",
        { path: "settings.account.account.account_number" },
        3,
      );
      const accounts = await tryInvoke<
        { index: number; username: string; is_custom: boolean }[]
      >("accounts_list", undefined, []);

      if (translations) {
        const language =
          (config as any)?.settings?.general?.appearance?.language ?? "en";
        loadTranslations(translations, language);
        useAppStore.setState({ language });
      }

      const appearance =
        (config as any)?.settings?.general?.appearance ?? {};
      const patch: Record<string, unknown> = {
        weDirectory: weDirectory ?? "",
        availableLanguages: availableLanguages ?? [],
        accountIndex: typeof accountIndex === "number" ? accountIndex : 3,
        accounts: accounts ?? [],
        ready: true,
      };
      // Only override persisted theme/accent when the backing config has an
      // explicit value. Otherwise we would clobber the user's in-session
      // selection on next bootstrap.
      if (appearance.theme) patch.theme = appearance.theme as ThemeCode;
      if (appearance.accent) patch.accent = appearance.accent as string;
      useAppStore.setState(patch);

      // Fire-and-forget: sign the hidden Steam webview into the dedicated
      // parser account (weworkshopmanager2) on startup so 18+ content is
      // visible and the scraper has a valid session. `accountIndex: null`
      // tells the backend to use the parser credentials rather than the
      // currently-selected download account. If login requires Steam Guard
      // or the password is stale this simply returns false — the user can
      // still log in manually via Settings → Steam web session.
      void tryInvoke<boolean>("steam_auto_login", {
        accountIndex: null,
      });

      // Restore saved window geometry if the feature is on.
      void invoke("app_restore_window_geometry").catch(() => undefined);

      // Auto-check for updates on startup if enabled.
      void maybeCheckForUpdates();

      // Auto-init metadata for installed wallpapers if enabled.
      void maybeAutoInitMetadata();

      // Persist window state on close if enabled.
      void registerWindowStatePersistence();

      // Prime the global "what's installed" cache so any view can render
      // installed-indicators before the user opens the Installed tab.
      void useInstalledStore.getState().refresh();

      await Promise.all([
        listen<{
          pubfileid: string;
          status: string;
          account: string;
          phase: string;
          progress?: number | null;
        }>("download://status", (event) => {
          useTasksStore.getState().upsert({
            ...event.payload,
            kind: "download",
            phase: event.payload.phase as any,
          });
          if (event.payload.phase === "failed") {
            void import("@/stores/toasts").then(({ pushToast }) => {
              pushToast(
                `Download failed (${event.payload.pubfileid}): ${event.payload.status}`,
                "error",
              );
            });
          } else if (event.payload.phase === "completed") {
            void import("@/stores/toasts").then(({ pushToast }) => {
              pushToast(
                `Download completed: ${event.payload.pubfileid}`,
                "success",
              );
            });
            // The newly-downloaded item should now show the Installed
            // indicator on cards regardless of which view we're in.
            // We refresh the installed store so cards update their
            // installed indicators, and fetch workshop metadata for
            // the new item so it's cached for future use.
            void useInstalledStore.getState().refresh();
            void (async () => {
              await tryInvoke(
                "workshop_get_item",
                { pubfileid: event.payload.pubfileid },
                null,
              );
            })();
            void maybeAutoApply(event.payload.pubfileid);
          }
        }),
        listen<{
          pubfileid: string;
          status: string;
          account: string;
          phase: string;
          progress?: number | null;
        }>("extract://status", (event) => {
          useTasksStore.getState().upsert({
            ...event.payload,
            kind: "extract",
            phase: event.payload.phase as any,
          });
          if (event.payload.phase === "failed") {
            void import("@/stores/toasts").then(({ pushToast }) => {
              pushToast(
                `Extract failed (${event.payload.pubfileid}): ${event.payload.status}`,
                "error",
              );
            });
          } else if (event.payload.phase === "completed") {
            void import("@/stores/toasts").then(({ pushToast }) => {
              pushToast(
                `Extract completed: ${event.payload.pubfileid}`,
                "success",
              );
            });
          }
        }),
      ]);
    })();
  }, []);
}

export async function changeLanguageTo(code: string) {
  useAppStore.setState({ language: code });
  await i18n.changeLanguage(code);
  if (inTauri) {
    await invoke<void>("i18n_set_language", { language: code }).catch(
      () => undefined,
    );
  }
}

interface UpdateInfo {
  current_version: string;
  latest_version: string;
  update_available: boolean;
  release_notes: string;
  html_url: string;
  error: string | null;
}

async function maybeCheckForUpdates() {
  if (!inTauri) return;
  const enabled = await tryInvoke<boolean>(
    "config_get",
    { path: "settings.general.behavior.auto_check_updates" },
    true,
  );
  if (!enabled) return;
  const info = await tryInvoke<UpdateInfo>("updater_check", undefined);
  if (info?.update_available) {
    const { useUpdaterStore } = await import("@/stores/updater");
    useUpdaterStore.getState().show(info);
  }
}

async function maybeAutoInitMetadata() {
  if (!inTauri) return;
  const enabled = await tryInvoke<boolean>(
    "config_get",
    { path: "settings.general.behavior.auto_init_metadata" },
    true,
  );
  if (!enabled) return;
  // Run in background so the UI is responsive immediately. When the batch
  // finishes, pulse the global refresh counter so every view re-reads
  // `metadata_get_all` — this is what keeps the Installed Misc/Genre
  // filter chips in sync with whatever tags the batch just persisted.
  setTimeout(() => {
    void (async () => {
      const count = await tryInvoke<number>(
        "app_init_metadata",
        undefined,
        0,
      );
      if ((count ?? 0) > 0) triggerGlobalRefresh();
    })();
  }, 5000);
}

async function maybeAutoApply(pubfileid: string) {
  if (!inTauri || !pubfileid) return;
  const enabled = await tryInvoke<boolean>(
    "config_get",
    { path: "settings.general.behavior.auto_apply_last_downloaded" },
    false,
  );
  if (!enabled) return;
  // Need the freshly-installed wallpaper's project.json path. Pull the
  // current installed list and find the matching pubfileid.
  type Installed = { pubfileid: string; project_json_path: string };
  const installed = await tryInvoke<Installed[]>(
    "we_list_installed",
    undefined,
    [],
  );
  const match = (installed ?? []).find((w) => w.pubfileid === pubfileid);
  if (!match) return;
  const ok = await tryInvokeOk("we_apply", {
    projectPath: match.project_json_path,
    monitor: null,
    force: false,
  });
  if (ok) {
    void maybeMinimize();
  }
}

async function registerWindowStatePersistence() {
  if (!inTauri) return;
  try {
    const { getCurrentWindow } = await import("@tauri-apps/api/window");
    const win = getCurrentWindow();

    const save = async () => {
      const enabled = await tryInvoke<boolean>(
        "config_get",
        { path: "settings.general.behavior.save_window_state" },
        true,
      );
      if (!enabled) return;
      const [size, pos, maximized] = await Promise.all([
        win.outerSize(),
        win.outerPosition(),
        win.isMaximized(),
      ]);
      void invoke("app_save_window_geometry", {
        geom: {
          x: pos.x,
          y: pos.y,
          width: size.width,
          height: size.height,
          is_maximized: Boolean(maximized),
        },
      }).catch(() => undefined);
    };

    await win.onCloseRequested(async () => {
      await save();
    });
    // Also save periodically while the user is using the app, so an
    // unexpected crash doesn't lose geometry entirely.
    setInterval(() => {
      void save();
    }, 60_000);
  } catch (err) {
    console.warn("window state persistence setup failed", err);
  }
}
