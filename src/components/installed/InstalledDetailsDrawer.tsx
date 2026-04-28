import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Copy,
  ExternalLink,
  FolderOpen,
  Languages,
  Package,
  Play,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { openUrl as openExternal } from "@tauri-apps/plugin-opener";

import Drawer from "@/components/common/Drawer";
import PreviewImage from "@/components/common/PreviewImage";
import {
  AuthorButton,
  CollectionsList,
  MetaGrid,
  TagGroups,
} from "@/components/workshop/DetailsDrawer";
import { CollectionRef, InstalledWallpaper } from "@/types/workshop";
import { inTauri, tryInvoke } from "@/lib/tauri";
import { pushToast } from "@/stores/toasts";
import { useNavStore } from "@/stores/nav";
import { formatBytes, formatTimestamp } from "@/lib/utils";

interface Props {
  item: InstalledWallpaper | null;
  onClose: () => void;
  onApply: (item: InstalledWallpaper) => void;
  onExtract: (item: InstalledWallpaper) => void;
  onDelete: (item: InstalledWallpaper) => void;
  onOpenFolder: (item: InstalledWallpaper) => void;
  onCopyId: (item: InstalledWallpaper) => void;
}

type RawTag = string | { tag?: string; category?: string };

interface MetadataShape {
  description?: string;
  posted_date?: string;
  updated_date?: string;
  author?: string;
  author_url?: string;
  num_ratings?: string;
  rating_star_file?: string;
  tags?: RawTag[];
  file_size?: string;
  collections?: CollectionRef[];
}

