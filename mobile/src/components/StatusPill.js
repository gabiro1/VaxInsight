import { StyleSheet, View } from "react-native";

import { useTheme } from "../context/ThemeContext";
import { radii, spacing, typography } from "../theme/tokens";
import { AppText } from "./AppText";

export function StatusPill({ label, tone = "neutral" }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const tones = {
    neutral: { background: colors.cream, text: colors.inkSecondary },
    accent: { background: colors.orangeLight, text: colors.orange },
    success: { background: colors.successBackground, text: colors.success },
    warning: { background: colors.warningBackground, text: colors.warning },
  };
  const palette = tones[tone] || tones.neutral;
  return (
    <View style={[styles.pill, { backgroundColor: palette.background }]}>
      <AppText style={[styles.label, { color: palette.text }]}>{label}</AppText>
    </View>
  );
}

const createStyles = (colors) => StyleSheet.create({
  pill: { alignSelf: "flex-start", borderRadius: radii.pill, paddingHorizontal: spacing.sm, paddingVertical: spacing.xxs },
  label: { fontFamily: typography.family.bodySemibold, fontSize: 11 },
});
