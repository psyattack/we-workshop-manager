import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import Sidebar, { NavKey } from "@/components/layout/Sidebar";
import TitleBar from "@/components/layout/TitleBar";
import TopBar from "@/components/layout/TopBar";
import WorkshopView from "@/components/views/WorkshopView";
import CollectionsView from "@/components/views/CollectionsView";
import InstalledView from "@/components/views/InstalledView";
import AuthorView from "@/components/views/AuthorView";
import SettingsDialog from "@/components/settings/SettingsDialog";
import MultiDownloadDialog from "@/components/dialogs/MultiDownloadDialog";
import InfoDialog from "@/components/dialogs/InfoDialog";
import UpdateDialog from "@/components/dialogs/UpdateDialog";
import TasksDrawer from "@/components/tasks/TasksDrawer";
import ToastStack from "@/components/common/ToastStack";
import { useBootstrap } from "@/hooks/useBootstrap";
import { useApplyTheme } from "@/hooks/useTheme";
import { useAppStore } from "@/stores/app";
import { useNavStore } from "@/stores/nav";
import { useFiltersStore } from "@/stores/filters";

export default function App() {
  useBootstrap();
  useApplyTheme();
  const ready = useAppStore((s) => s.ready);
  const sub = useNavStore((s) => s.sub);
  const resetNav = useNavStore((s) => s.reset);

  const [view, setView] = useState<NavKey>("workshop");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [multiOpen, setMultiOpen] = useState(false);
  const [infoOpen, setInfoOpen] = useState(false);
  const [updateOpen, setUpdateOpen] = useState(false);
  const [tasksOpen, setTasksOpen] = useState(false);

  const setPage = useFiltersStore((s) => s.setPage);

  // Clear any sub-view stack whenever the user switches primary nav by hand
  // and drop paging. We intentionally don't wipe sort/misc_tags/etc so that
  // a user who built up a filter in Workshop keeps it when they pop over to
  // Installed and back; the "tab shows nothing" bug was really driven by
  // `view` being force-mutated to "collections" when a sub-view opened —
  // that's fixed below via `activeKey` deriving from `sub.kind` directly.
  const changeView = (key: NavKey) => {
    resetNav();
    setPage(1);
    setView(key);
  };

  // Whenever we leave a sub-view (back to none) reset paging too — the
  // author view scrolls past the main grid's last page in many cases.
  useEffect(() => {
    if (sub.kind === "none") setPage(1);
  }, [sub.kind, setPage]);

  // Derive the mounted view entirely from state; we used to mutate `view`
  // when a collection was opened, which meant that closing the collection
  // left the user stranded on the Collections tab instead of returning to
  // whichever primary tab (Installed / Workshop / Collections) they were
  // actually on. Treat collection/author as pure sub-view overlays that
  // don't clobber the primary tab selection.
  const activeKey: NavKey | "author" =
    sub.kind === "author"
      ? "author"
      : sub.kind === "collection"
        ? "collections"
        : view;

  return (
    <div className="flex h-screen w-full flex-col overflow-hidden bg-background text-foreground">
      <TitleBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar current={view} onChange={changeView} />
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar
            onOpenSettings={() => setSettingsOpen(true)}
            onOpenMulti={() => setMultiOpen(true)}
            onOpenInfo={() => setInfoOpen(true)}
            onOpenTasks={() => setTasksOpen(true)}
          />
          <main
            className="relative flex-1 overflow-hidden"
          >
            <AnimatePresence mode="wait">
              {ready && activeKey === "workshop" && (
                <ViewWrap key="workshop">
                  <WorkshopView />
                </ViewWrap>
              )}
              {ready && activeKey === "collections" && (
                <ViewWrap key="collections">
                  <CollectionsView />
                </ViewWrap>
              )}
              {ready && activeKey === "installed" && (
                <ViewWrap key="installed">
                  <InstalledView />
                </ViewWrap>
              )}
              {ready && activeKey === "author" && (
                <ViewWrap key="author">
                  <AuthorView />
                </ViewWrap>
              )}
            </AnimatePresence>
            {!ready && <BootLoader />}
          </main>
        </div>
      </div>

      <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
      <MultiDownloadDialog open={multiOpen} onOpenChange={setMultiOpen} />
      <InfoDialog
        open={infoOpen}
        onOpenChange={setInfoOpen}
        onCheckUpdates={() => setUpdateOpen(true)}
      />
      <UpdateDialog open={updateOpen} onOpenChange={setUpdateOpen} />
      <TasksDrawer open={tasksOpen} onOpenChange={setTasksOpen} />
      <ToastStack />
    </div>
  );
}

function ViewWrap({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.18 }}
      className="absolute inset-0 overflow-hidden"
    >
      {children}
    </motion.div>
  );
}

function BootLoader() {
  return (
    <div className="flex h-full items-center justify-center">
      <motion.div
        className="h-10 w-10 rounded-full border-2 border-primary border-t-transparent"
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 0.9, ease: "linear" }}
      />
    </div>
  );
}
