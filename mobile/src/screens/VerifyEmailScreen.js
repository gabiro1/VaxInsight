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
import { InputField } from "../components/InputField";
import { LanguageSelector } from "../components/LanguageSelector";
import { PrimaryButton, SecondaryButton, TextButton } from "../components/PrimaryButton";

export function VerifyEmailScreen({ navigation, route }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { session, verifyEmail } = useAuth();
  const [otp, setOtp] = useState(route?.params?.otp || "");
  const [email, setEmail] = useState(route?.params?.email || "");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);

  const verify = async () => {
    if (!email.trim() || !otp.trim()) {
      setError(t.requiredField);
      return;
    }
    setError("");
    setLoading(true);
    try {
      const hadSession = Boolean(session);
      await verifyEmail({ email: email.trim(), otp: otp.trim() });
      if (hadSession) {
        navigation.reset({ index: 0, routes: [{ name: "Home" }] });
      }
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setLoading(false);
    }
  };

  const resend = async () => {
    if (!email.trim()) {
      setError(t.requiredField);
      return;
    }
    setError("");
    setResending(true);
    try {
      await api.resendEmailVerification(email.trim());
      setNotice(t.verificationPending);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setResending(false);
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
            <AppText accessibilityRole="header" variant="title">{t.verifyEmailTitle}</AppText>
            <AppText style={styles.description}>{t.verifyEmailIntro}</AppText>
          </View>
          <View style={styles.form}>
            {error ? <InlineNotice message={error} /> : null}
            {notice ? <InlineNotice message={notice} tone="success" /> : null}
            <InputField
              autoCapitalize="none"
              keyboardType="number-pad"
              label={t.verificationCode}
              maxLength={6}
              onChangeText={setOtp}
              placeholder="123456"
              value={otp}
            />
            <PrimaryButton icon={<Ionicons color={colors.primaryButtonText} name="checkmark" size={18} />} label={t.verifyEmail} loading={loading} onPress={verify} />
            <View style={styles.divider} />
            <InputField autoCapitalize="none" keyboardType="email-address" label={t.email} onChangeText={setEmail} placeholder="you@example.com" value={email} />
            <SecondaryButton label={t.resendVerification} loading={resending} onPress={resend} />
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
  divider: { height: 1, backgroundColor: colors.border, marginVertical: spacing.xs },
});
