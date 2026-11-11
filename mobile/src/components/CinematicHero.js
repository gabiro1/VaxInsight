import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { useEffect, useRef, useState } from "react";
import { Animated, StyleSheet, View, useWindowDimensions } from "react-native";

import { useTheme } from "../context/ThemeContext";
import { getShadows, radii, spacing, typography } from "../theme/tokens";
import { AppText } from "./AppText";

const HERO_IMAGE = require("../../assets/welcome-clinic-hero.jpg");

export function CinematicHero({
  eyebrow,
  tagline,
  accentTagline,
  cardHeading,
  cardDescription,
  secureLabel,
  badgeOne,
  badgeOneCaption,
  badgeTwo,
  badgeTwoCaption,
  phoneToday,
  metricValue,
  metricLabel,
  topContent,
  renderActions,
  onContinue,
}) {
  const { colors } = useTheme();
  const { width, height } = useWindowDimensions();
  const styles = createStyles(colors, width, height);
  const [leaving, setLeaving] = useState(false);
  const leavingRef = useRef(false);
  const callbackRef = useRef(onContinue);
  const heroProgress = useRef(new Animated.Value(0)).current;
  const cardProgress = useRef(new Animated.Value(0)).current;
  const detailProgress = useRef(new Animated.Value(0)).current;
  const actionProgress = useRef(new Animated.Value(0)).current;
  const ambientProgress = useRef(new Animated.Value(0)).current;
  const exitProgress = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    callbackRef.current = onContinue;
  }, [onContinue]);

  useEffect(() => {
    const entrance = Animated.sequence([
      Animated.parallel([
        Animated.timing(heroProgress, {
          toValue: 1,
          duration: 760,
          useNativeDriver: true,
        }),
      ]),
      Animated.timing(cardProgress, {
        toValue: 1,
        duration: 720,
        useNativeDriver: true,
      }),
      Animated.parallel([
        Animated.timing(detailProgress, {
          toValue: 1,
          duration: 560,
          useNativeDriver: true,
        }),
        Animated.timing(actionProgress, {
          toValue: 1,
          duration: 520,
          useNativeDriver: true,
        }),
      ]),
    ]);

    const ambient = Animated.loop(
      Animated.sequence([
        Animated.timing(ambientProgress, {
          toValue: 1,
          duration: 4200,
          useNativeDriver: true,
        }),
        Animated.timing(ambientProgress, {
          toValue: 0,
          duration: 4200,
          useNativeDriver: true,
        }),
      ]),
    );

    entrance.start();
    ambient.start();

    return () => {
      entrance.stop();
      ambient.stop();
    };
  }, [actionProgress, ambientProgress, cardProgress, detailProgress, heroProgress]);

  const handleContinue = () => {
    if (leavingRef.current) return;
    leavingRef.current = true;
    setLeaving(true);

    Animated.timing(exitProgress, {
      toValue: 1,
      duration: 330,
      useNativeDriver: true,
    }).start(({ finished }) => {
      if (finished) callbackRef.current?.();
    });
  };

  const backgroundScale = ambientProgress.interpolate({
    inputRange: [0, 1],
    outputRange: [1.06, 1.13],
  });
  const backgroundX = ambientProgress.interpolate({
    inputRange: [0, 1],
    outputRange: [-8, 8],
  });
  const backgroundY = ambientProgress.interpolate({
    inputRange: [0, 1],
    outputRange: [4, -4],
  });
  const headlineY = heroProgress.interpolate({
    inputRange: [0, 1],
    outputRange: [24, 0],
  });
  const headlineScale = heroProgress.interpolate({
    inputRange: [0, 1],
    outputRange: [0.94, 1],
  });
  const cardY = cardProgress.interpolate({
    inputRange: [0, 1],
    outputRange: [90, 0],
  });
  const cardScale = cardProgress.interpolate({
    inputRange: [0, 1],
    outputRange: [0.86, 1],
  });
  const detailY = detailProgress.interpolate({
    inputRange: [0, 1],
    outputRange: [18, 0],
  });
  const actionY = actionProgress.interpolate({
    inputRange: [0, 1],
    outputRange: [20, 0],
  });
  const exitY = exitProgress.interpolate({
    inputRange: [0, 1],
    outputRange: [0, -24],
  });
  const exitScale = exitProgress.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 0.98],
  });
  const deviceY = ambientProgress.interpolate({
    inputRange: [0, 1],
    outputRange: [4, -4],
  });
  const badgeY = ambientProgress.interpolate({
    inputRange: [0, 1],
    outputRange: [0, -6],
  });

  return (
    <View style={styles.root}>
      <Animated.View
        pointerEvents="box-none"
        style={[styles.scene, { opacity: exitProgress.interpolate({ inputRange: [0, 1], outputRange: [1, 0] }), transform: [{ translateY: exitY }, { scale: exitScale }] }]}
      >
        <Animated.Image
          accessible={false}
          resizeMode="cover"
          source={HERO_IMAGE}
          style={[styles.backgroundImage, { transform: [{ translateX: backgroundX }, { translateY: backgroundY }, { scale: backgroundScale }] }]}
        />
        <LinearGradient
          colors={["rgba(5, 12, 30, 0.2)", "rgba(5, 12, 30, 0.56)", "#071020"]}
          locations={[0, 0.46, 1]}
          pointerEvents="none"
          style={styles.backgroundScrim}
        />
        <LinearGradient
          colors={["rgba(10, 29, 78, 0.44)", "transparent", "rgba(3, 8, 22, 0.64)"]}
          pointerEvents="none"
          style={styles.colorWash}
        />

        <View pointerEvents="none" style={styles.grid}>
          {Array.from({ length: 7 }).map((_, index) => (
            <View key={`vertical-${index}`} style={[styles.gridLineVertical, { left: `${14 + index * 14}%` }]} />
          ))}
          {Array.from({ length: 8 }).map((_, index) => (
            <View key={`horizontal-${index}`} style={[styles.gridLineHorizontal, { top: `${12 + index * 13}%` }]} />
          ))}
        </View>

        <Animated.View pointerEvents="none" style={[styles.orb, { transform: [{ translateX: backgroundX }, { translateY: backgroundY }] }]} />

        <Animated.View style={[styles.topLayer, { opacity: heroProgress, transform: [{ translateY: headlineY }] }]}>
          {topContent}
        </Animated.View>

        <Animated.View pointerEvents="none" style={[styles.headline, { opacity: heroProgress, transform: [{ translateY: headlineY }, { scale: headlineScale }] }]}>
          <AppText style={styles.eyebrow}>{eyebrow}</AppText>
          <AppText style={styles.headlineLine}>{tagline}</AppText>
          <AppText style={styles.headlineAccent}>{accentTagline}</AppText>
        </Animated.View>

        <Animated.View style={[styles.cardShell, { opacity: cardProgress, transform: [{ translateY: cardY }, { scale: cardScale }] }]}>
          <LinearGradient
            colors={["#162C6D", "#0A101D"]}
            end={{ x: 1, y: 1 }}
            start={{ x: 0, y: 0 }}
            style={styles.card}
          >
            <View pointerEvents="none" style={styles.cardSheen} />
            <View style={styles.cardHeader}>
              <View style={styles.cardLabelRow}>
                <View style={styles.liveDot} />
                <AppText style={styles.cardLabel}>{eyebrow}</AppText>
              </View>
              <View style={styles.securePill}>
                <Ionicons color="#A9D3FF" name="shield-checkmark-outline" size={13} />
                <AppText style={styles.secureText}>{secureLabel}</AppText>
              </View>
            </View>

            <Animated.View style={[styles.cardCopy, { opacity: detailProgress, transform: [{ translateY: detailY }] }]}>
              <AppText style={styles.cardHeading}>{cardHeading}</AppText>
              <AppText numberOfLines={2} style={styles.cardDescription}>{cardDescription}</AppText>
            </Animated.View>

            <Animated.View style={[styles.deviceStage, { transform: [{ translateY: deviceY }] }]}>
              <Animated.View style={[styles.floatingBadge, styles.badgeTop, { opacity: detailProgress, transform: [{ translateY: badgeY }] }]}>
                <View style={[styles.badgeIcon, styles.badgeIconBlue]}>
                  <Ionicons color="#9BCBFF" name="checkmark-circle-outline" size={17} />
                </View>
                <View>
                  <AppText style={styles.badgeTitle}>{badgeOne}</AppText>
                  <AppText style={styles.badgeCaption}>{badgeOneCaption}</AppText>
                </View>
              </Animated.View>

              <View style={styles.phone}>
                <View style={styles.phoneScreen}>
                  <View style={styles.dynamicIsland} />
                  <View style={styles.phoneHeader}>
                    <View>
                      <AppText style={styles.phoneOverline}>{phoneToday}</AppText>
                      <AppText style={styles.phoneTitle}>VaxInsight</AppText>
                    </View>
                    <View style={styles.avatar}><Ionicons color="#DCEBFF" name="person-outline" size={15} /></View>
                  </View>

                  <View style={styles.metricDial}>
                    <View style={styles.metricDialInner}>
                      <Ionicons color="#74B9FF" name="pulse-outline" size={17} />
                      <AppText style={styles.metricValue}>{metricValue}</AppText>
                      <AppText style={styles.metricLabel}>{metricLabel}</AppText>
                    </View>
                  </View>

                  <View style={styles.phoneRows}>
                    <View style={styles.phoneRow}>
                      <View style={[styles.rowIcon, styles.rowIconBlue]}><Ionicons color="#7DBBFF" name="document-text-outline" size={14} /></View>
                      <View style={styles.rowCopy}><View style={styles.rowLineWide} /><View style={styles.rowLineShort} /></View>
                      <Ionicons color="#7DBBFF" name="arrow-up-right" size={14} />
                    </View>
                    <View style={styles.phoneRow}>
                      <View style={[styles.rowIcon, styles.rowIconGreen]}><Ionicons color="#80E0B2" name="people-outline" size={14} /></View>
                      <View style={styles.rowCopy}><View style={styles.rowLineMedium} /><View style={styles.rowLineShort} /></View>
                      <Ionicons color="#80E0B2" name="checkmark" size={15} />
                    </View>
                  </View>
                  <View style={styles.homeIndicator} />
                </View>
              </View>

              <Animated.View style={[styles.floatingBadge, styles.badgeBottom, { opacity: detailProgress, transform: [{ translateY: Animated.multiply(badgeY, -1) }] }]}>
                <View style={[styles.badgeIcon, styles.badgeIconGreen]}>
                  <Ionicons color="#8BE7BA" name="people-outline" size={17} />
                </View>
                <View>
                  <AppText style={styles.badgeTitle}>{badgeTwo}</AppText>
                  <AppText style={styles.badgeCaption}>{badgeTwoCaption}</AppText>
                </View>
              </Animated.View>
            </Animated.View>
          </LinearGradient>
        </Animated.View>

        <Animated.View style={[styles.actionLayer, { opacity: actionProgress, transform: [{ translateY: actionY }] }]}>
          {renderActions?.({ onContinue: handleContinue, leaving })}
        </Animated.View>
      </Animated.View>
    </View>
  );
}

