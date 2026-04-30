import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "@/App";
import "@/index.css";
import "@/lib/i18n";
import { THEME_CODES } from "@/hooks/useTheme";

// Apply the persisted theme class before React mounts so that the very first
// paint is already themed and doesn't flash the default dark palette when
// the user has chosen a different theme.
const saved = localStorage.getItem("weave.theme") ?? "dark";
const theme = THEME_CODES.includes(saved as (typeof THEME_CODES)[number])
  ? saved
  : "dark";
const html = document.documentElement;
THEME_CODES.forEach((t) => html.classList.remove(`theme-${t}`));
html.classList.add(`theme-${theme}`);
if (theme === "light") html.classList.remove("dark");
else html.classList.add("dark");
html.dataset.theme = theme;

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
