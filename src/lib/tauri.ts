import { invoke as tauriInvoke } from "@tauri-apps/api/core";

export const inTauri =
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

export async function invoke<T>(
  cmd: string,
  args?: Record<string, unknown>,
): Promise<T> {
  if (!inTauri) {
    throw new Error(`Not running inside Tauri (invoke '${cmd}' skipped)`);
  }
  return tauriInvoke<T>(cmd, args);
}

export async function tryInvoke<T>(
  cmd: string,
  args?: Record<string, unknown>,
  fallback?: T,
): Promise<T | undefined> {
  if (!inTauri) return fallback;
  try {
    return await tauriInvoke<T>(cmd, args);
  } catch (err) {
    console.warn(`invoke ${cmd} failed`, err);
    return fallback;
  }
}

/**
 * Like `tryInvoke`, but specifically for commands that return `()` /
 * `Result<(), _>` on the Rust side. Returns `true` on success and `false`
 * on either an exception or when running outside of Tauri.
 *
 * Many Rust commands do not return a value — using `tryInvoke<boolean>`
 * for them yields `undefined` even on success, which made the UI display
 * an error toast for every successful action. Use this helper instead.
 */
export async function tryInvokeOk(
  cmd: string,
  args?: Record<string, unknown>,
): Promise<boolean> {
  if (!inTauri) return false;
  try {
    await tauriInvoke<unknown>(cmd, args);
    return true;
  } catch (err) {
    console.warn(`invoke ${cmd} failed`, err);
    return false;
  }
}
