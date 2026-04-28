import { inTauri, tryInvoke } from "@/lib/tauri";

/**
 * Minimize the main app window if the user has enabled the
 * `minimize_on_apply` behavior (mirrors the original Python app).
 */
export async function maybeMinimize() {
  if (!inTauri) return;
  const enabled = await tryInvoke<boolean>(
    "config_get",
    { path: "settings.general.behavior.minimize_on_apply" },
    false,
  );
  if (!enabled) return;
  try {
    const { getCurrentWindow } = await import("@tauri-apps/api/window");
    const win = getCurrentWindow();
    await win.minimize();
  } catch (err) {
    console.warn("minimize failed", err);
  }
}
