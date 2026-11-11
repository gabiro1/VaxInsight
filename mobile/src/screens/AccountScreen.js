import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { accountStatusLabel, getErrorMessage, roleLabel } from "../utils/errors";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, layout, radii, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { AppearanceSelector } from "../components/AppearanceSelector";
import { BrandMark } from "../components/BrandMark";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { InlineNotice } from "../components/InlineNotice";
import { InputField, PasswordField } from "../components/InputField";
import { LanguageSelector } from "../components/LanguageSelector";
import {
  DangerButton,
  PrimaryButton,
  SecondaryButton,
  TextButton,
} from "../components/PrimaryButton";

export function AccountScreen({ navigation }) {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const { user, changePassword, updateProfile, deleteAccount, signOut } = useAuth();
  const styles = createStyles(colors);
  const [email, setEmail] = useState(user?.email || "");
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState("");
  const [dialog, setDialog] = useState(null);

  const confirmSignOut = () => {
    setDialog("signOut");
  };

  const confirmDeleteAccount = () => {
    setDialog("delete");
  };

  const deleteMyAccount = async () => {
    setError("");
    setNotice("");
    setBusy("delete");
    try {
      await deleteAccount();
    } catch (requestError) {
      setBusy("");
      setError(getErrorMessage(requestError, t));
    }
  };

  const savePersonalInformation = async () => {
    const trimmedName = fullName.trim();
    const trimmedEmail = email.trim();
    if (!trimmedName || !trimmedEmail) {
      setError(t.requiredField);
      return;
    }

    const emailChanged = trimmedEmail !== user?.email;
    const fullNameChanged = trimmedName !== (user?.full_name || "");
    if (!emailChanged && !fullNameChanged) return;

    setError("");
    setNotice("");
    setBusy("profile");
    try {
      const details = {
        ...(fullNameChanged ? { full_name: trimmedName } : {}),
        ...(emailChanged ? { email: trimmedEmail } : {}),
      };
      await updateProfile(details);
      setNotice(emailChanged ? t.verificationPending : t.profileUpdated);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setBusy("");
    }
  };

  const savePassword = async () => {
    if (!currentPassword || !newPassword || !confirmNewPassword) {
      setError(t.requiredField);
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setError(t.passwordMismatch);
      return;
    }
    setError("");
    setNotice("");
    setBusy("password");
    try {
      await changePassword({ current_password: currentPassword, new_password: newPassword });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmNewPassword("");
      setNotice(t.passwordChanged);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setBusy("");
    }
  };

  const resendVerification = async () => {
    setError("");
    setNotice("");
    setBusy("verification");
    try {
      await api.resendEmailVerification(user.email);
      setNotice(t.verificationPending);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setBusy("");
    }
  };

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
            <AppText accessibilityRole="header" variant="title">{t.profile}</AppText>
            <AppText style={styles.description}>{user?.full_name || user?.email}</AppText>
          </View>
          {error ? <InlineNotice message={error} /> : null}
          {notice ? <InlineNotice message={notice} tone="success" /> : null}

          <View style={styles.profileCard}>
            <View style={styles.avatar}><Ionicons color={colors.orange} name="person-outline" size={25} /></View>
            <View style={styles.profileCopy}>
              <AppText style={styles.profileLabel}>{t.signedInAs}</AppText>
              <AppText variant="card" numberOfLines={1}>{user?.full_name || user?.email}</AppText>
              {user?.full_name ? <AppText style={styles.meta} numberOfLines={1}>{user.email}</AppText> : null}
              <AppText style={styles.meta}>{roleLabel(user?.role, t)}</AppText>
              <AppText style={styles.meta}>{accountStatusLabel(user?.status, t)}</AppText>
            </View>
          </View>

          <AppearanceSelector />

          <View style={styles.aboutCard}>
            <View style={styles.aboutHeading}>
              <View style={styles.aboutIcon}>
                <Ionicons color={colors.orange} name="information-circle-outline" size={22} />
              </View>
              <View style={styles.aboutCopy}>
                <AppText variant="section">{t.aboutVaxInsightTitle}</AppText>
                <AppText style={styles.aboutDescription}>{t.aboutVaxInsightDescription}</AppText>
              </View>
            </View>
          </View>

          <View style={styles.section}>
            <AppText variant="section">{t.personalInformation}</AppText>
            <InputField autoCapitalize="words" label={t.fullName} onChangeText={setFullName} value={fullName} />
            <InputField autoCapitalize="none" keyboardType="email-address" label={t.email} onChangeText={setEmail} value={email} />
            <PrimaryButton label={t.saveChanges} loading={busy === "profile"} onPress={savePersonalInformation} />
            {!user?.email_verified_at ? (
              <SecondaryButton label={t.resendVerification} loading={busy === "verification"} onPress={resendVerification} />
            ) : null}
          </View>

          <View style={styles.section}>
            <AppText variant="section">{t.changePassword}</AppText>
            <PasswordField label={t.currentPassword} onChangeText={setCurrentPassword} value={currentPassword} />
            <PasswordField label={t.newPassword} onChangeText={setNewPassword} value={newPassword} />
            <PasswordField label={t.confirmNewPassword} onChangeText={setConfirmNewPassword} value={confirmNewPassword} />
            <PrimaryButton label={t.saveChanges} loading={busy === "password"} onPress={savePassword} />
          </View>

          <View style={styles.actions}>
            <AppText variant="section">{t.accountActions}</AppText>
            <SecondaryButton label={t.signOut} onPress={confirmSignOut} />
          </View>

          <View style={styles.dangerSection}>
            <AppText variant="section" style={styles.dangerTitle}>{t.dangerZone}</AppText>
            <AppText style={styles.dangerDescription}>{t.deleteAccountDescription}</AppText>
            <DangerButton
              label={t.deleteAccount}
              loading={busy === "delete"}
              onPress={confirmDeleteAccount}
            />
          </View>
        </ScrollView>
        <ConfirmDialog
          cancelLabel={t.cancel}
          confirmLabel={dialog === "delete" ? t.deleteAccount : t.signOut}
          description={dialog === "delete" ? t.confirmDeleteAccountDescription : t.confirmSignOutDescription}
          destructive={dialog === "delete"}
          onCancel={() => setDialog(null)}
          onConfirm={async () => {
            const action = dialog;
            setDialog(null);
            if (action === "delete") await deleteMyAccount();
            else await signOut();
          }}
          title={dialog === "delete" ? t.confirmDeleteAccountTitle : t.confirmSignOutTitle}
          visible={Boolean(dialog)}
        />
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.creamLight },
  flex: { flex: 1 },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.huge + 88, gap: spacing.lg },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  intro: { marginTop: spacing.xl },
  description: { marginTop: spacing.xs },
  profileCard: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surface, flexDirection: "row", gap: spacing.md, ...getShadows(colors).card },
  avatar: { width: 50, height: 50, borderRadius: 25, backgroundColor: colors.orangeLight, alignItems: "center", justifyContent: "center" },
  profileCopy: { flex: 1, gap: spacing.xxs },
  profileLabel: { fontSize: 12 },
  meta: { fontSize: 13 },
  aboutCard: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, ...getShadows(colors).card },
  aboutHeading: { flexDirection: "row", alignItems: "flex-start", gap: spacing.sm },
  aboutIcon: { width: 42, height: 42, borderRadius: 21, alignItems: "center", justifyContent: "center", backgroundColor: colors.accentBackground },
  aboutCopy: { flex: 1, gap: spacing.xs },
  aboutDescription: { color: colors.secondaryText, lineHeight: 21 },
  section: { padding: spacing.lg, borderRadius: radii.lg, backgroundColor: colors.surface, gap: spacing.md, ...getShadows(colors).card },
  actions: { gap: spacing.md, paddingTop: spacing.sm },
  dangerSection: {
    padding: spacing.lg,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.error,
    backgroundColor: colors.surface,
    gap: spacing.md,
  },
  dangerTitle: { color: colors.error },
  dangerDescription: { color: colors.inkSecondary },
});
