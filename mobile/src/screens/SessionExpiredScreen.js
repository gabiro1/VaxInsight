import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { layout, radii, spacing } from "../theme/tokens";
import { AppText } from "../components/AppText";
import { BrandMark } from "../components/BrandMark";
import { PrimaryButton } from "../components/PrimaryButton";

export function SessionExpiredScreen() {
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const { signOut } = useAuth();

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.content}>
        <BrandMark compact />
        <View style={styles.iconCircle}>
          <Ionicons color={colors.orange} name="lock-closed-outline" size={28} />
        </View>
        <AppText accessibilityRole="header" variant="title" style={styles.title}>{t.sessionExpiredTitle}</AppText>
        <AppText style={styles.description}>{t.sessionExpiredDescription}</AppText>
        <PrimaryButton label={t.signInAgain} onPress={signOut} />
      </View>
    </SafeAreaView>
  );
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.creamLight },
  content: { flex: 1, padding: layout.gutter, justifyContent: "center", alignItems: "stretch" },
  iconCircle: { width: 64, height: 64, borderRadius: 32, backgroundColor: colors.orangeLight, alignItems: "center", justifyContent: "center", marginTop: spacing.huge, alignSelf: "center" },
  title: { textAlign: "center", marginTop: spacing.lg },
  description: { textAlign: "center", marginTop: spacing.sm, marginBottom: spacing.xl },
});
