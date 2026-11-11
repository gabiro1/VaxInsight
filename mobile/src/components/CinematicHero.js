import { LinearGradient } from "expo-linear-gradient";
import { useEffect, useRef, useState } from "react";
import { Animated, StyleSheet, View, useWindowDimensions } from "react-native";

import { spacing, typography } from "../theme/tokens";
import { AppText } from "./AppText";

const HERO_IMAGE = require("../../assets/welcome-clinic-hero.jpg");

export function CinematicHero({
  eyebrow,
  tagline,
  accentTagline,
  topContent,
  renderActions,
  onContinue,
}) {
  const { width, height } = useWindowDimensions();
  const styles = createStyles(width, height);
  const [leaving, setLeaving] = useState(false);
  const leavingRef = useRef(false);
  const callbackRef = useRef(onContinue);
  const heroProgress = useRef(new Animated.Value(0)).current;
  const actionProgress = useRef(new Animated.Value(0)).current;
  const ambientProgress = useRef(new Animated.Value(0)).current;
  const exitProgress = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    callbackRef.current = onContinue;
  }, [onContinue]);

  useEffect(() => {
    const entrance = Animated.sequence([
      Animated.timing(heroProgress, {
        toValue: 1,
        duration: 760,
        useNativeDriver: true,
      }),
      Animated.timing(actionProgress, {
        toValue: 1,
        duration: 520,
        useNativeDriver: true,
      }),
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
  }, [actionProgress, ambientProgress, heroProgress]);

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

        <Animated.View style={[styles.actionLayer, { opacity: actionProgress, transform: [{ translateY: actionY }] }]}>
          {renderActions?.({ onContinue: handleContinue, leaving })}
        </Animated.View>
      </Animated.View>
    </View>
  );
}

const createStyles = (width, height) => {
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
    actionLayer: { position: "absolute", left: 0, right: 0, bottom: 0, zIndex: 30 },
  });
};
