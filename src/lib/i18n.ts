import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "@/locales/en.json";
import ru from "@/locales/ru.json";

export const DEFAULT_LANG = "en";

void i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      ru: { translation: ru },
    },
    lng: DEFAULT_LANG,
    fallbackLng: "en",
    interpolation: { escapeValue: false, prefix: "{", suffix: "}" },
    returnNull: false,
    returnEmptyString: false,
  });

export default i18n;

export function loadTranslations(
  bundles: Record<string, unknown>,
  current: string,
) {
  for (const [code, resource] of Object.entries(bundles)) {
    i18n.addResourceBundle(code, "translation", resource, true, true);
  }
  if (current && i18n.hasResourceBundle(current, "translation")) {
    void i18n.changeLanguage(current);
  }
}
