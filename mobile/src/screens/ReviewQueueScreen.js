import { Ionicons } from "@expo/vector-icons";
import { useCallback, useState } from "react";
import { useFocusEffect } from "@react-navigation/native";
import { Pressable, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { formatDate, getErrorMessage, reviewStatusLabel } from "../utils/errors";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, layout, radii, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { EmptyState, ErrorState, FullScreenLoader } from "../components/StateView";
import { InlineNotice } from "../components/InlineNotice";
import { LanguageSelector } from "../components/LanguageSelector";
import { SecondaryButton, TextButton } from "../components/PrimaryButton";
import { StatusPill } from "../components/StatusPill";

export function ReviewQueueScreen({ navigation }) {
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest, user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState("");

  const load = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError("");
      try {
        const result = await authenticatedRequest((token) =>
          api.listAssignments(token, { page: 1, page_size: 20 }),
        );
        setItems(result?.items || []);
        setPage(result?.page || 1);
        setTotalPages(result?.total_pages || 1);
      } catch (requestError) {
        setError(getErrorMessage(requestError, t));
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [authenticatedRequest, t],
  );

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const loadMore = async () => {
    if (loadingMore || page >= totalPages) return;
    const nextPage = page + 1;
    setLoadingMore(true);
    setError("");
    try {
      const result = await authenticatedRequest((token) =>
        api.listAssignments(token, { page: nextPage, page_size: 20 }),
      );
      setItems((current) => [...current, ...(result?.items || [])]);
      setPage(result?.page || nextPage);
      setTotalPages(result?.total_pages || totalPages);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setLoadingMore(false);
    }
  };

  if (loading && !items.length) return <FullScreenLoader label={t.loading} />;

  if (user?.role !== "reviewer") {
    return (
      <SafeAreaView style={styles.safeArea}>
        <ErrorState description={t.notAuthorized} onRetry={() => navigation.goBack()} title={t.notAuthorized} />
      </SafeAreaView>
    );
  }

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
          <AppText accessibilityRole="header" variant="title">{t.reviewQueue}</AppText>
          <AppText style={styles.description}>{t.reviewQueueIntro}</AppText>
          {totalPages > 1 ? <AppText style={styles.pageLabel}>{t.pageOf.replace("{page}", page).replace("{total}", totalPages)}</AppText> : null}
        </View>
        {error && items.length ? <InlineNotice message={error} /> : null}
        {error && !items.length ? <ErrorState actionLabel={t.retry} description={error} onRetry={() => load()} title={t.genericError} /> : null}
        {!error && !items.length ? <EmptyState description={t.noAssignmentsDescription} icon="checkmark-done-outline" title={t.noAssignmentsTitle} /> : null}
        <View style={styles.list}>
          {items.map((assignment) => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={assignment.narrative?.content || t.reviewDetails}
              key={assignment.id}
              onPress={() => navigation.navigate("ReviewDetail", { assignmentId: assignment.id })}
              style={({ pressed }) => [styles.card, pressed && styles.pressed]}
            >
              <View style={styles.cardTop}>
                <StatusPill label={reviewStatusLabel(assignment.review_status, t)} tone={assignment.review_status === "requires_escalation" ? "warning" : assignment.review_status === "reviewed" ? "success" : "accent"} />
                <Ionicons color={colors.muted} name="chevron-forward" size={19} />
              </View>
              <AppText numberOfLines={5} style={styles.content}>{assignment.narrative?.content || t.reviewDetails}</AppText>
              <View style={styles.metaRow}>
                <AppText style={styles.meta}>{t.assignedAt}: {formatDate(assignment.assigned_at, language)}</AppText>
                <AppText style={styles.meta}>{t.updatedAt}: {formatDate(assignment.updated_at, language)}</AppText>
              </View>
            </Pressable>
          ))}
        </View>
        {!error && page < totalPages ? <SecondaryButton label={t.loadMore} loading={loadingMore} onPress={loadMore} /> : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.creamLight },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.huge + 88, gap: spacing.lg },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  intro: { marginTop: spacing.xl, gap: spacing.sm },
  description: { maxWidth: 360 },
  list: { gap: spacing.md },
  card: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surface, gap: spacing.md, ...getShadows(colors).card },
  pressed: { opacity: 0.82, transform: [{ scale: 0.99 }] },
  cardTop: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  content: { color: colors.ink, fontSize: 16, lineHeight: 24 },
  pageLabel: { color: colors.muted, fontSize: 13 },
  metaRow: { flexDirection: "row", justifyContent: "space-between", gap: spacing.sm },
  meta: { color: colors.muted, fontSize: 12 },
});
