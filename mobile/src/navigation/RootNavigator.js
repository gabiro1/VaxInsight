import { NavigationContainer, DarkTheme } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { View } from "react-native";
import { StatusBar } from "expo-status-bar";

import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useTheme } from "../context/ThemeContext";
import { AuthChoiceScreen } from "../screens/AuthChoiceScreen";
import { HomeScreen } from "../screens/HomeScreen";
import { OfficialVaccineInfoScreen } from "../screens/OfficialVaccineInfoScreen";
import { ResourcesScreen } from "../screens/ResourcesScreen";
import { VaccineArticleDetailScreen } from "../screens/VaccineArticleDetailScreen";
import { LoginScreen } from "../screens/LoginScreen";
import { PasswordResetScreen } from "../screens/PasswordResetScreen";
import { PasswordResetConfirmScreen } from "../screens/PasswordResetConfirmScreen";
import { RegisterScreen } from "../screens/RegisterScreen";
import { VerifyEmailScreen } from "../screens/VerifyEmailScreen";
import { InvitationAcceptScreen } from "../screens/InvitationAcceptScreen";
import { AccountScreen } from "../screens/AccountScreen";
import { AdminAccessDeniedScreen } from "../screens/AdminAccessDeniedScreen";
import { AdminAuditScreen } from "../screens/AdminAuditScreen";
import { AdminDashboardScreen } from "../screens/AdminDashboardScreen";
import { AdminInvitationDetailScreen } from "../screens/AdminInvitationDetailScreen";
import { AdminInvitationsScreen } from "../screens/AdminInvitationsScreen";
import { AdminInviteScreen } from "../screens/AdminInviteScreen";
import { AdminPermissionsScreen } from "../screens/AdminPermissionsScreen";
import { AdminRoleDetailScreen } from "../screens/AdminRoleDetailScreen";
import { AdminRolesScreen } from "../screens/AdminRolesScreen";
import { AdminUserDetailScreen } from "../screens/AdminUserDetailScreen";
import { AdminUsersScreen } from "../screens/AdminUsersScreen";
import { AdminVaccineContentScreen } from "../screens/AdminVaccineContentScreen";
import { SessionExpiredScreen } from "../screens/SessionExpiredScreen";
import { NarrativeListScreen } from "../screens/NarrativeListScreen";
import { NarrativeComposerScreen } from "../screens/NarrativeComposerScreen";
import { NarrativeDetailScreen } from "../screens/NarrativeDetailScreen";
import { NarrativeHistoryScreen } from "../screens/NarrativeHistoryScreen";
import { ReviewQueueScreen } from "../screens/ReviewQueueScreen";
import { ReviewDetailScreen } from "../screens/ReviewDetailScreen";
import { ReviewHistoryScreen } from "../screens/ReviewHistoryScreen";
import { QuestionComposerScreen } from "../screens/QuestionComposerScreen";
import { QuestionDetailScreen } from "../screens/QuestionDetailScreen";
import { QuestionListScreen } from "../screens/QuestionListScreen";
import { QuestionReviewDetailScreen } from "../screens/QuestionReviewDetailScreen";
import { QuestionReviewQueueScreen } from "../screens/QuestionReviewQueueScreen";
import { WelcomeScreen } from "../screens/WelcomeScreen";
import { FullScreenLoader } from "../components/StateView";
import { BottomTabBar, isMainRoute } from "../components/BottomTabBar";

const Stack = createNativeStackNavigator();

function withAuthenticatedShell(ScreenComponent) {
  return function AuthenticatedShell(props) {
    const routeName = props.route?.name;
    const { user } = useAuth();
    const hideQuestionTabsForChw = user?.role === "chw" && routeName === "QuestionList";
    return (
      <View style={{ flex: 1 }}>
        <ScreenComponent {...props} />
        {isMainRoute(routeName) && !hideQuestionTabsForChw ? <BottomTabBar navigation={props.navigation} routeName={routeName} /> : null}
      </View>
    );
  };
}

const AuthenticatedHomeScreen = withAuthenticatedShell(HomeScreen);
const AuthenticatedOfficialVaccineInfoScreen = withAuthenticatedShell(
  OfficialVaccineInfoScreen,
);
const AuthenticatedAccountScreen = withAuthenticatedShell(AccountScreen);
const AuthenticatedResourcesScreen = withAuthenticatedShell(ResourcesScreen);
const AuthenticatedAdminDashboardScreen = withAuthenticatedShell(AdminDashboardScreen);
const AuthenticatedNarrativeListScreen = withAuthenticatedShell(NarrativeListScreen);
const AuthenticatedReviewQueueScreen = withAuthenticatedShell(ReviewQueueScreen);
const AuthenticatedQuestionListScreen = withAuthenticatedShell(QuestionListScreen);

