import { useTranslation } from "react-i18next";
import { AnimatePresence, motion } from "framer-motion";
import {
  ChevronDown,
  ChevronUp,
  Search,
  SortAsc,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";

import Select from "@/components/common/Select";
import {
  AGE_RATINGS,
  ASSET_GENRES,
  ASSET_TYPES,
  CATEGORIES,
  GENRE_TAGS,
  MISC_TAGS,
  RESOLUTIONS,
  SCRIPT_TYPES,
  SORT_OPTIONS,
  TIME_PERIODS,
  TYPES,
} from "@/lib/filter-options";
import { cn } from "@/lib/utils";
import { DEFAULT_FILTERS, useFiltersStore } from "@/stores/filters";

export default function FilterBar() {
  const { t } = useTranslation();
  const filters = useFiltersStore((s) => s.filters);
  const setFilters = useFiltersStore((s) => s.setFilters);
  const resetFilters = useFiltersStore((s) => s.resetFilters);
  const showAdvanced = useFiltersStore((s) => s.showAdvanced);
  const toggleAdvanced = useFiltersStore((s) => s.toggleAdvanced);

  // "Clear filters" should only be visible when something is actually set —
  // matches Installed's behaviour so the row stays calm at rest.
  const hasActiveFilters =
    filters.search !== DEFAULT_FILTERS.search ||
    filters.sort !== DEFAULT_FILTERS.sort ||
    filters.days !== DEFAULT_FILTERS.days ||
    filters.category !== DEFAULT_FILTERS.category ||
    filters.type_tag !== DEFAULT_FILTERS.type_tag ||
    filters.age_rating !== DEFAULT_FILTERS.age_rating ||
    filters.resolution !== DEFAULT_FILTERS.resolution ||
    filters.asset_type !== DEFAULT_FILTERS.asset_type ||
    filters.asset_genre !== DEFAULT_FILTERS.asset_genre ||
    filters.script_type !== DEFAULT_FILTERS.script_type ||
    filters.misc_tags.length > 0 ||
    filters.genre_tags.length > 0 ||
    filters.excluded_misc_tags.length > 0 ||
    filters.excluded_genre_tags.length > 0 ||
    filters.required_flags.length > 0;

  const [searchValue, setSearchValue] = useState(filters.search);

  useEffect(() => {
    setSearchValue(filters.search);
  }, [filters.search]);

  useEffect(() => {
    const t = setTimeout(() => {
      if (searchValue !== filters.search) {
        setFilters({ search: searchValue, page: 1 });
      }
    }, 400);
    return () => clearTimeout(t);
  }, [searchValue, filters.search, setFilters]);

  const toggleTag = (list: "misc_tags" | "genre_tags", tag: string) => {
    const current = filters[list];
    const next = current.includes(tag)
      ? current.filter((t) => t !== tag)
      : [...current, tag];
    setFilters({ [list]: next, page: 1 } as any);
  };

  return (
    <>
      <div className={cn(
        "flex flex-col gap-2 bg-surface/60 px-4 py-3",
        !showAdvanced && "border-b border-border"
      )}>
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-subtle" />
            <input
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              placeholder={t("labels.search_placeholder")}
              className="input pl-9"
            />
          </div>
          <Select
            value={filters.sort}
            onValueChange={(v) => setFilters({ sort: v, page: 1 })}
            options={SORT_OPTIONS}
            icon={<SortAsc className="h-4 w-4 text-muted" />}
          />
          {filters.sort === "trend" && (
            <Select
              value={filters.days}
              onValueChange={(v) => setFilters({ days: v, page: 1 })}
              options={TIME_PERIODS}
            />
          )}
          <Select
            value={filters.category}
            onValueChange={(v) => setFilters({ category: v, page: 1 })}
            options={CATEGORIES}
          />
          {filters.category !== "Asset" && (
            <Select
              value={filters.type_tag}
              onValueChange={(v) => setFilters({ type_tag: v, page: 1 })}
              options={TYPES}
            />
          )}
          {filters.category === "Wallpaper" && (
            <Select
              value={filters.resolution}
              onValueChange={(v) => setFilters({ resolution: v, page: 1 })}
              options={RESOLUTIONS}
            />
          )}
          {filters.category === "Asset" && (
            <>
              <Select
                value={filters.asset_type}
                onValueChange={(v) => setFilters({ asset_type: v, page: 1 })}
                options={ASSET_TYPES}
              />
              <Select
                value={filters.asset_genre}
                onValueChange={(v) => setFilters({ asset_genre: v, page: 1 })}
                options={ASSET_GENRES}
              />
              <Select
                value={filters.script_type}
                onValueChange={(v) => setFilters({ script_type: v, page: 1 })}
                options={SCRIPT_TYPES}
              />
            </>
          )}
          <Select
            value={filters.age_rating}
            onValueChange={(v) => setFilters({ age_rating: v, page: 1 })}
            options={AGE_RATINGS}
          />
          <button
            onClick={toggleAdvanced}
            className="btn-ghost text-xs"
            aria-expanded={showAdvanced}
          >
            {showAdvanced ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
            {t(showAdvanced ? "labels.less_filters" : "labels.more_filters")}
          </button>
          {hasActiveFilters && (
            <button onClick={resetFilters} className="btn-ghost text-xs">
              <X className="h-4 w-4" /> {t("labels.clear")}
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
              <TagBlock
                title={t("labels.miscellaneous")}
                tags={MISC_TAGS}
                included={filters.misc_tags}
                excluded={filters.excluded_misc_tags}
                onToggleInclude={(tag) => toggleTag("misc_tags", tag)}
                onToggleExclude={(tag) => {
                  const current = filters.excluded_misc_tags;
                  const next = current.includes(tag)
                    ? current.filter((t) => t !== tag)
                    : [...current, tag];
                  setFilters({ excluded_misc_tags: next, page: 1 });
                }}
                isFirst={true}
                isLast={false}
              />
            </motion.div>
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2, ease: "easeInOut", delay: 0.05 }}
            >
              <TagBlock
                title={t("labels.genre")}
                tags={GENRE_TAGS}
                included={filters.genre_tags}
                excluded={filters.excluded_genre_tags}
                onToggleInclude={(tag) => toggleTag("genre_tags", tag)}
                onToggleExclude={(tag) => {
                  const current = filters.excluded_genre_tags;
                  const next = current.includes(tag)
                    ? current.filter((t) => t !== tag)
                    : [...current, tag];
                  setFilters({ excluded_genre_tags: next, page: 1 });
                }}
                isFirst={false}
                isLast={true}
              />
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

function TagBlock({
  title,
  tags,
  included,
  excluded,
  onToggleInclude,
  onToggleExclude,
  isFirst,
  isLast,
}: {
  title: string;
  tags: string[];
  included: string[];
  excluded: string[];
  onToggleInclude: (tag: string) => void;
  onToggleExclude: (tag: string) => void;
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
      {tags.map((tag) => {
        const isIncluded = included.includes(tag);
        const isExcluded = excluded.includes(tag);
        return (
          <button
            key={tag}
            onClick={() => {
              if (isExcluded) {
                onToggleExclude(tag);
              } else if (isIncluded) {
                onToggleInclude(tag);
                onToggleExclude(tag);
              } else {
                onToggleInclude(tag);
              }
            }}
            className={cn(
              "chip cursor-pointer select-none text-[11px] transition-colors",
              !isIncluded && !isExcluded && "hover:bg-surface",
              isIncluded &&
                "border-primary/60 bg-primary/15 text-foreground",
              isExcluded &&
                "border-danger/60 bg-danger/10 text-danger line-through",
            )}
          >
            {tag}
          </button>
        );
      })}
    </div>
  );
}
