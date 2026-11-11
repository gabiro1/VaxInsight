import * as Haptics from "expo-haptics";
import { Ionicons } from "@expo/vector-icons";
import { useEffect, useRef, useState } from "react";
import { Animated, PanResponder, StyleSheet, View } from "react-native";

import { useTheme } from "../context/ThemeContext";
import { radii, spacing, typography } from "../theme/tokens";
import { AppText } from "./AppText";

const KNOB_SIZE = 58;

export function SlideToContinue({ label, hint, onComplete }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const [trackWidth, setTrackWidth] = useState(0);
  const progress = useRef(new Animated.Value(0)).current;
  const fillProgress = useRef(new Animated.Value(0)).current;
  const trackWidthRef = useRef(0);
  const completedRef = useRef(false);
  const callbackRef = useRef(onComplete);

  useEffect(() => {
    callbackRef.current = onComplete;
  }, [onComplete]);

  const complete = () => {
    if (completedRef.current || trackWidthRef.current === 0) return;
    completedRef.current = true;
    const max = Math.max(0, trackWidthRef.current - KNOB_SIZE - spacing.xs * 2);
    Animated.parallel([
      Animated.spring(progress, {
        toValue: max,
        useNativeDriver: true,
        damping: 18,
        stiffness: 180,
        mass: 0.7,
      }),
      Animated.spring(fillProgress, {
        toValue: max,
        useNativeDriver: false,
        damping: 18,
        stiffness: 180,
        mass: 0.7,
      }),
    ]).start(() => {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
      callbackRef.current();
    });
  };

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: (_, gestureState) => Math.abs(gestureState.dx) > 4,
      onPanResponderMove: (_, gestureState) => {
        if (completedRef.current) return;
        const max = Math.max(0, trackWidthRef.current - KNOB_SIZE - spacing.xs * 2);
        const nextProgress = Math.min(max, Math.max(0, gestureState.dx));
        progress.setValue(nextProgress);
        fillProgress.setValue(nextProgress);
      },
      onPanResponderRelease: (_, gestureState) => {
        if (completedRef.current) return;
        const max = Math.max(0, trackWidthRef.current - KNOB_SIZE - spacing.xs * 2);
        const current = Math.min(max, Math.max(0, gestureState.dx));
        if (current >= max * 0.72) {
          complete();
        } else {
          Animated.parallel([
            Animated.spring(progress, {
              toValue: 0,
              useNativeDriver: true,
              damping: 18,
              stiffness: 220,
              mass: 0.7,
            }),
            Animated.spring(fillProgress, {
              toValue: 0,
              useNativeDriver: false,
              damping: 18,
              stiffness: 220,
              mass: 0.7,
            }),
          ]).start();
        }
      },
    }),
  ).current;

  const onTrackLayout = (event) => {
    const width = event.nativeEvent.layout.width;
    trackWidthRef.current = width;
    setTrackWidth(width);
  };

  const max = Math.max(0, trackWidth - KNOB_SIZE - spacing.xs * 2);
  const fillWidth = fillProgress.interpolate({
    inputRange: [0, Math.max(1, max)],
    outputRange: [0, Math.max(1, max + KNOB_SIZE)],
    extrapolate: "clamp",
  });

  return (
    <View>
      <View
        accessibilityLabel={hint}
        onLayout={onTrackLayout}
        style={styles.track}
        {...panResponder.panHandlers}
      >
        <Animated.View style={[styles.fill, { width: fillWidth }]} />
        <AppText style={styles.trackLabel}>{label}</AppText>
        <Animated.View
          style={[styles.knob, { transform: [{ translateX: progress }] }]}
          {...panResponder.panHandlers}
        >
          <Ionicons color={colors.white} name="arrow-forward" size={22} />
        </Animated.View>
      </View>
    </View>
  );
}

const createStyles = (colors) => StyleSheet.create({
  track: {
    minHeight: 72,
    borderRadius: radii.pill,
    backgroundColor: colors.overlay,
    justifyContent: "center",
    overflow: "hidden",
    paddingHorizontal: spacing.xs,
  },
  fill: {
    position: "absolute",
    left: 0,
    top: 0,
    bottom: 0,
    backgroundColor: colors.accentBackground,
  },
  trackLabel: {
    color: colors.white,
    fontFamily: typography.family.bodySemibold,
    fontSize: 14,
    textAlign: "center",
    letterSpacing: 0.1,
  },
  knob: {
    position: "absolute",
    left: spacing.xs,
    top: 7,
    width: KNOB_SIZE,
    height: KNOB_SIZE,
    borderRadius: KNOB_SIZE / 2,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.orange,
  },
});
