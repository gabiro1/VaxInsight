const assert = require("node:assert/strict");
const test = require("node:test");

const {
  THEME_STORAGE_KEY,
  isValidThemePreference,
  loadThemePreference,
  resolveThemeMode,
  saveThemePreference,
  themePreferenceValues,
} = require("../src/theme/preference.js");

test("supports light, dark, and system preferences", () => {
  assert.deepEqual(themePreferenceValues, ["light", "dark", "system"]);
  assert.equal(isValidThemePreference("light"), true);
  assert.equal(isValidThemePreference("dark"), true);
  assert.equal(isValidThemePreference("system"), true);
  assert.equal(isValidThemePreference("sepia"), false);
});

test("manual preferences override the device appearance", () => {
  assert.equal(resolveThemeMode("light", "dark"), "light");
  assert.equal(resolveThemeMode("dark", "light"), "dark");
});

test("system preference follows the current device appearance", () => {
  assert.equal(resolveThemeMode("system", "light"), "light");
  assert.equal(resolveThemeMode("system", "dark"), "dark");
  assert.equal(resolveThemeMode("system", null), "light");
});

test("theme preference persists through the storage adapter", async () => {
  const values = new Map();
  const storage = {
    getItem: async (key) => values.get(key) || null,
    setItem: async (key, value) => values.set(key, value),
  };

  assert.equal(await loadThemePreference(storage), "system");
  await saveThemePreference(storage, "dark");
  assert.equal(values.get(THEME_STORAGE_KEY), "dark");
  assert.equal(await loadThemePreference(storage), "dark");
  await saveThemePreference(storage, "invalid");
  assert.equal(await loadThemePreference(storage), "dark");
});
