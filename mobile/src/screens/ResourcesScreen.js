import { Ionicons } from "@expo/vector-icons";
import { Pressable, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, layout, radii, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { EmptyState } from "../components/StateView";
import { LanguageSelector } from "../components/LanguageSelector";
import { TextButton } from "../components/PrimaryButton";

export function ResourcesScreen({ navigation }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const { user } = useAuth();
  const styles = createStyles(colors);
  const canAskQuestion = ["community_member", "chw"].includes(user?.role);

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <TextButton label={t.back} onPress={() => navigation.goBack()} />
          <BrandMark compact />
          <LanguageSelector />
        </View>

        <View style={styles.intro}>
          <AppText accessibilityRole="header" variant="title">{t.resources}</AppText>
          <AppText style={styles.description}>{t.resourcesIntro}</AppText>
        </View>

        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t.officialVaccineInfo}
          onPress={() => navigation.navigate("VaccineInfo")}
          style={({ pressed }) => [styles.featureCard, pressed && styles.pressed]}
        >
          <View style={styles.featureIcon}>
            <Ionicons color={colors.primaryAccent} name="shield-checkmark-outline" size={25} />
          </View>
          <View style={styles.cardCopy}>
            <AppText variant="card">{t.officialVaccineInfo}</AppText>
            <AppText style={styles.cardDescription}>{t.officialVaccineInfoIntro}</AppText>
            <View style={styles.cardAction}>
              <AppText style={styles.actionLabel}>{t.browseVaccineUpdates}</AppText>
              <Ionicons color={colors.primaryAccent} name="arrow-forward" size={18} />
            </View>
          </View>
        </Pressable>

        {canAskQuestion ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t.myQuestions}
            onPress={() => navigation.navigate("QuestionList")}
            style={({ pressed }) => [styles.featureCard, pressed && styles.pressed]}
          >
            <View style={[styles.featureIcon, styles.questionIcon]}>
              <Ionicons color={colors.primaryAccent} name="chatbubble-ellipses-outline" size={25} />
            </View>
            <View style={styles.cardCopy}>
              <AppText variant="card">{t.myQuestions}</AppText>
              <AppText style={styles.cardDescription}>{t.askCommunityQuestionDescription}</AppText>
              <View style={styles.cardAction}>
                <AppText style={styles.actionLabel}>{t.askQuestion}</AppText>
                <Ionicons color={colors.primaryAccent} name="arrow-forward" size={18} />
              </View>
            </View>
          </Pressable>
        ) : null}

        <View style={styles.learningSection}>
          <View style={styles.sectionHeading}>
            <View style={styles.sectionIcon}>
              <Ionicons color={colors.primaryAccent} name="school-outline" size={22} />
            </View>
            <View style={styles.cardCopy}>
              <AppText variant="section">{t.learningResources}</AppText>
              <AppText style={styles.cardDescription}>{t.learningResourcesIntro}</AppText>
            </View>
          </View>
          <EmptyState
            description={t.learningResourcesEmptyDescription}
            icon="library-outline"
            title={t.learningResourcesEmptyTitle}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.huge + 88, gap: spacing.md },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  intro: { marginTop: spacing.xl, gap: spacing.sm, marginBottom: spacing.sm },
  description: { color: colors.secondaryText, maxWidth: 370, lineHeight: 23 },
  featureCard: { flexDirection: "row", alignItems: "flex-start", gap: spacing.md, padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, ...getShadows(colors).card },
  featureIcon: { width: 48, height: 48, borderRadius: 24, alignItems: "center", justifyContent: "center", backgroundColor: colors.accentBackground },
  questionIcon: { backgroundColor: colors.surfaceSecondary },
  cardCopy: { flex: 1, gap: spacing.xs },
  cardDescription: { color: colors.secondaryText, lineHeight: 21 },
  cardAction: { flexDirection: "row", alignItems: "center", gap: spacing.xs, marginTop: spacing.xs },
  actionLabel: { color: colors.primaryAccent, fontFamily: "DMSans_600SemiBold", fontSize: 14 },
  learningSection: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border, gap: spacing.sm },
  sectionHeading: { flexDirection: "row", alignItems: "flex-start", gap: spacing.sm },
  sectionIcon: { width: 42, height: 42, borderRadius: 21, alignItems: "center", justifyContent: "center", backgroundColor: colors.accentBackground },
  pressed: { opacity: 0.82 },
});
