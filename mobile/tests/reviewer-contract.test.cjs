const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const projectRoot = path.resolve(__dirname, "..");

function read(relativePath) {
  return fs.readFileSync(path.join(projectRoot, relativePath), "utf8");
}

test("Health Experts get Assignments and question review in shared navigation", () => {
  const tabs = read("src/components/BottomTabBar.js");
  const navigator = read("src/navigation/RootNavigator.js");

  assert.match(tabs, /primaryRoute === "ReviewQueue"/);
  assert.match(tabs, /questionRoute/);
  assert.match(tabs, /questionsAwaitingResponse/);
  assert.match(tabs, /label: t\.assignments/);
  assert.match(tabs, /route: "NarrativeList"/);
  assert.match(navigator, /user\?\.role === "reviewer" \? "ReviewQueue" : "NarrativeList"/);
  assert.match(navigator, /user\?\.role === "reviewer" \? "QuestionReviewQueue" : null/);
  assert.match(navigator, /AuthenticatedQuestionReviewQueueScreen/);
  assert.match(navigator, /isMainRoute\(routeName, primaryRoute, questionRoute\)/);
});

test("Health Expert dashboard and queue use assigned-workload APIs and statuses", () => {
  const home = read("src/screens/HomeScreen.js");
  const queue = read("src/screens/ReviewQueueScreen.js");
  const reviewer = read("src/utils/reviewer.js");

  assert.match(reviewer, /api\.listAssignments/);
  assert.match(reviewer, /page_size: REVIEWER_PAGE_SIZE/);
  assert.match(home, /loadAllReviewerAssignments/);
  assert.match(home, /reviewerSummary\.pending/);
  assert.match(home, /reviewerSummary\.inReview/);
  assert.match(home, /reviewerSummary\.reviewed/);
  assert.match(home, /reviewerSummary\.escalated/);
  assert.match(queue, /useFocusEffect/);
  assert.match(queue, /setItems\(\(current\) => \[\.\.\.current, \.\.\.\(result\?\.items \|\| \[\]\)\]\)/);
  assert.match(queue, /t\.loadMore/);
});

test("Health Expert decisions require confirmation and evidence links stay external", () => {
  const detail = read("src/screens/ReviewDetailScreen.js");
  const history = read("src/screens/ReviewHistoryScreen.js");

  assert.match(detail, /ConfirmDialog/);
  assert.match(detail, /confirmReviewSubmissionTitle/);
  assert.match(detail, /confirmEscalationTitle/);
  assert.match(detail, /setNotice\(t\.reviewSubmitted\)/);
  assert.match(history, /Linking\.openURL/);
  assert.match(history, /Linking\.canOpenURL/);
});

test("Health Expert display copy does not create a new RBAC role", () => {
  const translations = read("src/i18n/translations.js");
  const audit = read("../reports/reviewer-mobile-screen-audit.md");
  const resources = read("src/screens/ResourcesScreen.js");

  assert.match(translations, /reviewer: "Health Expert"/);
  assert.match(translations, /reviewer: "Inzobere mu buzima"/);
  assert.doesNotMatch(translations, /health_expert/);
  assert.match(audit, /backend role remains `reviewer`/);
  assert.match(resources, /reviewerGuidanceTitle/);
  assert.match(resources, /helpSupportUnavailableDescription/);
  assert.match(resources, /aboutVaxInsightTitle/);
});
