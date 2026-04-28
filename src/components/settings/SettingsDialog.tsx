import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { open as openPath } from "@tauri-apps/plugin-dialog";
import { Trash2 } from "lucide-react";

import Dialog from "@/components/common/Dialog";
import Tabs from "@/components/common/Tabs";
import Select from "@/components/common/Select";
import { Switch } from "@/components/common/Switch";
import ParserDebugDialog from "@/components/dialogs/ParserDebugDialog";
import { changeLanguageTo } from "@/hooks/useBootstrap";
import { persistTheme } from "@/hooks/useTheme";
import { inTauri, invoke, tryInvoke, tryInvokeOk } from "@/lib/tauri";
import { pushToast } from "@/stores/toasts";
import { triggerGlobalRefresh } from "@/stores/refresh";
import { ThemeCode, useAppStore } from "@/stores/app";
import { useConfirm } from "@/hooks/useConfirm";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const THEMES: { value: ThemeCode; label: string }[] = [
  { value: "dark", label: "Dark" },
  { value: "light", label: "Light" },
  { value: "nord", label: "Nord" },
  { value: "monokai", label: "Monokai" },
  { value: "solarized", label: "Solarized" },
];

const ACCENTS: { value: string; label: string; color: string }[] = [
  { value: "indigo", label: "Indigo", color: "#6366f1" },
  { value: "blue", label: "Blue", color: "#3b82f6" },
  { value: "purple", label: "Purple", color: "#a855f7" },
  { value: "pink", label: "Pink", color: "#ec4899" },
  { value: "rose", label: "Rose", color: "#f43f5e" },
  { value: "orange", label: "Orange", color: "#f97316" },
  { value: "amber", label: "Amber", color: "#f59e0b" },
  { value: "emerald", label: "Emerald", color: "#10b981" },
  { value: "teal", label: "Teal", color: "#14b8a6" },
  { value: "cyan", label: "Cyan", color: "#06b6d4" },
];



