import { Ionicons } from "@expo/vector-icons";
import { useEffect } from "react";
import { StyleSheet, View } from "react-native";

import { useTheme } from "../context/ThemeContext";
import { radii, spacing, typography } from "../theme/tokens";
import { AppText } from "./AppText";

export function Toast({ message, tone = "success", onDismiss, duration = 3200 }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);

  useEffect(() => {
    if (!message) return undefined;
    const timeout = setTimeout(onDismiss, duration);
    return () => clearTimeout(timeout);
  }, [duration, message, onDismiss]);

  if (!message) return null;

  const palette = tone === "error"
    ? { background: colors.error, icon: "alert-circle-outline" }
    : { background: colors.success, icon: "checkmark-circle-outline" };

  return (
    <View pointerEvents="box-none" style={styles.container}>
      <View accessibilityRole="alert" style={[styles.toast, { backgroundColor: palette.background }]}>
        <Ionicons color={colors.primaryButtonText} name={palette.icon} size={19} />
        <AppText style={styles.message}>{message}</AppText>
      </View>
    </View>
  );
}

const createStyles = (colors) => StyleSheet.create({
  container: {
    position: "absolute",
    top: spacing.md,
    left: spacing.md,
    right: spacing.md,
    alignItems: "center",
    zIndex: 10,
  },
  toast: {
    maxWidth: 520,
    minHeight: 48,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radii.pill,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    elevation: 8,
    shadowColor: colors.primaryText,
    shadowOpacity: 0.2,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 5 },
  },
  message: {
    color: colors.primaryButtonText,
    fontFamily: typography.family.bodySemibold,
    fontSize: 13,
    lineHeight: 18,
  },
});
