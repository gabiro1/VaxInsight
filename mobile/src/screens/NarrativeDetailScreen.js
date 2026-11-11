import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useState } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { formatDate, getErrorMessage, ownerNarrativeStatusLabel, ownerNarrativeTone } from "../utils/errors";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, layout, radii, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { ErrorState, FullScreenLoader } from "../components/StateView";
import { InlineNotice } from "../components/InlineNotice";
import { LanguageSelector } from "../components/LanguageSelector";
import { PrimaryButton, SecondaryButton, TextButton } from "../components/PrimaryButton";
import { StatusPill } from "../components/StatusPill";

export function NarrativeDetailScreen({ navigation, route }) {
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest } = useAuth();
  const narrativeId = route?.params?.narrativeId;
  const [narrative, setNarrative] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await authenticatedRequest((token) => api.getNarrative(token, narrativeId));
      setNarrative(result);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setLoading(false);
    }
  }, [authenticatedRequest, narrativeId, t]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <FullScreenLoader label={t.loading} />;

  if (error || !narrative) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <ErrorState actionLabel={t.retry} description={error || t.notFound} onRetry={load} title={t.genericError} />
        <View style={styles.backRow}><TextButton label={t.back} onPress={() => navigation.goBack()} /></View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <TextButton label={t.back} onPress={() => navigation.goBack()} />
          <BrandMark compact />
          <LanguageSelector />
        </View>
        <View style={styles.intro}>
          <AppText accessibilityRole="header" variant="title">{t.narrativeDetails}</AppText>
          <View style={styles.statusRow}>
            <StatusPill label={ownerNarrativeStatusLabel(narrative, t)} tone={ownerNarrativeTone(narrative)} />
            <AppText style={styles.meta}>{t.version} {narrative.version}</AppText>
          </View>
        </View>
        <View style={styles.contentCard}>
          <AppText style={styles.content}>{narrative.content}</AppText>
          <View style={styles.metadata}>
            <View style={styles.metaRow}>
              <Ionicons color={colors.muted} name="calendar-outline" size={16} />
              <AppText style={styles.meta}>{t.submittedAt}: {formatDate(narrative.submitted_at, language)}</AppText>
            </View>
            <View style={styles.metaRow}>
              <Ionicons color={colors.muted} name="refresh-outline" size={16} />
              <AppText style={styles.meta}>{t.updatedAt}: {formatDate(narrative.updated_at, language)}</AppText>
            </View>
          </View>
        </View>
        {narrative.review_status ? (
          <View style={styles.lockNotice}>
            <Ionicons color={colors.primaryAccent} name="lock-closed-outline" size={19} />
            <AppText style={styles.lockNoticeText}>{t.editLockedDescription}</AppText>
          </View>
        ) : null}
        <View style={styles.actions}>
          {!narrative.review_status ? (
            <PrimaryButton label={t.editNarrative} onPress={() => navigation.navigate("NarrativeComposer", { narrativeId: narrative.id })} />
          ) : null}
          <SecondaryButton label={t.viewHistory} onPress={() => navigation.navigate("NarrativeHistory", { narrativeId: narrative.id })} />
        </View>
        {error ? <InlineNotice message={error} /> : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.creamLight },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl, gap: spacing.lg },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  intro: { marginTop: spacing.xl, gap: spacing.sm },
  statusRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  meta: { color: colors.muted, fontSize: 12 },
  contentCard: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surface, ...getShadows(colors).card },
  content: { color: colors.ink, fontSize: 17, lineHeight: 27 },
  metadata: { gap: spacing.sm, marginTop: spacing.xl, paddingTop: spacing.md, borderTopWidth: 1, borderTopColor: colors.border },
  metaRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  actions: { gap: spacing.sm },
  lockNotice: { flexDirection: "row", alignItems: "flex-start", gap: spacing.xs, padding: spacing.md, borderRadius: radii.md, backgroundColor: colors.accentBackground, borderWidth: 1, borderColor: colors.border },
  lockNoticeText: { flex: 1, color: colors.secondaryText, lineHeight: 19 },
  backRow: { alignItems: "center", paddingBottom: spacing.xl },
});
