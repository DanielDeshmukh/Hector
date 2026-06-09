import { useState, useCallback, createContext, useContext } from "react";
import translations from "./translations";

const LanguageContext = createContext();

const LANG_STORAGE_KEY = "hector.language";

function getInitialLang() {
  try {
    return window.localStorage.getItem(LANG_STORAGE_KEY) || "en";
  } catch {
    return "en";
  }
}

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(getInitialLang);

  const toggleLang = useCallback(() => {
    setLang((prev) => {
      const next = prev === "en" ? "hi" : "en";
      try {
        window.localStorage.setItem(LANG_STORAGE_KEY, next);
      } catch {}
      return next;
    });
  }, []);

  const t = useCallback(
    (key) => translations[lang]?.[key] || translations.en[key] || key,
    [lang]
  );

  return (
    <LanguageContext.Provider value={{ lang, toggleLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
