import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { formatDate, getErrorMessage, outcomeLabel, reviewStatusLabel } from "../utils/errors";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, layout, radii, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { ErrorState, FullScreenLoader } from "../components/StateView";
import { InlineNotice } from "../components/InlineNotice";
import { InputField, MultilineField } from "../components/InputField";
import { LanguageSelector } from "../components/LanguageSelector";
import { PrimaryButton, SecondaryButton, TextButton } from "../components/PrimaryButton";
import { StatusPill } from "../components/StatusPill";

const OUTCOMES = [
  "needs_further_review",
  "evidence_supports_claim",
  "evidence_does_not_support_claim",
  "insufficient_evidence",
];

function blankEvidence() {
  return {
    source_title: "",
    publisher: "",
    url: "",
    publication_date: "",
    accessed_at: new Date().toISOString(),
    relevance: "",
  };
}

export function ReviewDetailScreen({ navigation, route }) {
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest } = useAuth();
  const assignmentId = route?.params?.assignmentId;
  const [assignment, setAssignment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState("");
  const [error, setError] = useState("");
  const [outcome, setOutcome] = useState("");
  const [notes, setNotes] = useState("");
  const [evidence, setEvidence] = useState([blankEvidence()]);
  const [escalationReason, setEscalationReason] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await authenticatedRequest((token) => api.getAssignment(token, assignmentId));
      setAssignment(result);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setLoading(false);
    }
  }, [authenticatedRequest, assignmentId, t]);

  useEffect(() => {
    load();
  }, [load]);

  const outcomes = useMemo(
    () => OUTCOMES.map((value) => ({ value, label: outcomeLabel(value, t) })),
    [t],
  );

  const changeStatus = async (status) => {
    setError("");
    setAction(status);
    try {
      await authenticatedRequest((token) =>
        api.updateAssignmentStatus(token, assignmentId, { status }),
      );
      await load();
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setAction("");
    }
  };

  const escalate = async () => {
    if (!escalationReason.trim()) {
      setError(t.reasonRequired);
      return;
    }
    setError("");
    setAction("escalate");
    try {
      await authenticatedRequest((token) =>
        api.updateAssignmentStatus(token, assignmentId, {
          status: "requires_escalation",
          reason: escalationReason.trim(),
        }),
      );
      await load();
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setAction("");
    }
  };

  const updateEvidence = (index, field, value) => {
    setEvidence((current) => current.map((item, itemIndex) => (
      itemIndex === index ? { ...item, [field]: value } : item
    )));
  };

  const submitReview = async () => {
    if (!outcome) {
      setError(t.reviewOutcomeRequired);
      return;
    }
    const activeEvidence = evidence.filter((item) =>
      Object.entries(item).some(([key, value]) => key !== "accessed_at" && value.trim()),
    );
    if (activeEvidence.some((item) => !item.source_title.trim() || !item.publisher.trim() || !item.relevance.trim())) {
      setError(t.evidenceRequiredFields);
      return;
    }
    setError("");
    setAction("submit");
    try {
      await authenticatedRequest((token) =>
        api.submitReview(token, assignmentId, {
          outcome,
          notes: notes.trim() || null,
          evidence: activeEvidence.map((item) => ({
            source_title: item.source_title.trim(),
            publisher: item.publisher.trim(),
            url: item.url.trim() || undefined,
            publication_date: item.publication_date.trim() || undefined,
            accessed_at: item.accessed_at || new Date().toISOString(),
            relevance: item.relevance.trim(),
          })),
        }),
      );
      setOutcome("");
      setNotes("");
      setEvidence([blankEvidence()]);
      await load();
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setAction("");
    }
  };

  if (loading) return <FullScreenLoader label={t.loading} />;
  if (error && !assignment) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <ErrorState actionLabel={t.retry} description={error} onRetry={load} title={t.genericError} />
        <View style={styles.backRow}><TextButton label={t.back} onPress={() => navigation.goBack()} /></View>
      </SafeAreaView>
    );
  }

  const reviewStatus = assignment?.review_status;
  const canStart = reviewStatus === "pending";
  const canSubmit = reviewStatus === "in_review";
  const canEscalate = reviewStatus === "pending" || reviewStatus === "in_review";

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <TextButton label={t.back} onPress={() => navigation.goBack()} />
          <BrandMark compact />
          <LanguageSelector />
        </View>
        <View style={styles.intro}>
          <AppText accessibilityRole="header" variant="title">{t.reviewDetails}</AppText>
          <View style={styles.statusRow}>
            <StatusPill label={reviewStatusLabel(reviewStatus, t)} tone={reviewStatus === "requires_escalation" ? "warning" : reviewStatus === "reviewed" ? "success" : "accent"} />
            <AppText style={styles.meta}>{t.assignedAt}: {formatDate(assignment.assigned_at, language)}</AppText>
          </View>
        </View>
        {error ? <InlineNotice message={error} /> : null}
        <View style={styles.narrativeCard}>
          <AppText variant="section">{t.narrativeContent}</AppText>
          <AppText style={styles.narrative}>{assignment.narrative?.content || t.notFound}</AppText>
          <AppText style={styles.meta}>{t.version} {assignment.narrative?.version}</AppText>
        </View>

        {canStart ? <PrimaryButton label={t.startReview} loading={action === "in_review"} onPress={() => changeStatus("in_review")} /> : null}

        {canSubmit ? (
          <View style={styles.section}>
            <AppText variant="section">{t.submitReview}</AppText>
            <AppText style={styles.description}>{t.reviewOutcome}</AppText>
            <View style={styles.outcomes}>
              {outcomes.map((item) => (
                <SecondaryButton key={item.value} label={item.label} onPress={() => setOutcome(item.value)} />
              ))}
            </View>
            {outcome ? <StatusPill label={outcomeLabel(outcome, t)} tone="success" /> : null}
            <MultilineField label={t.reviewNotes} onChangeText={setNotes} placeholder={t.reviewNotesPlaceholder} value={notes} />
            <AppText variant="section">{t.evidence}</AppText>
            <AppText style={styles.description}>{t.evidenceIntro}</AppText>
            {evidence.map((item, index) => (
              <View key={`evidence-${index}`} style={styles.evidenceCard}>
                <InputField label={t.sourceTitle} onChangeText={(value) => updateEvidence(index, "source_title", value)} value={item.source_title} />
                <InputField label={t.publisher} onChangeText={(value) => updateEvidence(index, "publisher", value)} value={item.publisher} />
                <InputField autoCapitalize="none" keyboardType="url" label={t.sourceUrl} onChangeText={(value) => updateEvidence(index, "url", value)} value={item.url} />
                <InputField label={t.publicationDate} onChangeText={(value) => updateEvidence(index, "publication_date", value)} placeholder="YYYY-MM-DD" value={item.publication_date} />
                <InputField label={t.accessedAt} onChangeText={(value) => updateEvidence(index, "accessed_at", value)} value={item.accessed_at} />
                <MultilineField label={t.relevance} onChangeText={(value) => updateEvidence(index, "relevance", value)} placeholder={t.relevancePlaceholder} value={item.relevance} />
                {evidence.length > 1 ? <TextButton label={t.removeEvidence} onPress={() => setEvidence((current) => current.filter((_, itemIndex) => itemIndex !== index))} /> : null}
              </View>
            ))}
            {evidence.length < 20 ? <SecondaryButton label={t.addEvidence} onPress={() => setEvidence((current) => [...current, blankEvidence()])} /> : null}
            <PrimaryButton icon={<Ionicons color={colors.primaryButtonText} name="checkmark" size={18} />} label={t.submitReview} loading={action === "submit"} onPress={submitReview} />
          </View>
        ) : null}

        {canEscalate ? (
          <View style={styles.section}>
            <AppText variant="section">{t.requiresEscalation}</AppText>
            <MultilineField label={t.reason} onChangeText={setEscalationReason} placeholder={t.escalationReason} value={escalationReason} />
            <SecondaryButton label={t.requiresEscalation} loading={action === "escalate"} onPress={escalate} />
          </View>
        ) : null}

        <SecondaryButton label={t.reviewHistory} onPress={() => navigation.navigate("ReviewHistory", { assignmentId })} />
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.creamLight },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl, gap: spacing.lg },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  intro: { marginTop: spacing.xl, gap: spacing.sm },
  statusRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  meta: { color: colors.muted, fontSize: 12 },
  narrativeCard: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surface, gap: spacing.md, ...getShadows(colors).card },
  narrative: { color: colors.ink, fontSize: 17, lineHeight: 27 },
  section: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surface, gap: spacing.md, ...getShadows(colors).card },
  description: { marginTop: -spacing.xs },
  outcomes: { gap: spacing.sm },
  evidenceCard: { padding: spacing.md, borderWidth: 1, borderColor: colors.border, borderRadius: radii.md, gap: spacing.md },
  backRow: { alignItems: "center", paddingBottom: spacing.xl },
});
