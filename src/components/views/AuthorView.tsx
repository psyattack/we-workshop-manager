import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { useTranslation } from "react-i18next";
import { ArrowLeft, Layers, User } from "lucide-react";

import WorkshopCard from "@/components/workshop/WorkshopCard";
import DetailsPanel from "@/components/common/DetailsPanel";
import Pagination from "@/components/workshop/Pagination";
import { SkeletonCard } from "@/components/common/Skeleton";
import { useFiltersStore } from "@/stores/filters";
import { useRefreshStore } from "@/stores/refresh";
import { useAppStore } from "@/stores/app";
import { useNavStore } from "@/stores/nav";
import { pushToast } from "@/stores/toasts";
import { inTauri, tryInvoke, tryInvokeOk } from "@/lib/tauri";
import { cn } from "@/lib/utils";
import { WorkshopItem, WorkshopPage } from "@/types/workshop";

type Tab = "items" | "collections";

export default function AuthorView() {
  const { t } = useTranslation();
  const filters = useFiltersStore((s) => s.filters);
  const setPage = useFiltersStore((s) => s.setPage);
  const setViewPage = useFiltersStore((s) => s.setViewPage);
  const getViewPage = useFiltersStore((s) => s.getViewPage);
  const accountIndex = useAppStore((s) => s.accountIndex);
  const sub = useNavStore((s) => s.sub);
  const navBack = useNavStore((s) => s.back);
  const openCollectionNav = useNavStore((s) => s.openCollection);

  const profileUrl = sub.kind === "author" ? sub.profileUrl : "";
  const displayName = sub.kind === "author" ? sub.displayName : "";

  const [tab, setTab] = useState<Tab>("items");
  const [page, setPageData] = useState<WorkshopPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<WorkshopItem | null>(null);

  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Get the saved page for this author
  const currentPage = getViewPage("author", profileUrl);

  // Sync filters.page with the view-specific page
  useEffect(() => {
    if (profileUrl && filters.page !== currentPage) {
      setPage(currentPage);
    }
  }, [profileUrl, currentPage, filters.page, setPage]);

  const key = useMemo(
    () => JSON.stringify({ u: profileUrl, t: tab, p: filters.page, s: filters.sort }),
    [profileUrl, tab, filters.page, filters.sort],
  );

  const refreshCounter = useRefreshStore((s) => s.counter);

  useEffect(() => {
    // Reset scroll to top when page changes
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [filters.page]);

  useEffect(() => {
    if (!profileUrl) return;
    let active = true;
    setLoading(true);
    void (async () => {
      if (!inTauri) {
        setPageData({
          items: [],
          total_items: 0,
          total_pages: 1,
          current_page: 1,
        });
        setLoading(false);
        return;
      }
      if (refreshCounter > 0) {
        await tryInvokeOk("workshop_refresh_cache");
      }
      const cmd =
        tab === "items"
          ? "workshop_get_author_items"
          : "workshop_get_author_collections";
      const result = await tryInvoke<WorkshopPage>(cmd, {
        profileUrl,
        filters,
      });
      if (!active) return;
      setPageData(result ?? null);
      setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, [key, profileUrl, tab, filters, refreshCounter]);

  const handleOpen = (item: WorkshopItem) => {
    if (tab === "collections") {
      openCollectionNav(item.pubfileid, item.title);
      return;
    }
    setSelected(item);
  };

  const handleDownload = async (item: WorkshopItem) => {
    if (item.is_collection) {
      openCollectionNav(item.pubfileid, item.title);
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
      ok ? t("messages.download_started") : t("messages.error"),
      ok ? "success" : "error",
    );
  };

  const items = page?.items ?? [];
  const totalPages = page?.total_pages ?? 1;

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-wrap items-center gap-2 border-b border-border bg-surface/60 px-4 py-3">
        <button className="btn-ghost" onClick={navBack}>
          <ArrowLeft className="h-4 w-4" />
          {t("labels.back")}
        </button>
        <User className="h-4 w-4 text-primary" />
        <span className="font-medium truncate">
          {displayName || t("labels.author", { author: "" }).replace(/:$/, "")}
        </span>

        <div className="ml-auto flex items-center gap-1 rounded-md border border-border bg-surface-sunken p-0.5">
          <TabButton active={tab === "items"} onClick={() => setTab("items")}>
            <User className="h-3.5 w-3.5" />
            {t("labels.wallpapers")}
          </TabButton>
          <TabButton
            active={tab === "collections"}
            onClick={() => setTab("collections")}
          >
            <Layers className="h-3.5 w-3.5" />
            {t("labels.author_collections")}
          </TabButton>
        </div>
      </div>

      <div ref={scrollContainerRef} className="flex-1 overflow-auto px-4 py-3">
        {loading ? (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(190px,1fr))] gap-3">
            {Array.from({ length: 12 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="flex h-64 items-center justify-center text-sm text-muted">
            {tab === "items"
              ? t("labels.no_wallpapers_found")
              : t("labels.no_collections_found")}
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            <div className="grid grid-cols-[repeat(auto-fill,minmax(190px,1fr))] gap-3">
              {items.map((item) => {
                // On the author's own workshop page Steam strips the "By
                // NAME" chip from each tile (redundant — it's the same
                // author for every card). Inject the author we already
                // know from the nav entry so the grid stays consistent
                // with Workshop/Collections/Installed.
                const withAuthor: WorkshopItem = {
                  ...item,
                  author: item.author || displayName,
                  author_url: item.author_url || profileUrl,
                  ...(tab === "collections" ? { is_collection: true } : null),
                };
                return (
                  <WorkshopCard
                    key={item.pubfileid}
                    item={withAuthor}
                    onOpen={handleOpen}
                    onDownload={handleDownload}
                    hideDownload={tab === "collections"}
                  />
                );
              })}
            </div>
          </AnimatePresence>
        )}
      </div>

      <Pagination
        page={filters.page}
        totalPages={totalPages}
        onChange={(newPage) => {
          setPage(newPage);
          setViewPage("author", newPage, profileUrl);
        }}
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

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex items-center gap-1 rounded-sm px-2.5 py-1 text-xs font-medium transition-colors",
        active
          ? "bg-primary text-primary-foreground"
          : "text-muted hover:text-foreground hover:bg-surface-raised",
      )}
    >
      {children}
    </button>
  );
}