const linking = {
  prefixes: ["vaxinsight://", "exp://"],
  config: {
      screens: {
        Welcome: "",
        PasswordResetConfirm: "reset-password/:token",
        InvitationAccept: "invite/:token",
      },
  },
};

function getNavigationTheme(colors) {
  return {
    ...DarkTheme,
    dark: colors.background === "#111111",
    colors: {
      ...DarkTheme.colors,
      background: colors.background,
      card: colors.navigationBackground,
      text: colors.primaryText,
      border: colors.border,
      primary: colors.primaryAccent,
    },
  };
}

function LoadingScreen() {
  const { t } = useLanguage();
  const { isDark } = useTheme();
  return (
    <>
      <StatusBar style={isDark ? "light" : "dark"} />
      <FullScreenLoader label={t.loading} />
    </>
  );
}

export function RootNavigator() {
  const { session, sessionExpired, ready } = useAuth();
  const { colors, isDark } = useTheme();

  if (!ready) return <LoadingScreen />;

  return (
    <>
      <StatusBar style={isDark ? "light" : "dark"} />
      <NavigationContainer linking={linking} theme={getNavigationTheme(colors)}>
      <Stack.Navigator
        key={sessionExpired ? "expired" : session ? "authenticated" : "guest"}
        screenOptions={{
          headerShown: false,
          animation: "slide_from_right",
          contentStyle: { backgroundColor: colors.background },
          gestureEnabled: true,
        }}
      >
        {sessionExpired ? (
          <Stack.Screen name="SessionExpired" component={SessionExpiredScreen} />
        ) : session ? (
        <>
            <Stack.Screen name="Home" component={AuthenticatedHomeScreen} />
            <Stack.Screen
              name="VaccineInfo"
              component={AuthenticatedOfficialVaccineInfoScreen}
            />
            <Stack.Screen name="VaccineArticleDetail" component={VaccineArticleDetailScreen} />
            <Stack.Screen name="Resources" component={AuthenticatedResourcesScreen} />
            <Stack.Screen name="Account" component={AuthenticatedAccountScreen} />
            <Stack.Screen name="Admin" component={AuthenticatedAdminDashboardScreen} />
            <Stack.Screen name="AdminUsers" component={AdminUsersScreen} />
            <Stack.Screen name="AdminUserDetail" component={AdminUserDetailScreen} />
            <Stack.Screen name="AdminInvite" component={AdminInviteScreen} />
            <Stack.Screen name="AdminInvitations" component={AdminInvitationsScreen} />
            <Stack.Screen name="AdminInvitationDetail" component={AdminInvitationDetailScreen} />
            <Stack.Screen name="AdminAudit" component={AdminAuditScreen} />
            <Stack.Screen name="AdminRoles" component={AdminRolesScreen} />
            <Stack.Screen name="AdminRoleDetail" component={AdminRoleDetailScreen} />
            <Stack.Screen name="AdminPermissions" component={AdminPermissionsScreen} />
            <Stack.Screen name="AdminContent" component={AdminVaccineContentScreen} />
            <Stack.Screen name="AdminAccessDenied" component={AdminAccessDeniedScreen} />
            <Stack.Screen name="NarrativeList" component={AuthenticatedNarrativeListScreen} />
            <Stack.Screen name="NarrativeComposer" component={NarrativeComposerScreen} />
            <Stack.Screen name="NarrativeDetail" component={NarrativeDetailScreen} />
            <Stack.Screen name="NarrativeHistory" component={NarrativeHistoryScreen} />
            <Stack.Screen name="ReviewQueue" component={AuthenticatedReviewQueueScreen} />
            <Stack.Screen name="ReviewDetail" component={ReviewDetailScreen} />
            <Stack.Screen name="ReviewHistory" component={ReviewHistoryScreen} />
            <Stack.Screen name="QuestionList" component={AuthenticatedQuestionListScreen} />
            <Stack.Screen
              name="QuestionComposer"
              component={QuestionComposerScreen}
            />
            <Stack.Screen name="QuestionDetail" component={QuestionDetailScreen} />
            <Stack.Screen
              name="QuestionReviewQueue"
              component={QuestionReviewQueueScreen}
            />
            <Stack.Screen
              name="QuestionReviewDetail"
              component={QuestionReviewDetailScreen}
            />
          </>
        ) : (
          <>
            <Stack.Screen name="Welcome" component={WelcomeScreen} options={{ animation: "fade" }} />
            <Stack.Screen name="AuthChoice" component={AuthChoiceScreen} />
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="Register" component={RegisterScreen} />
            <Stack.Screen name="PasswordReset" component={PasswordResetScreen} />
          </>
        )}
        <Stack.Screen name="PasswordResetConfirm" component={PasswordResetConfirmScreen} />
        <Stack.Screen name="VerifyEmail" component={VerifyEmailScreen} />
        <Stack.Screen name="InvitationAccept" component={InvitationAcceptScreen} />
      </Stack.Navigator>
      </NavigationContainer>
    </>
  );
}
