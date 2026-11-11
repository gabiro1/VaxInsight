import * as SecureStore from "expo-secure-store";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { api } from "../api/client";

const ACCESS_TOKEN_KEY = "vaxinsight.access_token";
const REFRESH_TOKEN_KEY = "vaxinsight.refresh_token";

const AuthContext = createContext(null);

async function clearStoredTokens() {
  await Promise.all([
    SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY),
    SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY),
  ]);
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [ready, setReady] = useState(false);
  const [sessionExpired, setSessionExpired] = useState(false);
  const sessionRef = useRef(null);
  const refreshPromiseRef = useRef(null);
  const sessionVersionRef = useRef(0);

  const setActiveSession = useCallback((nextSession) => {
    sessionVersionRef.current += 1;
    sessionRef.current = nextSession;
    setSession(nextSession);
  }, []);

  const storeTokens = useCallback(async (tokens) => {
    await Promise.all([
      SecureStore.setItemAsync(ACCESS_TOKEN_KEY, tokens.access_token),
      tokens.refresh_token
        ? SecureStore.setItemAsync(REFRESH_TOKEN_KEY, tokens.refresh_token)
        : Promise.resolve(),
    ]);
  }, []);

  const loadProfile = useCallback(async (accessToken, refreshToken) => {
    try {
      const user = await api.getMe(accessToken);
      return { accessToken, refreshToken, user };
    } catch (error) {
      if (error.status !== 401 || !refreshToken) throw error;
      const refreshed = await api.refresh(refreshToken);
      await storeTokens(refreshed);
      const user = await api.getMe(refreshed.access_token);
      return {
        accessToken: refreshed.access_token,
        refreshToken: refreshed.refresh_token || refreshToken,
        user,
      };
    }
  }, [storeTokens]);

  const establishSession = useCallback(
    async (tokens) => {
      await storeTokens(tokens);
      try {
        const user = await api.getMe(tokens.access_token);
        setActiveSession({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          user,
        });
        setSessionExpired(false);
      } catch (error) {
        await clearStoredTokens();
        setActiveSession(null);
        throw error;
      }
    },
    [setActiveSession, storeTokens],
  );

  useEffect(() => {
    let active = true;

    Promise.all([
      SecureStore.getItemAsync(ACCESS_TOKEN_KEY),
      SecureStore.getItemAsync(REFRESH_TOKEN_KEY),
    ])
      .then(async ([accessToken, refreshToken]) => {
        if (!accessToken) return;
        try {
          const nextSession = await loadProfile(accessToken, refreshToken);
          if (active) setActiveSession(nextSession);
        } catch {
          await clearStoredTokens();
        }
      })
      .finally(() => {
        if (active) setReady(true);
      });

    return () => {
      active = false;
    };
  }, [loadProfile, setActiveSession]);

  const signIn = useCallback(
    async (credentials) => {
      const tokens = await api.login(credentials);
      await establishSession(tokens);
    },
    [establishSession],
  );

  const register = useCallback((details) => api.register(details), []);

  const verifyEmail = useCallback(
    async (details) => {
      const tokens = await api.verifyEmail(details);
      await establishSession(tokens);
    },
    [establishSession],
  );

  const refreshSession = useCallback(async () => {
    const currentSession = sessionRef.current;
    if (!currentSession?.refreshToken) throw new Error("No refresh token");
    const sessionVersion = sessionVersionRef.current;

    if (!refreshPromiseRef.current) {
      refreshPromiseRef.current = (async () => {
        const tokens = await api.refresh(currentSession.refreshToken);
        if (sessionVersion !== sessionVersionRef.current || !sessionRef.current) {
          throw new Error("Session changed while refreshing");
        }
        await storeTokens(tokens);
        if (sessionVersion !== sessionVersionRef.current || !sessionRef.current) {
          if (!sessionRef.current) await clearStoredTokens();
          throw new Error("Session changed while refreshing");
        }
        const nextSession = {
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token || currentSession.refreshToken,
          user: currentSession.user,
        };
        setActiveSession(nextSession);
        setSessionExpired(false);
        return nextSession.accessToken;
      })().finally(() => {
        refreshPromiseRef.current = null;
      });
    }

    return refreshPromiseRef.current;
  }, [setActiveSession, storeTokens]);

  const authenticatedRequest = useCallback(
    async (operation) => {
      const currentSession = sessionRef.current;
      if (!currentSession?.accessToken) throw new Error("No active session");

      try {
        return await operation(currentSession.accessToken);
      } catch (error) {
        if (error.status !== 401) throw error;
        if (!currentSession.refreshToken) {
          setSessionExpired(true);
          throw error;
        }

        try {
          const accessToken = await refreshSession();
          try {
            return await operation(accessToken);
          } catch (retryError) {
            if (retryError.status === 401) setSessionExpired(true);
            throw retryError;
          }
        } catch (refreshError) {
          if (refreshError.status === 401) setSessionExpired(true);
          throw refreshError;
        }
      }
    },
    [refreshSession],
  );

  const acceptInvitation = useCallback(
    async (details) => {
      const tokens = await api.acceptInvitation(details);
      await establishSession(tokens);
    },
    [establishSession],
  );

  const refreshProfile = useCallback(async () => {
    if (!sessionRef.current?.accessToken) return;
    const user = await authenticatedRequest((token) => api.getMe(token));
    const currentSession = sessionRef.current;
    if (currentSession) setActiveSession({ ...currentSession, user });
    return user;
  }, [authenticatedRequest, setActiveSession]);

  const changePassword = useCallback(
    async (details) => {
      const result = await authenticatedRequest((token) =>
        api.changePassword(token, details),
      );
      await clearStoredTokens();
      setActiveSession(null);
      setSessionExpired(false);
      return result;
    },
    [authenticatedRequest, setActiveSession],
  );

  const updateProfile = useCallback(
    async (details) => {
      const currentSession = sessionRef.current;
      const currentEmail = currentSession?.user?.email?.trim().toLowerCase();
      const nextEmail = details.email?.trim().toLowerCase();
      const user = await authenticatedRequest((token) =>
        api.updateProfile(token, details),
      );

      if (nextEmail && nextEmail !== currentEmail) {
        await clearStoredTokens();
        setActiveSession(null);
        setSessionExpired(false);
      } else if (currentSession) {
        setActiveSession({ ...currentSession, user });
      }

      return user;
    },
    [authenticatedRequest, setActiveSession],
  );

  const deleteAccount = useCallback(
    async () => {
      const result = await authenticatedRequest((token) => api.deleteAccount(token));
      await clearStoredTokens();
      setActiveSession(null);
      setSessionExpired(false);
      return result;
    },
    [authenticatedRequest, setActiveSession],
  );

  const signOut = useCallback(async () => {
    const currentSession = sessionRef.current;
    if (currentSession?.refreshToken && currentSession?.accessToken) {
      try {
        await api.logout(currentSession.refreshToken, currentSession.accessToken);
      } catch {
        // Local sign-out must still complete if the server session has expired.
      }
    }
    await clearStoredTokens();
    setActiveSession(null);
    setSessionExpired(false);
  }, [setActiveSession]);

  const value = useMemo(
    () => ({
      session,
      user: session?.user || null,
      isAdministrator: session?.user?.role === "administrator",
      ready,
      sessionExpired,
      authenticatedRequest,
      signIn,
      register,
      verifyEmail,
      acceptInvitation,
      refreshProfile,
      changePassword,
      updateProfile,
      deleteAccount,
      signOut,
    }),
    [acceptInvitation, authenticatedRequest, changePassword, deleteAccount, ready, refreshProfile, register, session, sessionExpired, signIn, signOut, updateProfile, verifyEmail],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
