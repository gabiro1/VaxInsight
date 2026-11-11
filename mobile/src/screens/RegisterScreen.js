import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { getErrorMessage } from "../utils/errors";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { layout, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { InlineNotice } from "../components/InlineNotice";
import { InputField, PasswordField } from "../components/InputField";
import { LanguageSelector } from "../components/LanguageSelector";
import { PrimaryButton, TextButton } from "../components/PrimaryButton";

export function RegisterScreen({ navigation }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!fullName.trim() || !email.trim() || !password || !confirmPassword) {
      setError(t.requiredField);
      return;
    }
    if (password !== confirmPassword) {
      setError(t.passwordMismatch);
      return;
    }
    setError("");
    setLoading(true);
    try {
      await register({
        full_name: fullName.trim(),
        email: email.trim(),
        password,
        confirm_password: confirmPassword,
      });
      navigation.navigate("VerifyEmail", { email: email.trim() });
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={styles.flex}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          <View style={styles.topRow}>
            <TextButton label={t.back} onPress={() => navigation.goBack()} />
            <BrandMark compact />
            <LanguageSelector />
          </View>
          <View style={styles.intro}>
            <AppText accessibilityRole="header" variant="title">{t.createAccountTitle}</AppText>
            <AppText style={styles.description}>{t.registerIntro}</AppText>
          </View>

          <View style={styles.form}>
            {error ? <InlineNotice message={error} /> : null}
            <InputField label={t.fullName} onChangeText={setFullName} placeholder="Amina Uwase" value={fullName} />
            <InputField autoCapitalize="none" autoComplete="email" keyboardType="email-address" label={t.email} onChangeText={setEmail} placeholder="you@example.com" textContentType="emailAddress" value={email} />
            <PasswordField autoComplete="new-password" label={t.password} onChangeText={setPassword} placeholder="••••••••••••" textContentType="newPassword" value={password} />
            <AppText style={styles.hint}>{t.passwordHint}</AppText>
            <PasswordField autoComplete="new-password" label={t.confirmPassword} onChangeText={setConfirmPassword} placeholder="••••••••••••" textContentType="newPassword" value={confirmPassword} />
            <PrimaryButton icon={<Ionicons color={colors.primaryButtonText} name="arrow-forward" size={18} />} label={t.createAccountAction} loading={loading} onPress={submit} />
          </View>

          <View style={styles.footer}>
            <AppText style={styles.footerText}>{t.hasAccount}</AppText>
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
  hint: { marginTop: -spacing.xs, fontSize: 12 },
  footer: { alignItems: "center", marginTop: spacing.xxl, gap: spacing.xs },
  footerText: { fontSize: 13 },
});
