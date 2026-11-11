import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
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
import { InputField, PasswordField } from "../components/InputField";
import { LanguageSelector } from "../components/LanguageSelector";
import { PrimaryButton, TextButton } from "../components/PrimaryButton";

export function PasswordResetConfirmScreen({ navigation, route }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { session, signOut } = useAuth();
  const [token, setToken] = useState(route?.params?.token || "");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!token.trim() || !password || !confirmPassword) {
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
      await api.confirmPasswordReset({ token: token.trim(), new_password: password });
      if (session) await signOut();
      setSuccess(true);
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
            <AppText accessibilityRole="header" variant="title">{t.resetPasswordConfirmTitle}</AppText>
            <AppText style={styles.description}>{t.resetPasswordConfirmIntro}</AppText>
          </View>
          <View style={styles.form}>
            {error ? <InlineNotice message={error} /> : null}
            {success ? (
              <>
                <InlineNotice message={t.passwordChanged} tone="success" />
                <PrimaryButton label={t.signIn} onPress={() => navigation.navigate("Login")} />
              </>
            ) : (
              <>
                <InputField label={t.resetToken} onChangeText={setToken} placeholder="Paste token" value={token} />
                <PasswordField label={t.newPassword} onChangeText={setPassword} placeholder="••••••••••••" value={password} />
                <PasswordField label={t.confirmNewPassword} onChangeText={setConfirmPassword} placeholder="••••••••••••" value={confirmPassword} />
            <PrimaryButton icon={<Ionicons color={colors.primaryButtonText} name="checkmark" size={18} />} label={t.resetPassword} loading={loading} onPress={submit} />
              </>
            )}
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
  intro: { marginTop: spacing.xxl },
  description: { marginTop: spacing.sm, maxWidth: 360 },
  form: { gap: spacing.md, marginTop: spacing.xxl },
});
