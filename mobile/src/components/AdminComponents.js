import { Ionicons } from "@expo/vector-icons";
import { Pressable, SafeAreaView, StyleSheet, View } from "react-native";

import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, layout, radii, spacing, typography } from "../theme/tokens";
import { AppText } from "./AppText";
import { BrandMark } from "./BrandMark";
import { ErrorState } from "./StateView";
import { LanguageSelector } from "./LanguageSelector";
import { SecondaryButton, TextButton } from "./PrimaryButton";

export function AdminHeader({ navigation, title, description, showBack = true }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);

  return (
    <>
      <View style={styles.header}>
        <View style={styles.headerSide}>
          {showBack ? <TextButton label={t.back} onPress={() => navigation.goBack()} /> : null}
        </View>
        <BrandMark compact />
        <View style={[styles.headerSide, styles.headerRight]}>
          <LanguageSelector />
        </View>
      </View>
      <View style={styles.intro}>
        <AppText accessibilityRole="header" variant="title">{title}</AppText>
        {description ? <AppText style={styles.description}>{description}</AppText> : null}
      </View>
    </>
  );
}

export function AdminCard({ children, style }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return <View style={[styles.card, style]}>{children}</View>;
}

export function AdminMetric({ icon, label, value, onPress }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const content = (
    <>
      <View style={styles.metricIcon}>
        <Ionicons color={colors.orange} name={icon} size={21} />
      </View>
      <AppText style={styles.metricValue}>{String(value ?? 0)}</AppText>
      <AppText style={styles.metricLabel}>{label}</AppText>
    </>
  );

  if (!onPress) return <View style={styles.metric}>{content}</View>;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${label}: ${value ?? 0}`}
      onPress={onPress}
      style={({ pressed }) => [styles.metric, pressed && styles.pressed]}
    >
      {content}
    </Pressable>
  );
}

export function AdminActionRow({ icon, title, description, onPress }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={title}
      onPress={onPress}
      style={({ pressed }) => [styles.actionRow, pressed && styles.pressed]}
    >
      <View style={styles.actionIcon}>
        <Ionicons color={colors.orange} name={icon} size={21} />
      </View>
      <View style={styles.actionCopy}>
        <AppText variant="card">{title}</AppText>
        {description ? <AppText style={styles.actionDescription}>{description}</AppText> : null}
      </View>
      <Ionicons color={colors.muted} name="chevron-forward" size={20} />
    </Pressable>
  );
}

export function ChoiceChip({ label, selected, onPress, accessibilityLabel, disabled = false }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel || label}
      accessibilityState={{ disabled, selected }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.chip,
        selected && styles.selectedChip,
        disabled && styles.disabledChip,
        pressed && styles.pressedChip,
      ]}
    >
      <AppText style={[styles.chipLabel, selected && styles.selectedChipLabel]}>{label}</AppText>
    </Pressable>
  );
}

export function AdminPagination({ page, totalPages, onPrevious, onNext }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  if (!totalPages || totalPages <= 1) return null;

  return (
    <View style={styles.pagination}>
      <SecondaryButton disabled={page <= 1} label={t.previous} onPress={onPrevious} />
      <AppText style={styles.pageLabel}>{t.pageOf.replace("{page}", page).replace("{total}", totalPages)}</AppText>
      <SecondaryButton disabled={page >= totalPages} label={t.next} onPress={onNext} />
    </View>
  );
}

export function AdminAccessDenied({ navigation }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.accessContent}>
        <AdminHeader navigation={navigation} title={t.adminAccessDeniedTitle} />
        <ErrorState
          actionLabel={t.back}
          description={t.adminAccessDeniedDescription}
          onRetry={() => (navigation.canGoBack() ? navigation.goBack() : navigation.navigate("Home"))}
          title={t.notAuthorized}
        />
      </View>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  accessContent: { flex: 1, padding: layout.gutter },
  header: {
    minHeight: 48,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  headerSide: { width: 92, minHeight: 44, justifyContent: "center" },
  headerRight: { alignItems: "flex-end" },
  intro: { marginTop: spacing.xl, gap: spacing.sm },
  description: { maxWidth: 370, lineHeight: 22 },
  card: {
    padding: spacing.lg,
    borderRadius: radii.lg,
    backgroundColor: colors.surface,
    ...getShadows(colors).card,
  },
  metric: {
    flex: 1,
    minWidth: 140,
    minHeight: 142,
    padding: spacing.md,
    borderRadius: radii.md,
    backgroundColor: colors.surface,
    gap: spacing.xs,
    ...getShadows(colors).card,
  },
  metricIcon: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.orangeLight,
  },
  metricValue: {
    marginTop: spacing.xs,
    fontFamily: typography.family.display,
    fontSize: 26,
    lineHeight: 30,
    color: colors.primaryText,
  },
  metricLabel: { color: colors.secondaryText, fontSize: 13, lineHeight: 18 },
  actionRow: {
    minHeight: 72,
    paddingVertical: spacing.sm,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  actionIcon: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.orangeLight,
  },
  actionCopy: { flex: 1, gap: spacing.xxs },
  actionDescription: { color: colors.secondaryText, fontSize: 12, lineHeight: 17 },
  pressed: { opacity: 0.78 },
  chip: {
    minHeight: 42,
    paddingHorizontal: spacing.md,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    justifyContent: "center",
  },
  selectedChip: { borderColor: colors.orange, backgroundColor: colors.orangeLight },
  disabledChip: { opacity: 0.42 },
  pressedChip: { opacity: 0.72 },
  chipLabel: { color: colors.secondaryText, fontSize: 13, fontFamily: typography.family.bodyMedium },
  selectedChipLabel: { color: colors.orange, fontFamily: typography.family.bodySemibold },
  pagination: { alignItems: "center", gap: spacing.sm },
  pageLabel: { color: colors.secondaryText, fontSize: 13 },
});
