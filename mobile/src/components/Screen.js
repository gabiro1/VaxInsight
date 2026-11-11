import { KeyboardAvoidingView, Platform, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useTheme } from "../context/ThemeContext";
import { layout } from "../theme/tokens";

export function Screen({ children, scroll = false, keyboard = false, style, edges }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const content = (
    <View style={[styles.content, style]}>
      {children}
    </View>
  );

  return (
    <SafeAreaView edges={edges || ["top", "bottom"]} style={styles.safeArea}>
      {keyboard ? (
        <KeyboardAvoidingView
          behavior={Platform.OS === "ios" ? "padding" : "height"}
          style={styles.flex}
        >
          {content}
        </KeyboardAvoidingView>
      ) : (
        content
      )}
    </SafeAreaView>
  );
}

export function ScreenGutter({ children, style }) {
  return <View style={[styles.gutter, style]}>{children}</View>;
}

const createStyles = (colors) => StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.creamLight,
  },
  flex: { flex: 1 },
  content: {
    flex: 1,
    width: "100%",
    maxWidth: layout.maxContentWidth,
    alignSelf: "center",
  },
  gutter: {
    paddingHorizontal: layout.gutter,
  },
});
