import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";

import {
  FolderHeart,
  Globe,
  Layers,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useAppStore } from "@/stores/app";
import AppIcon from "@/assets/icon.svg?react";

export type NavKey = "workshop" | "collections" | "installed";

interface SidebarProps {
  current: NavKey;
  onChange: (key: NavKey) => void;
}

const NAV: { key: NavKey; icon: typeof Globe; labelKey: string }[] = [
  { key: "workshop", icon: Globe, labelKey: "tabs.workshop" },
  { key: "collections", icon: Layers, labelKey: "tabs.collections" },
  { key: "installed", icon: FolderHeart, labelKey: "tabs.wallpapers" },
];

export default function Sidebar({ current, onChange }: SidebarProps) {
  const { t } = useTranslation();
  const collapsed = useAppStore((s) => s.sidebarCollapsed);
  const toggle = useAppStore((s) => s.toggleSidebar);



  return (
    <aside
      className={cn(
        "flex shrink-0 flex-col gap-2 border-r border-border bg-surface-sunken py-4 transition-[width] duration-200 ease-out",
        collapsed
          ? "w-[64px] items-center px-1"
          : "w-[165px] items-stretch px-3",
      )}
    >
      <div
        className={cn(
          "mb-2 flex items-center gap-2",
          collapsed ? "justify-center px-0" : "px-1",
        )}
      >
        <div className="flex h-9 w-9 items-center justify-center">
          <AppIcon className="h-9 w-9" />
        </div>
        {!collapsed && (
          <div className="flex flex-col">
            <span className="text-sm font-semibold tracking-tight">WEave</span>
            <span className="text-[11px] text-subtle">Wallpaper Engine</span>
          </div>
        )}
      </div>

      <nav className="flex flex-col gap-1">
        {NAV.map((item) => {
          const Icon = item.icon;
          const active = item.key === current;
          return (
            <button
              key={item.key}
              onClick={() => onChange(item.key)}
              className={cn(
                "nav-item relative",
                collapsed ? "justify-center" : "justify-start",
                active && "nav-item-active",
              )}
              aria-current={active ? "page" : undefined}
            >
              {active && (
                <motion.span
                  layoutId="nav-indicator"
                  className="absolute inset-0 -z-10 rounded-md bg-primary/10"
                  transition={{
                    type: "spring",
                    stiffness: 380,
                    damping: 32,
                  }}
                />
              )}
              <Icon className="h-5 w-5 shrink-0" />
              {!collapsed && <span>{t(item.labelKey)}</span>}
            </button>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-2">
        <button
          type="button"
          onClick={toggle}
          className={cn(
            "nav-item text-subtle hover:text-foreground",
            collapsed ? "justify-center" : "justify-start",
          )}
        >
          {collapsed ? (
            <PanelLeftOpen className="h-5 w-5 shrink-0" />
          ) : (
            <PanelLeftClose className="h-5 w-5 shrink-0" />
          )}
          {!collapsed && <span>{t("tooltips.collapse_sidebar")}</span>}
        </button>
      </div>
    </aside>
  );
}
