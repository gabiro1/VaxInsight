import { Ionicons } from "@expo/vector-icons";
import { StatusBar } from "expo-status-bar";
import { StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CinematicHero } from "../components/CinematicHero";
import { useLanguage } from "../context/LanguageContext";
import { layout, spacing } from "../theme/tokens";
import { BrandMark } from "../components/BrandMark";
import { LanguageSelector } from "../components/LanguageSelector";
import { SlideToContinue } from "../components/SlideToContinue";
import { TextButton } from "../components/PrimaryButton";

export function WelcomeScreen({ navigation }) {
  const { t } = useLanguage();
  const styles = createStyles();
  const insets = useSafeAreaInsets();

  const continueToAuth = () => navigation.navigate("AuthChoice");

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <CinematicHero
        accentTagline={t.heroTaglineAccent}
        eyebrow={t.heroEyebrow}
        onContinue={continueToAuth}
        renderActions={({ onContinue }) => (
          <View style={[styles.bottomContent, { paddingBottom: Math.max(insets.bottom, spacing.md) }]}>
            <View style={styles.sliderGroup}>
              <SlideToContinue label={t.getStarted} hint={t.slideHint} onComplete={onContinue} />
              <View style={styles.tapAlternative}>
                <Ionicons color="rgba(255,255,255,0.72)" name="hand-left-outline" size={15} />
                <TextButton inverse label={t.tapToContinue} onPress={onContinue} />
              </View>
            </View>
          </View>
        )}
        tagline={t.heroTaglinePrimary}
        topContent={(
          <View style={[styles.topRow, { paddingTop: Math.max(insets.top, spacing.md) }]}>
            <BrandMark inverse />
            <LanguageSelector inverse />
          </View>
        )}
      />
    </View>
  );
}

const createStyles = () => StyleSheet.create({
  root: { flex: 1, backgroundColor: "#071020" },
  topRow: {
    marginHorizontal: layout.gutter,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    minHeight: 52,
    paddingHorizontal: spacing.sm,
    paddingBottom: spacing.xs,
  },
  bottomContent: {
    width: "100%",
    maxWidth: 520,
    alignSelf: "center",
    paddingHorizontal: layout.gutter,
  },
  sliderGroup: { marginTop: spacing.lg },
  tapAlternative: {
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
    gap: spacing.xs,
    marginTop: spacing.sm,
  },
});
