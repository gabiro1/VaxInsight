import { StyleSheet, View } from "react-native";

import { AppText } from "./AppText";
import { useTheme } from "../context/ThemeContext";
import { typography } from "../theme/tokens";

export function BrandMark({ inverse = false, compact = false }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <View accessibilityRole="image" accessibilityLabel="VaxInsight" style={styles.row}>
      <AppText
        style={[
          styles.wordmark,
          compact && styles.compact,
          { color: inverse ? colors.inverseText : colors.primaryText },
        ]}
      >
        VaxInsight
      </AppText>
      <View style={[styles.dot, compact && styles.compactDot]} />
    </View>
  );
}

const createStyles = (colors) => StyleSheet.create({
  row: { flexDirection: "row", alignItems: "flex-end" },
  wordmark: {
    fontFamily: typography.family.heading,
    fontSize: 22,
    lineHeight: 25,
    letterSpacing: -0.6,
  },
  compact: { fontSize: 19, lineHeight: 22 },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.primaryAccent,
    marginBottom: 2,
    marginLeft: 2,
  },
  compactDot: { width: 5, height: 5, borderRadius: 2.5, marginBottom: 2 },
});
