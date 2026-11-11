import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useState } from "react";
import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import {
  AdminAccessDenied,
  AdminActionRow,
  AdminCard,
  AdminHeader,
  AdminMetric,
} from "../components/AdminComponents";
import { ErrorState, FullScreenLoader } from "../components/StateView";
import { PrimaryButton } from "../components/PrimaryButton";
import { AppText } from "../components/AppText";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getErrorMessage } from "../utils/errors";
import { layout, spacing, typography } from "../theme/tokens";

export function AdminDashboardScreen({ navigation }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest, user } = useAuth();
  const isAdmin = user?.role === "administrator";
  const [summary, setSummary] = useState(null);
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
          api.getAdminDashboardSummary(token),
        );
        setSummary(result);
      } catch (requestError) {
        setError(getErrorMessage(requestError, t));
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [authenticatedRequest, isAdmin, t],
  );

  useEffect(() => {
    load();
  }, [load]);

  if (!isAdmin) return <AdminAccessDenied navigation={navigation} />;
  if (loading && !summary) return <FullScreenLoader label={t.loading} />;
  if (error && !summary) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.content}>
          <AdminHeader
            description={t.adminDashboardIntro}
            navigation={navigation}
            showBack={false}
            title={t.adminDashboard}
          />
          <ErrorState actionLabel={t.retry} description={error} onRetry={() => load()} title={t.genericError} />
        </View>
      </SafeAreaView>
    );
  }

  const users = summary?.users || {};
  const invitations = summary?.invitations || {};
  const sessions = summary?.sessions || {};
  const roles = users.by_role || {};

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl onRefresh={() => load(true)} refreshing={refreshing} tintColor={colors.orange} />}
        showsVerticalScrollIndicator={false}
      >
        <AdminHeader
          description={t.adminDashboardIntro}
          navigation={navigation}
          showBack={false}
          title={t.adminDashboard}
        />
        {error ? <ErrorState actionLabel={t.retry} description={error} onRetry={() => load()} title={t.genericError} /> : null}

        <View style={styles.metricGrid}>
          <AdminMetric icon="people-outline" label={t.totalUsers} value={users.total} onPress={() => navigation.navigate("AdminUsers")} />
          <AdminMetric icon="shield-checkmark-outline" label={t.activeUsers} value={users.active} onPress={() => navigation.navigate("AdminUsers", { status: "active" })} />
          <AdminMetric icon="mail-unread-outline" label={t.invitationsPending} value={invitations.pending} onPress={() => navigation.navigate("AdminInvitations", { status: "pending" })} />
          <AdminMetric icon="phone-portrait-outline" label={t.activeSessions} value={sessions.active} />
        </View>

        <AdminCard>
          <View style={styles.sectionHeading}>
            <View style={styles.sectionIcon}>
              <Ionicons color={colors.orange} name="people-circle-outline" size={22} />
            </View>
            <AppText variant="section">{t.roleBreakdown}</AppText>
          </View>
          <View style={styles.roleList}>
            {[
              [t.communityMember, roles.community_member],
              [t.chw, roles.chw],
              [t.reviewer, roles.reviewer],
              [t.administrator, roles.administrator],
              [t.unassigned, roles.unassigned],
            ].map(([label, value]) => (
              <View key={label} style={styles.roleRow}>
                <AppText style={styles.roleLabel}>{label}</AppText>
                <AppText style={styles.roleValue}>{value ?? 0}</AppText>
              </View>
            ))}
          </View>
        </AdminCard>

        <View style={styles.actionsSection}>
          <AppText variant="section">{t.adminQuickActions}</AppText>
          <AdminCard style={styles.actionCard}>
            <AdminActionRow description={t.adminViewUsersIntro} icon="people-outline" onPress={() => navigation.navigate("AdminUsers")} title={t.adminViewUsers} />
            <AdminActionRow description={t.adminViewInvitationsIntro} icon="mail-outline" onPress={() => navigation.navigate("AdminInvitations")} title={t.adminViewInvitations} />
            <AdminActionRow description={t.adminViewAuditIntro} icon="finger-print-outline" onPress={() => navigation.navigate("AdminAudit")} title={t.adminViewAudit} />
            <AdminActionRow description={t.adminViewRolesIntro} icon="key-outline" onPress={() => navigation.navigate("AdminRoles")} title={t.adminViewRoles} />
            <AdminActionRow description={t.adminViewPermissionsIntro} icon="list-outline" onPress={() => navigation.navigate("AdminPermissions")} title={t.adminViewPermissions} />
            <AdminActionRow description={t.adminManageContentIntro} icon="shield-checkmark-outline" onPress={() => navigation.navigate("AdminContent")} title={t.adminManageContent} />
          </AdminCard>
          <PrimaryButton label={t.adminInviteStaff} onPress={() => navigation.navigate("AdminInvite")} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  content: { flex: 1, padding: layout.gutter },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.huge + 88, gap: spacing.lg },
  metricGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  sectionHeading: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  sectionIcon: { width: 42, height: 42, borderRadius: 21, alignItems: "center", justifyContent: "center", backgroundColor: colors.orangeLight },
  roleList: { marginTop: spacing.lg, gap: spacing.sm },
  roleRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: spacing.xs, borderBottomWidth: 1, borderBottomColor: colors.divider },
  roleLabel: { color: colors.secondaryText },
  roleValue: { fontFamily: typography.family.bodyBold, color: colors.primaryText },
  actionsSection: { gap: spacing.md },
  actionCard: { paddingVertical: spacing.xs },
});
