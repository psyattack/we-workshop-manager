import { useState } from "react";
import { useTranslation } from "react-i18next";

import Dialog from "@/components/common/Dialog";
import { inTauri, tryInvokeOk } from "@/lib/tauri";
import { extractWorkshopIds } from "@/lib/utils";
import { pushToast } from "@/stores/toasts";
import { useAppStore } from "@/stores/app";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function MultiDownloadDialog({ open, onOpenChange }: Props) {
  const { t } = useTranslation();
  const accountIndex = useAppStore((s) => s.accountIndex);
  const [text, setText] = useState("");
  const ids = extractWorkshopIds(text);

  const handleStart = async () => {
    if (ids.length === 0) {
      pushToast(t("messages.invalid_input"), "error");
      return;
    }
    if (!inTauri) {
      pushToast(t("messages.download_started"), "success");
      onOpenChange(false);
      return;
    }
    const ok = await tryInvokeOk("download_multi_start", {
      pubfileids: ids,
      accountIndex,
    });
    pushToast(
      ok
        ? t("labels.started_n_downloads", { count: ids.length })
        : t("messages.error"),
      ok ? "success" : "error",
    );
    onOpenChange(false);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={t("tooltips.multi_download")}
      size="md"
      footer={
        <div className="flex items-center justify-between gap-4">
          <span className="text-xs text-muted">
            {t("labels.detected_ids", { count: ids.length })}
          </span>
          <button className="btn-primary" onClick={handleStart}>
            {t("buttons.start_install")}
          </button>
        </div>
      }
    >
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={10}
        className="input font-mono text-xs"
        placeholder={t("messages.batch_input_placeholder")}
      />
    </Dialog>
  );
}
