import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import {
  ArrowDownAZ,
  ArrowUpAZ,
  ChevronDown,
  ChevronUp,
  Copy,
  FolderOpen,
  Package,
  Play,
  Search,
  SortAsc,
  Trash2,
  X,
} from "lucide-react";
import { open as openPath } from "@tauri-apps/plugin-dialog";

import PreviewImage from "@/components/common/PreviewImage";
import DetailsPanel from "@/components/common/DetailsPanel";
import Select from "@/components/common/Select";
import { useAppStore } from "@/stores/app";
import { inTauri, tryInvoke, tryInvokeOk } from "@/lib/tauri";
import { maybeMinimize } from "@/lib/window";
import { pushToast } from "@/stores/toasts";
import { useRefreshStore } from "@/stores/refresh";
import { InstalledWallpaper } from "@/types/workshop";
import { cn, formatBytes } from "@/lib/utils";
import {
  LOCAL_SORT_KEYS,
  LOCAL_SORT_OPTIONS,
  CATEGORY_KEYS,
  CATEGORIES,
  TYPE_KEYS,
  TYPES,
  AGE_RATING_KEYS,
  AGE_RATINGS,
  RESOLUTION_KEYS,
  RESOLUTIONS,
  MISC_TAG_KEYS,
  GENRE_TAG_KEYS,
  type LocalSortKey,
} from "@/lib/filterConfig";
import { useConfirm } from "@/hooks/useConfirm";
import { Tooltip } from "@/components/common/Tooltip";

