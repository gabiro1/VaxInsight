import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useState } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, layout, radii, spacing, typography } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { ErrorState, FullScreenLoader } from "../components/StateView";
import { InlineNotice } from "../components/InlineNotice";
import { LanguageSelector } from "../components/LanguageSelector";
import { SecondaryButton, TextButton } from "../components/PrimaryButton";
import { StatusPill } from "../components/StatusPill";
import { formatDate, getErrorMessage, questionStatusLabel } from "../utils/errors";

export function QuestionDetailScreen({ navigation, route }) {
  const { language, t } = useLanguage();
  const { authenticatedRequest } = useAuth();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const questionId = route?.params?.questionId;
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [requestingAnalysis, setRequestingAnalysis] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await authenticatedRequest((token) =>
        api.getQuestion(token, questionId),
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

  const requestAnalysis = async () => {
    setRequestingAnalysis(true);
    setError("");
    try {
      await authenticatedRequest((token) =>
        api.requestQuestionAnalysis(token, questionId),
      );
      await load();
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setRequestingAnalysis(false);
    }
  };

  if (loading) return <FullScreenLoader label={t.loading} />;

  if (error || !detail) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <ErrorState
          actionLabel={t.retry}
          description={error || t.notFound}
          onRetry={load}
          title={t.genericError}
        />
        <View style={styles.backRow}>
          <TextButton label={t.back} onPress={() => navigation.goBack()} />
        </View>
      </SafeAreaView>
    );
  }

  const { question, latest_analysis: analysis, latest_professional_response: response } = detail;
  const analysisUnavailable = analysis?.status === "unavailable";
  const analysisFailed = analysis?.status === "failed";
  const analysisReady = analysis?.status === "ready";

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <TextButton label={t.back} onPress={() => navigation.goBack()} />
          <BrandMark compact />
          <LanguageSelector />
        </View>

        <View style={styles.intro}>
          <AppText accessibilityRole="header" variant="title">
            {t.questionDetails}
          </AppText>
          <StatusPill label={questionStatusLabel(question.status, t)} tone={question.status === "responded" ? "success" : "accent"} />
        </View>

        {error ? <InlineNotice message={error} /> : null}

        <View style={styles.questionCard}>
          <View style={styles.cardHeading}>
            <Ionicons color={colors.orange} name="help-circle-outline" size={22} />
            <AppText variant="card">{t.questionContent}</AppText>
          </View>
          <AppText style={styles.questionText}>{question.content}</AppText>
          <AppText style={styles.meta}>
            {formatDate(question.created_at, language)}
          </AppText>
        </View>

        <View style={styles.sectionHeader}>
          <AppText variant="section">{t.aiAnalysis}</AppText>
          <AppText style={styles.privateLabel}>{t.aiGenerated}</AppText>
        </View>
        <View style={styles.analysisCard}>
          {analysisReady ? (
            <>
              <AppText variant="card">{t.aiAnswer}</AppText>
              <AppText style={styles.answer}>{analysis.answer}</AppText>
              {analysis.category ? (
                <AppText style={styles.meta}>
                  {t.aiCategory}: {analysis.category}
                </AppText>
              ) : null}
              {analysis.explanation ? (
                <View style={styles.explanation}>
                  <AppText style={styles.label}>{t.aiExplanation}</AppText>
                  <AppText style={styles.body}>{analysis.explanation}</AppText>
                </View>
              ) : null}
              {analysis.limitations ? (
                <AppText style={styles.limitations}>
                  {t.aiLimitations}: {analysis.limitations}
                </AppText>
              ) : null}
            </>
          ) : (
            <>
              <AppText variant="card">
                {analysisUnavailable
                  ? t.aiUnavailableTitle
                  : analysisFailed
                    ? t.aiFailedTitle
                    : t.loading}
              </AppText>
              <AppText style={styles.body}>
                {analysisUnavailable
                  ? t.aiUnavailableDescription
                  : analysisFailed
                    ? t.aiFailedDescription
                    : t.aiUnavailableDescription}
              </AppText>
              <SecondaryButton
                label={t.requestAnalysis}
                loading={requestingAnalysis}
                onPress={requestAnalysis}
              />
            </>
          )}
        </View>

        <View style={styles.sectionHeader}>
          <AppText variant="section">{t.professionalAnswer}</AppText>
        </View>
        <View style={styles.professionalCard}>
          {response ? (
            <>
              <View style={styles.answerHeading}>
                <Ionicons color={colors.success} name="person-circle-outline" size={23} />
                <AppText variant="card">{t.professionalAnswer}</AppText>
              </View>
              <AppText style={styles.answer}>{response.response}</AppText>
              <AppText style={styles.meta}>
                {formatDate(response.created_at, language)}
              </AppText>
            </>
          ) : (
            <>
              <AppText variant="card">{t.professionalAnswerPending}</AppText>
              <AppText style={styles.body}>{t.professionalAnswerDescription}</AppText>
            </>
          )}
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
  questionCard: {
    padding: spacing.lg,
    borderRadius: radii.lg,
    backgroundColor: colors.white,
    gap: spacing.md,
    ...getShadows(colors).card,
  },
  cardHeading: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  questionText: { color: colors.ink, fontSize: 17, lineHeight: 27 },
  meta: { color: colors.muted, fontSize: 12 },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.sm,
  },
  privateLabel: { color: colors.orange, fontSize: 12, fontFamily: typography.family.bodySemibold },
  analysisCard: {
    padding: spacing.lg,
    borderRadius: radii.lg,
    backgroundColor: colors.white,
    gap: spacing.md,
    ...getShadows(colors).card,
  },
  professionalCard: {
    padding: spacing.lg,
    borderRadius: radii.lg,
    backgroundColor: colors.white,
    gap: spacing.md,
    borderLeftWidth: 4,
    borderLeftColor: colors.success,
    ...getShadows(colors).card,
  },
  answerHeading: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  answer: { color: colors.ink, fontSize: 16, lineHeight: 25 },
  explanation: { gap: spacing.xs, paddingTop: spacing.md, borderTopWidth: 1, borderTopColor: colors.border },
  label: { color: colors.ink, fontFamily: typography.family.bodySemibold, fontSize: 13 },
  body: { color: colors.inkSecondary, lineHeight: 23 },
  limitations: { color: colors.warning, fontSize: 12, lineHeight: 18 },
  backRow: { alignItems: "center", paddingBottom: spacing.xl },
});
