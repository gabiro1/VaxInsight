import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { getShadows, radii, spacing } from "../theme/tokens";
import { AppText } from "./AppText";

const MAIN_ROUTES = new Set([
  "Home",
  "Resources",
  "NarrativeList",
  "QuestionList",
  "ReviewQueue",
  "Admin",
  "Account",
]);

export function isMainRoute(routeName) {
  return MAIN_ROUTES.has(routeName);
}

export function BottomTabBar({ navigation, routeName }) {
  const insets = useSafeAreaInsets();
  const { t } = useLanguage();
  const { user } = useAuth();
  const { colors } = useTheme();
  const styles = createStyles(colors);

  const items = [
    { route: "Home", label: t.home, icon: "home-outline", activeIcon: "home" },
  ];

  if (user?.role === "chw") {
    items.push({ route: "NarrativeList", label: t.myNarratives, icon: "document-text-outline", activeIcon: "document-text" });
    items.push({ route: "Resources", label: t.resources, icon: "library-outline", activeIcon: "library" });
  } else {
    items.push({ route: "Resources", label: t.resources, icon: "library-outline", activeIcon: "library" });
    if (["community_member", "reviewer", "administrator"].includes(user?.role)) {
      items.push({ route: "NarrativeList", label: t.myNarratives, icon: "document-text-outline", activeIcon: "document-text" });
    }
  }

  if (user?.role === "community_member") {
    items.push({ route: "QuestionList", label: t.myQuestions, icon: "help-circle-outline", activeIcon: "help-circle" });
  }

  if (user?.role === "reviewer") {
    items.push({ route: "ReviewQueue", label: t.reviewQueue, icon: "checkmark-circle-outline", activeIcon: "checkmark-circle" });
  }

  if (user?.role === "administrator") {
    items.push({ route: "Admin", label: t.admin, icon: "settings-outline", activeIcon: "settings" });
  }

  items.push({ route: "Account", label: t.profile, icon: "person-outline", activeIcon: "person" });

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
              {active ? <AppText style={styles.itemLabel}>{item.label}</AppText> : null}
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
    minWidth: 48,
    height: 48,
    paddingHorizontal: spacing.sm,
    borderRadius: radii.pill,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.creamLight,
    borderWidth: 1,
    borderColor: "transparent",
  },
  itemLabel: { color: colors.orange, fontFamily: "DMSans_600SemiBold", fontSize: 11 },
  activeItem: {
    backgroundColor: colors.orangeLight,
    borderWidth: 1,
    borderColor: colors.orange,
    transform: [{ translateY: -2 }],
    ...getShadows(colors).card,
  },
  pressed: { opacity: 0.72, transform: [{ scale: 0.94 }] },
});
