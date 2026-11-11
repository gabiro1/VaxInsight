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
import { ConfirmDialog } from "../components/ConfirmDialog";
import { EmptyState, ErrorState } from "../components/StateView";
import { InlineNotice } from "../components/InlineNotice";
import { InputField } from "../components/InputField";
import { PrimaryButton } from "../components/PrimaryButton";
import { StatusPill } from "../components/StatusPill";
import { Toast } from "../components/Toast";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { formatDate, getErrorMessage, invitationStatusLabel, roleLabel } from "../utils/errors";
import { getShadows, layout, radii, spacing, typography } from "../theme/tokens";

const PAGE_SIZE = 20;
const staffRoles = ["chw", "reviewer", "administrator"];
const invitationStatuses = ["pending", "accepted", "revoked", "expired"];

export function AdminInvitationsScreen({ navigation, route }) {
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest, user } = useAuth();
  const isAdmin = user?.role === "administrator";
  const requestedStatus = route?.params?.status || null;
  const requestedNotice = route?.params?.notice || "";
  const [items, setItems] = useState([]);
  const [searchInput, setSearchInput] = useState("");
  const [filters, setFilters] = useState({
    search: "",
    role: null,
    status: requestedStatus,
  });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [toast, setToast] = useState(requestedNotice);
  const [invitationToRevoke, setInvitationToRevoke] = useState(null);
  const [revoking, setRevoking] = useState(false);

  const load = useCallback(
    async (isRefresh = false) => {
      if (!isAdmin) return;
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError("");
      try {
        const result = await authenticatedRequest((token) =>
          api.listAdminInvitations(token, {
            page,
            page_size: PAGE_SIZE,
            search: filters.search || undefined,
            role: filters.role || undefined,
            status: filters.status || undefined,
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

  const revokeInvitation = async () => {
    if (!invitationToRevoke) return;
    setRevoking(true);
    setError("");
    try {
      await authenticatedRequest((token) => api.revokeAdminInvitation(token, invitationToRevoke.id));
      setNotice(t.invitationRevoked);
      setInvitationToRevoke(null);
      await load(true);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setRevoking(false);
    }
  };

  if (!isAdmin) return <AdminAccessDenied navigation={navigation} />;

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl onRefresh={() => load(true)} refreshing={refreshing} tintColor={colors.orange} />}
        showsVerticalScrollIndicator={false}
      >
        <AdminHeader description={t.adminInvitationsIntro} navigation={navigation} title={t.adminInvitations} />
        <PrimaryButton label={t.inviteStaff} onPress={() => navigation.navigate("AdminInvite")} />
        {error ? <InlineNotice message={error} /> : null}
        {notice ? <InlineNotice message={notice} tone="success" /> : null}
        <InputField
          autoCapitalize="none"
          autoCorrect={false}
          label={t.searchUsers}
          onChangeText={setSearchInput}
          onSubmitEditing={submitSearch}
          placeholder="staff@example.com"
          returnKeyType="search"
          value={searchInput}
        />
        <View style={styles.filterSection}>
          <AppText style={styles.filterLabel}>{t.filters}</AppText>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
            <ChoiceChip label={t.allRoles} onPress={() => setFilter("role", null)} selected={!filters.role} />
            {staffRoles.map((role) => (
              <ChoiceChip key={role} label={roleLabel(role, t)} onPress={() => setFilter("role", role)} selected={filters.role === role} />
            ))}
          </ScrollView>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
            <ChoiceChip label={t.allStatuses} onPress={() => setFilter("status", null)} selected={!filters.status} />
            {invitationStatuses.map((status) => (
              <ChoiceChip key={status} label={invitationStatusLabel(status, t)} onPress={() => setFilter("status", status)} selected={filters.status === status} />
            ))}
          </ScrollView>
        </View>
        <View style={styles.resultsHeading}>
          <AppText variant="section">{t.pendingInvitations}</AppText>
          <AppText style={styles.resultCount}>{total}</AppText>
        </View>
        {loading && !items.length ? <ActivityIndicator color={colors.orange} /> : null}
        {error && !items.length && !loading ? <ErrorState actionLabel={t.retry} description={error} onRetry={() => load()} title={t.genericError} /> : null}
        {!loading && !error && !items.length ? <EmptyState description={t.noInvitationsDescription} icon="mail-outline" title={t.noInvitationsTitle} /> : null}
        <View style={styles.list}>
          {items.map((item) => (
            <View key={item.id} style={styles.invitationCard}>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={`${item.email}, ${invitationStatusLabel(item.status, t)}`}
                onPress={() => navigation.navigate("AdminInvitationDetail", { invitationId: item.id })}
                style={({ pressed }) => [styles.cardBody, pressed && styles.pressed]}
              >
                <View style={styles.cardTop}>
                  <View style={styles.mailIcon}><Ionicons color={colors.orange} name="mail-outline" size={20} /></View>
                  <View style={styles.copy}>
                    <AppText variant="card" numberOfLines={1}>{item.email}</AppText>
                    <AppText style={styles.meta}>{roleLabel(item.role, t)}</AppText>
                  </View>
                  <Ionicons color={colors.muted} name="chevron-forward" size={20} />
                </View>
                <View style={styles.statusRow}>
                  <StatusPill label={invitationStatusLabel(item.status, t)} tone={item.status === "pending" ? "warning" : item.status === "accepted" ? "success" : "neutral"} />
                  <AppText style={styles.meta}>{t.invitationExpiry}: {formatDate(item.expires_at, language)}</AppText>
                </View>
              </Pressable>
              {item.status === "pending" ? (
                <Pressable accessibilityRole="button" accessibilityLabel={t.revokeInvitation} onPress={() => setInvitationToRevoke(item)} style={({ pressed }) => [styles.revokeButton, pressed && styles.pressed]}>
                  <Ionicons color={colors.error} name="close-circle-outline" size={18} />
                  <AppText style={styles.revokeLabel}>{t.revokeInvitation}</AppText>
                </Pressable>
              ) : null}
            </View>
          ))}
        </View>
        <AdminPagination onNext={() => setPage((current) => Math.min(current + 1, totalPages))} onPrevious={() => setPage((current) => Math.max(current - 1, 1))} page={page} totalPages={totalPages} />
      </ScrollView>
      <Toast message={toast} onDismiss={() => setToast("")} />
      <ConfirmDialog
        cancelLabel={t.cancel}
        confirmLabel={t.revokeInvitation}
        description={t.revokeInvitationDescription}
        destructive
        onCancel={() => setInvitationToRevoke(null)}
        onConfirm={revokeInvitation}
        title={t.revokeInvitationTitle}
        visible={Boolean(invitationToRevoke)}
      />
      {revoking ? <View style={styles.busyOverlay}><ActivityIndicator color={colors.orange} /></View> : null}
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl, gap: spacing.lg },
  filterSection: { gap: spacing.sm },
  filterLabel: { fontFamily: typography.family.bodySemibold, fontSize: 13, color: colors.primaryText },
  chips: { gap: spacing.xs, paddingRight: spacing.md },
  resultsHeading: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  resultCount: { color: colors.muted, fontSize: 13 },
  list: { gap: spacing.sm },
  invitationCard: { padding: spacing.md, borderRadius: radii.md, backgroundColor: colors.surface, gap: spacing.sm, ...getShadows(colors).card },
  cardBody: { gap: spacing.md },
  pressed: { opacity: 0.78 },
  cardTop: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  mailIcon: { width: 42, height: 42, borderRadius: 21, alignItems: "center", justifyContent: "center", backgroundColor: colors.orangeLight },
  copy: { flex: 1, gap: spacing.xxs },
  meta: { color: colors.muted, fontSize: 12 },
  statusRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm, flexWrap: "wrap" },
  revokeButton: { minHeight: 44, flexDirection: "row", alignItems: "center", gap: spacing.xs, borderTopWidth: 1, borderTopColor: colors.divider, paddingTop: spacing.sm },
  revokeLabel: { color: colors.error, fontFamily: typography.family.bodySemibold, fontSize: 13 },
  busyOverlay: { position: "absolute", left: 0, right: 0, top: 0, bottom: 0, alignItems: "center", justifyContent: "center", backgroundColor: colors.overlay },
});
