import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { AnimatePresence, motion } from "framer-motion";
import {
  CheckCircle2,
  Download,
  FileArchive,
  Loader2,
  X,
  XCircle,
} from "lucide-react";

import Drawer from "@/components/common/Drawer";
import PreviewImage from "@/components/common/PreviewImage";
import * as Progress from "@radix-ui/react-progress";
import { inTauri, tryInvoke } from "@/lib/tauri";
import { TaskStatus, useTasksStore } from "@/stores/tasks";
import { useInstalledStore } from "@/stores/installed";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function TasksDrawer({ open, onOpenChange }: Props) {
  const { t } = useTranslation();
  const tasks = useTasksStore((s) => s.tasks);
  const history = useTasksStore((s) => s.history);
  const clearFinished = useTasksStore((s) => s.clearFinished);

  const active = Object.values(tasks);

  const handleCancel = async (task: TaskStatus) => {
    if (!inTauri) return;
    if (task.kind === "download") {
      await tryInvoke("download_cancel", { pubfileid: task.pubfileid });
    }
  };

  return (
    <Drawer
      open={open}
      onOpenChange={onOpenChange}
      title={t("tooltips.tasks")}
      width="380px"
    >
      <div className="flex h-full flex-col">
        <div className="flex-1 overflow-auto p-3">
          {active.length === 0 && history.length === 0 ? (
            <div className="flex h-40 items-center justify-center text-sm text-muted">
              {t("labels.no_tasks")}
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              <AnimatePresence mode="popLayout">
                {active.map((task) => (
                  <motion.div
                    key={`${task.kind}-${task.pubfileid}`}
                    layout
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    className="card flex gap-3 p-3"
                  >
                    <TaskPreview pubfileid={task.pubfileid} />
                    <div className="min-w-0 flex-1">
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2 text-sm font-medium">
                          {task.kind === "download" ? (
                            <Download className="h-4 w-4 text-primary" />
                          ) : (
                            <FileArchive className="h-4 w-4 text-info" />
                          )}
                          {t(
                            task.kind === "download"
                              ? "labels.download_prefix"
                              : "labels.extract_prefix",
                            { id: task.pubfileid },
                          )}
                        </div>
                        <button
                          className="btn-icon"
                          onClick={() => handleCancel(task)}
                          title={t("tooltips.cancel_task")}
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        <span className="line-clamp-1">{task.status}</span>
                      </div>
                      {task.progress != null && task.progress > 0 && (
                        <Progress.Root
                          value={task.progress}
                          className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-sunken"
                        >
                          <Progress.Indicator
                            style={{
                              transform: `translateX(-${100 - task.progress}%)`,
                              transition: "transform 240ms",
                            }}
                            className="h-full w-full bg-primary"
                          />
                        </Progress.Root>
                      )}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {history.length > 0 && (
                <div className="mt-2 text-[11px] uppercase tracking-wide text-subtle">
                  {t("labels.tasks_history")}
                </div>
              )}
              {history.map((task, i) => (
                <div
                  key={`${task.kind}-${task.pubfileid}-${i}`}
                  className="card flex items-center gap-2 p-2 text-xs text-muted"
                >
                  <TaskPreview pubfileid={task.pubfileid} small />
                  {task.phase === "completed" ? (
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-success" />
                  ) : (
                    <XCircle className="h-4 w-4 shrink-0 text-danger" />
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-foreground">
                      {task.kind}: {task.pubfileid}
                    </div>
                    <div className="truncate">{task.status}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        {history.length > 0 && (
          <div className="border-t border-border p-3">
            <button className="btn-ghost w-full" onClick={clearFinished}>
              {t("tooltips.clear_history")}
            </button>
          </div>
        )}
      </div>
    </Drawer>
  );
}

/**
 * Small thumbnail for task rows. Resolves the preview URL through:
 *   1. The locally-installed cache (after the download finishes the
 *      file is on disk, so the path is immediately available).
 *   2. The Steam metadata cache (`metadata_get`) — populated by the
 *      original parser whenever we've seen this pubfileid.
 *   3. A live `workshop_get_item` fetch as a last resort.
 */
function TaskPreview({
  pubfileid,
  small,
}: {
  pubfileid: string;
  small?: boolean;
}) {
  const installed = useInstalledStore((s) => s.byId[pubfileid]);
  const [src, setSrc] = useState<string>("");
  useEffect(() => {
    if (installed?.preview) {
      setSrc(installed.preview);
      return;
    }
    setSrc("");
    if (!inTauri) return;
    let cancelled = false;
    void (async () => {
      const cached = await tryInvoke<{ preview?: string } | null>(
        "metadata_get",
        { pubfileid },
      );
      if (!cancelled && cached?.preview) {
        setSrc(cached.preview);
        return;
      }
      const remote = await tryInvoke<{ preview_url?: string } | null>(
        "workshop_get_item",
        { pubfileid },
      );
      if (!cancelled && remote?.preview_url) setSrc(remote.preview_url);
    })();
    return () => {
      cancelled = true;
    };
  }, [pubfileid, installed]);

  const dim = small ? "h-9 w-9" : "h-12 w-12";
  return (
    <div
      className={`${dim} shrink-0 overflow-hidden rounded-md border border-border bg-surface-sunken`}
    >
      {src ? (
        <PreviewImage
          src={src}
          alt={pubfileid}
          className="h-full w-full object-cover"
        />
      ) : null}
    </div>
  );
}
