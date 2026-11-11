import AsyncStorage from "@react-native-async-storage/async-storage";
import { Appearance, View } from "react-native";
import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { themes } from "../theme/tokens";

const {
  isValidThemePreference,
  loadThemePreference,
  resolveThemeMode,
  saveThemePreference,
} = require("../theme/preference");

const ThemeContext = createContext(null);

function getSystemTheme() {
  return Appearance.getColorScheme() === "dark" ? "dark" : "light";
}

export function ThemeProvider({ children }) {
  const [preference, setPreferenceState] = useState("system");
  const [systemTheme, setSystemTheme] = useState(getSystemTheme);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;
    loadThemePreference(AsyncStorage)
      .then((storedPreference) => {
        if (active) setPreferenceState(storedPreference);
      })
      .finally(() => {
        if (active) setReady(true);
      });

    const subscription = Appearance.addChangeListener(({ colorScheme }) => {
      setSystemTheme(colorScheme === "dark" ? "dark" : "light");
    });

    return () => {
      active = false;
      subscription?.remove?.();
    };
  }, []);

  const setPreference = async (nextPreference) => {
    if (!isValidThemePreference(nextPreference)) return;
    setPreferenceState(nextPreference);
    await saveThemePreference(AsyncStorage, nextPreference);
  };

  const mode = resolveThemeMode(preference, systemTheme);
  const value = useMemo(
    () => ({
      preference,
      setPreference,
      mode,
      isDark: mode === "dark",
      colors: themes[mode],
      ready,
    }),
    [mode, preference, ready],
  );

  if (!ready) {
    return <View style={{ flex: 1, backgroundColor: themes[getSystemTheme()].background }} />;
  }

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used inside ThemeProvider");
  return context;
}
