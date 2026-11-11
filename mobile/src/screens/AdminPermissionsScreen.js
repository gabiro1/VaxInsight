import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { AdminAccessDenied, AdminCard, AdminHeader } from "../components/AdminComponents";
import { AppText } from "../components/AppText";
import { EmptyState, ErrorState } from "../components/StateView";
import { StatusPill } from "../components/StatusPill";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getErrorMessage } from "../utils/errors";
import { layout, spacing } from "../theme/tokens";

export function AdminPermissionsScreen({ navigation }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest, user } = useAuth();
  const isAdmin = user?.role === "administrator";
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!isAdmin) return;
    setLoading(true);
    setError("");
    try {
      const result = await authenticatedRequest((token) => api.listAdminPermissions(token));
      setItems(result?.items || []);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setLoading(false);
    }
  }, [authenticatedRequest, isAdmin, t]);

  useEffect(() => {
    load();
  }, [load]);

  if (!isAdmin) return <AdminAccessDenied navigation={navigation} />;
  if (loading && !items.length) return <ActivityIndicator color={colors.orange} style={styles.loader} />;

  const implemented = items.filter((item) => item.implemented);
  const reserved = items.filter((item) => !item.implemented);

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <AdminHeader description={t.adminPermissionsIntro} navigation={navigation} title={t.adminPermissions} />
        {error && !items.length ? <ErrorState actionLabel={t.retry} description={error} onRetry={load} title={t.genericError} /> : null}
        {!loading && !error && !items.length ? <EmptyState description={t.emptyDescription} icon="list-outline" title={t.emptyTitle} /> : null}
        {implemented.length ? (
          <PermissionGroup items={implemented} assignableLabel={t.assignable} label={t.implemented} tone="success" title={t.implemented} />
        ) : null}
        {reserved.length ? (
          <PermissionGroup items={reserved} assignableLabel={t.notAssignable} label={t.reserved} tone="warning" title={t.reserved} />
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

function PermissionGroup({ items, assignableLabel, label, title, tone }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <View style={styles.group}>
      <View style={styles.groupHeading}>
        <AppText variant="section">{title}</AppText>
        <StatusPill label={label} tone={tone} />
      </View>
      <AdminCard>
        <View style={styles.list}>
          {items.map((item) => (
            <View key={item.name} style={styles.permissionRow}>
              <View style={styles.copy}>
                <AppText variant="card">{item.name}</AppText>
                <AppText style={styles.description}>{item.description}</AppText>
              </View>
              <StatusPill label={assignableLabel} tone={item.assignable ? "success" : "neutral"} />
            </View>
          ))}
        </View>
      </AdminCard>
    </View>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  loader: { flex: 1, backgroundColor: colors.background },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl, gap: spacing.lg },
  group: { gap: spacing.sm },
  groupHeading: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.sm },
  list: { gap: spacing.xs },
  permissionRow: { minHeight: 70, paddingVertical: spacing.xs, flexDirection: "row", alignItems: "center", gap: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.divider },
  copy: { flex: 1, gap: spacing.xxs },
  description: { color: colors.secondaryText, fontSize: 12, lineHeight: 18 },
});
