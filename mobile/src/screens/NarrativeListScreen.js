import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useState } from "react";
import { Pressable, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { formatDate, getErrorMessage, ownerNarrativeStatusLabel, ownerNarrativeTone } from "../utils/errors";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, layout, radii, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { ErrorState, EmptyState, FullScreenLoader } from "../components/StateView";
import { InlineNotice } from "../components/InlineNotice";
import { LanguageSelector } from "../components/LanguageSelector";
import { PrimaryButton, SecondaryButton, TextButton } from "../components/PrimaryButton";
import { StatusPill } from "../components/StatusPill";

export function NarrativeListScreen({ navigation }) {
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(
    async (pageNumber = 1, isRefresh = false) => {
      if (pageNumber === 1 && isRefresh) setRefreshing(true);
      else if (pageNumber === 1) setLoading(true);
      else setLoadingMore(true);
      setError("");
      try {
        const [page, dashboard] = await Promise.all([
          authenticatedRequest((token) =>
            api.listNarratives(token, { page: pageNumber, page_size: 20 }),
          ),
          pageNumber === 1
            ? authenticatedRequest((token) => api.getPersonalDashboardSummary(token)).catch(() => null)
            : Promise.resolve(null),
        ]);
        const statusById = new Map(
          (dashboard?.recent_narratives || []).map((item) => [item.id, item.review_status]),
        );
        const nextItems = (page?.items || []).map((item) => ({
          ...item,
          review_status: item.review_status || statusById.get(item.id) || null,
        }));
        setItems((current) => (pageNumber === 1 ? nextItems : [...current, ...nextItems]));
        setHasMore((page?.page || pageNumber) < (page?.total_pages || pageNumber));
      } catch (requestError) {
        setError(getErrorMessage(requestError, t));
      } finally {
        if (pageNumber === 1) setLoading(false);
        else setLoadingMore(false);
        setRefreshing(false);
      }
    },
    [authenticatedRequest, t],
  );

  useEffect(() => {
    load();
  }, [load]);

  if (loading && !items.length) return <FullScreenLoader label={t.loading} />;

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl onRefresh={() => load(1, true)} refreshing={refreshing} tintColor={colors.orange} />}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <TextButton label={t.back} onPress={() => navigation.goBack()} />
          <BrandMark compact />
          <LanguageSelector />
        </View>
        <View style={styles.intro}>
          <AppText accessibilityRole="header" variant="title">{t.myNarratives}</AppText>
          <AppText style={styles.description}>{t.myNarrativesIntro}</AppText>
        </View>
        <PrimaryButton icon={<Ionicons color={colors.primaryButtonText} name="add" size={19} />} label={t.newNarrative} onPress={() => navigation.navigate("NarrativeComposer")} />
        {error && items.length ? <InlineNotice message={error} /> : null}
        {error && !items.length ? <ErrorState actionLabel={t.retry} description={error} onRetry={() => load(1)} title={t.genericError} /> : null}
        {!error && !items.length ? <EmptyState description={t.noNarrativesDescription} icon="document-text-outline" title={t.noNarrativesTitle} /> : null}
        <View style={styles.list}>
          {items.map((narrative) => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={narrative.content}
              key={narrative.id}
              onPress={() => navigation.navigate("NarrativeDetail", { narrativeId: narrative.id })}
              style={({ pressed }) => [styles.card, pressed && styles.pressed]}
            >
              <View style={styles.cardTop}>
                <StatusPill label={ownerNarrativeStatusLabel(narrative, t)} tone={ownerNarrativeTone(narrative)} />
                <Ionicons color={colors.muted} name="chevron-forward" size={19} />
              </View>
              <AppText numberOfLines={4} style={styles.content}>{narrative.content}</AppText>
              <View style={styles.metaRow}>
                <AppText style={styles.meta}>{t.version} {narrative.version}</AppText>
                <AppText style={styles.meta}>{formatDate(narrative.updated_at || narrative.submitted_at, language)}</AppText>
              </View>
            </Pressable>
          ))}
        </View>
        {hasMore ? (
          <SecondaryButton
            label={t.loadMore}
            loading={loadingMore}
            onPress={() => load(items.length ? Math.floor(items.length / 20) + 1 : 1)}
          />
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.creamLight },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.huge + 88, gap: spacing.lg },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  intro: { marginTop: spacing.xl },
  description: { marginTop: spacing.sm, maxWidth: 360 },
  list: { gap: spacing.md },
  card: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surface, gap: spacing.md, ...getShadows(colors).card },
  pressed: { opacity: 0.82, transform: [{ scale: 0.99 }] },
  cardTop: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  content: { color: colors.primaryText, fontSize: 16, lineHeight: 24 },
  metaRow: { flexDirection: "row", justifyContent: "space-between", gap: spacing.sm },
  meta: { color: colors.muted, fontSize: 12 },
});
