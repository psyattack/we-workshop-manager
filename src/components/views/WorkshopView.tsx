import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { useTranslation } from "react-i18next";

import FilterBar from "@/components/workshop/FilterBar";
import Pagination from "@/components/workshop/Pagination";
import WorkshopCard from "@/components/workshop/WorkshopCard";
import DetailsPanel from "@/components/common/DetailsPanel";
import { SkeletonCard } from "@/components/common/Skeleton";
import { useFiltersStore } from "@/stores/filters";
import { useAppStore } from "@/stores/app";
import { pushToast } from "@/stores/toasts";
import { useRefreshStore } from "@/stores/refresh";
import { inTauri, tryInvoke, tryInvokeOk } from "@/lib/tauri";
import type { WorkshopFilters } from "@/stores/filters";
import { WorkshopItem, WorkshopPage } from "@/types/workshop";

export default function WorkshopView() {
  const { t } = useTranslation();
  const filters = useFiltersStore((s) => s.filters);
  const setPage = useFiltersStore((s) => s.setPage);
  const setViewPage = useFiltersStore((s) => s.setViewPage);
  const getViewPage = useFiltersStore((s) => s.getViewPage);
  const accountIndex = useAppStore((s) => s.accountIndex);
  const [page, setPageData] = useState<WorkshopPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<WorkshopItem | null>(null);

  // Get the saved page for workshop view
  const currentPage = getViewPage("workshop");

  // Sync filters.page with the view-specific page
  useEffect(() => {
    if (filters.page !== currentPage) {
      setPage(currentPage);
    }
  }, [currentPage, filters.page, setPage]);

  const filtersKey = useMemo(() => JSON.stringify(filters), [filters]);
  const refreshCounter = useRefreshStore((s) => s.counter);
  // Preloaded next-page cache. Keyed on the filters JSON so it survives
  // pagination but is invalidated the moment any filter / sort / search
  // changes. Reset on `workshop_refresh_cache` too (via refreshCounter).
  const cacheRef = useRef<Map<string, WorkshopPage>>(new Map());
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Whenever cache is forcibly refreshed from the outside, drop the
    // preload cache — the pages in it may be stale.
    cacheRef.current.clear();
  }, [refreshCounter]);

  useEffect(() => {
    // Reset scroll to top when page changes
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [filters.page]);

  useEffect(() => {
    let active = true;

    const cached = cacheRef.current.get(filtersKey);
    if (cached) {
      setPageData(cached);
      setLoading(false);
    } else {
      setLoading(true);
    }

    void (async () => {
      if (!inTauri) {
        setPageData(makeMockPage(filters.page));
        setLoading(false);
        return;
      }
      if (refreshCounter > 0) {
        await tryInvokeOk("workshop_refresh_cache");
      }
      let result = cached;
      if (!result) {
        result =
          (await tryInvoke<WorkshopPage>("workshop_browse", { filters })) ??
          undefined;
        if (result) cacheRef.current.set(filtersKey, result);
      }
      if (!active) return;
      setPageData(result ?? null);
      setLoading(false);

      // Background preload of the next page (if enabled + available).
      if (result && result.total_pages > filters.page) {
        const preloadOn = await tryInvoke<boolean>(
          "config_get",
          { path: "settings.general.behavior.preload_next_page" },
          true,
        );
        if (preloadOn === false) return;
        const nextFilters: WorkshopFilters = {
          ...filters,
          page: filters.page + 1,
        };
        const nextKey = JSON.stringify(nextFilters);
        if (!cacheRef.current.has(nextKey)) {
          void tryInvoke<WorkshopPage>("workshop_browse", {
            filters: nextFilters,
          }).then((next) => {
            if (next) cacheRef.current.set(nextKey, next);
          });
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [filtersKey, refreshCounter]);

  const items = page?.items ?? [];
  const total = page?.total_items ?? 0;
  const totalPages = page?.total_pages ?? 1;

  const handleDownload = async (item: WorkshopItem) => {
    if (item.is_collection) {
      setSelected(item);
      return;
    }
    if (!inTauri) {
      pushToast(t("messages.download_started"), "success");
      return;
    }
    const ok = await tryInvokeOk("download_start", {
      pubfileid: item.pubfileid,
      accountIndex,
    });
    pushToast(
      ok
        ? t("messages.download_started")
        : t("messages.error"),
      ok ? "success" : "error",
    );
  };

  return (
    <div className="flex h-full flex-col">
      <FilterBar />
      <div ref={scrollContainerRef} className="flex-1 overflow-auto px-4 py-3">
        {loading ? (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(190px,1fr))] gap-3">
            {Array.from({ length: 12 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="flex h-64 items-center justify-center text-sm text-muted">
            {t("labels.no_wallpapers_found")}
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            <div className="grid grid-cols-[repeat(auto-fill,minmax(190px,1fr))] gap-3">
              {items.map((item) => (
                <WorkshopCard
                  key={item.pubfileid}
                  item={item}
                  onOpen={setSelected}
                  onDownload={handleDownload}
                />
              ))}
            </div>
          </AnimatePresence>
        )}
      </div>
      <Pagination
        page={filters.page}
        totalPages={totalPages}
        onChange={(newPage) => {
          setPage(newPage);
          setViewPage("workshop", newPage);
        }}
        infoText={
          total
            ? t("labels.showing_wallpapers", {
                start: (filters.page - 1) * 30 + 1,
                end: (filters.page - 1) * 30 + items.length,
                total,
              })
            : ""
        }
      />
      <DetailsPanel
        kind="workshop"
        item={selected}
        onClose={() => setSelected(null)}
        onDownload={handleDownload}
      />
    </div>
  );
}

function makeMockPage(page: number): WorkshopPage {
  const items: WorkshopItem[] = Array.from({ length: 18 }, (_, i) => ({
    pubfileid: `${100000 + (page - 1) * 18 + i}`,
    title: `Sample Wallpaper #${(page - 1) * 18 + i + 1}`,
    preview_url: "",
    author: "Mock Author",
    author_url: "",
    description:
      "This is a mock wallpaper description shown when running outside of Tauri.",
    file_size: "42.5 MB",
    posted_date: "2024-01-01",
    updated_date: "2024-05-05",
    tags: [{ tag: "Scene" }, { tag: "3D" }],
    rating_star_file: "",
    num_ratings: `${100 + i}`,
    is_collection: i === 4,
  }));
  return {
    items,
    total_items: 500,
    total_pages: 10,
    current_page: page,
  };
}
