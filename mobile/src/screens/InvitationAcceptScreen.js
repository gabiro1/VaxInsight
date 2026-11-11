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
import { ErrorState } from "../components/StateView";
import { PasswordField } from "../components/InputField";
import { LanguageSelector } from "../components/LanguageSelector";
import { PrimaryButton, TextButton } from "../components/PrimaryButton";

export function InvitationAcceptScreen({ navigation, route }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { acceptInvitation } = useAuth();
  const token = route?.params?.token || "";
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!token || !password || !confirmPassword) {
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
      await acceptInvitation({ token, password });
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
             <AppText accessibilityRole="header" variant="title">{t.invitationTitle}</AppText>
             <AppText style={styles.description}>{token ? t.invitationReadyDescription : t.invitationLinkMissingDescription}</AppText>
           </View>
           {token ? (
             <View style={styles.form}>
               {error ? <InlineNotice message={error} /> : null}
               <PasswordField label={t.password} onChangeText={setPassword} placeholder="••••••••••••" value={password} />
               <PasswordField label={t.confirmPassword} onChangeText={setConfirmPassword} placeholder="••••••••••••" value={confirmPassword} />
               <AppText style={styles.hint}>{t.passwordHint}</AppText>
               <PrimaryButton icon={<Ionicons color={colors.primaryButtonText} name="arrow-forward" size={18} />} label={t.acceptInvitation} loading={loading} onPress={submit} />
             </View>
           ) : (
             <ErrorState
               actionLabel={t.back}
               description={t.invitationLinkMissingDescription}
               onRetry={() => navigation.goBack()}
               title={t.invitationLinkMissingTitle}
             />
           )}
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
  hint: { marginTop: -spacing.xs, fontSize: 12 },
});
