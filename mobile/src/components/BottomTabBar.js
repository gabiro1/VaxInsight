import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, radii, spacing } from "../theme/tokens";

const MAIN_ROUTES = new Set([
  "Home",
  "Resources",
  "NarrativeList",
  "Account",
]);

export function isMainRoute(routeName, primaryRoute = "NarrativeList", questionRoute = null) {
  return MAIN_ROUTES.has(routeName) || routeName === primaryRoute || routeName === questionRoute;
}

export function BottomTabBar({ navigation, primaryRoute = "NarrativeList", questionRoute = null, routeName }) {
  const insets = useSafeAreaInsets();
  const { t } = useLanguage();
  const { colors } = useTheme();
  const styles = createStyles(colors);

  const primaryItem = primaryRoute === "ReviewQueue"
    ? { route: primaryRoute, label: t.assignments, icon: "clipboard-outline", activeIcon: "clipboard" }
    : { route: "NarrativeList", label: t.myNarratives, icon: "document-text-outline", activeIcon: "document-text" };
  const questionItem = questionRoute
    ? { route: questionRoute, label: t.questionsAwaitingResponse, icon: "chatbubble-ellipses-outline", activeIcon: "chatbubble-ellipses" }
    : null;
  const items = [
    { route: "Home", label: t.home, icon: "home-outline", activeIcon: "home" },
    primaryItem,
    ...(questionItem ? [questionItem] : []),
    { route: "Resources", label: t.resources, icon: "library-outline", activeIcon: "library" },
    { route: "Account", label: t.profile, icon: "person-outline", activeIcon: "person" },
  ];

  return (
    <View
      pointerEvents="box-none"
      style={[
        styles.positioner,
        { paddingBottom: Math.max(insets.bottom, spacing.sm) },
      ]}
    >
      <View accessibilityRole="tablist" style={styles.bar}>
        {items.map((item) => {
          const active = routeName === item.route;
          return (
            <Pressable
              accessibilityRole="tab"
              accessibilityLabel={item.label}
              accessibilityState={{ selected: active }}
              key={item.route}
              onPress={() => {
                if (!active) navigation.navigate(item.route);
              }}
              style={({ pressed }) => [
                styles.item,
                active && styles.activeItem,
                pressed && styles.pressed,
              ]}
            >
              <Ionicons color={active ? colors.orange : colors.muted} name={active ? item.activeIcon : item.icon} size={22} />
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const createStyles = (colors) => StyleSheet.create({
  positioner: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    alignItems: "center",
    paddingHorizontal: spacing.md,
  },
  bar: {
    minHeight: 64,
    maxWidth: "100%",
    padding: spacing.xs,
    borderRadius: radii.pill,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    ...getShadows(colors).floating,
  },
  item: {
    width: 48,
    height: 48,
    paddingHorizontal: 0,
    borderRadius: radii.pill,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.creamLight,
    borderWidth: 1,
    borderColor: "transparent",
  },
  activeItem: {
    backgroundColor: colors.orangeLight,
    borderWidth: 1,
    borderColor: colors.orange,
    transform: [{ translateY: -2 }],
    ...getShadows(colors).card,
  },
  pressed: { opacity: 0.72, transform: [{ scale: 0.94 }] },
});
