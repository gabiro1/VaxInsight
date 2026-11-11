import { useCallback, useEffect, useState } from "react";
import { Linking, Pressable, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { formatDate, getErrorMessage, outcomeLabel } from "../utils/errors";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, layout, radii, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { EmptyState, ErrorState, FullScreenLoader } from "../components/StateView";
import { LanguageSelector } from "../components/LanguageSelector";
import { TextButton } from "../components/PrimaryButton";
import { StatusPill } from "../components/StatusPill";

export function ReviewHistoryScreen({ navigation, route }) {
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest } = useAuth();
  const assignmentId = route?.params?.assignmentId;
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const openEvidenceUrl = async (url) => {
    if (!/^https?:\/\//i.test(url || "")) return;
    try {
      if (await Linking.canOpenURL(url)) await Linking.openURL(url);
    } catch {
      // Keep the source visible when the device cannot open the returned URL.
    }
  };

  const load = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError("");
      try {
        const page = await authenticatedRequest((token) =>
          api.getReviewHistory(token, assignmentId, { page: 1, page_size: 100 }),
        );
        setItems(page?.items || []);
      } catch (requestError) {
        setError(getErrorMessage(requestError, t));
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [authenticatedRequest, assignmentId, t],
  );

  useEffect(() => {
    load();
  }, [load]);

  if (loading && !items.length) return <FullScreenLoader label={t.loading} />;

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl onRefresh={() => load(true)} refreshing={refreshing} tintColor={colors.orange} />}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <TextButton label={t.back} onPress={() => navigation.goBack()} />
          <BrandMark compact />
          <LanguageSelector />
        </View>
        <View style={styles.intro}>
          <AppText accessibilityRole="header" variant="title">{t.reviewHistory}</AppText>
          <AppText style={styles.description}>{t.noReviewHistoryDescription}</AppText>
        </View>
        {error && !items.length ? <ErrorState actionLabel={t.retry} description={error} onRetry={() => load()} title={t.genericError} /> : null}
        {!error && !items.length ? <EmptyState description={t.noReviewHistoryDescription} icon="time-outline" title={t.noReviewHistoryTitle} /> : null}
        <View style={styles.list}>
          {items.map((review) => (
            <View key={review.id} style={styles.card}>
              <StatusPill label={outcomeLabel(review.outcome, t)} tone="success" />
              <AppText style={styles.meta}>{formatDate(review.reviewed_at, language)}</AppText>
              {review.notes ? <AppText style={styles.notes}>{review.notes}</AppText> : null}
              {review.evidence?.length ? (
                <View style={styles.evidence}>
                  <AppText variant="section">{t.evidence}</AppText>
                  {review.evidence.map((item) => (
                    <View key={item.id} style={styles.evidenceRow}>
                      <AppText variant="card">{item.source_title}</AppText>
                      <AppText style={styles.meta}>{item.publisher}</AppText>
                      {item.url && /^https?:\/\//i.test(item.url) ? (
                        <Pressable accessibilityRole="link" accessibilityLabel={t.openSourceLink} onPress={() => openEvidenceUrl(item.url)}>
                          <AppText style={styles.link}>{t.openSourceLink}</AppText>
                        </Pressable>
                      ) : null}
                    </View>
                  ))}
                </View>
              ) : null}
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.creamLight },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl, gap: spacing.lg },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  intro: { marginTop: spacing.xl, gap: spacing.xs },
  description: { maxWidth: 360 },
  list: { gap: spacing.md },
  card: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surface, gap: spacing.md, ...getShadows(colors).card },
  meta: { color: colors.muted, fontSize: 12 },
  notes: { color: colors.ink, fontSize: 15, lineHeight: 23 },
  evidence: { gap: spacing.sm, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: spacing.md },
  evidenceRow: { gap: spacing.xxs },
  link: { color: colors.primaryAccent, fontSize: 13 },
});
