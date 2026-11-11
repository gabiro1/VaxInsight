import { Ionicons } from "@expo/vector-icons";
import { useEffect, useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { getErrorMessage } from "../utils/errors";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { layout, spacing, typography } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { InlineNotice } from "../components/InlineNotice";
import { InputField, PasswordField } from "../components/InputField";
import { LanguageSelector } from "../components/LanguageSelector";
import { PrimaryButton, TextButton } from "../components/PrimaryButton";

export function LoginScreen({ navigation, route }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState(route?.params?.registered ? t.accountCreatedDescription : "");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (route?.params?.registered) {
      navigation.setParams({ registered: undefined });
    }
  }, [navigation, route?.params?.registered]);

  const submit = async () => {
    if (!email.trim() || !password) {
      setError(t.requiredField);
      return;
    }
    setError("");
    setNotice("");
    setLoading(true);
    try {
      await signIn({ email: email.trim(), password });
    } catch (requestError) {
      setError(
        requestError?.status === 401
          ? t.invalidCredentials
          : getErrorMessage(requestError, t),
      );
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
            <AppText accessibilityRole="header" variant="title">{t.welcomeBack}</AppText>
            <AppText style={styles.description}>{t.signInIntro}</AppText>
          </View>

          <View style={styles.form}>
            {notice ? <InlineNotice message={notice} tone="success" /> : null}
            {error ? <InlineNotice message={error} /> : null}
            <InputField
              autoCapitalize="none"
              autoComplete="email"
              keyboardType="email-address"
              label={t.email}
              onChangeText={setEmail}
              placeholder="you@example.com"
              textContentType="emailAddress"
              value={email}
            />
            <PasswordField
              autoComplete="password"
              label={t.password}
              onChangeText={setPassword}
              placeholder="••••••••••••"
              textContentType="password"
              value={password}
            />
            <View style={styles.forgotRow}>
              <TextButton label={t.forgotPassword} onPress={() => navigation.navigate("PasswordReset")} />
            </View>
            <PrimaryButton icon={<Ionicons color={colors.primaryButtonText} name="arrow-forward" size={18} />} label={t.signInAction} loading={loading} onPress={submit} />
          </View>

          <View style={styles.footer}>
            <AppText style={styles.footerText}>{t.noAccount}</AppText>
            <TextButton label={t.registerAction} onPress={() => navigation.navigate("Register")} />
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
  description: { marginTop: spacing.sm, maxWidth: 340 },
  form: { gap: spacing.md, marginTop: spacing.xxl },
  forgotRow: { alignItems: "flex-end", marginTop: -spacing.xs },
  footer: { alignItems: "center", marginTop: "auto", paddingTop: spacing.xxl, gap: spacing.xs },
  footerText: { fontSize: 13 },
});
