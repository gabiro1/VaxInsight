import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { useCallback, useEffect } from "react";
import { ActivityIndicator, Image, Pressable, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";

import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import {
  formatDate,
  getErrorMessage,
  ownerNarrativeStatusLabel,
  ownerNarrativeTone,
} from "../utils/errors";
import { getShadows, layout, radii, spacing, typography } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { InlineNotice } from "../components/InlineNotice";
import { PrimaryButton, SecondaryButton } from "../components/PrimaryButton";
import { StatusPill } from "../components/StatusPill";

function PlatformMetric({ colors, icon, label, value, suffix = "", styles }) {
  return (
    <View style={styles.platformMetric}>
      <View style={styles.platformMetricTop}>
        <View style={styles.platformMetricIcon}>
          <Ionicons color={colors.primaryAccent} name={icon} size={24} />
        </View>
      </View>
      <AppText style={styles.platformMetricValue}>{`${value ?? 0}${suffix}`}</AppText>
      <AppText style={styles.platformMetricLabel}>{label}</AppText>
    </View>
  );
}

export function HomeScreen({ navigation }) {
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest, user, refreshProfile, signOut } = useAuth();
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [recentNarratives, setRecentNarratives] = useState([]);
  const [recentLoading, setRecentLoading] = useState(true);
  const [recentError, setRecentError] = useState("");
  const [personalSummary, setPersonalSummary] = useState(null);
  const [personalSummaryLoading, setPersonalSummaryLoading] = useState(false);
  const [personalSummaryError, setPersonalSummaryError] = useState("");
  const [vaccineContent, setVaccineContent] = useState([]);
  const [vaccineLoading, setVaccineLoading] = useState(true);
  const [vaccineError, setVaccineError] = useState("");
  const [adminSummary, setAdminSummary] = useState(null);
  const [adminSummaryLoading, setAdminSummaryLoading] = useState(false);
  const [adminSummaryError, setAdminSummaryError] = useState("");
  const [dialog, setDialog] = useState(null);

  const canManageNarratives = ["community_member", "chw", "reviewer", "administrator"].includes(user?.role);
  const isAdmin = user?.role === "administrator";
  const isChw = user?.role === "chw";

  const loadRecentNarratives = useCallback(async () => {
    if (!canManageNarratives || isChw) return;
    setRecentLoading(true);
    setRecentError("");
    try {
      const page = await authenticatedRequest((token) =>
        api.listNarratives(token, { page: 1, page_size: 3 }),
      );
      setRecentNarratives((page?.items || []).slice(0, 3));
    } catch (requestError) {
      setRecentError(getErrorMessage(requestError, t));
    } finally {
      setRecentLoading(false);
    }
  }, [authenticatedRequest, canManageNarratives, isChw, t]);

  const loadPersonalSummary = useCallback(async () => {
    if (!isChw) return;
    setPersonalSummaryLoading(true);
    setRecentLoading(true);
    setPersonalSummaryError("");
    setRecentError("");
    try {
      const result = await authenticatedRequest((token) =>
        api.getPersonalDashboardSummary(token),
      );
      setPersonalSummary(result);
      setRecentNarratives(result?.recent_narratives || []);
    } catch (requestError) {
      const message = getErrorMessage(requestError, t);
      setPersonalSummaryError(message);
      setRecentError(message);
    } finally {
      setPersonalSummaryLoading(false);
      setRecentLoading(false);
    }
  }, [authenticatedRequest, isChw, t]);

  const loadVaccineContent = useCallback(async () => {
    setVaccineLoading(true);
    setVaccineError("");
    try {
      const result = await authenticatedRequest((token) =>
        api.listVaccineContent(token, { language }),
      );
      setVaccineContent((result || []).slice(0, 1));
    } catch (requestError) {
      setVaccineError(getErrorMessage(requestError, t));
    } finally {
      setVaccineLoading(false);
    }
  }, [authenticatedRequest, language, t]);

  const loadAdminSummary = useCallback(async () => {
    if (!isAdmin) return;
    setAdminSummaryLoading(true);
    setAdminSummaryError("");
    try {
      const result = await authenticatedRequest((token) =>
        api.getAdminDashboardSummary(token),
      );
      setAdminSummary(result);
    } catch (requestError) {
      setAdminSummaryError(getErrorMessage(requestError, t));
    } finally {
      setAdminSummaryLoading(false);
    }
  }, [authenticatedRequest, isAdmin, t]);

  useEffect(() => {
    loadRecentNarratives();
    loadPersonalSummary();
    loadVaccineContent();
    loadAdminSummary();
  }, [loadAdminSummary, loadPersonalSummary, loadRecentNarratives, loadVaccineContent]);

  const refresh = async () => {
    setRefreshing(true);
    setError("");
    try {
      await Promise.all([
        refreshProfile(),
        isChw ? loadPersonalSummary() : canManageNarratives ? loadRecentNarratives() : Promise.resolve(),
        loadVaccineContent(),
        isAdmin ? loadAdminSummary() : Promise.resolve(),
      ]);
    } catch {
      setError(t.networkError);
    } finally {
      setRefreshing(false);
    }
  };

  const displayName = user?.full_name || user?.email?.split("@")[0] || "VaxInsight";

  const confirmSignOut = () => {
    setDialog("signOut");
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl onRefresh={refresh} refreshing={refreshing} tintColor={colors.orange} />}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <BrandMark compact />
          <View style={styles.headerActions}>
            <Pressable accessibilityRole="button" accessibilityLabel={t.profile} hitSlop={10} onPress={() => navigation.navigate("Account")} style={styles.logoutButton}>
              <Ionicons color={colors.ink} name="person-outline" size={21} />
            </Pressable>
            <Pressable accessibilityRole="button" accessibilityLabel={t.signOut} hitSlop={10} onPress={confirmSignOut} style={styles.logoutButton}>
              <Ionicons color={colors.ink} name="log-out-outline" size={21} />
            </Pressable>
          </View>
        </View>
        <View style={[styles.heroCopy, isChw && styles.chwHeroCopy]}>
          {user?.role === "administrator" ? (
            <>
              <AppText style={styles.adminEyebrow}>{t.adminDashboardLabel}</AppText>
              <AppText accessibilityRole="header" variant="title">{t.adminWelcomePrefix} {displayName}</AppText>
              <AppText style={styles.description}>{t.adminWelcomeDescription}</AppText>
            </>
          ) : isChw ? (
            <>
              <AppText style={styles.chwEyebrow}>{t.chwHeroEyebrow}</AppText>
              <AppText accessibilityRole="header" variant="title">{t.chwWelcomePrefix} {displayName}!</AppText>
              <AppText style={styles.chwDescription}>{t.chwHeroDescription}</AppText>
            </>
          ) : (
            <>
              <AppText style={styles.eyebrow}>{t.accountHome}</AppText>
              <AppText accessibilityRole="header" variant="title">{displayName}</AppText>
              <AppText style={styles.description}>{t.accountHomeDescription}</AppText>
            </>
          )}
        </View>

        {error ? <InlineNotice message={error} /> : null}

        {user?.role === "administrator" ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t.viewDashboard}
            onPress={() => navigation.navigate("Admin")}
            style={({ pressed }) => [styles.adminOverviewCard, pressed && styles.pressed]}
          >
            <View style={styles.adminOverviewCopy}>
              <View style={styles.adminOverviewPill}>
                <AppText style={styles.adminOverviewPillText}>{t.adminOverview}</AppText>
              </View>
              <AppText variant="card" style={styles.adminOverviewTitle}>{t.adminOverviewTitle}</AppText>
              <AppText style={styles.adminOverviewDescription}>{t.adminOverviewDescription}</AppText>
              <View style={styles.adminOverviewAction}>
                <AppText style={styles.adminOverviewActionText}>{t.viewDashboard}</AppText>
                <Ionicons color={colors.primaryAccent} name="arrow-forward" size={18} />
              </View>
            </View>
            <View style={styles.adminGraphic}>
              <View style={styles.adminGraphicRing} />
              <Ionicons color={colors.workspaceText} name="people-outline" size={64} />
              <View style={styles.adminGraphicBadge}>
                <Ionicons color={colors.primaryButtonText} name="checkmark" size={22} />
              </View>
            </View>
          </Pressable>
        ) : isChw ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t.newNarrative}
            onPress={() => navigation.navigate("NarrativeComposer")}
            style={({ pressed }) => [styles.chwHeroCard, pressed && styles.pressed]}
          >
            <LinearGradient
              colors={["#171311", "#251914", "#110F0E"]}
              end={{ x: 1, y: 0.8 }}
              start={{ x: 0, y: 0.2 }}
              style={styles.chwHeroGradient}
            >
              <View style={styles.chwHeroContent}>
                <View style={styles.chwRolePill}>
                   <Ionicons color={colors.inverseText} name="shield-checkmark" size={16} />
                  <AppText style={styles.chwRolePillText}>{t.chwRoleLabel}</AppText>
                </View>
                <AppText variant="card" style={styles.chwHeroTitle}>{t.chwHeroTitle}</AppText>
                <AppText style={styles.chwHeroCardDescription}>{t.chwHeroCardDescription}</AppText>
                <View style={styles.chwHeroAction}>
                  <View style={styles.chwHeroActionIcon}>
                      <Ionicons color={colors.inverseText} name="add" size={22} />
                  </View>
                   <AppText style={styles.chwHeroActionText}>{t.newNarrative}</AppText>
                   <Ionicons color={colors.inverseText} name="arrow-forward" size={19} />
                </View>
              </View>
              <View style={styles.chwHeroGraphic}>
                <View style={styles.chwHeroGlow} />
                <Image
                  accessibilityIgnoresInvertColors
                  source={require("../../assets/chw-worker-hero.png")}
                  style={styles.chwHeroImage}
                />
              </View>
            </LinearGradient>
          </Pressable>
        ) : (
          <View style={styles.workspaceCard}>
            <View style={styles.workspaceHeader}>
              <View style={styles.workspaceIcon}><Ionicons color={colors.success} name="sparkles-outline" size={22} /></View>
              <AppText variant="card" style={styles.workspaceTitle}>{t.workspaceTitle}</AppText>
            </View>
            <AppText style={styles.workspaceDescription}>{t.workspaceDescription}</AppText>
            <View style={styles.ruleRow}>
              <Ionicons color={colors.success} name="shield-checkmark-outline" size={18} />
              <AppText style={styles.ruleText}>{t.accessPermissionNote}</AppText>
            </View>
          </View>
        )}

        {isChw ? (
          <View style={styles.personalActivitySection}>
            <View style={styles.sectionHeader}>
              <View style={styles.sectionTitleCopy}>
                <AppText variant="section">{t.chwActivityTitle}</AppText>
                <AppText style={styles.sectionDescription}>{t.chwActivityDescription}</AppText>
              </View>
              {personalSummaryLoading ? <ActivityIndicator color={colors.orange} /> : null}
            </View>
            {personalSummaryError ? <InlineNotice message={personalSummaryError} /> : null}
            {personalSummary ? (
              <View style={styles.platformMetricGrid}>
                <PlatformMetric
                  colors={colors}
                  icon="document-text-outline"
                  label={t.submitted}
                  styles={styles}
                  value={personalSummary.activity?.submitted}
                />
                <PlatformMetric
                  colors={colors}
                  icon="time-outline"
                  label={t.underReview}
                  styles={styles}
                  value={personalSummary.activity?.under_review}
                />
                <PlatformMetric
                  colors={colors}
                  icon="checkmark-circle-outline"
                  label={t.reviewed}
                  styles={styles}
                  value={personalSummary.activity?.reviewed}
                />
              </View>
            ) : null}
          </View>
        ) : null}

        {isAdmin ? (
          <View style={styles.platformSection}>
            <View style={styles.platformHeader}>
              <AppText variant="section">{t.platformOverview}</AppText>
              <AppText style={styles.platformPeriod}>{t.last30Days}</AppText>
            </View>
            {adminSummaryLoading && !adminSummary ? <ActivityIndicator color={colors.primaryAccent} /> : null}
            {adminSummaryError ? <InlineNotice message={adminSummaryError} /> : null}
            {adminSummary ? (
              <View style={styles.platformMetricGrid}>
                <PlatformMetric
                  colors={colors}
                  icon="document-text-outline"
                  label={t.totalNarratives}
                  styles={styles}
                  value={adminSummary.platform?.total_narratives}
                />
                <PlatformMetric
                  colors={colors}
                  icon="people-outline"
                  label={t.activeUsers}
                  styles={styles}
                  value={adminSummary.platform?.active_users}
                />
                <PlatformMetric
                  colors={colors}
                  icon="checkmark-circle-outline"
                  label={t.reviewCompletion}
                  styles={styles}
                  suffix="%"
                  value={adminSummary.platform?.review_completion_rate}
                />
                <PlatformMetric
                  colors={colors}
                  icon="shield-checkmark-outline"
                  label={t.trustedInfoRate}
                  styles={styles}
                  suffix="%"
                  value={adminSummary.platform?.trusted_info_rate}
                />
              </View>
            ) : null}
          </View>
        ) : null}

        <View style={styles.updatesSection}>
          <View style={styles.sectionHeader}>
            <AppText variant="section">{t.vaccineUpdates}</AppText>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={t.seeAll}
              hitSlop={8}
               onPress={() => navigation.navigate("VaccineInfo")}
              style={styles.viewAll}
            >
              <AppText style={styles.viewAllLabel}>{t.seeAll}</AppText>
              <Ionicons color={colors.orange} name="arrow-forward" size={16} />
            </Pressable>
          </View>
          {vaccineLoading ? <ActivityIndicator color={colors.orange} /> : null}
          {vaccineError ? <InlineNotice message={vaccineError} /> : null}
          {!vaccineLoading && !vaccineError && !vaccineContent.length ? (
            <AppText style={styles.recentEmpty}>
              {t.officialVaccineInfoEmptyDescription}
            </AppText>
          ) : null}
          {!vaccineLoading && !vaccineError && vaccineContent.length ? (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={vaccineContent[0].title}
               onPress={() => navigation.navigate("VaccineArticleDetail", { contentId: vaccineContent[0].id })}
              style={({ pressed }) => [styles.updateCard, pressed && styles.pressed]}
            >
              <View style={styles.updateHeader}>
                <View style={styles.updateIcon}>
                  <Ionicons color={colors.orange} name="newspaper-outline" size={21} />
                </View>
                <View style={styles.updateCopy}>
                  <AppText variant="card">{vaccineContent[0].title}</AppText>
                  <AppText style={styles.updateMeta}>
                    {vaccineContent[0].source?.name} · {formatDate(vaccineContent[0].published_at, language)}
                  </AppText>
                </View>
              </View>
              <AppText style={styles.updateSummary}>{vaccineContent[0].summary}</AppText>
            </Pressable>
          ) : null}
        </View>

        {canManageNarratives ? (
          <View style={styles.recentSection}>
            <View style={styles.sectionHeader}>
              <AppText variant="section">{isChw ? t.myRecentSubmissions : t.recentNarratives}</AppText>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={t.viewAll}
                hitSlop={8}
                onPress={() => navigation.navigate("NarrativeList")}
                style={styles.viewAll}
              >
                <AppText style={styles.viewAllLabel}>{t.viewAll}</AppText>
                <Ionicons color={colors.orange} name="arrow-forward" size={16} />
              </Pressable>
            </View>
            {recentLoading ? <ActivityIndicator color={colors.orange} /> : null}
            {recentError ? <InlineNotice message={recentError} /> : null}
            {!recentLoading && !recentError && !recentNarratives.length ? (
              <AppText style={styles.recentEmpty}>{t.noNarrativesDescription}</AppText>
            ) : null}
            {!recentLoading && !recentError && recentNarratives.length ? (
              <View style={styles.recentList}>
                {recentNarratives.map((narrative) => (
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel={narrative.content}
                    key={narrative.id}
                    onPress={() => navigation.navigate("NarrativeDetail", { narrativeId: narrative.id })}
                    style={({ pressed }) => [styles.recentCard, pressed && styles.pressed]}
                  >
                    <View style={styles.recentCardTop}>
                      <StatusPill label={ownerNarrativeStatusLabel(narrative, t)} tone={ownerNarrativeTone(narrative)} />
                      <Ionicons color={colors.muted} name="chevron-forward" size={18} />
                    </View>
                    <AppText numberOfLines={2} style={styles.recentContent}>{narrative.content}</AppText>
                    <View style={styles.recentMetaRow}>
                      <AppText style={styles.recentMeta}>{t.version} {narrative.version}</AppText>
                      <AppText style={styles.recentMeta}>{formatDate(narrative.updated_at || narrative.submitted_at, language)}</AppText>
                    </View>
                  </Pressable>
                ))}
              </View>
            ) : null}
          </View>
        ) : null}

        {isChw ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t.resources}
            onPress={() => navigation.navigate("Resources")}
            style={({ pressed }) => [styles.resourcesShortcut, pressed && styles.pressed]}
          >
            <View style={styles.resourcesShortcutIcon}>
              <Ionicons color={colors.primaryAccent} name="library-outline" size={23} />
            </View>
            <View style={styles.resourcesShortcutCopy}>
              <AppText variant="card">{t.learningResources}</AppText>
              <AppText style={styles.resourcesShortcutDescription}>{t.learningResourcesShortcut}</AppText>
            </View>
            <Ionicons color={colors.mutedText} name="arrow-forward" size={19} />
          </Pressable>
        ) : null}

        {user?.role === "reviewer" ? (
          <View style={styles.workflowActions}>
            <SecondaryButton label={t.reviewQueue} onPress={() => navigation.navigate("ReviewQueue")} />
            <SecondaryButton label={t.professionalQuestionQueue} onPress={() => navigation.navigate("QuestionReviewQueue")} />
          </View>
        ) : null}

        {isChw ? (
          <View style={styles.workflowActions}>
            <SecondaryButton label={t.askQuestion} onPress={() => navigation.navigate("QuestionComposer")} />
          </View>
        ) : null}

        {user?.role === "administrator" ? (
          <View style={styles.adminSection}>
            <AppText variant="section">{t.admin}</AppText>
            <AppText style={styles.questionDescription}>{t.adminIntro}</AppText>
            <PrimaryButton label={t.adminDashboard} onPress={() => navigation.navigate("Admin")} />
            <SecondaryButton label={t.adminInviteStaff} onPress={() => navigation.navigate("AdminInvite")} />
            <SecondaryButton label={t.adminManageContent} onPress={() => navigation.navigate("AdminContent")} />
          </View>
        ) : null}

      </ScrollView>
      <ConfirmDialog
        cancelLabel={t.cancel}
        confirmLabel={t.signOut}
        description={t.confirmSignOutDescription}
        onCancel={() => setDialog(null)}
        onConfirm={() => {
          setDialog(null);
          signOut();
        }}
        title={t.confirmSignOutTitle}
        visible={dialog === "signOut"}
      />
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.huge + 88, gap: spacing.lg },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  headerActions: { flexDirection: "row", gap: spacing.xs },
  logoutButton: { width: 48, height: 48, borderRadius: 24, backgroundColor: colors.surface, alignItems: "center", justifyContent: "center", ...getShadows(colors).card },
  heroCopy: { marginTop: spacing.xl },
  eyebrow: { color: colors.orange, fontFamily: typography.family.bodyBold, fontSize: 12, letterSpacing: 1.4, marginBottom: spacing.xs },
  adminEyebrow: { color: colors.primaryAccent, fontFamily: typography.family.bodyBold, fontSize: 13, letterSpacing: 1.1, marginBottom: spacing.xs },
  description: { marginTop: spacing.sm, maxWidth: 350 },
  chwHeroCopy: { marginTop: spacing.lg },
  chwEyebrow: { color: colors.orange, fontFamily: typography.family.bodyBold, fontSize: 12, letterSpacing: 0.5, marginBottom: spacing.xs },
  chwDescription: { color: colors.secondaryText, fontSize: 17, lineHeight: 24, marginTop: spacing.xs, maxWidth: 350 },
  chwHeroCard: { minHeight: 252, borderRadius: radii.lg, overflow: "hidden", ...getShadows(colors).card },
  chwHeroGradient: { flex: 1, minHeight: 252, flexDirection: "row", overflow: "hidden", position: "relative" },
  chwHeroContent: { flex: 1, padding: spacing.lg, paddingRight: spacing.sm, zIndex: 2 },
  chwRolePill: { alignSelf: "flex-start", flexDirection: "row", alignItems: "center", gap: spacing.xs, paddingHorizontal: spacing.sm, paddingVertical: spacing.xs, borderRadius: radii.pill, backgroundColor: colors.orange },
   chwRolePillText: { color: colors.inverseText, fontFamily: typography.family.bodySemibold, fontSize: 14 },
   chwHeroTitle: { color: colors.inverseText, fontSize: 22, lineHeight: 28, marginTop: spacing.lg, maxWidth: 205 },
   chwHeroCardDescription: { color: colors.workspaceSecondary, fontSize: 14, lineHeight: 20, marginTop: spacing.xs, maxWidth: 208 },
  chwHeroAction: { alignSelf: "flex-start", flexDirection: "row", alignItems: "center", gap: spacing.xs, marginTop: spacing.lg, paddingRight: spacing.sm, borderRadius: radii.pill, backgroundColor: colors.orange },
  chwHeroActionIcon: { width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center", backgroundColor: "rgba(255,255,255,0.24)" },
   chwHeroActionText: { color: colors.inverseText, fontFamily: typography.family.bodySemibold, fontSize: 14 },
  chwHeroGraphic: { width: 142, alignSelf: "stretch", position: "relative", justifyContent: "flex-end", marginRight: -spacing.xs },
  chwHeroGlow: { position: "absolute", width: 156, height: 156, borderRadius: 78, backgroundColor: "rgba(160, 73, 31, 0.28)", top: 14, left: -10 },
  chwHeroImage: { position: "absolute", width: 222, height: 270, right: -30, bottom: -10 },
  workspaceCard: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.workspaceSurface, ...getShadows(colors).card },
  workspaceHeader: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  workspaceIcon: { width: 42, height: 42, borderRadius: 21, backgroundColor: colors.whiteScrim, alignItems: "center", justifyContent: "center" },
  workspaceTitle: { color: colors.workspaceText, flex: 1 },
  workspaceDescription: { color: colors.workspaceSecondary, marginTop: spacing.md },
  ruleRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs, marginTop: spacing.lg, paddingTop: spacing.md, borderTopWidth: 1, borderTopColor: colors.whiteScrim },
  ruleText: { color: colors.workspaceSecondary, fontSize: 12, flex: 1 },
  adminOverviewCard: { minHeight: 246, padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.workspaceSurface, flexDirection: "row", overflow: "hidden", ...getShadows(colors).card },
  adminOverviewCopy: { flex: 1, zIndex: 1 },
  adminOverviewPill: { alignSelf: "flex-start", paddingHorizontal: spacing.sm, paddingVertical: spacing.xs, borderRadius: radii.pill, backgroundColor: colors.primaryAccent },
  adminOverviewPillText: { color: colors.primaryButtonText, fontFamily: typography.family.bodySemibold, fontSize: 14 },
  adminOverviewTitle: { color: colors.workspaceText, marginTop: spacing.lg, maxWidth: 250 },
  adminOverviewDescription: { color: colors.workspaceSecondary, marginTop: spacing.sm, maxWidth: 250, lineHeight: 21 },
  adminOverviewAction: { flexDirection: "row", alignItems: "center", gap: spacing.sm, marginTop: spacing.lg },
  adminOverviewActionText: { color: colors.primaryAccent, fontFamily: typography.family.bodyBold, fontSize: 15 },
  adminGraphic: { width: 116, alignItems: "center", justifyContent: "center", marginRight: -spacing.sm },
  adminGraphicRing: { position: "absolute", width: 150, height: 150, borderRadius: 75, borderWidth: 2, borderColor: colors.whiteScrim, transform: [{ rotate: "28deg" }] },
  adminGraphicBadge: { position: "absolute", top: 37, right: 3, width: 40, height: 40, borderRadius: 20, backgroundColor: colors.primaryAccent, alignItems: "center", justifyContent: "center" },
  platformSection: { gap: spacing.md },
  platformHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.sm },
  platformPeriod: { color: colors.secondaryText, fontSize: 14 },
  platformMetricGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  platformMetric: { flex: 1, minWidth: 140, minHeight: 136, padding: spacing.md, borderRadius: radii.md, backgroundColor: colors.surface, gap: spacing.xs, ...getShadows(colors).card },
  platformMetricTop: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  platformMetricIcon: { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.accentBackground, alignItems: "center", justifyContent: "center" },
  platformMetricValue: { marginTop: spacing.xs, fontFamily: typography.family.display, fontSize: 28, lineHeight: 32, color: colors.primaryText },
  platformMetricLabel: { color: colors.secondaryText, fontSize: 13, lineHeight: 18 },
  recentSection: { gap: spacing.md },
  personalActivitySection: { gap: spacing.md },
  sectionTitleCopy: { flex: 1, gap: spacing.xxs },
  sectionDescription: { color: colors.secondaryText, fontSize: 13, lineHeight: 18 },
  sectionHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.sm },
  viewAll: { minHeight: 44, flexDirection: "row", alignItems: "center", gap: spacing.xxs },
  viewAllLabel: { color: colors.orange, fontFamily: typography.family.bodySemibold, fontSize: 13 },
  updatesSection: { gap: spacing.md },
  updateCard: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surface, gap: spacing.md, ...getShadows(colors).card },
  updateHeader: { flexDirection: "row", alignItems: "flex-start", gap: spacing.sm },
  updateIcon: { width: 42, height: 42, borderRadius: 21, backgroundColor: colors.orangeLight, alignItems: "center", justifyContent: "center" },
  updateCopy: { flex: 1, gap: spacing.xxs },
  updateMeta: { color: colors.muted, fontSize: 12 },
  updateSummary: { color: colors.secondaryText, lineHeight: 22 },
  questionDescription: { color: colors.secondaryText, lineHeight: 22 },
  recentList: { gap: spacing.sm },
  recentCard: { padding: spacing.md, borderRadius: radii.md, backgroundColor: colors.surface, gap: spacing.sm, ...getShadows(colors).card },
  pressed: { opacity: 0.82 },
  recentCardTop: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  recentContent: { color: colors.primaryText, fontSize: 15, lineHeight: 22 },
  recentMetaRow: { flexDirection: "row", justifyContent: "space-between", gap: spacing.sm },
  recentMeta: { color: colors.muted, fontSize: 11 },
  recentEmpty: { color: colors.muted, fontSize: 14 },
   workflowActions: { gap: spacing.sm },
   resourcesShortcut: { flexDirection: "row", alignItems: "center", gap: spacing.sm, padding: spacing.md, borderRadius: radii.lg, backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border },
   resourcesShortcutIcon: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.accentBackground },
   resourcesShortcutCopy: { flex: 1, gap: spacing.xxs },
   resourcesShortcutDescription: { color: colors.secondaryText, fontSize: 13, lineHeight: 18 },
  adminSection: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surface, gap: spacing.md, ...getShadows(colors).card },
});
