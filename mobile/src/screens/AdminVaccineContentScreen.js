import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { AdminAccessDenied, AdminCard, AdminHeader, ChoiceChip } from "../components/AdminComponents";
import { AppText } from "../components/AppText";
import { ErrorState } from "../components/StateView";
import { InlineNotice } from "../components/InlineNotice";
import { InputField, MultilineField } from "../components/InputField";
import { PrimaryButton } from "../components/PrimaryButton";
import { StatusPill } from "../components/StatusPill";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { formatDate, getErrorMessage } from "../utils/errors";
import { getShadows, layout, radii, spacing, typography } from "../theme/tokens";

const initialForm = {
  sourceAuthority: "",
  sourceName: "",
  sourceUrl: "",
  sourceJurisdiction: "",
  language: "rw",
  category: "",
  title: "",
  summary: "",
  body: "",
  version: "1",
  status: "draft",
};

export function AdminVaccineContentScreen({ navigation }) {
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest, user } = useAuth();
  const isAdmin = user?.role === "administrator";
  const [form, setForm] = useState(initialForm);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadPublished = useCallback(async () => {
    if (!isAdmin) return;
    setLoading(true);
    setError("");
    try {
      const result = await authenticatedRequest((token) =>
        api.listVaccineContent(token, { language: form.language }),
      );
      setItems(result || []);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setLoading(false);
    }
  }, [authenticatedRequest, form.language, isAdmin, t]);

  useEffect(() => {
    loadPublished();
  }, [loadPublished]);

  const updateField = (name, value) => {
    setForm((current) => ({ ...current, [name]: value }));
  };

  const submit = async () => {
    const requiredFields = [
      "sourceAuthority",
      "sourceName",
      "sourceUrl",
      "sourceJurisdiction",
      "category",
      "title",
      "summary",
      "body",
      "version",
    ];
    if (requiredFields.some((field) => !String(form[field]).trim())) {
      setError(t.requiredField);
      return;
    }

    const version = Number(form.version);
    if (!Number.isInteger(version) || version < 1) {
      setError(t.contentVersion);
      return;
    }

    setSaving(true);
    setError("");
    setNotice("");
    try {
      await authenticatedRequest((token) =>
        api.createVaccineContent(token, {
          source_authority: form.sourceAuthority.trim(),
          source_name: form.sourceName.trim(),
          source_url: form.sourceUrl.trim(),
          source_jurisdiction: form.sourceJurisdiction.trim(),
          language: form.language,
          category: form.category.trim(),
          title: form.title.trim(),
          summary: form.summary.trim(),
          body: form.body.trim(),
          version,
          status: form.status,
        }),
      );
      setNotice(`${t.contentCreated}. ${t.contentCreatedDescription}`);
      await loadPublished();
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setSaving(false);
    }
  };

  if (!isAdmin) return <AdminAccessDenied navigation={navigation} />;

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={styles.flex}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          <AdminHeader description={t.adminContentIntro} navigation={navigation} title={t.adminContent} />
          {error ? <InlineNotice message={error} /> : null}
          {notice ? <InlineNotice message={notice} tone="success" /> : null}

          <AdminCard>
            <View style={styles.formHeading}>
              <View style={styles.iconCircle}><Ionicons color={colors.orange} name="shield-checkmark-outline" size={23} /></View>
              <View style={styles.formCopy}>
                <AppText variant="card">{t.adminManageContent}</AppText>
                <AppText style={styles.helper}>{t.contentApprovalNote}</AppText>
              </View>
            </View>
            <AppText variant="section">{t.vaccineSource}</AppText>
            <InputField label={t.contentAuthority} onChangeText={(value) => updateField("sourceAuthority", value)} value={form.sourceAuthority} />
            <InputField label={t.contentSourceName} onChangeText={(value) => updateField("sourceName", value)} value={form.sourceName} />
            <InputField autoCapitalize="none" autoCorrect={false} keyboardType="url" label={t.contentSourceUrl} onChangeText={(value) => updateField("sourceUrl", value)} value={form.sourceUrl} />
            <InputField label={t.contentJurisdiction} onChangeText={(value) => updateField("sourceJurisdiction", value)} value={form.sourceJurisdiction} />

            <AppText variant="section">{t.contentLanguage}</AppText>
            <View style={styles.chipWrap}>
              <ChoiceChip label="Kinyarwanda" onPress={() => updateField("language", "rw")} selected={form.language === "rw"} />
              <ChoiceChip label="English" onPress={() => updateField("language", "en")} selected={form.language === "en"} />
            </View>
            <InputField label={t.contentCategory} onChangeText={(value) => updateField("category", value)} value={form.category} />
            <InputField label={t.contentTitle} onChangeText={(value) => updateField("title", value)} value={form.title} />
            <MultilineField label={t.contentSummary} onChangeText={(value) => updateField("summary", value)} value={form.summary} />
            <MultilineField label={t.contentBody} onChangeText={(value) => updateField("body", value)} style={styles.bodyField} value={form.body} />
            <InputField keyboardType="number-pad" label={t.contentVersion} onChangeText={(value) => updateField("version", value.replace(/[^0-9]/g, ""))} value={form.version} />
            <AppText variant="section">{t.contentStatus}</AppText>
            <View style={styles.chipWrap}>
              <ChoiceChip label={t.draft} onPress={() => updateField("status", "draft")} selected={form.status === "draft"} />
              <ChoiceChip label={t.published} onPress={() => updateField("status", "published")} selected={form.status === "published"} />
            </View>
            <PrimaryButton icon={<Ionicons color={colors.primaryButtonText} name="save-outline" size={18} />} label={t.saveContent} loading={saving} onPress={submit} />
          </AdminCard>

          <View style={styles.publishedSection}>
            <AppText variant="section">{t.publishedContent}</AppText>
            {error && !items.length ? <ErrorState actionLabel={t.retry} description={error} onRetry={loadPublished} title={t.genericError} /> : null}
            {!loading && !error && !items.length ? <AppText style={styles.helper}>{t.noPublishedContent}</AppText> : null}
            {items.map((item) => (
              <View key={item.id} style={styles.contentCard}>
                <View style={styles.contentTop}>
                  <View style={styles.contentIcon}><Ionicons color={colors.orange} name="newspaper-outline" size={20} /></View>
                  <View style={styles.contentCopy}>
                    <AppText variant="card">{item.title}</AppText>
                    <AppText style={styles.meta}>{item.category} · {formatDate(item.published_at, language)}</AppText>
                  </View>
                  <StatusPill label={t.published} tone="success" />
                </View>
                <AppText style={styles.summary}>{item.summary}</AppText>
                <AppText style={styles.meta}>{item.source?.name} · {item.source?.authority}</AppText>
              </View>
            ))}
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  flex: { flex: 1 },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl, gap: spacing.lg },
  formHeading: { flexDirection: "row", alignItems: "flex-start", gap: spacing.sm, marginBottom: spacing.md },
  iconCircle: { width: 46, height: 46, borderRadius: 23, alignItems: "center", justifyContent: "center", backgroundColor: colors.orangeLight },
  formCopy: { flex: 1, gap: spacing.xs },
  helper: { color: colors.secondaryText, lineHeight: 20 },
  chipWrap: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  bodyField: { minHeight: 230 },
  publishedSection: { gap: spacing.md },
  contentCard: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surface, gap: spacing.md, ...getShadows(colors).card },
  contentTop: { flexDirection: "row", alignItems: "flex-start", gap: spacing.sm },
  contentIcon: { width: 42, height: 42, borderRadius: 21, alignItems: "center", justifyContent: "center", backgroundColor: colors.orangeLight },
  contentCopy: { flex: 1, gap: spacing.xxs },
  summary: { color: colors.secondaryText, lineHeight: 21 },
  meta: { color: colors.muted, fontSize: 12, lineHeight: 18 },
});
