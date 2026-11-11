import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, layout, radii, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { ErrorState, FullScreenLoader } from "../components/StateView";
import { InlineNotice } from "../components/InlineNotice";
import { MultilineField } from "../components/InputField";
import { LanguageSelector } from "../components/LanguageSelector";
import { PrimaryButton, TextButton } from "../components/PrimaryButton";
import { getErrorMessage } from "../utils/errors";

export function QuestionReviewDetailScreen({ navigation, route }) {
  const { t } = useLanguage();
  const { authenticatedRequest } = useAuth();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const questionId = route?.params?.questionId;
  const [detail, setDetail] = useState(null);
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await authenticatedRequest((token) =>
        api.getQuestionForReview(token, questionId),
      );
      setDetail(result);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setLoading(false);
    }
  }, [authenticatedRequest, questionId, t]);

  useEffect(() => {
    load();
  }, [load]);

  const publish = async () => {
    if (!response.trim()) {
      setError(t.responseRequired);
      return;
    }
    setError("");
    setPublishing(true);
    try {
      await authenticatedRequest((token) =>
        api.publishProfessionalResponse(token, questionId, {
          response: response.trim(),
        }),
      );
      navigation.replace("QuestionReviewQueue");
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setPublishing(false);
    }
  };

  if (loading) return <FullScreenLoader label={t.loading} />;

  if (error && !detail) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <ErrorState
          actionLabel={t.retry}
          description={error}
          onRetry={load}
          title={t.genericError}
        />
        <View style={styles.backRow}>
          <TextButton label={t.back} onPress={() => navigation.goBack()} />
        </View>
      </SafeAreaView>
    );
  }

  const analysis = detail?.latest_analysis;

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={styles.flex}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.header}>
            <TextButton label={t.back} onPress={() => navigation.goBack()} />
            <BrandMark compact />
            <LanguageSelector />
          </View>
          <View style={styles.intro}>
            <AppText accessibilityRole="header" variant="title">
              {t.questionReviewDetails}
            </AppText>
            <AppText style={styles.description}>{t.professionalQuestionQueueIntro}</AppText>
          </View>
          {error ? <InlineNotice message={error} /> : null}
          <View style={styles.questionCard}>
            <View style={styles.cardHeading}>
              <Ionicons color={colors.orange} name="help-circle-outline" size={22} />
              <AppText variant="card">{t.questionContent}</AppText>
            </View>
            <AppText style={styles.question}>{detail.question.content}</AppText>
          </View>
          <View style={styles.analysisCard}>
            <AppText variant="card">{t.aiAnalysis}</AppText>
            {analysis?.status === "ready" ? (
              <>
                <AppText style={styles.answer}>{analysis.answer}</AppText>
                {analysis.explanation ? (
                  <AppText style={styles.body}>{analysis.explanation}</AppText>
                ) : null}
              </>
            ) : (
              <AppText style={styles.body}>{t.aiUnavailableDescription}</AppText>
            )}
          </View>
          <View style={styles.formCard}>
            <AppText variant="section">{t.professionalResponse}</AppText>
            <MultilineField
              label={t.professionalResponse}
              onChangeText={setResponse}
              placeholder={t.professionalResponsePlaceholder}
              value={response}
            />
            <PrimaryButton
              label={t.publishResponse}
              loading={publishing}
              onPress={publish}
            />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.creamLight },
  flex: { flex: 1 },
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
  questionCard: {
    padding: spacing.lg,
    borderRadius: radii.lg,
    backgroundColor: colors.white,
    gap: spacing.md,
    ...getShadows(colors).card,
  },
  cardHeading: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  question: { color: colors.ink, fontSize: 17, lineHeight: 27 },
  analysisCard: {
    padding: spacing.lg,
    borderRadius: radii.lg,
    backgroundColor: colors.ink,
    gap: spacing.md,
    ...getShadows(colors).card,
  },
  answer: { color: colors.white, fontSize: 16, lineHeight: 25 },
  body: { color: "rgba(255,255,255,0.78)", lineHeight: 23 },
  formCard: {
    padding: spacing.lg,
    borderRadius: radii.lg,
    backgroundColor: colors.white,
    gap: spacing.md,
    ...getShadows(colors).card,
  },
  backRow: { alignItems: "center", paddingBottom: spacing.xl },
});
