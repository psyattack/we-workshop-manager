import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Trash2, RefreshCw } from "lucide-react";

import Dialog from "@/components/common/Dialog";
import { tryInvoke, tryInvokeOk } from "@/lib/tauri";

interface DebugEntry {
  url: string;
  status: number;
  elapsed_ms: number;
  size_bytes: number;
  timestamp_ms: number;
  kind: string;
  html: string;
  items_parsed: number;
}

export default function ParserDebugDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const [entries, setEntries] = useState<DebugEntry[]>([]);
  const [selected, setSelected] = useState<number | null>(null);

  const refresh = async () => {
    const log = await tryInvoke<DebugEntry[]>("workshop_debug_log", {}, []);
    setEntries(log ?? []);
  };

  useEffect(() => {
    if (!open) return;
    void refresh();
    const id = window.setInterval(() => void refresh(), 1500);
    return () => window.clearInterval(id);
  }, [open]);

  const clear = async () => {
    await tryInvokeOk("workshop_debug_clear");
    setSelected(null);
    void refresh();
  };

  const ordered = [...entries].reverse();
  const current = selected != null ? ordered[selected] : null;

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        if (!o) onClose();
      }}
      size="xl"
      title={t("settings.parser_log") || "Parser log"}
    >
      <div className="flex items-center justify-between border-b border-border px-4 py-2">
        <div className="text-sm font-medium">
          {t("settings.parser_log") || "Parser log"}
          <span className="ml-2 text-xs text-muted">
            ({entries.length} {t("debug.entries") || "entries"})
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-ghost text-xs" onClick={() => void refresh()}>
            <RefreshCw className="mr-1 inline h-3 w-3" />
            {t("common.refresh") || "Refresh"}
          </button>
          <button className="btn-ghost text-xs" onClick={() => void clear()}>
            <Trash2 className="mr-1 inline h-3 w-3" />
            {t("common.clear") || "Clear"}
          </button>
        </div>
      </div>
      <div className="grid h-[60vh] grid-cols-[280px_1fr] gap-0">
        <div className="overflow-auto border-r border-border">
          {ordered.length === 0 && (
            <div className="p-4 text-xs text-muted">
              {t("debug.no_entries") ||
                "No parser responses recorded yet. Browse the workshop to populate the log."}
            </div>
          )}
          {ordered.map((e, idx) => (
            <button
              key={idx}
              onClick={() => setSelected(idx)}
              className={`block w-full border-b border-border px-3 py-2 text-left text-xs hover:bg-surface ${
                selected === idx ? "bg-surface" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <span
                  className={`font-mono text-[10px] ${
                    e.status >= 400 ? "text-danger" : "text-emerald-400"
                  }`}
                >
                  {e.status}
                </span>
                <span className="text-[10px] text-muted">{e.elapsed_ms}ms</span>
              </div>
              <div className="mt-0.5 flex items-center gap-1">
                <span className="rounded bg-surface-raised px-1 py-px text-[9px] uppercase text-muted">
                  {e.kind}
                </span>
                <span className="text-[10px] text-muted">
                  {e.items_parsed} items
                </span>
              </div>
              <div className="mt-1 truncate text-[10px] text-foreground/80">
                {e.url.replace(/^https?:\/\/[^/]+/, "")}
              </div>
            </button>
          ))}
        </div>
        <div className="flex flex-col overflow-hidden">
          {current ? (
            <>
              <div className="border-b border-border px-3 py-2">
                <div className="break-all font-mono text-[11px] text-foreground/90">
                  {current.url}
                </div>
                <div className="mt-1 flex flex-wrap gap-2 text-[10px] text-muted">
                  <span>HTTP {current.status}</span>
                  <span>•</span>
                  <span>{(current.size_bytes / 1024).toFixed(1)} KiB</span>
                  <span>•</span>
                  <span>{current.elapsed_ms}ms</span>
                  <span>•</span>
                  <span>{current.items_parsed} items parsed</span>
                </div>
              </div>
              <pre className="flex-1 overflow-auto whitespace-pre-wrap break-all bg-surface-sunken p-3 font-mono text-[10px] text-foreground/80">
                {current.html}
              </pre>
            </>
          ) : (
            <div className="flex flex-1 items-center justify-center text-xs text-muted">
              {t("debug.select_entry") || "Select an entry to inspect."}
            </div>
          )}
        </div>
      </div>
    </Dialog>
  );
}
