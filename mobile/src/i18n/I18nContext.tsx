import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useContext, useEffect, useState } from "react";

import { Language, TranslationKey, translations } from "./translations";

const STORAGE_KEY = "@parent_language_pref";

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => Promise<void>;
  t: (key: TranslationKey) => string;
}

const defaultContext: I18nContextType = {
  language: "en",
  setLanguage: async () => {},
  t: (key: TranslationKey) => translations.en[key] ?? key,
};

const I18nContext = createContext<I18nContextType>(defaultContext);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>("en");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((saved) => {
        if (saved === "en" || saved === "hi") {
          setLanguageState(saved);
        }
      })
      .catch(() => {})
      .finally(() => {
        setLoaded(true);
      });
  }, []);

  const setLanguage = async (newLang: Language) => {
    setLanguageState(newLang);
    try {
      await AsyncStorage.setItem(STORAGE_KEY, newLang);
    } catch (e) {
      console.warn("Failed to persist language preference:", e);
    }
  };

  const t = (key: TranslationKey): string => {
    const dict = translations[language] ?? translations.en;
    return dict[key] ?? translations.en[key] ?? key;
  };

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  );
}

/** Hook to consume parent app translations. Returns English fallbacks if used outside provider. */
export function useTranslation(): I18nContextType {
  const ctx = useContext(I18nContext);
  return ctx || defaultContext;
}
