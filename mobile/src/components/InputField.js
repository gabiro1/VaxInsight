import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { Pressable, StyleSheet, TextInput, View } from "react-native";

import { useTheme } from "../context/ThemeContext";
import { radii, spacing, typography } from "../theme/tokens";
import { AppText } from "./AppText";

export function InputField({ label, error, style, ...props }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <View style={[styles.wrapper, style]}>
      <AppText style={styles.label}>{label}</AppText>
      <TextInput
        accessibilityLabel={label}
        placeholderTextColor={colors.mutedText}
        style={[styles.input, error && styles.inputError]}
        {...props}
      />
      {error ? <AppText style={styles.error}>{error}</AppText> : null}
    </View>
  );
}

export function PasswordField({ label, error, ...props }) {
  const [visible, setVisible] = useState(false);
  const { colors } = useTheme();
  const styles = createStyles(colors);

  return (
    <View style={styles.wrapper}>
      <AppText style={styles.label}>{label}</AppText>
      <View style={[styles.passwordContainer, error && styles.inputError]}>
        <TextInput
          accessibilityLabel={label}
          placeholderTextColor={colors.mutedText}
          secureTextEntry={!visible}
          style={styles.passwordInput}
          {...props}
        />
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={visible ? "Hide password" : "Show password"}
          hitSlop={8}
          onPress={() => setVisible((current) => !current)}
          style={styles.visibilityButton}
        >
          <Ionicons
            color={colors.mutedText}
            name={visible ? "eye-off-outline" : "eye-outline"}
            size={20}
          />
        </Pressable>
      </View>
      {error ? <AppText style={styles.error}>{error}</AppText> : null}
    </View>
  );
}

export function MultilineField({ label, error, style, ...props }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <View style={[styles.wrapper, style]}>
      <AppText style={styles.label}>{label}</AppText>
      <TextInput
        accessibilityLabel={label}
        multiline
        numberOfLines={8}
        placeholderTextColor={colors.mutedText}
        style={[styles.multilineInput, error && styles.inputError]}
        textAlignVertical="top"
        {...props}
      />
      {error ? <AppText style={styles.error}>{error}</AppText> : null}
    </View>
  );
}

const createStyles = (colors) => StyleSheet.create({
  wrapper: { gap: spacing.xs },
  label: { fontFamily: typography.family.bodySemibold, fontSize: 13, color: colors.primaryText },
  input: {
    minHeight: 52,
    paddingHorizontal: spacing.md,
    borderWidth: 1,
    borderColor: colors.inputBorder,
    borderRadius: radii.sm,
    backgroundColor: colors.inputBackground,
    color: colors.primaryText,
    fontFamily: typography.family.body,
    fontSize: 16,
  },
  multilineInput: {
    minHeight: 190,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    borderWidth: 1,
    borderColor: colors.inputBorder,
    borderRadius: radii.sm,
    backgroundColor: colors.inputBackground,
    color: colors.primaryText,
    fontFamily: typography.family.body,
    fontSize: 16,
    lineHeight: 24,
  },
  passwordContainer: {
    minHeight: 52,
    borderWidth: 1,
    borderColor: colors.inputBorder,
    borderRadius: radii.sm,
    backgroundColor: colors.inputBackground,
    flexDirection: "row",
    alignItems: "center",
  },
  passwordInput: {
    flex: 1,
    minHeight: 50,
    paddingHorizontal: spacing.md,
    color: colors.primaryText,
    fontFamily: typography.family.body,
    fontSize: 16,
  },
  visibilityButton: { minWidth: 48, minHeight: 48, alignItems: "center", justifyContent: "center" },
  inputError: { borderColor: colors.error },
  error: { color: colors.error, fontSize: 12, lineHeight: 17 },
});