const createStyles = (colors, width, height) => {
  const cardWidth = Math.min(width - spacing.lg * 2, width > 700 ? 560 : 390);
  const cardHeight = Math.min(364, Math.max(300, height * 0.43));
  const cardTop = height < 720 ? 216 : 246;

  return StyleSheet.create({
    root: { flex: 1, backgroundColor: "#071020" },
    scene: { flex: 1, overflow: "hidden" },
    backgroundImage: { ...StyleSheet.absoluteFillObject, width: "100%", height: "100%" },
    backgroundScrim: { ...StyleSheet.absoluteFillObject },
    colorWash: { ...StyleSheet.absoluteFillObject, opacity: 0.72 },
    grid: { ...StyleSheet.absoluteFillObject, opacity: 0.22 },
    gridLineVertical: {
      position: "absolute",
      top: 0,
      bottom: 0,
      width: 1,
      backgroundColor: "rgba(179, 216, 255, 0.22)",
    },
    gridLineHorizontal: {
      position: "absolute",
      left: 0,
      right: 0,
      height: 1,
      backgroundColor: "rgba(179, 216, 255, 0.2)",
    },
    orb: {
      position: "absolute",
      width: width * 0.85,
      height: width * 0.85,
      borderRadius: width,
      right: -width * 0.38,
      top: height * 0.08,
      backgroundColor: "rgba(49, 109, 212, 0.18)",
      shadowColor: "#6CB5FF",
      shadowOpacity: 0.24,
      shadowRadius: 70,
    },
    topLayer: { position: "absolute", top: 0, left: 0, right: 0, zIndex: 20 },
    headline: {
      position: "absolute",
      top: height < 720 ? 96 : 112,
      left: spacing.lg,
      right: spacing.lg,
      alignItems: "center",
      zIndex: 10,
    },
    eyebrow: {
      color: "rgba(224, 239, 255, 0.68)",
      fontFamily: typography.family.bodyBold,
      fontSize: 10,
      letterSpacing: 2.2,
      marginBottom: spacing.sm,
    },
    headlineLine: {
      color: "#F7FAFF",
      fontFamily: typography.family.display,
      fontSize: width < 380 ? 34 : 39,
      lineHeight: width < 380 ? 40 : 45,
      letterSpacing: -1.4,
      textAlign: "center",
      textShadowColor: "rgba(0,0,0,0.4)",
      textShadowOffset: { width: 0, height: 8 },
      textShadowRadius: 22,
    },
    headlineAccent: {
      color: "#A9D3FF",
      fontFamily: typography.family.display,
      fontSize: width < 380 ? 37 : 43,
      lineHeight: width < 380 ? 42 : 48,
      letterSpacing: -1.7,
      textAlign: "center",
      textShadowColor: "rgba(82, 157, 255, 0.42)",
      textShadowOffset: { width: 0, height: 4 },
      textShadowRadius: 18,
    },
    cardShell: {
      position: "absolute",
      top: cardTop,
      left: (width - cardWidth) / 2,
      width: cardWidth,
      height: cardHeight,
      borderRadius: width < 380 ? 28 : 34,
      ...getShadows(colors).floating,
      shadowColor: "#000",
      shadowOpacity: 0.56,
    },
    card: {
      flex: 1,
      overflow: "hidden",
      borderRadius: width < 380 ? 28 : 34,
      borderWidth: 1,
      borderColor: "rgba(255,255,255,0.12)",
      padding: width < 380 ? spacing.md : spacing.lg,
    },
    cardSheen: {
      position: "absolute",
      top: -80,
      right: -90,
      width: 260,
      height: 220,
      borderRadius: 180,
      backgroundColor: "rgba(255,255,255,0.08)",
      transform: [{ rotate: "-24deg" }],
    },
    cardHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
    cardLabelRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
    liveDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: "#7DBBFF" },
    cardLabel: { color: "rgba(229, 240, 255, 0.66)", fontFamily: typography.family.bodyBold, fontSize: 9, letterSpacing: 1.4 },
    securePill: {
      flexDirection: "row",
      alignItems: "center",
      gap: 4,
      borderRadius: radii.pill,
      paddingHorizontal: spacing.sm,
      paddingVertical: 6,
      backgroundColor: "rgba(255,255,255,0.08)",
      borderWidth: 1,
      borderColor: "rgba(255,255,255,0.12)",
    },
    secureText: { color: "#C7E1FF", fontFamily: typography.family.bodySemibold, fontSize: 9 },
    cardCopy: { marginTop: width < 380 ? spacing.sm : spacing.md, maxWidth: cardWidth * 0.64 },
    cardHeading: { color: "#FFFFFF", fontFamily: typography.family.heading, fontSize: width < 380 ? 21 : 24, lineHeight: width < 380 ? 25 : 29, letterSpacing: -0.5 },
    cardDescription: { color: "rgba(222, 234, 255, 0.64)", fontFamily: typography.family.body, fontSize: 11, lineHeight: 16, marginTop: 5 },
    deviceStage: { flex: 1, justifyContent: "center", alignItems: "center", minHeight: 170 },
    phone: {
      width: width < 380 ? 118 : 130,
      height: width < 380 ? 174 : 192,
      borderRadius: 25,
      padding: 5,
      backgroundColor: "#101114",
      borderWidth: 1,
      borderColor: "#575B65",
      shadowColor: "#000",
      shadowOpacity: 0.72,
      shadowRadius: 18,
      shadowOffset: { width: 0, height: 12 },
      elevation: 8,
      zIndex: 2,
    },
    phoneScreen: { flex: 1, borderRadius: 20, overflow: "hidden", backgroundColor: "#050914", padding: 10 },
    dynamicIsland: { position: "absolute", top: 4, left: "50%", marginLeft: -24, width: 48, height: 12, borderRadius: 8, backgroundColor: "#000", zIndex: 2 },
    phoneHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 9 },
    phoneOverline: { color: "rgba(192, 213, 240, 0.52)", fontFamily: typography.family.bodyBold, fontSize: 6, letterSpacing: 1 },
    phoneTitle: { color: "#FFFFFF", fontFamily: typography.family.heading, fontSize: 12, marginTop: 2 },
    avatar: { width: 22, height: 22, borderRadius: 11, alignItems: "center", justifyContent: "center", backgroundColor: "rgba(255,255,255,0.08)", borderWidth: 1, borderColor: "rgba(255,255,255,0.12)" },
    metricDial: { alignSelf: "center", width: width < 380 ? 72 : 80, height: width < 380 ? 72 : 80, borderRadius: 50, borderWidth: 6, borderColor: "rgba(255,255,255,0.08)", alignItems: "center", justifyContent: "center", marginTop: 9, transform: [{ rotate: "-18deg" }] },
    metricDialInner: { alignItems: "center", transform: [{ rotate: "18deg" }] },
    metricValue: { color: "#FFFFFF", fontFamily: typography.family.display, fontSize: 17, lineHeight: 19, marginTop: 1 },
    metricLabel: { color: "#84BFFF", fontFamily: typography.family.bodyBold, fontSize: 5, letterSpacing: 0.6, textTransform: "uppercase" },
    phoneRows: { gap: 5, marginTop: 10 },
    phoneRow: { minHeight: 28, borderRadius: 9, backgroundColor: "rgba(255,255,255,0.045)", borderWidth: 1, borderColor: "rgba(255,255,255,0.04)", flexDirection: "row", alignItems: "center", paddingHorizontal: 5, gap: 5 },
    rowIcon: { width: 18, height: 18, borderRadius: 6, alignItems: "center", justifyContent: "center" },
    rowIconBlue: { backgroundColor: "rgba(59,130,246,0.17)" },
    rowIconGreen: { backgroundColor: "rgba(16,185,129,0.17)" },
    rowCopy: { flex: 1, gap: 3 },
    rowLineWide: { width: "78%", height: 3, borderRadius: 2, backgroundColor: "rgba(222,236,255,0.72)" },
    rowLineMedium: { width: "64%", height: 3, borderRadius: 2, backgroundColor: "rgba(222,236,255,0.72)" },
    rowLineShort: { width: "45%", height: 2, borderRadius: 2, backgroundColor: "rgba(133,157,190,0.62)" },
    homeIndicator: { position: "absolute", bottom: 5, left: "50%", marginLeft: -20, width: 40, height: 2, borderRadius: 2, backgroundColor: "rgba(255,255,255,0.28)" },
    floatingBadge: {
      position: "absolute",
      flexDirection: "row",
      alignItems: "center",
      gap: 7,
      borderRadius: 14,
      paddingVertical: 8,
      paddingHorizontal: 9,
      backgroundColor: "rgba(20, 31, 57, 0.88)",
      borderWidth: 1,
      borderColor: "rgba(255,255,255,0.14)",
      ...getShadows(colors).card,
      shadowColor: "#000",
      shadowOpacity: 0.34,
      zIndex: 4,
    },
    badgeTop: { top: 20, left: 0 },
    badgeBottom: { bottom: 20, right: 0 },
    badgeIcon: { width: 28, height: 28, borderRadius: 10, alignItems: "center", justifyContent: "center", borderWidth: 1 },
    badgeIconBlue: { backgroundColor: "rgba(59,130,246,0.18)", borderColor: "rgba(125,187,255,0.28)" },
    badgeIconGreen: { backgroundColor: "rgba(16,185,129,0.18)", borderColor: "rgba(128,224,178,0.28)" },
    badgeTitle: { color: "#F4F8FF", fontFamily: typography.family.bodySemibold, fontSize: 9 },
    badgeCaption: { color: "rgba(177,203,238,0.62)", fontFamily: typography.family.body, fontSize: 8, marginTop: 2 },
    actionLayer: { position: "absolute", left: 0, right: 0, bottom: 0, zIndex: 30 },
  });
};