export default function InstalledView() {
  const { t } = useTranslation();
  const { confirm, ConfirmDialog } = useConfirm();
  const weDirectory = useAppStore((s) => s.weDirectory);
  const [items, setItems] = useState<InstalledWallpaper[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [age, setAge] = useState<string>("");
  const [resolution, setResolution] = useState<string>("");
  const [tagFilters, setTagFilters] = useState<string[]>([]);
  const [excludedTagFilters, setExcludedTagFilters] = useState<string[]>([]);
  const [sort, setSort] = useState<LocalSortKey>("install_date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selected, setSelected] = useState<InstalledWallpaper | null>(null);
  const [metaMap, setMetaMap] = useState<Record<string, { tags?: unknown[] }>>(
    {},
  );

  const refresh = async () => {
    if (!inTauri) {
      setItems(makeMockInstalled());
      setLoading(false);
      return;
    }
    setLoading(true);
    const list = await tryInvoke<InstalledWallpaper[]>(
      "we_list_installed",
      undefined,
      [],
    );
    setItems(list ?? []);
    const meta = await tryInvoke<Record<string, { tags?: unknown[] }>>(
      "metadata_get_all",
      undefined,
      {},
    );
    setMetaMap(meta ?? {});
    setLoading(false);
  };

  useEffect(() => {
    void refresh();
  }, [weDirectory]);

  const refreshCounter = useRefreshStore((s) => s.counter);
  useEffect(() => {
    if (refreshCounter === 0) return;
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshCounter]);

  // Re-fetch cached metadata (without re-scanning disk) whenever the
  // details drawer closes — so tags pulled via workshop_get_item while the
  // drawer was open immediately populate the filter chips below.
  useEffect(() => {
    if (!inTauri || selected !== null) return;
    void (async () => {
      const meta = await tryInvoke<Record<string, { tags?: unknown[] }>>(
        "metadata_get_all",
        undefined,
        {},
      );
      if (meta) setMetaMap(meta);
    })();
  }, [selected]);

  const tagsFor = (item: InstalledWallpaper): Set<string> => {
    const set = new Set<string>(item.tags);
    const raw = metaMap[item.pubfileid]?.tags;
    if (Array.isArray(raw)) {
      for (const t of raw) {
        const label =
          typeof t === "string"
            ? t
            : typeof t === "object" && t && "tag" in t
              ? String((t as { tag?: unknown }).tag ?? "")
              : "";
        if (label) set.add(label);
      }
    }
    return set;
  };

  const metaFor = (item: InstalledWallpaper) =>
    metaMap[item.pubfileid] as
      | { rating_star_file?: string; posted_date?: string; updated_date?: string }
      | undefined;

  // Collapse every tag actually present on the local wallpapers (both from
  // `project.json` and the Workshop metadata cache) into a single Set. This
  // drives the Misc/Genre filter chips so users only see tags that will
  // actually narrow the current Installed list — the original PyQt6 app
  // behaved the same way.
  const presentTags = useMemo(() => {
    const set = new Set<string>();
    for (const it of items) {
      for (const tag of tagsFor(it)) set.add(tag);
    }
    return set;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items, metaMap]);

  const visibleMiscTags = useMemo(
    () => MISC_TAG_KEYS.filter((k) => presentTags.has(k)),
    [presentTags],
  );
  const visibleGenreTags = useMemo(
    () => GENRE_TAG_KEYS.filter((k) => presentTags.has(k)),
    [presentTags],
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let result = items.filter((item) => {
      if (q) {
        const inTitle = item.title.toLowerCase().includes(q);
        const inId = item.pubfileid.includes(q);
        if (!inTitle && !inId) return false;
      }
      const has = tagsFor(item);
      if (category && !has.has(category)) return false;
      if (typeFilter) {
        // Steam tags both Workshop "Type" and project.json's `type` (e.g. "scene"
        // / "video" / "web" / "application") — match either.
        const ft = item.file_type?.toLowerCase() ?? "";
        const want = typeFilter.toLowerCase();
        if (!has.has(typeFilter) && ft !== want) return false;
      }
      if (age && !has.has(age)) return false;
      if (resolution && !has.has(resolution)) return false;
      if (tagFilters.length > 0) {
        if (!tagFilters.every((f) => has.has(f))) return false;
      }
      if (excludedTagFilters.length > 0) {
        if (excludedTagFilters.some((f) => has.has(f))) return false;
      }
      return true;
    });
    const dir = sortOrder === "asc" ? 1 : -1;
    const ratingScore = (it: InstalledWallpaper) => {
      const star = metaFor(it)?.rating_star_file ?? "";
      const m = star.match(/(\d+)/);
      return m ? parseInt(m[1], 10) : 0;
    };
    const dateMs = (s?: string) => {
      if (!s) return 0;
      const t = Date.parse(s);
      return Number.isFinite(t) ? t : 0;
    };
    result = [...result].sort((a, b) => {
      switch (sort) {
        case "install_date":
          return (a.installed_ts - b.installed_ts) * dir;
        case "name":
          return (
            a.title.localeCompare(b.title, undefined, { sensitivity: "base" }) *
            dir
          );
        case "rating":
          return (ratingScore(a) - ratingScore(b)) * dir;
        case "size":
          return (a.size_bytes - b.size_bytes) * dir;
        case "posted_date":
          return (dateMs(metaFor(a)?.posted_date) - dateMs(metaFor(b)?.posted_date)) * dir;
        case "updated_date":
          return (dateMs(metaFor(a)?.updated_date) - dateMs(metaFor(b)?.updated_date)) * dir;
      }
    });
    return result;
  }, [
    items,
    search,
    category,
    typeFilter,
    age,
    resolution,
    tagFilters,
    sort,
    sortOrder,
    metaMap,
    excludedTagFilters,
  ]);

  const handleApply = async (item: InstalledWallpaper) => {
    if (!inTauri) {
      pushToast(`Apply ${item.pubfileid}`, "info");
      return;
    }
    const ok = await tryInvokeOk("we_apply", {
      projectPath: item.project_json_path,
      monitor: null,
      force: false,
    });
    pushToast(
      ok ? t("messages.wallpaper_applied") : t("messages.error"),
      ok ? "success" : "error",
    );
    if (ok) {
      void maybeMinimize();
    }
  };

  const handleDelete = async (item: InstalledWallpaper) => {
    if (inTauri) {
      // Block deletion of the currently-displayed wallpaper — Wallpaper
      // Engine still holds file handles and rmdir would half-complete.
      const active = await tryInvoke<string[]>(
        "we_active_pubfileids",
        undefined,
        [],
      );
      if ((active ?? []).includes(item.pubfileid)) {
        pushToast(
          t("messages.cannot_delete_active_single") ||
            "Wallpaper is currently active — switch first.",
          "error",
        );
        return;
      }
    }
    const confirmed = await confirm({
      title: t("tooltips.delete_wallpaper") || "Delete Wallpaper",
      message: t("messages.confirm_delete") || "Delete this wallpaper?\n\nThe wallpaper folder will be removed from your Wallpaper Engine library permanently. This action cannot be undone.",
      confirmLabel: t("buttons.delete") || "Delete",
      cancelLabel: t("buttons.cancel") || "Cancel",
      variant: "danger",
    });
    if (!confirmed) return;
    if (!inTauri) {
      setItems((prev) => prev.filter((i) => i.pubfileid !== item.pubfileid));
      pushToast(t("messages.wallpaper_deleted"), "success");
      return;
    }
    const ok = await tryInvokeOk("we_delete_wallpaper", {
      pubfileid: item.pubfileid,
    });
    if (ok) {
      pushToast(t("messages.wallpaper_deleted"), "success");
      await refresh();
      setSelected(null);
    } else {
      // Backend may also catch the active-wallpaper case (race: user
      // applied the wallpaper between our check and the delete call).
      pushToast(
        t("messages.cannot_delete_active_single") ||
          "Wallpaper is currently active — switch first.",
        "error",
      );
    }
  };

  const handleExtract = async (item: InstalledWallpaper) => {
    if (!item.has_pkg) {
      pushToast(t("messages.no_pkg_file"), "warning");
      return;
    }
    if (!inTauri) {
      pushToast(t("messages.extraction_started"), "success");
      return;
    }
    const folder = await openPath({ directory: true });
    if (!folder || Array.isArray(folder)) return;
    const ok = await tryInvokeOk("extract_start", {
      pubfileid: item.pubfileid,
      outputDir: folder,
    });
    pushToast(
      ok ? t("messages.extraction_started") : t("messages.error"),
      ok ? "success" : "error",
    );
  };

  const handleOpenFolder = async (item: InstalledWallpaper) => {
    if (!inTauri) return;
    await tryInvoke("open_path", { path: item.folder });
  };

  const handleCopyId = async (item: InstalledWallpaper) => {
    await navigator.clipboard.writeText(item.pubfileid);
    pushToast(t("messages.id_copied"), "success");
  };


  // Tristate cycle — idle → include → exclude → idle — matches the
  // Workshop / Collections FilterBar, so clicking a chip twice switches it
  // from "only show items with this tag" to "hide items with this tag",
  // and a third click resets it back to neutral.
  const toggleTag = (tag: string) => {
    const isIncluded = tagFilters.includes(tag);
    const isExcluded = excludedTagFilters.includes(tag);
    if (isExcluded) {
      setExcludedTagFilters((prev) => prev.filter((t) => t !== tag));
    } else if (isIncluded) {
      setTagFilters((prev) => prev.filter((t) => t !== tag));
      setExcludedTagFilters((prev) => [...prev, tag]);
    } else {
      setTagFilters((prev) => [...prev, tag]);
    }
  };

  const totalSize = filtered.reduce((sum, i) => sum + i.size_bytes, 0);
  const hasActiveFilters =
    tagFilters.length > 0 ||
    excludedTagFilters.length > 0 ||
    category !== "" ||
    typeFilter !== "" ||
    age !== "" ||
    resolution !== "" ||
    search.length > 0;
  const hasAnyExtraTags =
    visibleMiscTags.length > 0 || visibleGenreTags.length > 0;

  // Prepare options for Select components
  const sortOptions = LOCAL_SORT_KEYS.map((k) => ({
    value: k,
    label: t(`filters.local_sort.${k}`, LOCAL_SORT_OPTIONS[k]),
  }));

  const categoryOptions = CATEGORY_KEYS.map((k) => ({
    value: k,
    label: t(`filters.category.${k || "empty"}`, CATEGORIES[k] ?? k),
  }));

  const typeOptions = TYPE_KEYS.map((k) => ({
    value: k,
    label: t(`filters.type.${k || "empty"}`, TYPES[k] ?? k),
  }));

  const ageOptions = AGE_RATING_KEYS.map((k) => ({
    value: k,
    label: t(`filters.age_rating.${k || "empty"}`, AGE_RATINGS[k] ?? k),
  }));

  const resolutionOptions = RESOLUTION_KEYS.map((k) => ({
    value: k,
    label: t(
      `filters.resolution.${(k || "empty").replace(/ /g, "_")}`,
      RESOLUTIONS[k] ?? k,
    ),
  }));

  return (
    <div className="flex h-full flex-col">
      <div className={cn(
        "flex flex-col gap-2 bg-surface/60 px-4 py-3",
        !showAdvanced && "border-b border-border"
      )}>
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative min-w-[220px] flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-subtle" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input pl-9"
              placeholder={t("labels.search_placeholder")}
            />
          </div>
          <Tooltip
            content={
              sortOrder === "asc"
                ? t("tooltips.sort_asc") || "Ascending"
                : t("tooltips.sort_desc") || "Descending"
            }
            side="bottom"
          >
            <button
              type="button"
              onClick={() => setSortOrder((o) => (o === "asc" ? "desc" : "asc"))}
              className={cn(
                "flex h-[38px] items-center gap-2 rounded-md bg-surface-sunken border border-border px-3 py-2 text-sm outline-none hover:border-border-strong transition-colors",
              )}
            >
              <motion.span
                key={sortOrder}
                initial={{ rotate: -90, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                transition={{ duration: 0.18 }}
                className="inline-flex"
              >
                {sortOrder === "asc" ? (
                  <ArrowUpAZ className="h-4 w-4" />
                ) : (
                  <ArrowDownAZ className="h-4 w-4" />
                )}
              </motion.span>
            </button>
          </Tooltip>
          <Select
            value={sort}
            onValueChange={(v) => setSort(v as LocalSortKey)}
            options={sortOptions}
            icon={<SortAsc className="h-4 w-4 text-muted" />}
          />
          <Select
            value={category}
            onValueChange={(v) => setCategory(v)}
            options={categoryOptions}
          />
          <Select
            value={typeFilter}
            onValueChange={(v) => setTypeFilter(v)}
            options={typeOptions}
          />
          <Select
            value={age}
            onValueChange={(v) => setAge(v)}
            options={ageOptions}
          />
          <Select
            value={resolution}
            onValueChange={(v) => setResolution(v)}
            options={resolutionOptions}
          />
          <button
            type="button"
            onClick={() => setShowAdvanced((v) => !v)}
            className="btn-ghost text-xs"
            aria-expanded={showAdvanced}
            disabled={!hasAnyExtraTags}
          >
            {showAdvanced ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
            {t(showAdvanced ? "labels.less_filters" : "labels.more_filters")}
          </button>
          {hasActiveFilters && (
            <button
              type="button"
              className="btn-ghost text-xs"
              onClick={() => {
                setTagFilters([]);
                setExcludedTagFilters([]);
                setCategory("");
                setTypeFilter("");
                setAge("");
                setResolution("");
                setSearch("");
              }}
            >
              <X className="h-4 w-4" />
              {t("labels.clear")}
            </button>
          )}
        </div>
      </div>
      <AnimatePresence>
        {showAdvanced && (
          <>
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2, ease: "easeInOut" }}
            >
              {visibleMiscTags.length > 0 && (
                <FilterChipsRow
                  title={t("labels.miscellaneous") || "Miscellaneous"}
                  keys={visibleMiscTags}
                  active={tagFilters}
                  excluded={excludedTagFilters}
                  toggle={toggleTag}
                  isFirst={true}
                  isLast={visibleGenreTags.length === 0}
                />
              )}
            </motion.div>
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2, ease: "easeInOut", delay: 0.05 }}
            >
              {visibleGenreTags.length > 0 && (
                <FilterChipsRow
                  title={t("labels.genre") || "Genre"}
                  keys={visibleGenreTags}
                  active={tagFilters}
                  excluded={excludedTagFilters}
                  toggle={toggleTag}
                  isFirst={visibleMiscTags.length === 0}
                  isLast={true}
                />
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <div className="flex-1 overflow-auto px-4 py-3">
        {loading ? (
          <div className="flex h-64 items-center justify-center text-sm text-muted">
            {t("labels.loading_dots")}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex h-64 flex-col items-center justify-center gap-2 text-center text-sm text-muted">
            <Package className="h-10 w-10 text-subtle" />
            {t("labels.no_wallpapers_found")}
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            <div className="grid grid-cols-[repeat(auto-fill,minmax(190px,1fr))] gap-3">
              {filtered.map((item) => (
                <motion.article
                  key={item.pubfileid}
                  layout
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  transition={{ duration: 0.18 }}
                  onClick={() => setSelected(item)}
                  className={cn(
                    "card card-hover group overflow-hidden cursor-pointer",
                    selected?.pubfileid === item.pubfileid &&
                      "ring-2 ring-primary/70",
                  )}
                >
                  <div className="relative aspect-square overflow-hidden bg-surface-sunken">
                    <PreviewImage
                      src={item.preview}
                      alt={item.title}
                      className="h-full w-full scale-[1.02] object-cover transition-transform duration-500 ease-out group-hover:scale-110"
                    />
                    <div className="absolute right-2 top-2 flex flex-col gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                      <IconBtn
                        onClick={(e) => {
                          e.stopPropagation();
                          handleApply(item);
                        }}
                        tooltip={t("tooltips.install_wallpaper")}
                      >
                        <Play className="h-3.5 w-3.5" />
                      </IconBtn>
                      <IconBtn
                        onClick={(e) => {
                          e.stopPropagation();
                          handleExtract(item);
                        }}
                        tooltip={t("tooltips.extract_wallpaper")}
                        disabled={!item.has_pkg}
                      >
                        <Package className="h-3.5 w-3.5" />
                      </IconBtn>
                      <IconBtn
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenFolder(item);
                        }}
                        tooltip={t("tooltips.open_folder")}
                      >
                        <FolderOpen className="h-3.5 w-3.5" />
                      </IconBtn>
                      <IconBtn
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCopyId(item);
                        }}
                        tooltip={t("buttons.copy_id")}
                      >
                        <Copy className="h-3.5 w-3.5" />
                      </IconBtn>
                      <IconBtn
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(item);
                        }}
                        tooltip={t("tooltips.delete_wallpaper")}
                        kind="danger"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </IconBtn>
                    </div>
                  </div>
                  <div className="flex flex-col gap-0.5 px-2.5 py-2">
                    <h3
                      className="line-clamp-1 text-[13px] font-semibold leading-tight"
                      title={item.title}
                    >
                      {item.title}
                    </h3>
                    <div className="flex items-center justify-between text-[11px] text-muted">
                      {(() => {
                        const author =
                          (metaMap[item.pubfileid] as
                            | { author?: string }
                            | undefined)?.author || "";
                        return (
                          <span className="truncate" title={author || undefined}>
                            {author || "—"}
                          </span>
                        );
                      })()}
                      <span className="shrink-0">{formatBytes(item.size_bytes)}</span>
                    </div>
                  </div>
                </motion.article>
              ))}
            </div>
          </AnimatePresence>
        )}
      </div>

      <div className="flex items-center justify-between border-t border-border bg-surface/60 px-4 py-2 text-xs text-muted">
        <span>
          {t("labels.wallpapers_filtered", {
            filtered: filtered.length,
            total: items.length,
          })}
        </span>
        <span>{t("labels.total_size", { size: formatBytes(totalSize) })}</span>
      </div>

      <DetailsPanel
        kind="installed"
        item={selected}
        onClose={() => setSelected(null)}
        onApply={handleApply}
        onExtract={handleExtract}
        onDelete={handleDelete}
        onOpenFolder={handleOpenFolder}
        onCopyId={handleCopyId}
      />
      <ConfirmDialog />
    </div>
  );
}

