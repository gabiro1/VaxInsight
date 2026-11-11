import { Ionicons } from "@expo/vector-icons";
import { Modal, StyleSheet, View } from "react-native";

import { useTheme } from "../context/ThemeContext";
import { getShadows, radii, spacing } from "../theme/tokens";
import { AppText } from "./AppText";
import { DangerButton, PrimaryButton, SecondaryButton } from "./PrimaryButton";

export function ConfirmDialog({
  visible,
  title,
  description,
  cancelLabel,
  confirmLabel,
  destructive = false,
  onCancel,
  onConfirm,
}) {
  const { colors } = useTheme();
  const styles = createStyles(colors);

  return (
    <Modal animationType="fade" transparent visible={visible} onRequestClose={onCancel}>
      <View style={styles.overlay}>
        <View accessibilityViewIsModal style={styles.card}>
          <View style={styles.iconCircle}>
            <Ionicons color={destructive ? colors.error : colors.primaryAccent} name={destructive ? "warning-outline" : "help-outline"} size={24} />
          </View>
          <AppText accessibilityRole="header" variant="section" style={styles.title}>{title}</AppText>
          <AppText style={styles.description}>{description}</AppText>
          <View style={styles.actions}>
            <SecondaryButton label={cancelLabel} onPress={onCancel} />
            {destructive ? <DangerButton label={confirmLabel} onPress={onConfirm} /> : <PrimaryButton label={confirmLabel} onPress={onConfirm} />}
          </View>
        </View>
      </View>
    </Modal>
  );
}

const createStyles = (colors) => StyleSheet.create({
  overlay: { flex: 1, padding: spacing.lg, alignItems: "center", justifyContent: "center", backgroundColor: colors.overlay },
  card: { width: "100%", maxWidth: 420, padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.elevatedSurface, ...getShadows(colors).floating },
  iconCircle: { width: 48, height: 48, borderRadius: 24, alignItems: "center", justifyContent: "center", backgroundColor: colors.accentBackground },
  title: { marginTop: spacing.md, color: colors.primaryText },
  description: { marginTop: spacing.xs, color: colors.secondaryText },
  actions: { marginTop: spacing.lg, gap: spacing.sm },
});
