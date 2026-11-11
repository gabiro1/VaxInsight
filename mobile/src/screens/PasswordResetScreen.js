import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { getErrorMessage } from "../utils/errors";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { layout, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { InlineNotice } from "../components/InlineNotice";
import { InputField } from "../components/InputField";
import { LanguageSelector } from "../components/LanguageSelector";
import { PrimaryButton, TextButton } from "../components/PrimaryButton";

export function PasswordResetScreen({ navigation }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!email.trim()) {
      setError(t.requiredField);
      return;
    }
    setError("");
    setLoading(true);
    try {
      await api.requestPasswordReset({ email: email.trim() });
      setSent(true);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={styles.flex}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <View style={styles.topRow}>
            <TextButton label={t.back} onPress={() => navigation.goBack()} />
            <BrandMark compact />
            <LanguageSelector />
          </View>
          <View style={styles.intro}>
            <AppText accessibilityRole="header" variant="title">{t.resetPasswordTitle}</AppText>
            <AppText style={styles.description}>{t.resetPasswordIntro}</AppText>
          </View>
          <View style={styles.form}>
            {error ? <InlineNotice message={error} /> : null}
            {sent ? <InlineNotice message={t.resetSentDescription} tone="success" /> : null}
            {!sent ? (
              <>
                <InputField autoCapitalize="none" keyboardType="email-address" label={t.email} onChangeText={setEmail} placeholder="you@example.com" value={email} />
                <PrimaryButton icon={<Ionicons color={colors.primaryButtonText} name="arrow-forward" size={18} />} label={t.sendResetLink} loading={loading} onPress={submit} />
              </>
            ) : null}
          </View>
          <View style={styles.footer}>
            <TextButton label={t.signIn} onPress={() => navigation.navigate("Login")} />
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
  topRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  spacer: { width: 48 },
  intro: { marginTop: spacing.xxl },
  description: { marginTop: spacing.sm, maxWidth: 360 },
  form: { gap: spacing.md, marginTop: spacing.xxl },
  footer: { alignItems: "center", marginTop: "auto", paddingTop: spacing.xxl },
});
