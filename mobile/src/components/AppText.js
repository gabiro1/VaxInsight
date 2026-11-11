import { Text } from "react-native";

import { useTheme } from "../context/ThemeContext";
import { typography } from "../theme/tokens";

const createVariants = (colors) => ({
  display: {
    fontFamily: typography.family.display,
    fontSize: typography.size.display,
    lineHeight: typography.lineHeight.display,
    color: colors.inverseText,
  },
  title: {
    fontFamily: typography.family.display,
    fontSize: typography.size.title,
    lineHeight: typography.lineHeight.title,
    color: colors.ink,
  },
  section: {
    fontFamily: typography.family.heading,
    fontSize: typography.size.section,
    lineHeight: typography.lineHeight.section,
    color: colors.ink,
  },
  card: {
    fontFamily: typography.family.heading,
    fontSize: typography.size.card,
    lineHeight: 23,
    color: colors.ink,
  },
  body: {
    fontFamily: typography.family.body,
    fontSize: typography.size.body,
    lineHeight: typography.lineHeight.body,
    color: colors.inkSecondary,
  },
  label: {
    fontFamily: typography.family.bodySemibold,
    fontSize: typography.size.label,
    lineHeight: 19,
    color: colors.ink,
  },
  supporting: {
    fontFamily: typography.family.body,
    fontSize: typography.size.supporting,
    lineHeight: typography.lineHeight.supporting,
    color: colors.muted,
  },
});

export function AppText({ variant = "body", style, children, ...props }) {
  const { colors } = useTheme();
  const variants = createVariants(colors);
  return (
    <Text allowFontScaling style={[variants[variant], style]} {...props}>
      {children}
    </Text>
  );
}
