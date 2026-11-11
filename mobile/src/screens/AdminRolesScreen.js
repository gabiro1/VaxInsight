import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { AdminAccessDenied, AdminHeader } from "../components/AdminComponents";
import { AppText } from "../components/AppText";
import { EmptyState, ErrorState } from "../components/StateView";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getErrorMessage, roleLabel } from "../utils/errors";
import { getShadows, layout, radii, spacing } from "../theme/tokens";

export function AdminRolesScreen({ navigation }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest, user } = useAuth();
  const isAdmin = user?.role === "administrator";
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!isAdmin) return;
    setLoading(true);
    setError("");
    try {
      const result = await authenticatedRequest((token) => api.listAdminRoles(token));
      setRoles(result?.items || []);
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
  if (loading && !roles.length) return <ActivityIndicator color={colors.orange} style={styles.loader} />;

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <AdminHeader description={t.adminRolesIntro} navigation={navigation} title={t.adminRoles} />
        {error && !roles.length ? <ErrorState actionLabel={t.retry} description={error} onRetry={load} title={t.genericError} /> : null}
        {error && roles.length ? <ErrorState actionLabel={t.retry} description={error} onRetry={load} title={t.genericError} /> : null}
        {!loading && !error && !roles.length ? <EmptyState description={t.emptyDescription} icon="key-outline" title={t.emptyTitle} /> : null}
        <View style={styles.list}>
          {roles.map((item) => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={roleLabel(item.role, t)}
              key={item.role}
              onPress={() => navigation.navigate("AdminRoleDetail", { role: item.role })}
              style={({ pressed }) => [styles.card, pressed && styles.pressed]}
            >
              <View style={styles.iconCircle}><Ionicons color={colors.orange} name="key-outline" size={21} /></View>
              <View style={styles.copy}>
                <AppText variant="card">{roleLabel(item.role, t)}</AppText>
                <AppText style={styles.meta}>{t.permissionCount.replace("{count}", item.permissions?.length || 0)}</AppText>
              </View>
              <Ionicons color={colors.muted} name="chevron-forward" size={20} />
            </Pressable>
          ))}
        </View>
        <Pressable accessibilityRole="button" accessibilityLabel={t.adminPermissions} onPress={() => navigation.navigate("AdminPermissions")} style={({ pressed }) => [styles.catalogueLink, pressed && styles.pressed]}>
          <Ionicons color={colors.orange} name="list-outline" size={20} />
          <AppText style={styles.catalogueLabel}>{t.adminPermissions}</AppText>
          <Ionicons color={colors.orange} name="arrow-forward" size={18} />
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  loader: { flex: 1, backgroundColor: colors.background },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl, gap: spacing.lg },
  list: { gap: spacing.sm },
  card: { minHeight: 78, padding: spacing.md, borderRadius: radii.md, backgroundColor: colors.surface, flexDirection: "row", alignItems: "center", gap: spacing.sm, ...getShadows(colors).card },
  pressed: { opacity: 0.78 },
  iconCircle: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.orangeLight },
  copy: { flex: 1, gap: spacing.xxs },
  meta: { color: colors.muted, fontSize: 13 },
  catalogueLink: { minHeight: 52, paddingHorizontal: spacing.md, borderRadius: radii.md, backgroundColor: colors.surface, flexDirection: "row", alignItems: "center", gap: spacing.sm, ...getShadows(colors).card },
  catalogueLabel: { flex: 1, color: colors.orange, fontFamily: "DMSans_600SemiBold", fontSize: 14 },
});
