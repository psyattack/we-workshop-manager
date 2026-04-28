import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Download, ExternalLink, Languages, Layers, User } from "lucide-react";
import { openUrl as openExternal } from "@tauri-apps/plugin-opener";

import Drawer from "@/components/common/Drawer";
import PreviewImage from "@/components/common/PreviewImage";
import { CollectionRef, WorkshopItem } from "@/types/workshop";
import { inTauri, tryInvoke } from "@/lib/tauri";
import { pushToast } from "@/stores/toasts";
import { useNavStore } from "@/stores/nav";

interface Props {
  item: WorkshopItem | null;
  onClose: () => void;
  onDownload: (item: WorkshopItem) => void;
}

type RawTag = string | { tag?: string; category?: string };

export default function DetailsDrawer({ item, onClose, onDownload }: Props) {
  const { t, i18n } = useTranslation();
  const openAuthor = useNavStore((s) => s.openAuthor);
  const openCollection = useNavStore((s) => s.openCollection);
  const [detail, setDetail] = useState<WorkshopItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [translated, setTranslated] = useState<string>("");
  const [translating, setTranslating] = useState(false);
  const [showTranslation, setShowTranslation] = useState(false);

  // Fetch fresh metadata (tags, collections, dates) from Steam when the
  // drawer opens — mirrors Python's fetch_item_details_background.
  useEffect(() => {
    if (!item) {
      setDetail(null);
      setTranslated("");
      setShowTranslation(false);
      return;
    }
    setDetail(item);
    setTranslated("");
    setShowTranslation(false);
    if (!inTauri) return;
    setLoading(true);
    void (async () => {
      const fresh = await tryInvoke<WorkshopItem>("workshop_get_item", {
        pubfileid: item.pubfileid,
      });
      if (fresh) setDetail(fresh);
      setLoading(false);
    })();
  }, [item]);

  const current = detail ?? item;

  const groupedTags = useMemo(() => {
    if (!current || !Array.isArray(current.tags))
      return [] as { category: string; values: string[] }[];
    const groups = new Map<string, string[]>();
    for (const raw of current.tags as RawTag[]) {
      const label = typeof raw === "string" ? raw : raw.tag ?? "";
      const cat = typeof raw === "string" ? "" : raw.category ?? "";
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
  }, [current]);

  const handleTranslate = async () => {
    if (!current) return;
    if (translated) {
      setShowTranslation((v) => !v);
      return;
    }
    if (!inTauri) return;
    setTranslating(true);
    try {
      const out = await tryInvoke<string>("translator_translate", {
        text: current.description,
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

  const openWorkshopPage = async () => {
    if (!current) return;
    const url = `https://steamcommunity.com/sharedfiles/filedetails/?id=${current.pubfileid}`;
    if (inTauri) await openExternal(url);
    else window.open(url, "_blank");
  };

  const goToAuthor = () => {
    if (!current?.author_url) return;
    openAuthor(current.author_url, current.author || "");
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
      title={current?.title ?? ""}
      width="min(440px, 92vw)"
    >
      {current && (
        <div className="flex flex-col gap-3 p-3 text-sm">
          <div className="overflow-hidden rounded-md border border-border bg-surface-sunken">
            <PreviewImage
              src={current.preview_url}
              alt={current.title}
              className="aspect-square w-full object-cover"
            />
          </div>

          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              onClick={() => onDownload(current)}
              disabled={current.is_collection}
            >
              <Download className="h-3.5 w-3.5" />
              {t("buttons.install")}
            </button>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md border border-border-strong px-2.5 py-1.5 text-xs font-semibold hover:bg-surface-raised"
              onClick={openWorkshopPage}
            >
              <ExternalLink className="h-3.5 w-3.5" />
              {t("buttons.open_workshop")}
            </button>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-semibold hover:bg-surface-raised disabled:opacity-50"
              onClick={handleTranslate}
              disabled={!current.description || translating}
            >
              <Languages className="h-3.5 w-3.5" />
              {translating
                ? t("labels.translating")
                : showTranslation
                  ? t("tooltips.show_original")
                  : t("tooltips.translate_description")}
            </button>
          </div>

          <MetaGrid
            rows={[
              ["ID", current.pubfileid],
              [t("labels.size", { size: "" }).replace(/:$/, ""), current.file_size],
              [t("labels.posted", { date: "" }).replace(/:$/, ""), current.posted_date],
              [t("labels.updated", { date: "" }).replace(/:$/, ""), current.updated_date],
              ...(current.num_ratings
                ? [[t("labels.rating"), current.num_ratings] as [string, string]]
                : []),
            ]}
          />

          {current.author && (
            <AuthorButton
              name={current.author}
              url={current.author_url}
              onClick={goToAuthor}
              label={t("labels.author", { author: "" }).replace(/:$/, "")}
            />
          )}

          {loading && (
            <div className="text-xs text-subtle">
              {t("messages.loading") || "Loading…"}
            </div>
          )}

          {groupedTags.length > 0 && <TagGroups groups={groupedTags} />}

          {current.collections && current.collections.length > 0 && (
            <CollectionsList
              collections={current.collections}
              onOpen={goToCollection}
              label={t("labels.collections") || "Collections"}
            />
          )}

          <div className="flex flex-col gap-1">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-subtle">
              {t("labels.description")}
            </span>
            <div className="max-h-60 overflow-auto whitespace-pre-wrap rounded-md border border-border bg-surface-sunken p-2 text-xs leading-relaxed">
              {(showTranslation ? translated : current.description) ||
                t("labels.no_description")}
            </div>
          </div>
        </div>
      )}
    </Drawer>
  );
}

/* ---- shared presentational pieces used by both drawers ---- */

export function MetaGrid({ rows }: { rows: [string, string][] }) {
  return (
    <div className="grid grid-cols-2 gap-1.5 text-[11px]">
      {rows.map(([label, value]) => (
        <div
          key={label}
          className="flex flex-col gap-0.5 rounded-md border border-border bg-surface-sunken px-2 py-1.5"
        >
          <span className="text-[10px] uppercase tracking-wide text-subtle">
            {label}
          </span>
          <span
            className="truncate text-foreground"
            title={value || "—"}
          >
            {value || "—"}
          </span>
        </div>
      ))}
    </div>
  );
}

export function AuthorButton({
  name,
  url,
  onClick,
  label,
}: {
  name: string;
  url?: string;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!url}
      title={url}
      className="inline-flex items-center gap-2 self-start rounded-md px-2 py-1.5 text-xs hover:bg-surface-raised disabled:opacity-50"
    >
      <User className="h-3.5 w-3.5 text-primary" />
      <span className="text-subtle">
        {label}:{" "}
        <span className="font-semibold text-foreground">{name}</span>
      </span>
    </button>
  );
}

export function TagGroups({
  groups,
}: {
  groups: { category: string; values: string[] }[];
}) {
  return (
    <div className="flex flex-col gap-1.5">
      {groups.map((g) => (
        <div key={g.category}>
          <div className="mb-0.5 text-[10px] font-semibold uppercase tracking-wide text-subtle">
            {g.category}
          </div>
          <div className="flex flex-wrap gap-1">
            {g.values.map((v, i) => (
              <span key={`${v}-${i}`} className="chip !py-0 text-[11px]">
                {v}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export function CollectionsList({
  collections,
  onOpen,
  label,
}: {
  collections: CollectionRef[];
  onOpen: (c: CollectionRef) => void;
  label: string;
}) {
  return (
    <div>
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-subtle">
        {label}
      </div>
      <div className="flex flex-col gap-1">
        {collections.map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => onOpen(c)}
            className="flex items-center justify-between gap-2 rounded-md border border-border bg-surface-sunken px-2 py-1.5 text-left text-xs hover:bg-surface-raised"
          >
            <span className="flex items-center gap-1.5 truncate">
              <Layers className="h-3.5 w-3.5 shrink-0 text-primary" />
              <span className="truncate">{c.title}</span>
            </span>
            {c.item_count > 0 && (
              <span className="shrink-0 text-[11px] text-subtle">
                {c.item_count}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
