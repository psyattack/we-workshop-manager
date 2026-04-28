import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Copy,
  Download,
  ExternalLink,
  FolderOpen,
  Languages,
  Package,
  Play,
  Trash2,
  User,
} from "lucide-react";
import { openUrl as openExternal } from "@tauri-apps/plugin-opener";
import { open as openPath } from "@tauri-apps/plugin-dialog";

import Drawer from "@/components/common/Drawer";
import PreviewImage from "@/components/common/PreviewImage";
import {
  CollectionRef,
  InstalledWallpaper,
  WorkshopItem,
} from "@/types/workshop";
import { inTauri, tryInvoke, tryInvokeOk } from "@/lib/tauri";
import { pushToast } from "@/stores/toasts";
import { useNavStore } from "@/stores/nav";
import { useInstalledStore } from "@/stores/installed";
import { formatBytes, formatTimestamp } from "@/lib/utils";
import { maybeMinimize } from "@/lib/window";
import { useConfirm } from "@/hooks/useConfirm";
import { Tooltip } from "@/components/common/Tooltip";

/**
 * One unified details drawer used by both the Workshop view and the
 * Installed view. Until now we had two near-duplicate components that
 * drifted in spacing, button copy and meta layout — the user wanted
 * "точь в точь идентичные" panels, so we collapse them here.
 *
 * The drawer always shows:
 *   1. a square preview,
 *   2. a tight row of action buttons (varies by item kind),
 *   3. a 2-column meta grid,
 *   4. an inline author chip,
 *   5. tag groups and parent collections,
 *   6. description with translate / refresh.
 *
 * Width is 340px (down from 440px) so the drawer feels compact like the
 * original Python panel rather than a full sheet.
 */

export type DetailsKind = "workshop" | "installed";

interface CommonProps {
  onClose: () => void;
}

interface WorkshopProps extends CommonProps {
  kind: "workshop";
  item: WorkshopItem | null;
  onDownload: (item: WorkshopItem) => void;
}

interface InstalledProps extends CommonProps {
  kind: "installed";
  item: InstalledWallpaper | null;
  onApply: (item: InstalledWallpaper) => void;
  onExtract: (item: InstalledWallpaper) => void;
  onDelete: (item: InstalledWallpaper) => void;
  onOpenFolder: (item: InstalledWallpaper) => void;
  onCopyId: (item: InstalledWallpaper) => void;
}

type Props = WorkshopProps | InstalledProps;

type RawTag = string | { tag?: string; category?: string };

/** Row in the two-column info grid. Optional 3rd slot tints the value. */
type MetaRow = [string, string | React.ReactNode] | [string, string | React.ReactNode, "warning"];

/**
 * Extract star rating (0-5) from Steam's rating filename.
 */
function getRatingStars(ratingStarFile: string | undefined): number {
  if (!ratingStarFile) return 0;
  const m = ratingStarFile.match(/(\d+)/);
  if (!m) return 0;
  const n = parseInt(m[1], 10);
  return Number.isFinite(n) ? Math.max(0, Math.min(5, n)) : 0;
}



interface Meta {
  pubfileid: string;
  title: string;
  preview: string;
  description: string;
  author?: string;
  author_url?: string;
  posted_date?: string;
  updated_date?: string;
  num_ratings?: string;
  rating_star_file?: string;
  file_size?: string;
  tags?: RawTag[];
  collections?: CollectionRef[];
  // installed-only
  file_type?: string;
  size_bytes?: number;
  installed_ts?: number;
  has_pkg?: boolean;
  is_collection?: boolean;
}

function workshopToMeta(w: WorkshopItem): Meta {
  return {
    pubfileid: w.pubfileid,
    title: w.title,
    preview: w.preview_url,
    description: w.description,
    author: w.author,
    author_url: w.author_url,
    posted_date: w.posted_date,
    updated_date: w.updated_date,
    num_ratings: w.num_ratings,
    rating_star_file: w.rating_star_file,
    file_size: w.file_size,
    tags: Array.isArray(w.tags) ? (w.tags as RawTag[]) : [],
    collections: w.collections,
    is_collection: w.is_collection,
  };
}

