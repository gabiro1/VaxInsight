import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import {
  AdminAccessDenied,
  AdminHeader,
  AdminPagination,
  ChoiceChip,
} from "../components/AdminComponents";
import { AppText } from "../components/AppText";
import { EmptyState, ErrorState } from "../components/StateView";
import { InputField } from "../components/InputField";
import { StatusPill } from "../components/StatusPill";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import {
  accountStatusLabel,
  formatDate,
  getErrorMessage,
  roleLabel,
} from "../utils/errors";
import { getShadows, layout, radii, spacing } from "../theme/tokens";

const PAGE_SIZE = 20;
const roles = ["community_member", "chw", "reviewer", "administrator"];
const statuses = ["active", "pending", "suspended", "deactivated", "deleted"];

export function AdminUsersScreen({ navigation, route }) {
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest, user } = useAuth();
  const isAdmin = user?.role === "administrator";
  const requestedStatus = route?.params?.status || null;
  const [items, setItems] = useState([]);
  const [searchInput, setSearchInput] = useState("");
  const [filters, setFilters] = useState({
    search: "",
    role: null,
    status: requestedStatus,
    emailVerified: null,
  });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(
    async (isRefresh = false) => {
      if (!isAdmin) return;
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError("");
      try {
        const result = await authenticatedRequest((token) =>
          api.listAdminUsers(token, {
            page,
            page_size: PAGE_SIZE,
            search: filters.search || undefined,
            role: filters.role || undefined,
            status: filters.status || undefined,
            email_verified: filters.emailVerified ?? undefined,
            sort_by: "created_at",
            sort_order: "desc",
          }),
        );
        setItems(result?.items || []);
        setTotalPages(result?.total_pages || 1);
        setTotal(result?.total || 0);
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

  useEffect(() => {
    if (requestedStatus && requestedStatus !== filters.status) {
      setPage(1);
      setFilters((current) => ({ ...current, status: requestedStatus }));
    }
  }, [requestedStatus]);

  const setFilter = (name, value) => {
    setPage(1);
    setFilters((current) => ({ ...current, [name]: value }));
  };

  const submitSearch = () => {
    setPage(1);
    setFilters((current) => ({ ...current, search: searchInput.trim() }));
  };

  if (!isAdmin) return <AdminAccessDenied navigation={navigation} />;

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl onRefresh={() => load(true)} refreshing={refreshing} tintColor={colors.orange} />}
        showsVerticalScrollIndicator={false}
      >
        <AdminHeader description={t.adminUsersIntro} navigation={navigation} title={t.adminUsers} />

        <InputField
          autoCapitalize="none"
          autoCorrect={false}
          label={t.searchUsers}
          onChangeText={setSearchInput}
          onSubmitEditing={submitSearch}
          placeholder="person@example.com"
          returnKeyType="search"
          value={searchInput}
        />

        <View style={styles.filterSection}>
          <AppText style={styles.filterLabel}>{t.filters}</AppText>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
            <ChoiceChip label={t.allRoles} onPress={() => setFilter("role", null)} selected={!filters.role} />
            {roles.map((role) => (
              <ChoiceChip key={role} label={roleLabel(role, t)} onPress={() => setFilter("role", role)} selected={filters.role === role} />
            ))}
          </ScrollView>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
            <ChoiceChip label={t.allStatuses} onPress={() => setFilter("status", null)} selected={!filters.status} />
            {statuses.map((status) => (
              <ChoiceChip key={status} label={accountStatusLabel(status, t)} onPress={() => setFilter("status", status)} selected={filters.status === status} />
            ))}
          </ScrollView>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
            <ChoiceChip label={t.allVerification} onPress={() => setFilter("emailVerified", null)} selected={filters.emailVerified === null} />
            <ChoiceChip label={t.verified} onPress={() => setFilter("emailVerified", true)} selected={filters.emailVerified === true} />
            <ChoiceChip label={t.unverified} onPress={() => setFilter("emailVerified", false)} selected={filters.emailVerified === false} />
          </ScrollView>
        </View>

        <View style={styles.resultsHeading}>
          <AppText variant="section">{t.accountDirectory}</AppText>
          <AppText style={styles.resultCount}>{total}</AppText>
        </View>

        {loading && !items.length ? <ActivityIndicator color={colors.orange} /> : null}
        {error && items.length ? <ErrorState actionLabel={t.retry} description={error} onRetry={() => load()} title={t.genericError} /> : null}
        {error && !items.length && !loading ? <ErrorState actionLabel={t.retry} description={error} onRetry={() => load()} title={t.genericError} /> : null}
        {!loading && !error && !items.length ? <EmptyState description={t.noUsersDescription} icon="people-outline" title={t.noUsersTitle} /> : null}

        <View style={styles.list}>
          {items.map((item) => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`${item.email}, ${roleLabel(item.role, t)}`}
              key={item.id}
              onPress={() => navigation.navigate("AdminUserDetail", { userId: item.id })}
              style={({ pressed }) => [styles.userCard, pressed && styles.pressed]}
            >
              <View style={styles.cardTop}>
                <View style={styles.userIcon}>
                  <Ionicons color={colors.orange} name="person-outline" size={20} />
                </View>
                <View style={styles.userCopy}>
                  <AppText variant="card" numberOfLines={1}>{item.email}</AppText>
                  <AppText style={styles.meta}>{roleLabel(item.role, t)}</AppText>
                </View>
                <Ionicons color={colors.muted} name="chevron-forward" size={20} />
              </View>
              <View style={styles.statusRow}>
                <StatusPill label={accountStatusLabel(item.status, t)} tone={item.status === "active" ? "success" : item.status === "pending" ? "warning" : "neutral"} />
                <AppText style={styles.meta}>{item.email_verified ? t.emailVerified : t.emailNotVerified}</AppText>
                <AppText style={styles.meta}>{formatDate(item.last_login_at || item.created_at, language)}</AppText>
              </View>
            </Pressable>
          ))}
        </View>

        <AdminPagination
          onNext={() => setPage((current) => Math.min(current + 1, totalPages))}
          onPrevious={() => setPage((current) => Math.max(current - 1, 1))}
          page={page}
          totalPages={totalPages}
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl, gap: spacing.lg },
  filterSection: { gap: spacing.sm },
  filterLabel: { fontFamily: "DMSans_600SemiBold", fontSize: 13, color: colors.primaryText },
  chips: { gap: spacing.xs, paddingRight: spacing.md },
  resultsHeading: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  resultCount: { color: colors.muted, fontSize: 13 },
  list: { gap: spacing.sm },
  userCard: { padding: spacing.md, borderRadius: radii.md, backgroundColor: colors.surface, gap: spacing.md, ...getShadows(colors).card },
  pressed: { opacity: 0.78 },
  cardTop: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  userIcon: { width: 42, height: 42, borderRadius: 21, alignItems: "center", justifyContent: "center", backgroundColor: colors.orangeLight },
  userCopy: { flex: 1, gap: spacing.xxs },
  meta: { color: colors.muted, fontSize: 12 },
  statusRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm, flexWrap: "wrap" },
});
