import AsyncStorage from "@react-native-async-storage/async-storage";
import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { translations } from "../i18n/translations";

const LANGUAGE_KEY = "vaxinsight.language";
const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState("rw");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;

    AsyncStorage.getItem(LANGUAGE_KEY)
      .then((storedLanguage) => {
        if (active && storedLanguage && translations[storedLanguage]) {
          setLanguageState(storedLanguage);
        }
      })
      .finally(() => {
        if (active) setReady(true);
      });

    return () => {
      active = false;
    };
  }, []);

  const setLanguage = async (nextLanguage) => {
    if (!translations[nextLanguage]) return;
    setLanguageState(nextLanguage);
    await AsyncStorage.setItem(LANGUAGE_KEY, nextLanguage);
  };

  const value = useMemo(
    () => ({ language, setLanguage, t: translations[language], ready }),
    [language, ready],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be used inside LanguageProvider");
  return context;
}
