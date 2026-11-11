import { Ionicons } from "@expo/vector-icons";
import { Pressable, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, layout, radii, spacing, typography } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { LanguageSelector } from "../components/LanguageSelector";
import { PrimaryButton, TextButton } from "../components/PrimaryButton";

function AuthPathCard({ icon, title, description, action, onPress, accent }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${title}. ${action}`}
      onPress={onPress}
      style={({ pressed }) => [styles.card, accent && styles.accentCard, pressed && styles.cardPressed]}
    >
      <View style={[styles.iconCircle, accent && styles.accentIconCircle]}>
        <Ionicons color={accent ? colors.primaryButtonText : colors.primaryAccent} name={icon} size={23} />
      </View>
      <View style={styles.cardCopy}>
        <AppText variant="card">{title}</AppText>
        <AppText style={styles.cardDescription}>{description}</AppText>
      </View>
      <View style={styles.cardActionRow}>
        <AppText style={[styles.cardAction, accent && styles.accentAction]}>{action}</AppText>
        <Ionicons color={accent ? colors.primaryAccent : colors.icon} name="arrow-forward" size={18} />
      </View>
    </Pressable>
  );
}

export function AuthChoiceScreen({ navigation }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t.back}
            hitSlop={10}
            onPress={() => navigation.goBack()}
            style={styles.backButton}
          >
            <Ionicons color={colors.ink} name="arrow-back" size={22} />
          </Pressable>
          <BrandMark compact />
          <LanguageSelector />
        </View>

        <View style={styles.intro}>
          <AppText style={styles.eyebrow}>VAXINSIGHT</AppText>
          <AppText accessibilityRole="header" variant="title" style={styles.title}>
            {t.chooseTitle}
          </AppText>
          <AppText style={styles.description}>{t.chooseDescription}</AppText>
        </View>

        <View style={styles.cards}>
          <AuthPathCard
            action={t.register}
            accent
            description={t.createAccountDescription}
            icon="person-add-outline"
            onPress={() => navigation.navigate("Register")}
            title={t.createAccount}
          />
          <AuthPathCard
            action={t.signIn}
            description={t.signInDescription}
            icon="log-in-outline"
            onPress={() => navigation.navigate("Login")}
            title={t.existingAccount}
          />
        </View>

        <View style={styles.footerNote}>
          <Ionicons color={colors.success} name="shield-checkmark-outline" size={19} />
          <AppText style={styles.footerText}>{t.workspaceDescription}</AppText>
        </View>
        <View style={styles.backText}>
          <TextButton label={t.back} onPress={() => navigation.goBack()} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.creamLight },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  backButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.white,
    alignItems: "center",
    justifyContent: "center",
    ...getShadows(colors).card,
  },
  headerSpacer: { width: 48 },
  intro: { marginTop: spacing.xxl, maxWidth: 410 },
  eyebrow: {
    color: colors.orange,
    fontFamily: typography.family.bodyBold,
    fontSize: 12,
    letterSpacing: 1.8,
    marginBottom: spacing.sm,
  },
  title: { letterSpacing: -0.7 },
  description: { marginTop: spacing.sm, maxWidth: 340 },
  cards: { gap: spacing.md, marginTop: spacing.xxl },
  card: {
    padding: spacing.lg,
    borderRadius: radii.lg,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
    ...getShadows(colors).card,
  },
  accentCard: { borderColor: colors.orange, backgroundColor: colors.orangeLight },
  cardPressed: { transform: [{ scale: 0.985 }], opacity: 0.9 },
  iconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.orangeLight,
    alignItems: "center",
    justifyContent: "center",
  },
  accentIconCircle: { backgroundColor: colors.orange },
  cardCopy: { marginTop: spacing.md },
  cardDescription: { marginTop: spacing.xs, maxWidth: 300 },
  cardActionRow: { marginTop: spacing.lg, flexDirection: "row", alignItems: "center", gap: spacing.xs },
  cardAction: { color: colors.ink, fontFamily: typography.family.bodySemibold, fontSize: 14 },
  accentAction: { color: colors.orange },
  footerNote: {
    marginTop: spacing.xxl,
    padding: spacing.md,
    borderRadius: radii.md,
    backgroundColor: colors.white,
    flexDirection: "row",
    gap: spacing.sm,
    alignItems: "flex-start",
  },
  footerText: { flex: 1, fontSize: 13, lineHeight: 19 },
  backText: { alignItems: "center", marginTop: spacing.lg },
});
