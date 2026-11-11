import { Ionicons } from "@expo/vector-icons";
import { ActivityIndicator, StyleSheet, View } from "react-native";

import { useTheme } from "../context/ThemeContext";
import { layout, spacing } from "../theme/tokens";
import { AppText } from "./AppText";
import { PrimaryButton } from "./PrimaryButton";

export function FullScreenLoader({ label }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <View style={styles.fullScreen}>
      <ActivityIndicator color={colors.orange} size="small" />
      {label ? <AppText style={styles.supporting}>{label}</AppText> : null}
    </View>
  );
}

export function EmptyState({ title, description, icon = "file-tray-outline" }) {
  return <StateView description={description} icon={icon} title={title} />;
}

export function ErrorState({ title, description, actionLabel, onRetry, icon = "alert-circle-outline" }) {
  return (
    <StateView
      actionLabel={actionLabel}
      description={description}
      icon={icon}
      onRetry={onRetry}
      title={title}
    />
  );
}

export function OfflineState({ title, description, actionLabel, onRetry }) {
  return (
    <StateView
      actionLabel={actionLabel}
      description={description}
      icon="cloud-offline-outline"
      onRetry={onRetry}
      title={title}
    />
  );
}

function StateView({ title, description, icon, actionLabel, onRetry }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <View accessibilityRole="alert" style={styles.state}>
      <View style={styles.iconCircle}>
        <Ionicons color={colors.orange} name={icon} size={26} />
      </View>
      <AppText accessibilityRole="header" variant="section" style={styles.title}>{title}</AppText>
      {description ? <AppText style={styles.description}>{description}</AppText> : null}
      {actionLabel && onRetry ? <PrimaryButton label={actionLabel} onPress={onRetry} /> : null}
    </View>
  );
}

const createStyles = (colors) => StyleSheet.create({
  fullScreen: { flex: 1, backgroundColor: colors.creamLight, alignItems: "center", justifyContent: "center", padding: layout.gutter },
  supporting: { marginTop: spacing.sm, textAlign: "center" },
  state: { alignItems: "center", justifyContent: "center", padding: layout.gutter, minHeight: 240 },
  iconCircle: { width: 60, height: 60, borderRadius: 30, backgroundColor: colors.orangeLight, alignItems: "center", justifyContent: "center" },
  title: { textAlign: "center", marginTop: spacing.md },
  description: { textAlign: "center", maxWidth: 340, marginTop: spacing.xs, marginBottom: spacing.lg },
});
