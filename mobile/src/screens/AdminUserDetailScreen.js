import { useCallback, useEffect, useState } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import {
  AdminAccessDenied,
  AdminCard,
  AdminHeader,
  ChoiceChip,
} from "../components/AdminComponents";
import { AppText } from "../components/AppText";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { ErrorState, FullScreenLoader } from "../components/StateView";
import { InlineNotice } from "../components/InlineNotice";
import { PrimaryButton, SecondaryButton } from "../components/PrimaryButton";
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
import { layout, spacing, typography } from "../theme/tokens";

const roles = ["community_member", "chw", "reviewer", "administrator"];
const statuses = ["active", "suspended", "deactivated", "deleted"];

export function AdminUserDetailScreen({ navigation, route }) {
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest, user: currentUser } = useAuth();
  const isAdmin = currentUser?.role === "administrator";
  const userId = route?.params?.userId;
  const [account, setAccount] = useState(null);
  const [permissionData, setPermissionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState("");
  const [selectedRole, setSelectedRole] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");
  const [pendingChange, setPendingChange] = useState(null);

  const load = useCallback(async () => {
    if (!isAdmin || !userId) return;
    setLoading(true);
    setError("");
    try {
      const [accountResult, permissionsResult] = await authenticatedRequest((token) =>
        Promise.all([
          api.getAdminUser(token, userId),
          api.getAdminUserPermissions(token, userId),
        ]),
      );
      setAccount(accountResult);
      setPermissionData(permissionsResult);
      setSelectedRole(accountResult.role || "");
      setSelectedStatus(accountResult.status || "");
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setLoading(false);
    }
  }, [authenticatedRequest, isAdmin, t, userId]);

  useEffect(() => {
    load();
  }, [load]);

  const updateRole = async () => {
    setBusy("role");
    setError("");
    try {
      await authenticatedRequest((token) =>
        api.updateAdminUserRole(token, userId, { role: selectedRole }),
      );
      setNotice(t.roleUpdated);
      await load();
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setBusy("");
      setPendingChange(null);
    }
  };

  const updateStatus = async () => {
    setBusy("status");
    setError("");
    try {
      await authenticatedRequest((token) =>
        api.updateAdminUserStatus(token, userId, { status: selectedStatus }),
      );
      setNotice(t.accountUpdated);
      await load();
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setBusy("");
      setPendingChange(null);
    }
  };

  if (!isAdmin) return <AdminAccessDenied navigation={navigation} />;
  if (loading && !account) return <FullScreenLoader label={t.loading} />;
  if (error && !account) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.content}>
          <AdminHeader navigation={navigation} title={t.adminUserDetails} />
          <ErrorState actionLabel={t.retry} description={error} onRetry={load} title={t.genericError} />
        </View>
      </SafeAreaView>
    );
  }

  const isSelf = account?.id === currentUser?.id;
  const roleChanged = selectedRole !== account?.role;
  const statusChanged = selectedStatus !== account?.status;
  const permissions = permissionData?.permissions || [];

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <AdminHeader description={t.adminUserDetails} navigation={navigation} title={account?.email || t.userDetails} />
        {error ? <InlineNotice message={error} /> : null}
        {notice ? <InlineNotice message={notice} tone="success" /> : null}

        <AdminCard>
          <View style={styles.identityRow}>
            <View style={styles.avatar}><AppText style={styles.avatarText}>{account?.email?.slice(0, 1).toUpperCase()}</AppText></View>
            <View style={styles.identityCopy}>
              <AppText variant="card" numberOfLines={1}>{account?.email}</AppText>
              <AppText style={styles.meta}>{roleLabel(account?.role, t)}</AppText>
            </View>
            <StatusPill label={accountStatusLabel(account?.status, t)} tone={account?.status === "active" ? "success" : account?.status === "pending" ? "warning" : "neutral"} />
          </View>
          <View style={styles.detailGrid}>
            <Detail label={t.emailVerified} value={account?.email_verified ? t.verified : t.emailNotVerified} />
            <Detail label={t.createdAt} value={formatDate(account?.created_at, language)} />
            <Detail label={t.lastLogin} value={account?.last_login_at ? formatDate(account.last_login_at, language) : t.emptyDescription} />
            <Detail label={t.updatedAt} value={formatDate(account?.updated_at, language)} />
          </View>
        </AdminCard>

        <AdminCard>
          <AppText variant="section">{t.changeRole}</AppText>
          <AppText style={styles.helper}>{t.chooseRole}</AppText>
          <View style={styles.chipWrap}>
            {roles.map((role) => (
              <ChoiceChip
                disabled={isSelf && role !== "administrator"}
                key={role}
                label={roleLabel(role, t)}
                onPress={() => setSelectedRole(role)}
                selected={selectedRole === role}
              />
            ))}
          </View>
          {isSelf ? <AppText style={styles.warning}>{t.confirmRoleChangeDescription}</AppText> : null}
          <SecondaryButton disabled={!roleChanged || Boolean(busy)} label={t.saveRole} loading={busy === "role"} onPress={() => setPendingChange({ type: "role" })} />
        </AdminCard>

        <AdminCard>
          <AppText variant="section">{t.changeStatus}</AppText>
          <AppText style={styles.helper}>{t.chooseStatus}</AppText>
          <View style={styles.chipWrap}>
            {statuses.map((status) => (
              <ChoiceChip
                disabled={isSelf && status !== "active"}
                key={status}
                label={accountStatusLabel(status, t)}
                onPress={() => setSelectedStatus(status)}
                selected={selectedStatus === status}
              />
            ))}
          </View>
          {isSelf ? <AppText style={styles.warning}>{t.confirmStatusChangeDescription}</AppText> : null}
          <PrimaryButton disabled={!statusChanged || Boolean(busy)} label={t.saveStatus} loading={busy === "status"} onPress={() => setPendingChange({ type: "status" })} />
        </AdminCard>

        <AdminCard>
          <View style={styles.permissionHeading}>
            <AppText variant="section">{t.effectivePermissions}</AppText>
            <AppText style={styles.meta}>{roleLabel(permissionData?.role, t)}</AppText>
          </View>
          {!permissions.length ? <AppText style={styles.helper}>{t.noPermissions}</AppText> : null}
          <View style={styles.permissionList}>
            {permissions.map((permission) => (
              <View key={permission} style={styles.permissionRow}>
                <AppText style={styles.permissionText}>{permission}</AppText>
                <StatusPill label={t.implemented} tone="success" />
              </View>
            ))}
          </View>
        </AdminCard>
      </ScrollView>
      <ConfirmDialog
        cancelLabel={t.cancel}
        confirmLabel={pendingChange?.type === "role" ? t.saveRole : t.saveStatus}
        description={pendingChange?.type === "role" ? t.confirmRoleChangeDescription : t.confirmStatusChangeDescription}
        onCancel={() => setPendingChange(null)}
        onConfirm={pendingChange?.type === "role" ? updateRole : updateStatus}
        title={pendingChange?.type === "role" ? t.confirmRoleChangeTitle : t.confirmStatusChangeTitle}
        visible={Boolean(pendingChange)}
      />
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
  content: { flex: 1, padding: layout.gutter },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl, gap: spacing.lg },
  identityRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  avatar: { width: 52, height: 52, borderRadius: 26, alignItems: "center", justifyContent: "center", backgroundColor: colors.orangeLight },
  avatarText: { color: colors.orange, fontFamily: typography.family.display, fontSize: 22 },
  identityCopy: { flex: 1, gap: spacing.xxs },
  meta: { color: colors.muted, fontSize: 12 },
  detailGrid: { marginTop: spacing.lg, gap: spacing.sm, borderTopWidth: 1, borderTopColor: colors.divider, paddingTop: spacing.md },
  detail: { flexDirection: "row", justifyContent: "space-between", gap: spacing.md },
  detailLabel: { color: colors.muted, fontSize: 13 },
  detailValue: { flex: 1, color: colors.primaryText, fontSize: 13, textAlign: "right" },
  helper: { color: colors.secondaryText, lineHeight: 20 },
  warning: { color: colors.warning, fontSize: 12, lineHeight: 18 },
  chipWrap: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  permissionHeading: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: spacing.sm },
  permissionList: { marginTop: spacing.md, gap: spacing.xs },
  permissionRow: { minHeight: 42, paddingVertical: spacing.xs, flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.divider },
  permissionText: { color: colors.secondaryText, fontSize: 13, flex: 1 },
});
