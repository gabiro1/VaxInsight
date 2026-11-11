import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useState } from "react";
import { Linking, Pressable, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, layout, radii, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { EmptyState, ErrorState, FullScreenLoader } from "../components/StateView";
import { InlineNotice } from "../components/InlineNotice";
import { LanguageSelector } from "../components/LanguageSelector";
import { SecondaryButton, TextButton } from "../components/PrimaryButton";
import { formatDate, getErrorMessage } from "../utils/errors";

export function OfficialVaccineInfoScreen({ navigation }) {
  const { language, t } = useLanguage();
  const { authenticatedRequest } = useAuth();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [sourceError, setSourceError] = useState("");

  const load = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError("");
      try {
        const result = await authenticatedRequest((token) =>
          api.listVaccineContent(token, { language }),
        );
        setItems(result || []);
      } catch (requestError) {
        setError(getErrorMessage(requestError, t));
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [authenticatedRequest, language, t],
  );

  useEffect(() => {
    load();
  }, [load]);

  const openSource = async (url) => {
    if (!url) return;
    setSourceError("");
    try {
      await Linking.openURL(url);
    } catch {
      setSourceError(t.sourceLinkUnavailable);
    }
  };

  if (loading && !items.length) return <FullScreenLoader label={t.loading} />;

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={
          <RefreshControl
            onRefresh={() => load(true)}
            refreshing={refreshing}
            tintColor={colors.orange}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <TextButton label={t.back} onPress={() => navigation.goBack()} />
          <BrandMark compact />
          <LanguageSelector />
        </View>

        <View style={styles.intro}>
          <AppText accessibilityRole="header" variant="title">
            {t.officialVaccineInfo}
          </AppText>
          <AppText style={styles.description}>{t.officialVaccineInfoIntro}</AppText>
        </View>

        {error && items.length ? <InlineNotice message={error} /> : null}
        {error && !items.length ? (
          <ErrorState
            actionLabel={t.retry}
            description={error}
            onRetry={() => load()}
            title={t.genericError}
          />
        ) : null}
        {!error && !items.length ? (
          <EmptyState
            description={t.officialVaccineInfoEmptyDescription}
            icon="shield-checkmark-outline"
            title={t.officialVaccineInfoEmptyTitle}
          />
        ) : null}
        {sourceError ? <InlineNotice message={sourceError} /> : null}

        <View style={styles.list}>
          {items.map((item) => (
            <View key={item.id} style={styles.card}>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={item.title}
                onPress={() => navigation.navigate("VaccineArticleDetail", { contentId: item.id })}
                style={({ pressed }) => [styles.articlePressable, pressed && styles.pressed]}
              >
                <View style={styles.cardHeading}>
                  <View style={styles.iconCircle}>
                    <Ionicons
                      color={colors.primaryAccent}
                      name="shield-checkmark-outline"
                      size={22}
                    />
                  </View>
                  <View style={styles.headingCopy}>
                    <AppText variant="card">{item.title}</AppText>
                    <AppText style={styles.category}>
                      {t.vaccineCategory}: {item.category}
                    </AppText>
                  </View>
                </View>
                <AppText style={styles.summary}>{item.summary}</AppText>
              </Pressable>
              <View style={styles.meta}>
                <AppText style={styles.metaText}>
                  {t.vaccineSource}: {item.source?.name}
                </AppText>
                <AppText style={styles.metaText}>
                  {t.publishedAt}: {formatDate(item.published_at, language)}
                </AppText>
              </View>
              <AppText style={styles.authority}>
                {t.vaccineAuthority}: {item.source?.authority}
              </AppText>
              {item.source?.url ? (
                <SecondaryButton label={t.openSourceLink} onPress={() => openSource(item.source.url)} />
              ) : (
                <AppText style={styles.authority}>{t.sourceLinkUnavailable}</AppText>
              )}
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.creamLight },
  scroll: {
    flexGrow: 1,
    padding: layout.gutter,
    paddingBottom: spacing.huge + 88,
    gap: spacing.lg,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  intro: { marginTop: spacing.xl, gap: spacing.sm },
  description: { maxWidth: 370 },
  list: { gap: spacing.md },
  card: {
    padding: spacing.lg,
    borderRadius: radii.lg,
     backgroundColor: colors.surface,
    gap: spacing.md,
    ...getShadows(colors).card,
  },
   articlePressable: { gap: spacing.md },
   pressed: { opacity: 0.82 },
   cardHeading: { flexDirection: "row", alignItems: "flex-start", gap: spacing.sm },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.orangeLight,
    alignItems: "center",
    justifyContent: "center",
  },
  headingCopy: { flex: 1, gap: spacing.xxs },
  category: { color: colors.orange, fontSize: 12 },
   summary: { color: colors.primaryText, fontFamily: "DMSans_600SemiBold", lineHeight: 23 },
   body: { color: colors.secondaryText, lineHeight: 24 },
  meta: {
    gap: spacing.xs,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  metaText: { color: colors.muted, fontSize: 12 },
  authority: { color: colors.muted, fontSize: 12 },
});
