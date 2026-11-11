const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const projectRoot = path.resolve(__dirname, "..");

function read(relativePath) {
  return fs.readFileSync(path.join(projectRoot, relativePath), "utf8");
}

test("CHW navigation exposes the supported home, narrative, resources, and profile routes", () => {
  const tabs = read("src/components/BottomTabBar.js");
  const navigator = read("src/navigation/RootNavigator.js");

  assert.match(tabs, /route: "Home"/);
  assert.match(tabs, /route: "NarrativeList"/);
  assert.match(tabs, /route: "Resources"/);
  assert.match(tabs, /route: "Account"/);
  assert.doesNotMatch(tabs, /user\?\.role/);
  assert.doesNotMatch(tabs, /route: "(QuestionList|ReviewQueue|Admin)"/);
  assert.match(navigator, /name="Resources"/);
  assert.match(navigator, /name="VaccineArticleDetail"/);
});

test("CHW home copy and data sections remain source-backed", () => {
  const translations = read("src/i18n/translations.js");
  const home = read("src/screens/HomeScreen.js");

  assert.match(translations, /chwHeroTitle: "Listen\. Understand\. Share\."/);
  assert.match(
    translations,
    /chwHeroCardDescription:\s*"Capture community vaccine-related concerns and connect them with reliable information\."/,
  );
  assert.match(home, /personalSummary\.activity\?\.submitted/);
  assert.match(home, /personalSummary\.activity\?\.under_review/);
  assert.match(home, /personalSummary\.activity\?\.reviewed/);
  assert.match(home, /api\.listVaccineContent/);
  assert.match(home, /VaccineArticleDetail/);
});

test("resources keep unavailable learning content honest and expose original sources", () => {
  const resources = read("src/screens/ResourcesScreen.js");
  const article = read("src/screens/VaccineArticleDetailScreen.js");
  const vaccineInfo = read("src/screens/OfficialVaccineInfoScreen.js");

  assert.match(resources, /<EmptyState/);
  assert.match(resources, /learningResourcesEmptyDescription/);
  assert.match(article, /Linking\.openURL/);
  assert.match(vaccineInfo, /item\.source\?\.url/);
});

test("account email changes enter the explicit verification state", () => {
  const auth = read("src/context/AuthContext.js");
  const navigator = read("src/navigation/RootNavigator.js");

  assert.match(auth, /persistPendingEmailVerification\(nextEmail\)/);
  assert.match(navigator, /pendingEmailVerification/);
  assert.match(navigator, /name="VerifyEmail"/);
});

test("mobile requests have a bounded timeout and theme follows the system by default", () => {
  const client = read("src/api/client.js");
  const appConfig = read("app.json");

  assert.match(client, /REQUEST_TIMEOUT_MS = 15_000/);
  assert.match(client, /controller\.abort\(\)/);
  assert.match(appConfig, /"userInterfaceStyle": "automatic"/);
});

test("welcome screen does not render the removed evidence card CTA", () => {
  const welcome = read("src/screens/WelcomeScreen.js");
  const hero = read("src/components/CinematicHero.js");
  const translations = read("src/i18n/translations.js");

  assert.doesNotMatch(welcome, /heroCardHeading|heroDescription/);
  assert.doesNotMatch(hero, /cardShell|cardHeading|cardDescription/);
  assert.doesNotMatch(translations, /Evidence, made human\./);
});

test("Health Expert accounts use the Health Expert display label", () => {
  const translations = read("src/i18n/translations.js");

  assert.match(translations, /reviewer: "Health Expert"/);
  assert.match(translations, /reviewer: "Inzobere mu buzima"/);
});