export default function InstalledDetailsDrawer({
  item,
  onClose,
  onApply,
  onExtract,
  onDelete,
  onOpenFolder,
  onCopyId,
}: Props) {
  const { t, i18n } = useTranslation();
  const openAuthor = useNavStore((s) => s.openAuthor);
  const openCollection = useNavStore((s) => s.openCollection);
  const [meta, setMeta] = useState<MetadataShape | null>(null);
  const [translated, setTranslated] = useState("");
  const [translating, setTranslating] = useState(false);
  const [showTranslation, setShowTranslation] = useState(false);
  const [fetchingFresh, setFetchingFresh] = useState(false);

  // Same two-phase load as the Workshop drawer: cached meta first
  // (offline-friendly), fresh from Steam second (latest tags/dates).
  useEffect(() => {
    setMeta(null);
    setTranslated("");
    setShowTranslation(false);
    if (!item || !inTauri) return;
    let cancelled = false;
    void (async () => {
      const saved = await tryInvoke<MetadataShape | null>("metadata_get", {
        pubfileid: item.pubfileid,
      });
      if (!cancelled && saved) setMeta(saved);
      const fresh = await tryInvoke<MetadataShape>("workshop_get_item", {
        pubfileid: item.pubfileid,
      });
      if (!cancelled && fresh) setMeta(fresh);
    })();
    return () => {
      cancelled = true;
    };
  }, [item?.pubfileid]);

  const openWorkshopPage = async () => {
    if (!item) return;
    const url = `https://steamcommunity.com/sharedfiles/filedetails/?id=${item.pubfileid}`;
    if (inTauri) await openExternal(url);
    else window.open(url, "_blank");
  };

  const fetchFresh = async () => {
    if (!item || !inTauri) return;
    setFetchingFresh(true);
    try {
      const fresh = await tryInvoke<MetadataShape>("workshop_get_item", {
        pubfileid: item.pubfileid,
      });
      if (fresh) setMeta(fresh);
    } finally {
      setFetchingFresh(false);
    }
  };

  const handleTranslate = async () => {
    if (!item) return;
    const source = meta?.description ?? item.description ?? "";
    if (!source) return;
    if (translated) {
      setShowTranslation((v) => !v);
      return;
    }
    if (!inTauri) return;
    setTranslating(true);
    try {
      const out = await tryInvoke<string>("translator_translate", {
        text: source,
        sourceLang: "auto",
        targetLang: i18n.language || "en",
      });
      if (out) {
        setTranslated(out);
        setShowTranslation(true);
      } else {
        pushToast(t("messages.translation_error"), "error");
      }
    } finally {
      setTranslating(false);
    }
  };

  const description = meta?.description ?? item?.description ?? "";
  const displayedDescription =
    showTranslation && translated ? translated : description;

  const groupedTags = useMemo(() => {
    const raw = (meta?.tags ?? item?.tags ?? []) as RawTag[];
    const groups = new Map<string, string[]>();
    for (const r of raw) {
      const label = typeof r === "string" ? r : r.tag ?? "";
      const cat = typeof r === "string" ? "" : r.category ?? "";
      if (!label) continue;
      const key = cat || "Tags";
      const arr = groups.get(key) ?? [];
      arr.push(label);
      groups.set(key, arr);
    }
    return Array.from(groups.entries()).map(([category, values]) => ({
      category,
      values,
    }));
  }, [meta, item]);

  const goToAuthor = () => {
    if (!meta?.author_url) return;
    openAuthor(meta.author_url, meta.author || "");
    onClose();
  };

  const goToCollection = (c: CollectionRef) => {
    openCollection(c.id, c.title);
    onClose();
  };

  return (
    <Drawer
      open={!!item}
      onOpenChange={(o) => !o && onClose()}
      title={item?.title ?? ""}
      width="min(440px, 92vw)"
    >
      {item && (
        <div className="flex flex-col gap-3 p-3 text-sm">
          <div className="overflow-hidden rounded-md border border-border bg-surface-sunken">
            <PreviewImage
              src={item.preview}
              alt={item.title}
              className="aspect-square w-full object-cover"
            />
          </div>

          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
              onClick={() => onApply(item)}
            >
              <Play className="h-3.5 w-3.5" />
              {t("tooltips.install_wallpaper")}
            </button>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md border border-border-strong px-2.5 py-1.5 text-xs font-semibold hover:bg-surface-raised disabled:opacity-50"
              onClick={() => onExtract(item)}
              disabled={!item.has_pkg}
            >
              <Package className="h-3.5 w-3.5" />
              {t("tooltips.extract_wallpaper")}
            </button>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-semibold hover:bg-surface-raised"
              onClick={() => onOpenFolder(item)}
            >
              <FolderOpen className="h-3.5 w-3.5" />
              {t("tooltips.open_folder")}
            </button>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-semibold hover:bg-surface-raised"
              onClick={openWorkshopPage}
            >
              <ExternalLink className="h-3.5 w-3.5" />
              {t("buttons.open_workshop")}
            </button>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-semibold hover:bg-surface-raised"
              onClick={() => onCopyId(item)}
            >
              <Copy className="h-3.5 w-3.5" />
              ID
            </button>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-semibold text-danger hover:bg-danger/10"
              onClick={() => onDelete(item)}
            >
              <Trash2 className="h-3.5 w-3.5" />
              {t("tooltips.delete_wallpaper")}
            </button>
          </div>

          <MetaGrid
            rows={[
              ["ID", item.pubfileid],
              [t("labels.type"), item.file_type || "—"],
              [
                t("labels.size", { size: "" }).replace(/:$/, ""),
                formatBytes(item.size_bytes),
              ],
              ["Installed", formatTimestamp(item.installed_ts)],
              ...(meta?.posted_date
                ? [[t("labels.posted", { date: "" }).replace(/:$/, ""), meta.posted_date] as [string, string]]
                : []),
              ...(meta?.updated_date
                ? [[t("labels.updated", { date: "" }).replace(/:$/, ""), meta.updated_date] as [string, string]]
                : []),
              ...(meta?.num_ratings
                ? [[t("labels.rating"), meta.num_ratings] as [string, string]]
                : []),
            ]}
          />

          {meta?.author && (
            <AuthorButton
              name={meta.author}
              url={meta.author_url}
              onClick={goToAuthor}
              label={t("labels.author", { author: "" }).replace(/:$/, "")}
            />
          )}

          {groupedTags.length > 0 && <TagGroups groups={groupedTags} />}

          {meta?.collections && meta.collections.length > 0 && (
            <CollectionsList
              collections={meta.collections}
              onOpen={goToCollection}
              label={t("labels.collections") || "Collections"}
            />
          )}

          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[11px] font-semibold uppercase tracking-wide text-subtle">
                {t("labels.description")}
              </span>
              <div className="flex items-center gap-0.5">
                <button
                  type="button"
                  className="inline-flex items-center gap-1 rounded-md px-1.5 py-1 text-[11px] hover:bg-surface-raised disabled:opacity-50"
                  onClick={handleTranslate}
                  disabled={!description || translating}
                >
                  <Languages className="h-3 w-3" />
                  {translating
                    ? t("labels.translating")
                    : showTranslation
                      ? t("tooltips.show_original")
                      : t("tooltips.translate_description")}
                </button>
                {inTauri && (
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 rounded-md px-1.5 py-1 text-[11px] hover:bg-surface-raised disabled:opacity-50"
                    onClick={fetchFresh}
                    disabled={fetchingFresh}
                    title={t("tooltips.refresh")}
                  >
                    <RefreshCw
                      className={`h-3 w-3 ${fetchingFresh ? "animate-spin" : ""}`}
                    />
                  </button>
                )}
              </div>
            </div>
            <div className="max-h-60 overflow-auto whitespace-pre-wrap rounded-md border border-border bg-surface-sunken p-2 text-xs leading-relaxed">
              {displayedDescription || t("labels.no_description")}
            </div>
          </div>
        </div>
      )}
    </Drawer>
  );
}