async function pickDir(): Promise<string | null> {
  if (!inTauri) return null;
  const r = await openPath({ directory: true });
  if (!r || Array.isArray(r)) return null;
  return r;
}

function installedToMeta(i: InstalledWallpaper): Meta {
  return {
    pubfileid: i.pubfileid,
    title: i.title,
    preview: i.preview,
    description: i.description,
    file_type: i.file_type,
    size_bytes: i.size_bytes,
    installed_ts: i.installed_ts,
    has_pkg: i.has_pkg,
    tags: i.tags,
  };
}

export default function DetailsPanel(props: Props) {
  const { t, i18n } = useTranslation();
  const openAuthor = useNavStore((s) => s.openAuthor);
  const openCollection = useNavStore((s) => s.openCollection);
  const refreshInstalled = useInstalledStore((s) => s.refresh);
  // If a workshop item is already on disk we promote the panel to a
  // mixed Workshop+Installed view (extra Apply/Folder/Delete buttons,
  // Installed timestamp in the meta grid). Same panel works in every
  // view (Workshop, Author, Collection contents, Collections grid).
  const installedEntry = useInstalledStore((s) =>
    props.item ? s.byId[props.item.pubfileid] : undefined,
  );
  const showInstalledActions =
    props.kind === "installed" || Boolean(installedEntry);

  const baseMeta: Meta | null = props.item
    ? props.kind === "workshop"
      ? workshopToMeta(props.item)
      : installedToMeta(props.item)
    : null;
  // When the workshop-mode item is installed locally, augment the meta
  // with installed-only fields (size on disk, install time, has_pkg).
  const augmentedBase: Meta | null = useMemo(() => {
    if (!baseMeta) return null;
    if (props.kind === "installed") return baseMeta;
    if (!installedEntry) return baseMeta;
    return {
      ...baseMeta,
      file_type: installedEntry.file_type,
      size_bytes: installedEntry.size_bytes,
      installed_ts: installedEntry.installed_ts,
      has_pkg: installedEntry.has_pkg,
      // Local title/description/preview are usually richer.
      title: baseMeta.title || installedEntry.title,
      preview: baseMeta.preview || installedEntry.preview,
      description: baseMeta.description || installedEntry.description,
      tags:
        baseMeta.tags && baseMeta.tags.length > 0
          ? baseMeta.tags
          : installedEntry.tags,
    };
  }, [baseMeta, installedEntry, props.kind]);

  const [fresh, setFresh] = useState<Partial<Meta> | null>(null);
  const [translated, setTranslated] = useState("");
  const [showTranslation, setShowTranslation] = useState(false);
  const [translating, setTranslating] = useState(false);

  const pubfileid = props.item?.pubfileid ?? null;

  // Two-phase load: cached metadata first (offline-friendly), fresh from
  // Steam second. For workshop items the base already has data, but we
  // still re-fetch to update tags / posted-date.
  useEffect(() => {
    setFresh(null);
    setTranslated("");
    setShowTranslation(false);
    if (!pubfileid || !inTauri) return;
    let cancelled = false;
    void (async () => {
      if (props.kind === "installed") {
        const saved = await tryInvoke<Partial<Meta> | null>("metadata_get", {
          pubfileid,
        });
        if (!cancelled && saved) setFresh(saved);
      }
      const remote = await tryInvoke<Partial<Meta>>("workshop_get_item", {
        pubfileid,
      });
      if (!cancelled && remote) setFresh(remote);
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pubfileid]);

  // Merge base + fresh; non-empty fresh values win.
  const meta: Meta | null = useMemo(() => {
    const root = augmentedBase;
    if (!root) return null;
    if (!fresh) return root;
    const merged: Meta = { ...root };
    for (const k of Object.keys(fresh) as (keyof Meta)[]) {
      const v = fresh[k];
      if (v === undefined || v === null) continue;
      if (typeof v === "string" && v.length === 0) continue;
      if (Array.isArray(v) && v.length === 0) continue;
      // @ts-expect-error generic merge across union fields
      merged[k] = v;
    }
    return merged;
  }, [augmentedBase, fresh]);

  const groupedTags = useMemo(() => {
    if (!meta?.tags) return [] as { category: string; values: string[] }[];
    const groups = new Map<string, string[]>();
    const fallbackKey = t("labels.tags") || "Tags";
    for (const r of meta.tags) {
      const label = typeof r === "string" ? r : r.tag ?? "";
      const rawCat = typeof r === "string" ? "" : r.category ?? "";
      // Skip values that are purely punctuation (".", "·") so we never
      // render a bogus "·" / "." chip the user reported seeing.
      if (!label || /^\W*$/.test(label)) continue;
      // Same defensive sanitization for the category label — if Steam
      // produced a category that is pure punctuation, drop it.
      const cat =
        rawCat && /\w/.test(rawCat) ? rawCat : fallbackKey;
      const arr = groups.get(cat) ?? [];
      arr.push(label);
      groups.set(cat, arr);
    }
    return Array.from(groups.entries()).map(([category, values]) => ({
      category,
      values,
    }));
  }, [meta, t]);

  const description = meta?.description ?? "";
  const displayedDescription =
    showTranslation && translated ? translated : description;

  const openWorkshopPage = async () => {
    if (!meta) return;
    const url = `https://steamcommunity.com/sharedfiles/filedetails/?id=${meta.pubfileid}`;
    if (inTauri) await openExternal(url);
    else window.open(url, "_blank");
  };

  const handleTranslate = async () => {
    if (!description) return;
    if (translated) {
      setShowTranslation((v) => !v);
      return;
    }
    if (!inTauri) return;
    setTranslating(true);
    try {
      const out = await tryInvoke<string>("translator_translate", {
        text: description,
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


  const goToAuthor = () => {
    if (!meta?.author_url) return;
    openAuthor(meta.author_url, meta.author || "");
    props.onClose();
  };

  const goToCollection = (c: CollectionRef) => {
    openCollection(c.id, c.title);
    props.onClose();
  };

  const datesAndStats: MetaRow[] = [];
  if (meta) {
    if (showInstalledActions) {
      datesAndStats.push([
        t("labels.size", { size: "" }).replace(/:$/, ""),
        meta.size_bytes
          ? formatBytes(meta.size_bytes)
          : meta.file_size || "—",
      ]);
      if (meta.installed_ts) {
        datesAndStats.push([
          t("labels.installed") || "Installed",
          formatTimestamp(meta.installed_ts),
        ]);
      }
    } else if (meta.file_size) {
      datesAndStats.push([
        t("labels.size", { size: "" }).replace(/:$/, ""),
        meta.file_size,
      ]);
    }
    if (meta.posted_date) {
      datesAndStats.push([
        t("labels.posted", { date: "" }).replace(/:$/, ""),
        meta.posted_date,
      ]);
    }
    if (meta.updated_date) {
      datesAndStats.push([
        t("labels.updated", { date: "" }).replace(/:$/, ""),
        meta.updated_date,
      ]);
    }
    // Rating lives inside the info grid so it sits alongside the other
    // metadata rather than hanging off the action row. Unicode stars +
    // vote count, rendered in the same warning-yellow as before.
    const ratingStars = getRatingStars(meta.rating_star_file);
    const votes = (meta.num_ratings || "").trim();
    if (ratingStars > 0 || votes) {
      const filled = "★".repeat(ratingStars);
      const empty = "☆".repeat(Math.max(0, 5 - ratingStars));
      datesAndStats.push([
        t("labels.rating") || "Rating",
        (
          <span className="flex items-center">
            <span className="text-warning">{filled}</span>
            <span className="text-warning/30">{empty}</span>
            {votes && <span className="ml-1 text-foreground">({votes})</span>}
          </span>
        ),
        "warning",
      ]);
    }
  }

  return (
    <Drawer
      open={!!props.item}
      onOpenChange={(o) => !o && props.onClose()}
      title={meta?.title ?? ""}
      width="min(340px, 92vw)"
    >
      {meta && (
        <div className="flex flex-col gap-2.5 p-3 text-[13px]">
          <div className="overflow-hidden rounded-md border border-border bg-surface-sunken">
            <PreviewImage
              src={meta.preview}
              alt={meta.title}
              className="aspect-square w-full object-cover"
            />
          </div>

          <ActionRow
            {...props}
            meta={meta}
            installedEntry={installedEntry}
            showInstalledActions={showInstalledActions}
            openWorkshopPage={openWorkshopPage}
            refreshInstalled={refreshInstalled}
          />

          <MetaGrid rows={datesAndStats} />

          {meta.author && (
            <button
              type="button"
              onClick={goToAuthor}
              disabled={!meta.author_url}
              title={meta.author_url}
              className="inline-flex items-center gap-1 self-start rounded-md px-2 py-1 text-xs hover:bg-surface-raised disabled:opacity-60"
            >
              <User className="h-3.5 w-3.5 text-primary" />
              <span className="text-subtle">
                {t("labels.author", { author: "" })}{" "}
                <span className="font-semibold text-foreground">
                  {meta.author}
                </span>
              </span>
            </button>
          )}

          {groupedTags.length > 0 && (
            <div className="flex flex-col gap-1">
              {groupedTags.map((g) => (
                <div key={g.category}>
                  <div className="mb-0.5 text-[10px] font-semibold uppercase tracking-wide text-subtle">
                    {g.category}
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {g.values.map((v, i) => (
                      <span
                        key={`${v}-${i}`}
                        className="chip !py-0 text-[11px]"
                      >
                        {v}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {meta.collections && meta.collections.length > 0 && (
            <div>
              <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-subtle">
                {t("labels.collections") || "Collections"}
              </div>
              <div className="flex flex-col gap-1">
                {meta.collections.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => goToCollection(c)}
                    className="flex items-center justify-between gap-2 rounded-md bg-surface-sunken/50 px-2 py-1.5 text-left hover:bg-surface-raised"
                  >
                    <span className="line-clamp-1 text-xs font-medium">
                      {c.title}
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
          )}

          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-subtle">
                {t("labels.description")}
              </span>
              <div className="flex items-center gap-0.5">
                <button
                  type="button"
                  className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] hover:bg-surface-raised disabled:opacity-50"
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
              </div>
            </div>
            <div className="max-h-60 overflow-auto whitespace-pre-wrap rounded-md bg-surface-sunken/50 p-2 text-xs leading-relaxed">
              {displayedDescription || t("labels.no_description")}
            </div>
          </div>
        </div>
      )}
    </Drawer>
  );
}

function MetaGrid({ rows }: { rows: MetaRow[] }) {
  if (rows.length === 0) return null;
  return (
    <div className="grid grid-cols-2 gap-1 text-[11px]">
      {rows.map((row) => {
        const [label, value, tone] = row;
        const isReactNode = typeof value !== 'string';
        return (
          <div
            key={label + (typeof value === 'string' ? value : '')}
            className="flex flex-col gap-0.5 rounded-md bg-surface-sunken/50 px-2 py-1"
          >
            <span className="text-[9px] uppercase tracking-wide text-subtle">
              {label}
            </span>
            {isReactNode ? (
              <div className="truncate">{value}</div>
            ) : (
              <span
                className={
                  tone === "warning"
                    ? "truncate font-semibold text-warning"
                    : "truncate text-foreground"
                }
                title={value || "—"}
              >
                {value || "—"}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

function ActionRow(
  props: Props & {
    meta: Meta;
    installedEntry: InstalledWallpaper | undefined;
    showInstalledActions: boolean;
    openWorkshopPage: () => Promise<void>;
    refreshInstalled: () => Promise<void>;
  },
) {
  const { t } = useTranslation();
  const { confirm, ConfirmDialog } = useConfirm();
  const buttons: { node: React.ReactNode; key: string }[] = [];

  // Resolve the InstalledWallpaper handle to act on. In the Installed
  // tab `props.item` already is one. In Workshop/Author/Collection the
  // installed entry comes from the global cache (props.installedEntry).
  const installedHandle: InstalledWallpaper | null =
    props.kind === "installed"
      ? (props.item as InstalledWallpaper | null)
      : (props.installedEntry ?? null);

  // Inline fallbacks when called from the Workshop/Collections side
  // (where the parent doesn't pass apply/extract/delete handlers).
  const overlayApply = async () => {
    if (!installedHandle) return;
    const ok = await tryInvokeOk("we_apply", {
      projectPath: installedHandle.project_json_path,
      monitor: null,
      force: false,
    });
    if (ok) {
      pushToast(t("messages.applied") || "Applied", "success");
      void maybeMinimize();
    } else {
      pushToast(t("messages.apply_failed") || "Apply failed", "error");
    }
  };
  const overlayExtract = async () => {
    if (!installedHandle) return;
    if (!installedHandle.has_pkg) {
      pushToast(t("messages.no_pkg_file") || "No .pkg file", "warning");
      return;
    }
    // Same flow the Installed tab uses — pick a directory, then start
    // a background extract task.
    const folder = await pickDir();
    if (!folder) return;
    const ok = await tryInvokeOk("extract_start", {
      pubfileid: installedHandle.pubfileid,
      outputDir: folder,
    });
    pushToast(
      ok
        ? t("messages.extraction_started") || "Extract started"
        : t("messages.error") || "Extract failed",
      ok ? "success" : "error",
    );
  };
  const overlayOpenFolder = async () => {
    if (!installedHandle) return;
    await tryInvokeOk("open_path", { path: installedHandle.folder });
  };
  const overlayDelete = async () => {
    if (!installedHandle) return;
    // Block deleting a wallpaper Wallpaper Engine is currently painting —
    // otherwise we hit file locks mid-delete and the library ends up in a
    // bad state.
    const active = await tryInvoke<string[]>(
      "we_active_pubfileids",
      undefined,
      [],
    );
    if ((active ?? []).includes(installedHandle.pubfileid)) {
      pushToast(
        t("messages.cannot_delete_active_single") ||
          "Wallpaper is currently active — switch first.",
        "error",
      );
      return;
    }
    const confirmed = await confirm({
      title: t("tooltips.delete_wallpaper") || "Delete Wallpaper",
      message: t("messages.confirm_delete") || "Delete this wallpaper?\n\nThe wallpaper folder will be removed from your Wallpaper Engine library permanently. This action cannot be undone.",
      confirmLabel: t("buttons.delete") || "Delete",
      cancelLabel: t("buttons.cancel") || "Cancel",
      variant: "danger",
    });
    if (!confirmed) return;
    const ok = await tryInvokeOk("we_delete_wallpaper", {
      pubfileid: installedHandle.pubfileid,
    });
    if (ok) {
      pushToast(t("messages.deleted") || "Deleted", "success");
      void props.refreshInstalled();
      props.onClose();
    } else {
      pushToast(
        t("messages.cannot_delete_active_single") ||
          t("messages.delete_failed") ||
          "Delete failed",
        "error",
      );
    }
  };


  if (props.showInstalledActions && installedHandle) {
    buttons.push({
      key: "apply",
      node: (
        <ActionBtn
          variant="primary"
          icon={<Play className="h-3.5 w-3.5" />}
          label={t("tooltips.install_wallpaper")}
          onClick={() =>
            props.kind === "installed"
              ? props.onApply(installedHandle)
              : void overlayApply()
          }
        />
      ),
    });
    buttons.push({
      key: "extract",
      node: (
        <ActionBtn
          icon={<Package className="h-3.5 w-3.5" />}
          label={t("tooltips.extract_wallpaper")}
          disabled={!props.meta.has_pkg}
          onClick={() =>
            props.kind === "installed"
              ? props.onExtract(installedHandle)
              : void overlayExtract()
          }
        />
      ),
    });
    // Delete sits directly after Extract as a compact trash-can icon
    // (no label) — same row, so it's reachable in one glance but too
    // small to hit by accident.
    buttons.push({
      key: "delete",
      node: (
        <ActionBtn
          variant="danger"
          iconOnly
          icon={<Trash2 className="h-3.5 w-3.5" />}
          label={t("tooltips.delete_wallpaper")}
          onClick={() =>
            props.kind === "installed"
              ? props.onDelete(installedHandle)
              : void overlayDelete()
          }
        />
      ),
    });
    buttons.push({
      key: "open",
      node: (
        <ActionBtn
          icon={<FolderOpen className="h-3.5 w-3.5" />}
          label={t("tooltips.open_folder")}
          onClick={() =>
            props.kind === "installed"
              ? props.onOpenFolder(installedHandle)
              : void overlayOpenFolder()
          }
        />
      ),
    });
  } else if (props.kind === "workshop") {
    buttons.push({
      key: "install",
      node: (
        <ActionBtn
          variant="primary"
          icon={<Download className="h-3.5 w-3.5" />}
          label={t("buttons.install")}
          disabled={props.meta.is_collection}
          onClick={() => props.item && props.onDownload(props.item)}
        />
      ),
    });
  }

  buttons.push({
    key: "workshop",
    node: (
      <ActionBtn
        icon={<ExternalLink className="h-3.5 w-3.5" />}
        label={t("buttons.open_workshop")}
        onClick={() => void props.openWorkshopPage()}
      />
    ),
  });

  // Copy ID button - show for both installed and workshop items
  const copyIdHandle = installedHandle || (props.kind === "workshop" ? props.item : null);
  if (copyIdHandle) {
    buttons.push({
      key: "id",
      node: (
        <ActionBtn
          icon={<Copy className="h-3.5 w-3.5" />}
          label="ID"
          onClick={async () => {
            if (typeof navigator !== "undefined" && navigator.clipboard) {
              await navigator.clipboard.writeText(copyIdHandle.pubfileid);
              pushToast(t("messages.copied") || "Copied", "success");
            }
          }}
        />
      ),
    });
  }

  return (
    <>
      <div className="flex flex-wrap items-center gap-1">
        {buttons.map((b) => (
          <span key={b.key}>{b.node}</span>
        ))}
      </div>
      <ConfirmDialog />
    </>
  );
}

function ActionBtn({
  icon,
  label,
  onClick,
  disabled,
  variant = "default",
  iconOnly = false,
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  disabled?: boolean;
  variant?: "default" | "primary" | "danger";
  iconOnly?: boolean;
}) {
  const cls =
    variant === "primary"
      ? "bg-primary text-primary-foreground hover:bg-primary/90"
      : variant === "danger"
        ? "text-danger hover:bg-danger/10"
        : "border border-border-strong hover:bg-surface-raised";
  
  const button = (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={iconOnly ? label : undefined}
      className={`inline-flex items-center gap-1 rounded-md ${
        iconOnly ? "px-1.5 py-1" : "px-2 py-1"
      } text-[11px] font-semibold disabled:opacity-50 ${cls}`}
    >
      {icon}
      {!iconOnly && label}
    </button>
  );

  if (iconOnly) {
    return (
      <Tooltip content={label} side="top">
        {button}
      </Tooltip>
    );
  }

  return button;
}
