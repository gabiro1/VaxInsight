import { Platform } from "react-native";

const lightTheme = {
  background: "#F3EEE3",
  surface: "#FFFFFF",
  surfaceSecondary: "#F9F6F0",
  elevatedSurface: "#FFFFFF",
  primaryText: "#111111",
  secondaryText: "#55514B",
  mutedText: "#89837A",
  border: "#E5DED3",
  divider: "#E5DED3",
  primaryAccent: "#D9541E",
  accentBackground: "#F8E4DA",
  primaryButtonText: "#FFFFFF",
  inverseText: "#FFFFFF",
  inputBackground: "#FFFFFF",
  inputBorder: "#E5DED3",
  success: "#2F7D5A",
  warning: "#9A6A19",
  error: "#B13A2D",
  information: "#346B9A",
  icon: "#111111",
  navigationBackground: "#FFFFFF",
  overlay: "rgba(17, 17, 17, 0.62)",
  workspaceSurface: "#111111",
  workspaceText: "#FFFFFF",
  workspaceSecondary: "rgba(255,255,255,0.74)",
  successBackground: "#E4F1EA",
  warningBackground: "#F6EDD6",
  errorBackground: "#F9E5E1",
  whiteScrim: "rgba(255, 255, 255, 0.18)",
};

const darkTheme = {
  background: "#111111",
  surface: "#1B1B1B",
  surfaceSecondary: "#202020",
  elevatedSurface: "#242424",
  primaryText: "#F3EEE3",
  secondaryText: "#B8B1A6",
  mutedText: "#89837A",
  border: "#343434",
  divider: "#343434",
  primaryAccent: "#F07845",
  accentBackground: "#382219",
  primaryButtonText: "#111111",
  inverseText: "#F3EEE3",
  inputBackground: "#1B1B1B",
  inputBorder: "#343434",
  success: "#72C49A",
  warning: "#E1B45C",
  error: "#F08A7E",
  information: "#79B4E5",
  icon: "#F3EEE3",
  navigationBackground: "#1B1B1B",
  overlay: "rgba(0, 0, 0, 0.72)",
  workspaceSurface: "#242424",
  workspaceText: "#F3EEE3",
  workspaceSecondary: "#B8B1A6",
  successBackground: "#183426",
  warningBackground: "#3A2F18",
  errorBackground: "#3A1F1C",
  whiteScrim: "rgba(255, 255, 255, 0.14)",
};

function withLegacyAliases(theme) {
  return {
    ...theme,
    cream: theme.surfaceSecondary,
    creamLight: theme.background,
    ink: theme.primaryText,
    inkSecondary: theme.secondaryText,
    white: theme.surface,
    orange: theme.primaryAccent,
    orangeLight: theme.accentBackground,
    muted: theme.mutedText,
    scrim: theme.overlay,
  };
}

export const themes = {
  light: withLegacyAliases(lightTheme),
  dark: withLegacyAliases(darkTheme),
};

export const colors = themes.light;

export const spacing = {
  xxs: 4,
  xs: 8,
  sm: 12,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  huge: 64,
};

export const radii = {
  sm: 12,
  md: 18,
  lg: 24,
  pill: 999,
};

export const typography = {
  family: {
    display: "SpaceGrotesk_700Bold",
    heading: "SpaceGrotesk_600SemiBold",
    body: "DMSans_400Regular",
    bodyMedium: "DMSans_500Medium",
    bodySemibold: "DMSans_600SemiBold",
    bodyBold: "DMSans_700Bold",
  },
  size: {
    display: 38,
    title: 28,
    section: 20,
    card: 17,
    body: 16,
    label: 14,
    supporting: 13,
    tiny: 11,
  },
  lineHeight: {
    display: 43,
    title: 34,
    section: 25,
    body: 24,
    supporting: 19,
  },
};

export function getShadows(themeColors) {
  const dark = themeColors.background === "#111111";
  return {
    card: Platform.select({
      ios: {
        shadowColor: themeColors.primaryText,
        shadowOpacity: dark ? 0.24 : 0.08,
        shadowRadius: 18,
        shadowOffset: { width: 0, height: 8 },
      },
      android: { elevation: dark ? 5 : 3 },
      default: {},
    }),
    floating: Platform.select({
      ios: {
        shadowColor: themeColors.primaryText,
        shadowOpacity: dark ? 0.34 : 0.16,
        shadowRadius: 20,
        shadowOffset: { width: 0, height: 10 },
      },
      android: { elevation: dark ? 9 : 7 },
      default: {},
    }),
  };
}

export const shadows = getShadows(themes.light);

export const motion = {
  press: 120,
  icon: 180,
  card: 210,
  screen: 300,
  entrance: 720,
};

export const layout = {
  gutter: 24,
  maxContentWidth: 520,
  touchTarget: 48,
};
