import { ActivityIndicator, Pressable, StyleSheet } from "react-native";

import { useTheme } from "../context/ThemeContext";
import { getShadows, radii, spacing, typography } from "../theme/tokens";
import { AppText } from "./AppText";

export function PrimaryButton({ label, onPress, loading = false, disabled = false, icon }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: disabled || loading, busy: loading }}
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        (disabled || loading) && styles.disabled,
        pressed && !disabled && !loading && styles.pressed,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={colors.primaryButtonText} />
      ) : (
        <>
          <AppText style={styles.label}>{label}</AppText>
          {icon}
        </>
      )}
    </Pressable>
  );
}

export function SecondaryButton({ label, onPress, loading = false, disabled = false }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: disabled || loading, busy: loading }}
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        styles.secondary,
        (disabled || loading) && styles.disabledSecondary,
        pressed && !disabled && !loading && styles.pressedSecondary,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={colors.orange} />
      ) : (
        <AppText style={styles.secondaryLabel}>{label}</AppText>
      )}
    </Pressable>
  );
}

export function DangerButton({ label, onPress, loading = false, disabled = false }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: disabled || loading, busy: loading }}
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        styles.danger,
        (disabled || loading) && styles.disabled,
        pressed && !disabled && !loading && styles.pressed,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={colors.primaryButtonText} />
      ) : (
        <AppText style={styles.dangerLabel}>{label}</AppText>
      )}
    </Pressable>
  );
}

export function TextButton({ label, onPress, inverse = false }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      hitSlop={8}
      onPress={onPress}
      style={({ pressed }) => [pressed && styles.textPressed]}
    >
      <AppText style={[styles.textLabel, inverse && styles.textInverse]}>{label}</AppText>
    </Pressable>
  );
}

const createStyles = (colors) => StyleSheet.create({
  button: {
    minHeight: 52,
    paddingHorizontal: spacing.lg,
    borderRadius: radii.pill,
    backgroundColor: colors.orange,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
    gap: spacing.sm,
    ...getShadows(colors).card,
  },
  label: {
    color: colors.primaryButtonText,
    fontFamily: typography.family.bodySemibold,
    fontSize: 15,
  },
  pressed: { opacity: 0.86, transform: [{ scale: 0.985 }] },
  disabled: { opacity: 0.48 },
  secondary: {
    minHeight: 52,
    paddingHorizontal: spacing.lg,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.orange,
    alignItems: "center",
    justifyContent: "center",
  },
  secondaryLabel: {
    color: colors.orange,
    fontFamily: typography.family.bodySemibold,
    fontSize: 15,
  },
  pressedSecondary: { backgroundColor: colors.orangeLight },
  disabledSecondary: { opacity: 0.45 },
  danger: {
    minHeight: 52,
    paddingHorizontal: spacing.lg,
    borderRadius: radii.pill,
    backgroundColor: colors.error,
    alignItems: "center",
    justifyContent: "center",
  },
  dangerLabel: {
    color: colors.primaryButtonText,
    fontFamily: typography.family.bodySemibold,
    fontSize: 15,
  },
  textLabel: {
    color: colors.orange,
    fontFamily: typography.family.bodySemibold,
    fontSize: 14,
  },
  textInverse: { color: colors.inverseText },
  textPressed: { opacity: 0.58 },
});
