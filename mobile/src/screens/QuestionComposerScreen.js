import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { layout, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { InlineNotice } from "../components/InlineNotice";
import { LanguageSelector } from "../components/LanguageSelector";
import { MultilineField } from "../components/InputField";
import { PrimaryButton, TextButton } from "../components/PrimaryButton";
import { getErrorMessage } from "../utils/errors";

export function QuestionComposerScreen({ navigation }) {
  const { language, t } = useLanguage();
  const { authenticatedRequest } = useAuth();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    const trimmed = content.trim();
    if (!trimmed) {
      setError(t.questionEmpty);
      return;
    }
    if (trimmed.length > 10000) {
      setError(t.questionTooLong);
      return;
    }

    setError("");
    setSaving(true);
    try {
      const detail = await authenticatedRequest((token) =>
        api.createQuestion(token, {
          content: trimmed,
          language: language === "en" ? "en" : "rw",
        }),
      );
      navigation.replace("QuestionDetail", {
        questionId: detail.question.id,
      });
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setSaving(false);
    }
  };

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
              {t.questionTitle}
            </AppText>
            <AppText style={styles.description}>{t.questionIntro}</AppText>
          </View>
          <View style={styles.form}>
            {error ? <InlineNotice message={error} /> : null}
            <MultilineField
              label={t.questionContent}
              maxLength={10000}
              onChangeText={setContent}
              placeholder={t.questionPlaceholder}
              value={content}
            />
            <AppText style={styles.counter}>
              {content.length.toLocaleString()} / 10,000
            </AppText>
            <PrimaryButton
               icon={<Ionicons color={colors.primaryButtonText} name="send-outline" size={18} />}
              label={t.submitQuestion}
              loading={saving}
              onPress={submit}
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
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  intro: { marginTop: spacing.xl, gap: spacing.sm },
  description: { maxWidth: 370 },
  form: { gap: spacing.md, marginTop: spacing.xxl },
  counter: { alignSelf: "flex-end", marginTop: -spacing.xs, fontSize: 12 },
});
