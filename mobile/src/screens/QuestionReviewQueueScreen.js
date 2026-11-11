import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useState } from "react";
import { Pressable, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, layout, radii, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { EmptyState, ErrorState, FullScreenLoader } from "../components/StateView";
import { InlineNotice } from "../components/InlineNotice";
import { LanguageSelector } from "../components/LanguageSelector";
import { TextButton } from "../components/PrimaryButton";
import { StatusPill } from "../components/StatusPill";
import { getErrorMessage, questionStatusLabel } from "../utils/errors";

export function QuestionReviewQueueScreen({ navigation }) {
  const { t } = useLanguage();
  const { authenticatedRequest } = useAuth();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError("");
      try {
        const result = await authenticatedRequest((token) =>
          api.listQuestionReviewQueue(token),
        );
        setItems(result || []);
      } catch (requestError) {
        setError(getErrorMessage(requestError, t));
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [authenticatedRequest, t],
  );

  useEffect(() => {
    load();
  }, [load]);

  if (loading && !items.length) return <FullScreenLoader label={t.loading} />;

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={
          <RefreshControl
            onRefresh={() => load(true)}
            refreshing={refreshing}
            tintColor={colors.orange}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <TextButton label={t.back} onPress={() => navigation.goBack()} />
          <BrandMark compact />
          <LanguageSelector />
        </View>
        <View style={styles.intro}>
          <AppText accessibilityRole="header" variant="title">
            {t.professionalQuestionQueue}
          </AppText>
          <AppText style={styles.description}>{t.professionalQuestionQueueIntro}</AppText>
        </View>
        {error && items.length ? <InlineNotice message={error} /> : null}
        {error && !items.length ? (
          <ErrorState
            actionLabel={t.retry}
            description={error}
            onRetry={() => load()}
            title={t.genericError}
          />
        ) : null}
        {!error && !items.length ? (
          <EmptyState
            description={t.noQuestionsForReviewDescription}
            icon="checkmark-done-outline"
            title={t.noQuestionsForReviewTitle}
          />
        ) : null}
        <View style={styles.list}>
          {items.map((item) => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={item.question.content}
              key={item.question.id}
              onPress={() =>
                navigation.navigate("QuestionReviewDetail", {
                  questionId: item.question.id,
                })
              }
              style={({ pressed }) => [styles.card, pressed && styles.pressed]}
            >
              <View style={styles.cardTop}>
                <StatusPill
                  label={questionStatusLabel(item.question.status, t)}
                  tone="accent"
                />
                <Ionicons color={colors.muted} name="chevron-forward" size={19} />
              </View>
              <AppText numberOfLines={5} style={styles.content}>
                {item.question.content}
              </AppText>
              <AppText style={styles.meta}>
                {item.latest_analysis?.status === "ready"
                  ? t.aiGenerated
                  : t.aiUnavailableTitle}
              </AppText>
            </Pressable>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.creamLight },
  scroll: {
    flexGrow: 1,
    padding: layout.gutter,
    paddingBottom: spacing.xxl,
    gap: spacing.lg,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  intro: { marginTop: spacing.xl, gap: spacing.sm },
  description: { maxWidth: 370 },
  list: { gap: spacing.md },
  card: {
    padding: spacing.lg,
    borderRadius: radii.lg,
    backgroundColor: colors.white,
    gap: spacing.md,
    ...getShadows(colors).card,
  },
  pressed: { opacity: 0.82, transform: [{ scale: 0.99 }] },
  cardTop: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  content: { color: colors.ink, fontSize: 16, lineHeight: 24 },
  meta: { color: colors.muted, fontSize: 12 },
});
