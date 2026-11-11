const themePreferenceValues = ["light", "dark", "system"];
const THEME_STORAGE_KEY = "vaxinsight.themePreference";

function isValidThemePreference(value) {
  return themePreferenceValues.includes(value);
}

function resolveThemeMode(preference, systemTheme = "light") {
  if (preference === "light" || preference === "dark") return preference;
  return systemTheme === "dark" ? "dark" : "light";
}

async function loadThemePreference(storage) {
  const storedPreference = await storage.getItem(THEME_STORAGE_KEY);
  return isValidThemePreference(storedPreference) ? storedPreference : "system";
}

async function saveThemePreference(storage, preference) {
  if (!isValidThemePreference(preference)) return;
  await storage.setItem(THEME_STORAGE_KEY, preference);
}

module.exports = {
  THEME_STORAGE_KEY,
  themePreferenceValues,
  isValidThemePreference,
  resolveThemeMode,
  loadThemePreference,
  saveThemePreference,
};
