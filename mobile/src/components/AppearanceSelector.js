import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, radii, spacing, typography } from "../theme/tokens";
import { AppText } from "./AppText";

const options = [
  { key: "light", icon: "sunny-outline", label: "lightMode", description: "lightModeDescription" },
  { key: "dark", icon: "moon-outline", label: "darkMode", description: "darkModeDescription" },
  { key: "system", icon: "phone-portrait-outline", label: "systemDefault", description: "systemDefaultDescription" },
];

export function AppearanceSelector() {
  const { t } = useLanguage();
  const { colors, preference, setPreference } = useTheme();
  const styles = createStyles(colors);

  return (
    <View style={styles.wrapper}>
      <AppText variant="section">{t.appearance}</AppText>
      <AppText style={styles.description}>{t.appearanceDescription}</AppText>
      <View style={styles.options}>
        {options.map((option) => {
          const selected = preference === option.key;
          return (
            <Pressable
              accessibilityRole="radio"
              accessibilityLabel={t[option.label]}
              accessibilityState={{ selected }}
              key={option.key}
              onPress={() => setPreference(option.key)}
              style={({ pressed }) => [styles.option, selected && styles.selected, pressed && styles.pressed]}
            >
              <View style={[styles.iconCircle, selected && styles.selectedIconCircle]}>
                <Ionicons color={selected ? colors.primaryAccent : colors.icon} name={option.icon} size={21} />
              </View>
              <View style={styles.copy}>
                <AppText style={styles.label}>{t[option.label]}</AppText>
                <AppText style={styles.optionDescription}>{t[option.description]}</AppText>
              </View>
              <Ionicons
                color={selected ? colors.primaryAccent : colors.mutedText}
                name={selected ? "checkmark-circle" : "ellipse-outline"}
                size={23}
              />
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

function createStyles(colors) {
  return StyleSheet.create({
    wrapper: {
      padding: spacing.lg,
      borderRadius: radii.lg,
      backgroundColor: colors.surface,
      gap: spacing.xs,
      ...getShadows(colors).card,
    },
    description: { color: colors.secondaryText, marginBottom: spacing.sm },
    options: { gap: spacing.sm },
    option: {
      minHeight: 72,
      padding: spacing.sm,
      borderRadius: radii.md,
      borderWidth: 1,
      borderColor: colors.border,
      backgroundColor: colors.surfaceSecondary,
      flexDirection: "row",
      alignItems: "center",
      gap: spacing.sm,
    },
    selected: { borderColor: colors.primaryAccent, backgroundColor: colors.accentBackground },
    iconCircle: {
      width: 40,
      height: 40,
      borderRadius: 20,
      alignItems: "center",
      justifyContent: "center",
      backgroundColor: colors.surface,
    },
    selectedIconCircle: { backgroundColor: colors.surface },
    copy: { flex: 1, gap: 2 },
    label: { fontFamily: typography.family.bodySemibold, color: colors.primaryText, fontSize: 14 },
    optionDescription: { color: colors.secondaryText, fontSize: 12, lineHeight: 17 },
    pressed: { opacity: 0.78 },
  });
}
