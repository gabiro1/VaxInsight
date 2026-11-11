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
import { getErrorMessage, roleLabel } from "../utils/errors";
import { layout, spacing } from "../theme/tokens";

export function AdminRoleDetailScreen({ navigation, route }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest, user } = useAuth();
  const isAdmin = user?.role === "administrator";
  const role = route?.params?.role;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!isAdmin || !role) return;
    setLoading(true);
    setError("");
    try {
      const result = await authenticatedRequest((token) => api.getAdminRole(token, role));
      setData(result);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setLoading(false);
    }
  }, [authenticatedRequest, isAdmin, role, t]);

  useEffect(() => {
    load();
  }, [load]);

  if (!isAdmin) return <AdminAccessDenied navigation={navigation} />;
  if (loading && !data) return <ActivityIndicator color={colors.orange} style={styles.loader} />;

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <AdminHeader description={t.roleDetails} navigation={navigation} title={roleLabel(data?.role || role, t)} />
        {error && !data ? <ErrorState actionLabel={t.retry} description={error} onRetry={load} title={t.genericError} /> : null}
        {!loading && !error && !data?.permissions?.length ? <EmptyState description={t.noPermissions} icon="key-outline" title={t.emptyTitle} /> : null}
        {data ? (
          <AdminCard>
            <AppText variant="section">{t.rolePermissions}</AppText>
            <View style={styles.list}>
              {(data.permissions || []).map((permission) => (
                <View key={permission} style={styles.row}>
                  <AppText style={styles.permission}>{permission}</AppText>
                  <StatusPill label={t.assignable} tone="success" />
                </View>
              ))}
            </View>
          </AdminCard>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  loader: { flex: 1, backgroundColor: colors.background },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl, gap: spacing.lg },
  list: { marginTop: spacing.md, gap: spacing.xs },
  row: { minHeight: 46, paddingVertical: spacing.xs, flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.divider },
  permission: { flex: 1, color: colors.secondaryText, fontSize: 13 },
});
