import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useState } from "react";
import { Linking, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { formatDate, getErrorMessage } from "../utils/errors";
import { getShadows, layout, radii, spacing, typography } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { ErrorState, FullScreenLoader } from "../components/StateView";
import { InlineNotice } from "../components/InlineNotice";
import { LanguageSelector } from "../components/LanguageSelector";
import { SecondaryButton, TextButton } from "../components/PrimaryButton";

export function VaccineArticleDetailScreen({ navigation, route }) {
  const { language, t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest } = useAuth();
  const contentId = route?.params?.contentId;
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [linkError, setLinkError] = useState("");

  const load = useCallback(async () => {
    if (!contentId) {
      setError(t.notFound);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = await authenticatedRequest((token) => api.getVaccineContent(token, contentId));
      setItem(result);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setLoading(false);
    }
  }, [authenticatedRequest, contentId, t]);

  useEffect(() => {
    load();
  }, [load]);

  const openSource = async () => {
    if (!item?.source?.url) return;
    setLinkError("");
    try {
      await Linking.openURL(item.source.url);
    } catch {
      setLinkError(t.sourceLinkUnavailable);
    }
  };

  if (loading) return <FullScreenLoader label={t.loading} />;

  if (error || !item) {
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
          <AppText accessibilityRole="header" variant="title">{t.articleDetails}</AppText>
          <AppText style={styles.category}>{item.category}</AppText>
        </View>

        <View style={styles.articleCard}>
          <AppText variant="title" style={styles.articleTitle}>{item.title}</AppText>
          <View style={styles.metadata}>
            <View style={styles.metaRow}>
              <Ionicons color={colors.primaryAccent} name="business-outline" size={17} />
              <AppText style={styles.meta}>{item.source?.name || item.source?.authority}</AppText>
            </View>
            <View style={styles.metaRow}>
              <Ionicons color={colors.primaryAccent} name="calendar-outline" size={17} />
              <AppText style={styles.meta}>{t.publishedAt}: {formatDate(item.published_at, language)}</AppText>
            </View>
          </View>
          <View style={styles.rule} />
          <AppText variant="card">{item.summary}</AppText>
          <AppText style={styles.body}>{item.body}</AppText>
        </View>

        <View style={styles.sourceCard}>
          <View style={styles.sourceHeading}>
            <Ionicons color={colors.primaryAccent} name="shield-checkmark-outline" size={22} />
            <AppText variant="card">{t.sourceAttribution}</AppText>
          </View>
          <AppText style={styles.meta}>{item.source?.authority}</AppText>
          <AppText style={styles.meta}>{item.source?.jurisdiction}</AppText>
          {linkError ? <InlineNotice message={linkError} /> : null}
          {item.source?.url ? (
            <SecondaryButton label={t.openSourceLink} onPress={openSource} />
          ) : (
            <AppText style={styles.meta}>{t.sourceLinkUnavailable}</AppText>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl, gap: spacing.lg },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  intro: { marginTop: spacing.xl, gap: spacing.xs },
  category: { color: colors.primaryAccent, fontFamily: typography.family.bodySemibold, textTransform: "capitalize" },
  articleCard: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surface, gap: spacing.md, ...getShadows(colors).card },
  articleTitle: { fontSize: 25, lineHeight: 31 },
  metadata: { gap: spacing.xs },
  metaRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  meta: { color: colors.secondaryText, fontSize: 13, lineHeight: 19 },
  rule: { height: 1, backgroundColor: colors.border },
  body: { color: colors.secondaryText, lineHeight: 25 },
  sourceCard: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border, gap: spacing.sm },
  sourceHeading: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  backRow: { alignItems: "center", paddingBottom: spacing.xl },
});
