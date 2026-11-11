import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet } from "react-native";

import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { radii, spacing, typography } from "../theme/tokens";
import { AppText } from "./AppText";

export function LanguageSelector({ inverse = false }) {
  const { language, setLanguage, t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors, inverse);
  const nextLanguage = language === "en" ? "rw" : "en";

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${t.languageSwitchLabel}. ${t.languageName}`}
      accessibilityHint="Double tap to switch language"
      onPress={() => setLanguage(nextLanguage)}
      style={({ pressed }) => [styles.container, pressed && styles.pressed]}
    >
      <Ionicons
        color={inverse ? colors.inverseText : colors.icon}
        name="globe-outline"
        size={16}
      />
      <AppText style={[styles.label, { color: inverse ? colors.inverseText : colors.primaryText }]}>
        {language.toUpperCase()}
      </AppText>
      <Ionicons
        color={inverse ? colors.inverseText : colors.icon}
        name="chevron-down"
        size={14}
      />
    </Pressable>
  );
}

const createStyles = (colors, inverse) => StyleSheet.create({
  container: {
    minHeight: 44,
    paddingHorizontal: spacing.sm,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: inverse ? colors.whiteScrim : colors.border,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
  },
  label: {
    fontFamily: typography.family.bodySemibold,
    fontSize: 12,
    letterSpacing: 0.4,
  },
  pressed: { opacity: 0.72 },
});
