import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { CheckCircle2, Loader2, RefreshCw } from "lucide-react";
import { openUrl as openExternal } from "@tauri-apps/plugin-opener";

import Dialog from "@/components/common/Dialog";
import Markdown from "@/components/common/Markdown";
import { inTauri, invoke, tryInvoke } from "@/lib/tauri";
import { useUpdaterStore } from "@/stores/updater";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface UpdateInfo {
  current_version: string;
  latest_version: string;
  update_available: boolean;
  release_notes: string;
  html_url: string;
  error?: string | null;
}

export default function UpdateDialog({ open, onOpenChange }: Props) {
  const { t } = useTranslation();
  const cachedInfo = useUpdaterStore((s) => s.info);
  const [info, setInfo] = useState<UpdateInfo | null>(cachedInfo);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    if (inTauri) {
      const data = await tryInvoke<UpdateInfo>("updater_check");
      setInfo(data ?? null);
      if (data) useUpdaterStore.getState().show(data);
    } else {
      setInfo({
        current_version: "3.0.0",
        latest_version: "3.0.0",
        update_available: false,
        release_notes: "(mock) You are up to date.",
        html_url: "",
      });
    }
    setLoading(false);
  };

  useEffect(() => {
    if (open) void run();
  }, [open]);

  const skipThisVersion = async () => {
    if (!info?.latest_version || !inTauri) return;
    await invoke("updater_skip_version", { version: info.latest_version }).catch(
      () => undefined,
    );
    useUpdaterStore.getState().dismiss();
    onOpenChange(false);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={t("buttons.check_updates")}
      size="sm"
    >
      <div className="space-y-3">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted">
            <Loader2 className="h-4 w-4 animate-spin" />
            {t("labels.loading_dots")}
          </div>
        ) : info ? (
          <>
            <div className="flex items-center justify-between rounded-md border border-border bg-surface-sunken p-3 text-sm">
              <span className="text-muted">{t("labels.current_version")}</span>
              <span>{info.current_version}</span>
            </div>
            <div className="flex items-center justify-between rounded-md border border-border bg-surface-sunken p-3 text-sm">
              <span className="text-muted">{t("labels.latest_version")}</span>
              <span>{info.latest_version || "—"}</span>
            </div>
            {info.update_available ? (
              <div className="card border-primary/40 bg-primary/10 p-3 text-sm">
                <p className="mb-2 font-medium">
                  {t("labels.update_available_for", { version: info.latest_version })}
                </p>
                <div className="max-h-60 overflow-auto rounded-md border border-border bg-background/40 p-2 text-xs text-muted">
                  <Markdown source={info.release_notes} />
                </div>
                <div className="mt-3 flex gap-2">
                  <button
                    className="btn-primary flex-1"
                    onClick={() =>
                      info.html_url && inTauri && openExternal(info.html_url)
                    }
                  >
                    {t("buttons.download")}
                  </button>
                  <button className="btn-ghost" onClick={skipThisVersion}>
                    {t("buttons.skip_version") || "Skip this version"}
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 rounded-md border border-success/40 bg-success/10 p-3 text-sm text-success">
                <CheckCircle2 className="h-4 w-4" />
                {t("labels.up_to_date")}
              </div>
            )}
            {info.error && (
              <p className="text-xs text-danger">{info.error}</p>
            )}
            <button className="btn-ghost w-full" onClick={run}>
              <RefreshCw className="h-4 w-4" />
              {t("tooltips.refresh")}
            </button>
          </>
        ) : null}
      </div>
    </Dialog>
  );
}
