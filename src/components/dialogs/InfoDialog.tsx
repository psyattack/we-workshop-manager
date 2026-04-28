import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { openUrl as openExternal } from "@tauri-apps/plugin-opener";
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  FolderOpen,
  Github,
  Loader2,
  RefreshCw,
} from "lucide-react";

import Dialog from "@/components/common/Dialog";
import Markdown from "@/components/common/Markdown";
import { inTauri, invoke, tryInvoke } from "@/lib/tauri";
import AppIcon from "@/assets/icon.svg?react";

interface GithubRelease {
  tag_name: string;
  name: string;
  body: string;
  html_url: string;
  published_at?: string;
  prerelease?: boolean;
}

const RELEASES_URL = "https://api.github.com/repos/psyattack/WEave/releases";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCheckUpdates?: () => void;
}

const TOOLS: { label: string; url: string }[] = [
  { label: "Tauri", url: "https://v2.tauri.app/" },
  { label: "React", url: "https://react.dev/" },
  {
    label: "DepotDownloaderMod",
    url: "https://gitlab.com/steamautocracks/DepotDownloaderMod",
  },
  { label: "RePKG", url: "https://github.com/notscuffed/repkg" },
];

export default function InfoDialog({
  open,
  onOpenChange,
  onCheckUpdates,
}: Props) {
  const { t } = useTranslation();
  const [version, setVersion] = useState<string>("");
  const [dataDir, setDataDir] = useState<string>("");
  const [showChangelog, setShowChangelog] = useState(false);
  const [releases, setReleases] = useState<GithubRelease[] | null>(null);
  const [selectedTag, setSelectedTag] = useState<string>("");
  const [changelogError, setChangelogError] = useState<string | null>(null);
  const [loadingReleases, setLoadingReleases] = useState(false);

  useEffect(() => {
    if (!open || !inTauri) return;
    void tryInvoke<{ version: string; name: string }>("app_get_info").then(
      (v) => {
        if (v?.version) setVersion(v.version);
      },
    );
    void tryInvoke<string>("app_get_data_dir", undefined, "").then((p) => {
      if (p) setDataDir(p);
    });
  }, [open]);

  // Reset the changelog on every open so stale data from a previous
  // session (e.g. a network hiccup) doesn't stick around.
  useEffect(() => {
    if (!open) {
      setShowChangelog(false);
      setChangelogError(null);
    }
  }, [open]);

  const loadReleases = async () => {
    setLoadingReleases(true);
    setChangelogError(null);
    try {
      const res = await fetch(RELEASES_URL, {
        headers: { Accept: "application/vnd.github+json" },
      });
      if (!res.ok) {
        throw new Error(`GitHub API ${res.status}`);
      }
      const data = (await res.json()) as GithubRelease[];
      const list = Array.isArray(data) ? data : [];
      setReleases(list);
      if (list.length > 0 && !selectedTag) {
        setSelectedTag(list[0].tag_name);
      }
    } catch (err) {
      setChangelogError(
        err instanceof Error ? err.message : String(err ?? "unknown error"),
      );
    } finally {
      setLoadingReleases(false);
    }
  };

  const toggleChangelog = () => {
    const next = !showChangelog;
    setShowChangelog(next);
    if (next && !releases && !loadingReleases) {
      void loadReleases();
    }
  };

  const selectedRelease =
    releases?.find((r) => r.tag_name === selectedTag) ?? null;

  const openLink = async (url: string) => {
    if (inTauri) await openExternal(url);
    else window.open(url, "_blank");
  };

  const openDataFolder = async () => {
    if (!inTauri) return;
    await invoke("app_open_data_dir").catch(() => undefined);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={t("dialog.about")}
      size="sm"
    >
      <div className="flex flex-col items-center gap-3 text-center">
        <AppIcon className="h-32 w-32" />
        <div className="space-y-1">
          <div className="text-lg font-semibold">
            {t("info.app_full_name")}
          </div>
          <div className="text-xs text-muted">
            {t("info.version_label")}{" "}
            <span className="text-foreground">{version || "—"}</span>
          </div>
        </div>
        <p className="text-sm text-muted">
          {t("info.description")}
        </p>
        <p className="text-xs text-subtle">
          {t("info.developed")} —{" "}
          <button
            type="button"
            className="text-primary hover:underline"
            onClick={() =>
              openLink(`https://github.com/${t("info.author") || "psyattack"}`)
            }
          >
            {t("info.author")}
          </button>
        </p>

        <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
          <button
            className="btn-outline"
            onClick={() => openLink("https://github.com/psyattack/WEave")}
          >
            <Github className="h-4 w-4" />
            {t("buttons.github")}
          </button>
          <button
            className="btn-outline"
            onClick={() => {
              if (onCheckUpdates) {
                onOpenChange(false);
                onCheckUpdates();
              }
            }}
          >
            <RefreshCw className="h-4 w-4" />
            {t("buttons.check_updates")}
          </button>
          <button
            className="btn-outline"
            onClick={openDataFolder}
            disabled={!inTauri}
            title={dataDir}
          >
            <FolderOpen className="h-4 w-4" />
            {t("buttons.open_data_folder")}
          </button>
          <button
            className="btn-outline"
            onClick={toggleChangelog}
            aria-expanded={showChangelog}
          >
            <BookOpen className="h-4 w-4" />
            {t("buttons.changelog") || "Changelog"}
            {showChangelog ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
          </button>
        </div>

        {showChangelog && (
          <div className="w-full rounded-md border border-border bg-surface-sunken p-3 text-left">
            <div className="mb-2 flex items-center justify-between gap-2">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-subtle">
                {t("info.changelog_title") || "Release notes"}
              </div>
              <div className="flex items-center gap-1">
                <select
                  className="input h-9 w-auto text-xs disabled:opacity-50"
                  value={selectedTag}
                  onChange={(e) => setSelectedTag(e.target.value)}
                  disabled={!releases || releases.length === 0}
                >
                  {(releases ?? []).map((r) => (
                    <option key={r.tag_name} value={r.tag_name}>
                      {r.tag_name}
                      {r.prerelease ? " (pre)" : ""}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className="btn-ghost px-1.5 text-[11px]"
                  onClick={() => void loadReleases()}
                  disabled={loadingReleases}
                  title={t("buttons.refresh") || "Refresh"}
                >
                  <RefreshCw
                    className={`h-3.5 w-3.5 ${
                      loadingReleases ? "animate-spin" : ""
                    }`}
                  />
                </button>
              </div>
            </div>

            {loadingReleases && !releases && (
              <div className="flex items-center gap-2 py-2 text-xs text-muted">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                {t("labels.loading") || "Loading…"}
              </div>
            )}
            {changelogError && (
              <div className="py-2 text-xs text-danger">
                {t("messages.changelog_error", { error: changelogError }) ||
                  `Failed to load changelog: ${changelogError}`}
              </div>
            )}
            {!loadingReleases &&
              !changelogError &&
              releases &&
              releases.length === 0 && (
                <div className="py-2 text-xs text-muted">
                  {t("messages.no_releases") || "No releases published yet."}
                </div>
              )}
            {selectedRelease && (
              <div className="max-h-72 overflow-auto pr-1">
                <div className="mb-1 flex items-center justify-between gap-2">
                  <div className="text-sm font-semibold">
                    {selectedRelease.name || selectedRelease.tag_name}
                  </div>
                  <button
                    type="button"
                    className="text-[11px] text-muted hover:text-primary"
                    onClick={() => openLink(selectedRelease.html_url)}
                    title={selectedRelease.html_url}
                  >
                    <ExternalLink className="inline h-3 w-3" />{" "}
                    {t("buttons.view_on_github") || "GitHub"}
                  </button>
                </div>
                {selectedRelease.published_at && (
                  <div className="mb-2 text-[10px] uppercase tracking-wide text-subtle">
                    {new Date(selectedRelease.published_at).toLocaleDateString()}
                  </div>
                )}
                <Markdown source={selectedRelease.body || ""} />
              </div>
            )}
          </div>
        )}

        <div className="w-full pt-3">
          <div className="mb-1 text-[11px] uppercase tracking-wide text-subtle">
            {t("info.tools_section_title")}
          </div>
          <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-xs">
            {TOOLS.map((tool) => (
              <button
                key={tool.label}
                type="button"
                className="inline-flex items-center gap-1 text-muted hover:text-primary"
                onClick={() => openLink(tool.url)}
              >
                {tool.label}
                <ExternalLink className="h-3 w-3" />
              </button>
            ))}
          </div>
        </div>

        {dataDir && (
          <div
            className="w-full overflow-hidden text-ellipsis text-[10px] text-subtle"
            title={dataDir}
          >
            {dataDir}
          </div>
        )}
      </div>
    </Dialog>
  );
}
