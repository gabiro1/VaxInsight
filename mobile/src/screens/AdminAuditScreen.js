import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { AdminAccessDenied, AdminHeader, AdminPagination, ChoiceChip } from "../components/AdminComponents";
import { AppText } from "../components/AppText";
import { EmptyState, ErrorState } from "../components/StateView";
import { InputField } from "../components/InputField";
import { StatusPill } from "../components/StatusPill";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { formatDate, getErrorMessage } from "../utils/errors";
import { getShadows, layout, radii, spacing, typography } from "../theme/tokens";

const PAGE_SIZE = 50;

export function AdminAuditScreen({ navigation }) {
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest, user } = useAuth();
  const isAdmin = user?.role === "administrator";
  const [items, setItems] = useState([]);
  const [actionInput, setActionInput] = useState("");
  const [outcome, setOutcome] = useState(null);
  const [filters, setFilters] = useState({ action: "", outcome: null });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [expandedId, setExpandedId] = useState(null);

  const load = useCallback(
    async (isRefresh = false) => {
      if (!isAdmin) return;
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError("");
      try {
        const result = await authenticatedRequest((token) =>
          api.listAdminAuditEvents(token, {
            page,
            page_size: PAGE_SIZE,
            action: filters.action || undefined,
            outcome: filters.outcome || undefined,
          }),
        );
        setItems(result?.items || []);
        setTotalPages(result?.total_pages || 1);
      } catch (requestError) {
        setError(getErrorMessage(requestError, t));
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [authenticatedRequest, filters, isAdmin, page, t],
  );

  useEffect(() => {
    load();
  }, [load]);

  const submitAction = () => {
    setPage(1);
    setFilters((current) => ({ ...current, action: actionInput.trim() }));
  };

  const setOutcomeFilter = (value) => {
    setPage(1);
    setOutcome(value);
    setFilters((current) => ({ ...current, outcome: value }));
  };

  if (!isAdmin) return <AdminAccessDenied navigation={navigation} />;

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl onRefresh={() => load(true)} refreshing={refreshing} tintColor={colors.orange} />}
        showsVerticalScrollIndicator={false}
      >
        <AdminHeader description={t.adminAuditIntro} navigation={navigation} title={t.adminAudit} />
        <InputField autoCapitalize="none" autoCorrect={false} label={t.actionFilter} onChangeText={setActionInput} onSubmitEditing={submitAction} placeholder="account_status_changed" returnKeyType="search" value={actionInput} />
        <View style={styles.filterSection}>
          <AppText style={styles.filterLabel}>{t.outcomeFilter}</AppText>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
            <ChoiceChip label={t.allOutcomes} onPress={() => setOutcomeFilter(null)} selected={!outcome} />
            <ChoiceChip label={t.success} onPress={() => setOutcomeFilter("success")} selected={outcome === "success"} />
            <ChoiceChip label={t.failure} onPress={() => setOutcomeFilter("failure")} selected={outcome === "failure"} />
          </ScrollView>
        </View>
        {loading && !items.length ? <ActivityIndicator color={colors.orange} /> : null}
        {error && !items.length && !loading ? <ErrorState actionLabel={t.retry} description={error} onRetry={() => load()} title={t.genericError} /> : null}
        {!loading && !error && !items.length ? <EmptyState description={t.noAuditDescription} icon="finger-print-outline" title={t.noAuditTitle} /> : null}
        <View style={styles.list}>
          {items.map((event) => {
            const expanded = expandedId === event.id;
            return (
              <Pressable
                accessibilityRole="button"
                accessibilityState={{ expanded }}
                key={event.id}
                onPress={() => setExpandedId(expanded ? null : event.id)}
                style={({ pressed }) => [styles.eventCard, pressed && styles.pressed]}
              >
                <View style={styles.eventTop}>
                  <View style={styles.eventIcon}><Ionicons color={colors.orange} name="finger-print-outline" size={19} /></View>
                  <View style={styles.eventCopy}>
                    <AppText variant="card">{event.action}</AppText>
                    <AppText style={styles.meta}>{formatDate(event.created_at, language)}</AppText>
                  </View>
                  <StatusPill label={event.outcome === "success" ? t.success : event.outcome} tone={event.outcome === "success" ? "success" : "warning"} />
                </View>
                {expanded ? (
                  <View style={styles.expandedDetails}>
                    <Detail label={t.auditActor} value={event.actor_user_id || t.emptyDescription} />
                    <Detail label={t.auditTarget} value={event.target_user_id || t.emptyDescription} />
                    <Detail label={t.auditDetails} value={Object.entries(event.details || {}).map(([key, value]) => `${key}: ${value}`).join("\n") || t.emptyDescription} />
                    {event.ip_address ? <Detail label="IP" value={event.ip_address} /> : null}
                  </View>
                ) : null}
                <View style={styles.expandHint}>
                  <AppText style={styles.meta}>{expanded ? t.hideDetails : t.auditDetails}</AppText>
                  <Ionicons color={colors.muted} name={expanded ? "chevron-up" : "chevron-down"} size={18} />
                </View>
              </Pressable>
            );
          })}
        </View>
        <AdminPagination onNext={() => setPage((current) => Math.min(current + 1, totalPages))} onPrevious={() => setPage((current) => Math.max(current - 1, 1))} page={page} totalPages={totalPages} />
      </ScrollView>
    </SafeAreaView>
  );
}

function Detail({ label, value }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <View style={styles.detail}>
      <AppText style={styles.detailLabel}>{label}</AppText>
      <AppText style={styles.detailValue}>{value}</AppText>
    </View>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl, gap: spacing.lg },
  filterSection: { gap: spacing.sm },
  filterLabel: { fontFamily: typography.family.bodySemibold, fontSize: 13, color: colors.primaryText },
  chips: { gap: spacing.xs, paddingRight: spacing.md },
  list: { gap: spacing.sm },
  eventCard: { padding: spacing.md, borderRadius: radii.md, backgroundColor: colors.surface, gap: spacing.sm, ...getShadows(colors).card },
  pressed: { opacity: 0.78 },
  eventTop: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  eventIcon: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", backgroundColor: colors.orangeLight },
  eventCopy: { flex: 1, gap: spacing.xxs },
  meta: { color: colors.muted, fontSize: 12 },
  expandedDetails: { paddingTop: spacing.sm, gap: spacing.xs, borderTopWidth: 1, borderTopColor: colors.divider },
  detail: { gap: spacing.xxs },
  detailLabel: { color: colors.muted, fontSize: 12 },
  detailValue: { color: colors.secondaryText, fontSize: 12, lineHeight: 18 },
  expandHint: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
});
