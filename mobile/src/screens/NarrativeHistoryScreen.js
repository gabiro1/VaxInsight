import { useCallback, useEffect, useState } from "react";
import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { formatDate, getErrorMessage } from "../utils/errors";
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

function revisionLabel(action, t) {
  return action === "created" ? t.revisionCreated : t.revisionUpdated;
}

export function NarrativeHistoryScreen({ navigation, route }) {
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest } = useAuth();
  const narrativeId = route?.params?.narrativeId;
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError("");
      try {
        const page = await authenticatedRequest((token) =>
          api.getNarrativeHistory(token, narrativeId, { page: 1, page_size: 100 }),
        );
        setItems(page?.items || []);
      } catch (requestError) {
        setError(getErrorMessage(requestError, t));
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [authenticatedRequest, narrativeId, t],
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
          <AppText accessibilityRole="header" variant="title">{t.narrativeHistory}</AppText>
          <AppText style={styles.description}>{t.noHistoryDescription}</AppText>
        </View>
        {error && !items.length ? <ErrorState actionLabel={t.retry} description={error} onRetry={() => load()} title={t.genericError} /> : null}
        {!error && !items.length ? <EmptyState description={t.noHistoryDescription} icon="time-outline" title={t.noHistoryTitle} /> : null}
        <View style={styles.list}>
          {items.map((revision) => (
            <View key={revision.id} style={styles.card}>
              <View style={styles.cardTop}>
                <StatusPill label={revisionLabel(revision.action, t)} tone="accent" />
                <AppText style={styles.meta}>{t.version} {revision.version}</AppText>
              </View>
              <AppText style={styles.content}>{revision.content}</AppText>
              <AppText style={styles.meta}>{formatDate(revision.changed_at, language)}</AppText>
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
  cardTop: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  content: { color: colors.ink, fontSize: 15, lineHeight: 23 },
  meta: { color: colors.muted, fontSize: 12 },
});
