import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { getErrorMessage } from "../utils/errors";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { layout, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { InlineNotice } from "../components/InlineNotice";
import { MultilineField } from "../components/InputField";
import { LanguageSelector } from "../components/LanguageSelector";
import { FullScreenLoader } from "../components/StateView";
import { PrimaryButton, TextButton } from "../components/PrimaryButton";

export function NarrativeComposerScreen({ navigation, route }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest } = useAuth();
  const narrativeId = route?.params?.narrativeId;
  const editing = Boolean(narrativeId);
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(editing);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadNarrative = useCallback(async () => {
    if (!narrativeId) return;
    setLoading(true);
    try {
      const narrative = await authenticatedRequest((token) => api.getNarrative(token, narrativeId));
      setContent(narrative?.content || "");
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setLoading(false);
    }
  }, [authenticatedRequest, narrativeId, t]);

  useEffect(() => {
    loadNarrative();
  }, [loadNarrative]);

  const submit = async () => {
    const trimmed = content.trim();
    if (!trimmed) {
      setError(t.narrativeEmpty);
      return;
    }
    if (trimmed.length > 10000) {
      setError(t.narrativeTooLong);
      return;
    }
    setError("");
    setSaving(true);
    try {
      const narrative = await authenticatedRequest((token) =>
        editing
          ? api.updateNarrative(token, narrativeId, { content })
          : api.createNarrative(token, { content }),
      );
      navigation.replace("NarrativeDetail", { narrativeId: narrative.id });
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <FullScreenLoader label={t.loading} />;

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={styles.flex}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          <View style={styles.header}>
            <TextButton label={t.back} onPress={() => navigation.goBack()} />
            <BrandMark compact />
            <LanguageSelector />
          </View>
          <View style={styles.intro}>
            <AppText accessibilityRole="header" variant="title">{editing ? t.editNarrative : t.narrativeTitle}</AppText>
            <AppText style={styles.description}>{t.narrativeIntro}</AppText>
          </View>
          <View style={styles.form}>
            {error ? <InlineNotice message={error} /> : null}
            <MultilineField
              label={t.narrativeContent}
              maxLength={10000}
              onChangeText={setContent}
              placeholder={t.narrativeContentPlaceholder}
              value={content}
            />
            <AppText style={styles.counter}>{content.length.toLocaleString()} / 10,000</AppText>
            <PrimaryButton icon={<Ionicons color={colors.primaryButtonText} name="arrow-forward" size={18} />} label={editing ? t.updateNarrative : t.submitNarrative} loading={saving} onPress={submit} />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.creamLight },
  flex: { flex: 1 },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  intro: { marginTop: spacing.xl },
  description: { marginTop: spacing.sm, maxWidth: 370 },
  form: { gap: spacing.md, marginTop: spacing.xxl },
  counter: { alignSelf: "flex-end", marginTop: -spacing.xs, fontSize: 12 },
});
