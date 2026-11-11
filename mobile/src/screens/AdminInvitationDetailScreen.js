import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { AdminAccessDenied, AdminCard, AdminHeader } from "../components/AdminComponents";
import { AppText } from "../components/AppText";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { ErrorState, FullScreenLoader } from "../components/StateView";
import { InlineNotice } from "../components/InlineNotice";
import { DangerButton, SecondaryButton } from "../components/PrimaryButton";
import { StatusPill } from "../components/StatusPill";
import { Toast } from "../components/Toast";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { formatDate, getErrorMessage, invitationStatusLabel, roleLabel } from "../utils/errors";
import { layout, radii, spacing } from "../theme/tokens";

export function AdminInvitationDetailScreen({ navigation, route }) {
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { authenticatedRequest, user } = useAuth();
  const isAdmin = user?.role === "administrator";
  const invitationId = route?.params?.invitationId;
  const [invitation, setInvitation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [confirmingAction, setConfirmingAction] = useState(null);
  const [busyAction, setBusyAction] = useState("");

  const load = useCallback(async () => {
    if (!isAdmin || !invitationId) return;
    setLoading(true);
    setError("");
    try {
      const result = await authenticatedRequest((token) => api.getAdminInvitation(token, invitationId));
      setInvitation(result);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setLoading(false);
    }
  }, [authenticatedRequest, invitationId, isAdmin, t]);

  useEffect(() => {
    load();
  }, [load]);

  const revoke = async () => {
    setBusyAction("revoke");
    setError("");
    try {
      const result = await authenticatedRequest((token) => api.revokeAdminInvitation(token, invitationId));
      setInvitation(result);
      setNotice(t.invitationRevoked);
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setBusyAction("");
      setConfirmingAction(null);
    }
  };

  const resend = async () => {
    setBusyAction("resend");
    setError("");
    try {
      await authenticatedRequest((token) =>
        api.createInvitation(token, {
          email: invitation.email,
          role: invitation.role,
        }),
      );
      navigation.replace("AdminInvitations", {
        notice: t.invitationResent,
        status: "pending",
      });
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setBusyAction("");
      setConfirmingAction(null);
    }
  };

  const deleteInvitation = async () => {
    setBusyAction("delete");
    setError("");
    try {
      await authenticatedRequest((token) => api.deleteAdminInvitation(token, invitationId));
      navigation.replace("AdminInvitations", { notice: t.invitationDeleted });
    } catch (requestError) {
      setError(getErrorMessage(requestError, t));
    } finally {
      setBusyAction("");
      setConfirmingAction(null);
    }
  };

  if (!isAdmin) return <AdminAccessDenied navigation={navigation} />;
  if (loading && !invitation) return <FullScreenLoader label={t.loading} />;
  if (error && !invitation) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.content}>
          <AdminHeader navigation={navigation} title={t.adminInvitationDetails} />
          <ErrorState actionLabel={t.retry} description={error} onRetry={load} title={t.genericError} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <AdminHeader description={t.adminInvitationDetails} navigation={navigation} title={invitation?.email || t.adminInvitations} />
        {error ? <InlineNotice message={error} /> : null}
        <Toast message={notice} onDismiss={() => setNotice("")} />
        <AdminCard>
          <View style={styles.heading}>
            <View style={styles.iconCircle}><AppText style={styles.iconText}>{invitation?.email?.slice(0, 1).toUpperCase()}</AppText></View>
            <View style={styles.copy}>
              <AppText variant="card" numberOfLines={1}>{invitation?.email}</AppText>
              <AppText style={styles.meta}>{roleLabel(invitation?.role, t)}</AppText>
            </View>
            <StatusPill label={invitationStatusLabel(invitation?.status, t)} tone={invitation?.status === "pending" ? "warning" : invitation?.status === "accepted" ? "success" : "neutral"} />
          </View>
          <View style={styles.details}>
            <Detail label={t.createdAt} value={formatDate(invitation?.created_at, language)} />
            <Detail label={t.invitationExpiry} value={formatDate(invitation?.expires_at, language)} />
            <Detail label={t.accepted} value={formatDate(invitation?.accepted_at, language) || t.emptyDescription} />
            <Detail label={t.revoked} value={formatDate(invitation?.revoked_at, language) || t.emptyDescription} />
          </View>
        </AdminCard>
        <View style={styles.actions}>
          {invitation?.status === "pending" ? (
            <DangerButton
              label={t.revokeInvitation}
              loading={busyAction === "revoke"}
              onPress={() => setConfirmingAction("revoke")}
            />
          ) : null}
          {(["pending", "revoked", "expired"].includes(invitation?.status)) ? (
            <SecondaryButton
              label={t.resendInvitation}
              loading={busyAction === "resend"}
              onPress={() => setConfirmingAction("resend")}
            />
          ) : null}
          {invitation?.status === "revoked" ? (
            <DangerButton
              label={t.deleteInvitation}
              loading={busyAction === "delete"}
              onPress={() => setConfirmingAction("delete")}
            />
          ) : null}
        </View>
      </ScrollView>
      <ConfirmDialog
        cancelLabel={t.cancel}
        confirmLabel={confirmingAction === "delete" ? t.deleteInvitation : confirmingAction === "resend" ? t.resendInvitation : t.revokeInvitation}
        description={confirmingAction === "delete" ? t.deleteInvitationDescription : confirmingAction === "resend" ? t.resendInvitationDescription : t.revokeInvitationDescription}
        destructive={confirmingAction !== "resend"}
        onCancel={() => setConfirmingAction(null)}
        onConfirm={confirmingAction === "delete" ? deleteInvitation : confirmingAction === "resend" ? resend : revoke}
        title={confirmingAction === "delete" ? t.deleteInvitationTitle : confirmingAction === "resend" ? t.resendInvitationTitle : t.revokeInvitationTitle}
        visible={Boolean(confirmingAction)}
      />
      {busyAction ? <View style={styles.busyOverlay}><ActivityIndicator color={colors.orange} /></View> : null}
    </SafeAreaView>
  );
}

function Detail({ label, value }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  return (
    <View style={styles.detail}>
      <AppText style={styles.detailLabel}>{label}</AppText>
      <AppText style={styles.detailValue}>{value}</AppText>
    </View>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  content: { flex: 1, padding: layout.gutter },
  scroll: { flexGrow: 1, padding: layout.gutter, paddingBottom: spacing.xxl, gap: spacing.lg },
  heading: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  iconCircle: { width: 52, height: 52, borderRadius: 26, alignItems: "center", justifyContent: "center", backgroundColor: colors.orangeLight },
  iconText: { color: colors.orange, fontSize: 22, fontFamily: "SpaceGrotesk_700Bold" },
  copy: { flex: 1, gap: spacing.xxs },
  meta: { color: colors.muted, fontSize: 12 },
  details: { marginTop: spacing.lg, paddingTop: spacing.md, borderTopWidth: 1, borderTopColor: colors.divider, gap: spacing.sm },
  actions: { gap: spacing.md },
  detail: { flexDirection: "row", justifyContent: "space-between", gap: spacing.md },
  detailLabel: { color: colors.muted, fontSize: 13 },
  detailValue: { flex: 1, color: colors.primaryText, fontSize: 13, textAlign: "right" },
  busyOverlay: { position: "absolute", left: 0, right: 0, top: 0, bottom: 0, alignItems: "center", justifyContent: "center", backgroundColor: colors.overlay },
});