function FilterChipsRow({
  title,
  keys,
  active,
  excluded,
  toggle,
  isFirst,
  isLast,
}: {
  title: string;
  keys: readonly string[];
  active: string[];
  excluded: string[];
  toggle: (k: string) => void;
  isFirst?: boolean;
  isLast?: boolean;
}) {
  return (
    <div className={cn(
      "flex flex-wrap items-center gap-1.5 bg-surface/60 px-4 py-1",
      isFirst && "pt-1",
      isLast && "pb-2 border-b border-border"
    )}>
      <span className="text-[11px] uppercase tracking-wide text-subtle">
        {title}
      </span>
      {keys.map((k) => {
        const isIncluded = active.includes(k);
        const isExcluded = excluded.includes(k);
        return (
          <button
            key={k}
            type="button"
            onClick={() => toggle(k)}
            className={cn(
              "chip cursor-pointer select-none text-[11px] transition-colors",
              isIncluded &&
                "border-primary/60 bg-primary/15 text-foreground",
              isExcluded &&
                "border-danger/60 bg-danger/10 text-danger line-through",
            )}
          >
            {k}
          </button>
        );
      })}
    </div>
  );
}

function IconBtn({
  onClick,
  children,
  tooltip,
  disabled,
  kind = "default",
}: {
  onClick: (e: React.MouseEvent) => void;
  children: React.ReactNode;
  tooltip: string;
  disabled?: boolean;
  kind?: "default" | "danger";
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={tooltip}
      className={cn(
        "flex h-7 w-7 items-center justify-center rounded-md bg-background/80 text-foreground shadow ring-1 ring-border backdrop-blur transition-colors",
        disabled && "opacity-40 cursor-not-allowed",
        kind === "danger" && "text-danger",
      )}
    >
      {children}
    </button>
  );
}

function makeMockInstalled(): InstalledWallpaper[] {
  return Array.from({ length: 6 }, (_, i) => ({
    pubfileid: `${2000000 + i}`,
    folder: `/mock/projects/myprojects/${2000000 + i}`,
    project_json_path: `/mock/projects/myprojects/${2000000 + i}/project.json`,
    has_pkg: i % 2 === 0,
    title: `Installed Wallpaper #${i + 1}`,
    preview: "",
    description:
      "Mock description shown when running outside Tauri. Includes more information about the wallpaper.",
    file_type: i % 3 === 0 ? "scene" : i % 3 === 1 ? "video" : "web",
    tags: i % 2 === 0 ? ["Anime", "3D"] : ["Nature", "Abstract"],
    size_bytes: (i + 1) * 30 * 1024 * 1024,
    installed_ts: Date.now() / 1000 - i * 86400,
  }));
}
