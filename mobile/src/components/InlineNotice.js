import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import { useTheme } from "../context/ThemeContext";
import { radii, spacing, typography } from "../theme/tokens";
import { AppText } from "./AppText";

export function InlineNotice({ message, tone = "error" }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  if (!message) return null;
  const palette = tone === "success"
    ? { background: colors.successBackground, icon: colors.success, text: colors.success, name: "checkmark-circle-outline" }
    : { background: colors.errorBackground, icon: colors.error, text: colors.error, name: "alert-circle-outline" };

  return (
    <View accessibilityRole="alert" style={[styles.notice, { backgroundColor: palette.background }]}> 
      <Ionicons color={palette.icon} name={palette.name} size={19} />
      <AppText style={[styles.text, { color: palette.text }]}>{message}</AppText>
    </View>
  );
}

const createStyles = (colors) => StyleSheet.create({
  notice: {
    borderRadius: radii.sm,
    padding: spacing.sm,
    flexDirection: "row",
    gap: spacing.xs,
    alignItems: "flex-start",
  },
  text: {
    flex: 1,
    fontFamily: typography.family.bodyMedium,
    fontSize: 13,
    lineHeight: 19,
  },
});