export default function SettingsDialog({ open, onOpenChange }: Props) {
  const { t } = useTranslation();
  const state = useAppStore();
  const [tab, setTab] = useState("general");
  const [debugOpen, setDebugOpen] = useState(false);

  useEffect(() => {
    if (!open || !inTauri) return;
    void tryInvoke<{ index: number; username: string; is_custom: boolean }[]>(
      "accounts_list",
      undefined,
      [],
    ).then((list) => {
      if (list) state.setAccounts(list);
    });
  }, [open]);

  const persist = async (path: string, value: unknown) => {
    if (!inTauri) return;
    await invoke("config_set", { path, value }).catch(() => undefined);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={t("tooltips.settings")}
      size="md"
    >
      <Tabs
        value={tab}
        onValueChange={setTab}
        items={[
          {
            value: "general",
            label: t("settings.general") || "General",
            content: (
              <div className="space-y-2 p-3">
                <Section
                  title={t("settings.appearance") || "Appearance"}
                  defaultOpen
                >
                  <Row label={t("settings.language") || "Language"}>
                    <Select
                      value={state.language}
                      options={state.availableLanguages.map((l) => ({
                        value: l.code,
                        label: l.label,
                      }))}
                      onValueChange={(v) => {
                        void changeLanguageTo(v);
                        void persist("settings.general.appearance.language", v);
                      }}
                    />
                  </Row>
                  <Row label={t("settings.theme") || "Theme"}>
                    <Select
                      value={state.theme}
                      options={THEMES}
                      onValueChange={(v) => {
                        state.setTheme(v as ThemeCode);
                        void persistTheme(v as ThemeCode);
                      }}
                    />
                  </Row>
                  <Row label={t("settings.accent_color") || "Accent color"}>
                    <AccentPicker />
                  </Row>
                </Section>

                <Section title={t("settings.behavior") || "Behavior"}>
                  <Row
                    label={
                      t("settings.auto_check_updates") || "Auto check updates"
                    }
                  >
                    <SettingSwitch
                      path="settings.general.behavior.auto_check_updates"
                      fallback={true}
                    />
                  </Row>
                  <Row
                    label={
                      t("settings.preload_next_page") || "Preload next page"
                    }
                  >
                    <SettingSwitch
                      path="settings.general.behavior.preload_next_page"
                      fallback={true}
                    />
                  </Row>
                  <Row
                    label={
                      t("settings.minimize_on_apply") || "Minimize on apply"
                    }
                  >
                    <SettingSwitch
                      path="settings.general.behavior.minimize_on_apply"
                      fallback={false}
                    />
                  </Row>
                  <Row
                    label={
                      t("settings.auto_init_metadata") || "Auto init metadata"
                    }
                  >
                    <SettingSwitch
                      path="settings.general.behavior.auto_init_metadata"
                      fallback={true}
                    />
                  </Row>
                  <Row
                    label={
                      t("settings.auto_apply_last_downloaded") ||
                      "Auto apply last downloaded"
                    }
                  >
                    <SettingSwitch
                      path="settings.general.behavior.auto_apply_last_downloaded"
                      fallback={false}
                    />
                  </Row>
                  <Row
                    label={
                      t("settings.save_window_state") || "Save window state"
                    }
                  >
                    <SettingSwitch
                      path="settings.general.behavior.save_window_state"
                      fallback={true}
                    />
                  </Row>
                  <Row
                    label={
                      t("settings.run_metadata_init") ||
                      "Initialize metadata for installed wallpapers"
                    }
                    description={
                      t("settings.metadata_init_hint") ||
                      "Fetch and cache Workshop metadata for every locally installed wallpaper."
                    }
                  >
                    <button
                      className="btn-outline text-xs"
                      disabled={!inTauri}
                      onClick={async () => {
                        if (!inTauri) return;
                        const count = await tryInvoke<number>(
                          "app_init_metadata",
                          undefined,
                          0,
                        );
                        pushToast(
                          t("labels.metadata_initialized", {
                            count: count ?? 0,
                          }),
                          "success",
                        );
                        // Ensure the Installed view re-pulls
                        // `metadata_get_all` so the Misc/Genre filter
                        // chips immediately reflect the newly cached
                        // tags — otherwise they stay stuck showing only
                        // whatever was in the bundled project.json
                        // files until a manual refresh.
                        triggerGlobalRefresh();
                      }}
                    >
                      {t("settings.initialize_now") || "Initialize now"}
                    </button>
                  </Row>
                </Section>

                <Section
                  title={t("settings.wallpaper_engine") || "Wallpaper Engine"}
                >
                  <Row
                    label={t("settings.we_directory") || "WE Directory"}
                    description={
                      t("settings.we_directory_hint") ||
                      "Path to your Wallpaper Engine install folder. Required for Apply / Extract and for detecting already-installed workshop items."
                    }
                  >
                    <div className="flex flex-wrap gap-2">
                      <input
                        className="input min-w-[220px]"
                        readOnly
                        value={state.weDirectory}
                      />
                      <button
                        className="btn-outline"
                        onClick={async () => {
                          const folder = await openPath({ directory: true });
                          if (!folder || Array.isArray(folder)) return;
                          if (!inTauri) return;
                          const ok = await tryInvokeOk("we_set_directory", {
                            path: folder,
                          });
                          if (ok) state.setWeDirectory(folder);
                          else
                            pushToast(
                              t("messages.invalid_we_directory"),
                              "error",
                            );
                        }}
                      >
                        {t("buttons.browse") || "Browse"}
                      </button>
                    </div>
                  </Row>
                </Section>

                <Section title={t("settings.debug") || "Debug"}>
                  <Row
                    label={t("settings.parser_log") || "Parser log"}
                    description={
                      t("settings.parser_log_hint") ||
                      "Inspect raw HTML/JSON returned by the Steam parser"
                    }
                  >
                    <button
                      className="btn-ghost text-xs"
                      onClick={() => setDebugOpen(true)}
                    >
                      {t("buttons.open") || "Open"}
                    </button>
                  </Row>
                </Section>
              </div>
            ),
          },
          {
            value: "account",
            label: t("settings.account") || "Account",
            content: (
              <div className="space-y-5 p-4">
                <div className="space-y-2">
                  <p className="text-xs font-medium uppercase tracking-wide text-subtle">
                    {t("settings.steam_session") || "Steam web session"}
                  </p>
                  <p className="text-xs text-muted">
                    {t("settings.steam_session_description") ||
                      "Log in to Steam so authenticated Workshop browsing (age-gated items, personal subscriptions, following lists) works the same as in a browser."}
                  </p>
                  <SteamSessionRow />
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-medium uppercase tracking-wide text-subtle">
                    {t("settings.download_account") || "Download account"}
                  </p>
                  <p className="text-xs text-muted">
                    {t("settings.download_account_description") ||
                      "Pick a Steam account used for downloading via DepotDownloaderMod. Custom credentials can be added below."}
                  </p>
                  <div className="divide-y divide-border rounded-md border border-border bg-surface-sunken">
                    {state.accounts.map((a) => (
                      <label
                        key={`${a.index}-${a.username}`}
                        className="flex cursor-pointer items-center gap-3 p-2.5 text-sm"
                      >
                        <input
                          type="radio"
                          name="account"
                          checked={state.accountIndex === a.index}
                          onChange={() => {
                            state.setAccountIndex(a.index);
                            void persist(
                              "settings.account.account.account_number",
                              a.index,
                            );
                          }}
                        />
                        <span className="flex-1">{a.username}</span>
                        {a.is_custom && (
                          <span className="chip text-info">
                            {t("settings.custom_badge") || "custom"}
                          </span>
                        )}
                      </label>
                    ))}
                  </div>
                </div>
                <CustomAccountsSection />
              </div>
            ),
          },
        ]}
      />
      <ParserDebugDialog
        open={debugOpen}
        onClose={() => setDebugOpen(false)}
      />
    </Dialog>
  );
}

