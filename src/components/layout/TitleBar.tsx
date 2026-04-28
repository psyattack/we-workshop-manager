import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Maximize2, Minus, Square, X } from "lucide-react";

import { inTauri, tryInvokeOk } from "@/lib/tauri";

async function getWindow() {
  if (!inTauri) return null;
  try {
    const mod = await import("@tauri-apps/api/window");
    return mod.getCurrentWindow();
  } catch {
    return null;
  }
}

export default function TitleBar() {
  const { t } = useTranslation();
  const [maximized, setMaximized] = useState(false);

  useEffect(() => {
    let unlisten: (() => void) | undefined;
    void (async () => {
      const w = await getWindow();
      if (!w) return;
      try {
        setMaximized(await w.isMaximized());
        unlisten = await w.onResized(async () => {
          setMaximized(await w.isMaximized());
        });
      } catch {
        /* ignore */
      }
    })();
    return () => {
      unlisten?.();
    };
  }, []);

  const minimize = async () => {
    const w = await getWindow();
    await w?.minimize();
  };

  const toggleMaximize = async () => {
    const w = await getWindow();
    if (!w) return;
    await w.toggleMaximize();
    try {
      setMaximized(await w.isMaximized());
    } catch {
      /* ignore */
    }
  };

  const close = async () => {
    // Route the close request through the backend's `app_quit` command so
    // every webview (including the hidden `steam-webview`) is destroyed and
    // the process exits — calling `w.close()` on the main window only leaves
    // the hidden webview alive on some platforms, which is why the X button
    // appeared to "do nothing" for the user. `app_quit` schedules a hard
    // `process::exit` so we don't await it (the promise may never resolve).
    if (inTauri) {
      void tryInvokeOk("app_quit");
      // Fallback in case the backend is unreachable for some reason.
      setTimeout(() => {
        void (async () => {
          const w = await getWindow();
          await w?.close();
        })();
      }, 500);
      return;
    }
    const w = await getWindow();
    await w?.close();
  };

  return (
    <div
      data-tauri-drag-region
      className="titlebar relative flex h-9 select-none items-center border-b border-border"
    >
      <div
        data-tauri-drag-region
        className="flex items-center px-3"
      >
        <span
          data-tauri-drag-region
          className="text-xs font-medium tracking-tight opacity-80"
        >
          WEave
        </span>
      </div>
      <div data-tauri-drag-region className="flex-1" />
      {inTauri && (
        <div className="flex">
          <button
            className="titlebar-btn"
            onClick={minimize}
            aria-label={t("window.minimize")}
          >
            <Minus className="h-3.5 w-3.5" />
          </button>
          <button
            className="titlebar-btn"
            onClick={toggleMaximize}
            aria-label={maximized ? t("window.restore") : t("window.maximize")}
          >
            {maximized ? (
              <Square className="h-3 w-3" />
            ) : (
              <Maximize2 className="h-3 w-3" />
            )}
          </button>
          <button
            className="titlebar-btn titlebar-btn-close"
            onClick={close}
            aria-label={t("window.close")}
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
