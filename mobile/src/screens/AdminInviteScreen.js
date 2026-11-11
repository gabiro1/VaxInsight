import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { AdminAccessDenied, AdminCard, AdminHeader, ChoiceChip } from "../components/AdminComponents";
import { AppText } from "../components/AppText";
import { InlineNotice } from "../components/InlineNotice";
import { InputField } from "../components/InputField";
import { PrimaryButton, SecondaryButton } from "../components/PrimaryButton";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { formatDate, getErrorMessage, roleLabel } from "../utils/errors";
import { layout, spacing } from "../theme/tokens";

const staffRoles = ["chw", "reviewer", "administrator"];

export function AdminInviteScreen({ navigation }) {
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest, user } = useAuth();
  const isAdmin = user?.role === "administrator";
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("chw");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(null);

  if (!isAdmin) return <AdminAccessDenied navigation={navigation} />;

  const submit = async () => {
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail) {
      setError(t.requiredField);
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(normalizedEmail)) {
      setError(t.invalidEmail);
      return;
    }

    setLoading(true);
    setError("");
    setSuccess(null);
    try {
      const result = await authenticatedRequest((token) =>
        api.createInvitation(token, { email: normalizedEmail, role }),
      );
      setEmail("");
      setSuccess(result);
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
          <AdminHeader description={t.inviteStaffDescription} navigation={navigation} title={t.inviteStaff} />
          {error ? <InlineNotice message={error} /> : null}
          {success ? (
            <InlineNotice
              message={`${t.invitationSent}. ${t.invitationSentDescription} ${t.invitationExpiry}: ${formatDate(success.expires_at, language)}`}
              tone="success"
            />
          ) : null}

          <AdminCard>
            <View style={styles.formHeader}>
              <View style={styles.iconCircle}><Ionicons color={colors.orange} name="mail-open-outline" size={23} /></View>
              <View style={styles.headerCopy}>
                <AppText variant="card">{t.inviteStaff}</AppText>
                <AppText style={styles.helper}>{t.inviteStaffDescription}</AppText>
              </View>
            </View>
            <InputField
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="email-address"
              label={t.invitationEmail}
              onChangeText={setEmail}
              placeholder="staff@example.com"
              value={email}
            />
            <AppText style={styles.label}>{t.invitationRole}</AppText>
            <View style={styles.roleChoices}>
              {staffRoles.map((staffRole) => (
                <ChoiceChip key={staffRole} label={roleLabel(staffRole, t)} onPress={() => setRole(staffRole)} selected={role === staffRole} />
              ))}
            </View>
            <PrimaryButton icon={<Ionicons color={colors.primaryButtonText} name="send-outline" size={18} />} label={t.sendInvitation} loading={loading} onPress={submit} />
          </AdminCard>
          <SecondaryButton label={t.adminInvitations} onPress={() => navigation.navigate("AdminInvitations")} />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  flex: { flex: 1 },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl, gap: spacing.lg },
  formHeader: { flexDirection: "row", gap: spacing.sm, alignItems: "flex-start", marginBottom: spacing.md },
  iconCircle: { width: 46, height: 46, borderRadius: 23, alignItems: "center", justifyContent: "center", backgroundColor: colors.orangeLight },
  headerCopy: { flex: 1, gap: spacing.xs },
  helper: { color: colors.secondaryText, lineHeight: 20 },
  label: { fontFamily: "DMSans_600SemiBold", fontSize: 13, color: colors.primaryText },
  roleChoices: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
});