function Row({
  label,
  children,
  description,
}: {
  label: string;
  children: React.ReactNode;
  description?: string | null;
}) {
  return (
    <div className="flex items-center justify-between gap-3 py-1">
      <div className="min-w-0">
        <div className="text-[13px] text-foreground">{label}</div>
        {description ? (
          <div className="text-[11px] text-muted">{description}</div>
        ) : null}
      </div>
      <div className="flex-shrink-0">{children}</div>
    </div>
  );
}

/**
 * Collapsible group used to keep Settings tabs short. Mirrors the
 * grouping in the original PyQt window where related options shared a
 * QGroupBox.
 */
function Section({
  title,
  children,
  defaultOpen = false,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  return (
    <details
      open={defaultOpen}
      className="group rounded-md border border-border bg-surface-sunken/40"
    >
      <summary className="flex cursor-pointer list-none items-center justify-between rounded-md px-3 py-2 text-xs font-semibold uppercase tracking-wide text-subtle hover:bg-surface-raised/50">
        <span>{title}</span>
        <span className="transition-transform group-open:rotate-90">›</span>
      </summary>
      <div className="divide-y divide-border/40 px-3 pb-2 pt-1">
        {children}
      </div>
    </details>
  );
}

interface SteamAccountInfo {
  persona_name: string;
  account_name: string;
  steamid: string;
  profile_url: string;
}

function SteamSessionRow() {
  const { t } = useTranslation();
  const [loggedIn, setLoggedIn] = useState<boolean | null>(null);
  const [account, setAccount] = useState<SteamAccountInfo | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    if (!inTauri) return;
    const v = await tryInvoke<boolean>("steam_is_logged_in", undefined, false);
    setLoggedIn(Boolean(v));
    // Ask Steam itself who we're signed in as. This is the verification
    // path the user asked for — whatever comes back here takes precedence
    // over the "Download account" selector because it reflects the real
    // Workshop session cookies, not a settings value.
    if (v) {
      const info = await tryInvoke<SteamAccountInfo | null>(
        "steam_current_account",
        undefined,
        null,
      );
      setAccount(info ?? null);
    } else {
      setAccount(null);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const openLogin = async () => {
    if (!inTauri) return;
    // "Re-open Steam" path — user is already signed in and just wants to
    // manage the web session (switch account, clear cookies, check 18+
    // settings, …). Don't start the "wait for login and auto-hide" loop
    // or the window will blink open and immediately disappear. Show the
    // window and leave it to the user to close it via the title bar.
    if (loggedIn) {
      await invoke<void>("steam_login_show").catch(() => undefined);
      return;
    }
    setBusy(true);
    try {
      await invoke<void>("steam_login_show").catch(() => undefined);
      for (let i = 0; i < 180; i++) {
        await new Promise((r) => setTimeout(r, 2000));
        const v = await tryInvoke<boolean>(
          "steam_is_logged_in",
          undefined,
          false,
        );
        if (v) {
          await invoke<number>("steam_sync_cookies").catch(() => 0);
          await invoke<void>("steam_login_hide").catch(() => undefined);
          setLoggedIn(true);
          pushToast(t("messages.signed_in_to_steam") || "Signed in to Steam", "success");
          break;
        }
      }
    } finally {
      setBusy(false);
      void refresh();
    }
  };

  const displayName =
    account?.persona_name?.trim() ||
    account?.account_name?.trim() ||
    (account?.steamid ? `Steam ${account.steamid}` : "");

  return (
    <div className="flex flex-col gap-2 rounded-md border border-border bg-surface-sunken p-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm">
          <span
            className={
              loggedIn
                ? "inline-block h-2 w-2 rounded-full bg-success"
                : "inline-block h-2 w-2 rounded-full bg-subtle"
            }
          />
          <span>
            {loggedIn
              ? t("settings.signed_in") || "Signed in"
              : t("settings.not_signed_in") || "Not signed in"}
          </span>
          {loggedIn && displayName && (
            <span
              className="ml-2 inline-flex max-w-[260px] items-center truncate rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary"
              title={
                account?.profile_url
                  ? `${displayName} · ${account.profile_url}`
                  : displayName
              }
            >
              {displayName}
            </span>
          )}
        </div>
        <button
          className="btn-outline"
          onClick={openLogin}
          disabled={busy || !inTauri}
        >
          {busy
            ? t("settings.waiting_for_login") || "Waiting for login…"
            : loggedIn
              ? t("settings.reopen_steam") || "Re-open Steam"
              : t("settings.open_steam_login") || "Open Steam login"}
        </button>
      </div>
      {loggedIn && !account && (
        <div className="text-[11px] text-warning">
          {t("settings.steam_account_unknown") ||
            "Logged in, but Steam didn't return account details — the parser may be running anonymously."}
        </div>
      )}
    </div>
  );
}

function CustomAccountsSection() {
  const { t } = useTranslation();
  const { confirm: showConfirm, ConfirmDialog } = useConfirm();
  const state = useAppStore();
  const [list, setList] = useState<string[]>([]);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  const refreshAccounts = async () => {
    if (!inTauri) return;
    const custom = await tryInvoke<string[]>(
      "accounts_list_custom",
      undefined,
      [],
    );
    setList(custom ?? []);
    const all = await tryInvoke<
      { index: number; username: string; is_custom: boolean }[]
    >("accounts_list", undefined, []);
    if (all) state.setAccounts(all);
  };

  useEffect(() => {
    void refreshAccounts();
  }, []);

  const add = async () => {
    if (!inTauri) return;
    if (!username.trim() || !password) {
      pushToast(t("messages.invalid_input"), "error");
      return;
    }
    setBusy(true);
    try {
      const ok = await tryInvokeOk("accounts_set_custom", {
        username: username.trim(),
        password,
      });
      if (ok) {
        pushToast(t("settings.account_added") || "Account added", "success");
        setUsername("");
        setPassword("");
        await refreshAccounts();
      } else {
        pushToast(
          t("settings.account_exists") || "Account already exists",
          "error",
        );
      }
    } finally {
      setBusy(false);
    }
  };

  const remove = async (u: string) => {
    if (!inTauri) return;
    const confirmed = await showConfirm({
      title: t("labels.remove_account") || "Remove Account",
      message: t("settings.confirm_remove_account") ||
        t("labels.remove_account_question", { user: u }),
      confirmLabel: t("buttons.remove") || "Remove",
      cancelLabel: t("buttons.cancel") || "Cancel",
      variant: "danger",
    });
    if (!confirmed) return;
    const ok = await tryInvokeOk("accounts_remove_custom", { username: u });
    if (ok) {
      pushToast(t("messages.removed"), "success");
      await refreshAccounts();
    }
  };

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium uppercase tracking-wide text-subtle">
        {t("settings.custom_accounts") || "Custom accounts"}
      </p>
      <p className="text-xs text-muted">
        {t("settings.custom_accounts_description") ||
          "Encrypted on disk with a machine-bound key (PBKDF2 + AES-256-GCM)."}
      </p>
      <div className="flex flex-wrap items-end gap-2">
        <div className="flex-1 min-w-[160px]">
          <label className="block text-xs text-subtle mb-1">
            {t("settings.username") || "Username"}
          </label>
          <input
            className="input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div className="flex-1 min-w-[160px]">
          <label className="block text-xs text-subtle mb-1">
            {t("settings.password") || "Password"}
          </label>
          <input
            className="input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button className="btn-primary" onClick={add} disabled={busy || !inTauri}>
          {t("settings.add_account_button") || "Add"}
        </button>
      </div>

      {list.length === 0 ? (
        <p className="text-xs text-muted italic">
          {t("settings.no_custom_accounts") || "No custom accounts yet."}
        </p>
      ) : (
        <ul className="divide-y divide-border rounded-md border border-border bg-surface-sunken">
          {list.map((u) => (
            <li
              key={u}
              className="flex items-center gap-3 p-2.5 text-sm"
            >
              <span className="flex-1">{u}</span>
              <button
                className="btn-ghost text-error"
                onClick={() => remove(u)}
                title={t("settings.remove_account") || "Remove account"}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
      <ConfirmDialog />
    </div>
  );
}

function AccentPicker() {
  const state = useAppStore();
  return (
    <div className="flex flex-wrap gap-1.5">
      {ACCENTS.map((a) => (
        <button
          key={a.value}
          aria-label={a.label}
          title={a.label}
          onClick={() => {
            state.setAccent(a.value);
            if (inTauri) {
              void invoke("config_set", {
                path: "settings.general.appearance.accent",
                value: a.value,
              }).catch(() => undefined);
            }
          }}
          className={
            state.accent === a.value
              ? "h-6 w-6 rounded-full ring-2 ring-offset-2 ring-offset-surface-sunken ring-foreground"
              : "h-6 w-6 rounded-full ring-1 ring-border hover:ring-foreground"
          }
          style={{ backgroundColor: a.color }}
        />
      ))}
    </div>
  );
}

function SettingSwitch({
  path,
  fallback,
}: {
  path: string;
  fallback: boolean;
}) {
  const [value, setValue] = useState<boolean>(fallback);
  useEffect(() => {
    if (!inTauri) return;
    void tryInvoke<boolean>("config_get", { path }, fallback).then((v) => {
      if (typeof v === "boolean") setValue(v);
    });
  }, [path]);
  return (
    <Switch
      checked={value}
      onCheckedChange={(v) => {
        setValue(v);
        if (inTauri) {
          void invoke("config_set", { path, value: v }).catch(() => undefined);
        }
      }}
    />
  );
}
