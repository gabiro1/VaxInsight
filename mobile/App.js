import { useFonts } from "expo-font";
import { View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";

import {
  DMSans_400Regular,
  DMSans_500Medium,
  DMSans_600SemiBold,
  DMSans_700Bold,
} from "@expo-google-fonts/dm-sans";
import {
  SpaceGrotesk_600SemiBold,
  SpaceGrotesk_700Bold,
} from "@expo-google-fonts/space-grotesk";

import { AuthProvider } from "./src/context/AuthContext";
import { LanguageProvider } from "./src/context/LanguageContext";
import { ThemeProvider } from "./src/context/ThemeContext";
import { RootNavigator } from "./src/navigation/RootNavigator";
import { colors } from "./src/theme/tokens";

export default function App() {
  const [fontsLoaded] = useFonts({
    DMSans_400Regular,
    DMSans_500Medium,
    DMSans_600SemiBold,
    DMSans_700Bold,
    SpaceGrotesk_600SemiBold,
    SpaceGrotesk_700Bold,
  });

  if (!fontsLoaded) {
    return <View style={{ flex: 1, backgroundColor: colors.creamLight }} />;
  }

  return (
    <SafeAreaProvider>
      <LanguageProvider>
      <ThemeProvider>
        <AuthProvider>
          <RootNavigator />
        </AuthProvider>
      </ThemeProvider>
      </LanguageProvider>
    </SafeAreaProvider>
  );
}
