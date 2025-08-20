import { useEffect, useRef, useState, useCallback } from "react";
import liff from "@line/liff";
import eruda from "eruda";
import { useGetBotInfoQuery } from "../store/apis/botApi";
import {
  useCustomerLoginMutation,
  useRefreshTokenMutation,
} from "../store/apis/userApi";

interface LiffState {
  isInitialized: boolean;
  isLoggedIn: boolean;
  idToken: string | null;
  userProfile: {
    userId: string;
    displayName: string;
    pictureUrl?: string;
    statusMessage?: string;
  } | null;
  error: string | null;
  isLoading: boolean; // 僅代表「初始化/登入交換階段」
}

// 🔥 全局標記，防止多個組件實例重複初始化
let globalLiffInitialized = false;
let globalUserData: {
  idToken: string | null;
  userProfile: { displayName: string; pictureUrl: string; userId: string };
} | null = null;

function extractBotUUIDFromURL(): string | null {
  const urlParams = new URLSearchParams(window.location.search);
  let found = urlParams.get("bot_uuid");

  if (!found) {
    const liffState = urlParams.get("liff.state");
    if (liffState) {
      const stateParams = new URLSearchParams(
        liffState.startsWith("?") ? liffState : `?${liffState}`
      );
      found = stateParams.get("bot_uuid");
    }
  }
  return found;
}

function buildRedirectUriWithBotUUID(botUUID: string) {
  const url = new URL(window.location.href);
  url.searchParams.set("bot_uuid", botUUID); // 重導回來仍帶著
  return url.toString();
}

function clearURLParams() {
  const url = new URL(window.location.href);
  url.searchParams.delete("bot_uuid");
  url.searchParams.delete("liff.state");
  window.history.replaceState({}, "", url.toString());
}

// 檢查 token 是否有效的輔助函數
function isTokenValid(token: string | null): boolean {
  if (!token) return false;

  try {
    // 簡單的 JWT 過期檢查
    const payload = JSON.parse(atob(token.split(".")[1]));
    const now = Math.floor(Date.now() / 1000);
    // 提前 5 分鐘認為過期，避免邊界情況
    return payload.exp > now + 300;
  } catch {
    return false;
  }
}

// 檢查 refresh token 是否有效
function isRefreshTokenValid(refreshToken: string | null): boolean {
  if (!refreshToken) return false;

  try {
    const payload = JSON.parse(atob(refreshToken.split(".")[1]));
    const now = Math.floor(Date.now() / 1000);
    return payload.exp > now;
  } catch {
    return false;
  }
}

export const useLiff = () => {
  const [botUUID, setBotUUID] = useState<string | null>(null);
  const [state, setState] = useState<LiffState>({
    isInitialized: false,
    isLoggedIn: false,
    idToken: null,
    userProfile: null,
    error: null,
    isLoading: true,
  });

  // ⚠️ 用 useRef 避免 StrictMode 的雙呼叫，不用 module-level 變數
  const didInitRef = useRef(false);

  // 只有當 botUUID 存在時才取 bot info
  const {
    data: botInfo,
    error: botError,
    isLoading: isBotLoading,
  } = useGetBotInfoQuery(botUUID!, { skip: !botUUID });

  const [customerLogin, { isLoading: isLoginLoading }] =
    useCustomerLoginMutation();

  // 啟用 refresh token API
  const [refreshTokenMutation, { isLoading: isRefreshLoading }] =
    useRefreshTokenMutation();

  // Step 1: 啟動時解析/保存 bot_uuid（不要急著清 URL）
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        eruda.init();

        let foundBotUUID = extractBotUUIDFromURL();
        const existingBotUUID = localStorage.getItem("bot_uuid");

        if (!foundBotUUID) {
          foundBotUUID = existingBotUUID || null;
        }
        if (!foundBotUUID) throw new Error("缺少 bot_uuid 參數");

        // 若新 bot_uuid 與現存不同：清 token、覆寫
        if (foundBotUUID !== existingBotUUID) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          localStorage.removeItem("id_token");
          localStorage.removeItem("user_profile");
          localStorage.setItem("bot_uuid", foundBotUUID);
          // 清除全局狀態
          globalLiffInitialized = false;
          globalUserData = null;
        }

        setBotUUID(foundBotUUID);
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : String(error);
        console.log("❌ 初始化失敗:", errorMessage);
        setState((prev) => ({
          ...prev,
          error: errorMessage,
          isLoading: false,
        }));
      }
    };

    initializeAuth();
  }, []);

  // 🔥 使用 useCallback 穩定函數引用
  const attemptTokenRefresh = useCallback(
    async (refreshToken: string) => {
      try {
        console.log("🔄 Attempting to refresh token...");
        const refreshResult = await refreshTokenMutation({
          refresh_token: refreshToken,
        }).unwrap();

        localStorage.setItem("access_token", refreshResult.access_token);
        if (refreshResult.refresh_token) {
          localStorage.setItem("refresh_token", refreshResult.refresh_token);
        }

        console.log("✅ Token refreshed successfully");
        return refreshResult.access_token;
      } catch (error) {
        console.log("❌ Token refresh failed:", error);
        // Clear invalid tokens
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        // 清除全局狀態
        globalLiffInitialized = false;
        globalUserData = null;
        return null;
      }
    },
    [refreshTokenMutation]
  );

  // Step 2: botInfo 到位後，初始化 LIFF 並處理登入/換 token
  useEffect(() => {
    console.log("🔄 Effect triggered:", {
      hasBotInfo: !!botInfo,
      botUUID,
      didInit: didInitRef.current,
      globalInitialized: globalLiffInitialized,
      timestamp: Date.now(),
      liffId: botInfo?.liff_id,
    });

    if (!botInfo || !botUUID) return;

    // 🔥 檢查全局狀態和本地狀態
    if (didInitRef.current || globalLiffInitialized) {
      console.log("⏭️ Skipped: already initialized");

      // 如果全局已初始化但本地狀態未更新，從 localStorage 恢復
      if (globalLiffInitialized && !state.isInitialized) {
        const existingToken = localStorage.getItem("access_token");
        const existingBotUUID = localStorage.getItem("bot_uuid");

        if (
          existingToken &&
          existingBotUUID === botUUID &&
          isTokenValid(existingToken)
        ) {
          const storedIdToken = localStorage.getItem("id_token");
          const storedUserProfile = localStorage.getItem("user_profile");

          let userProfile = null;
          try {
            userProfile = storedUserProfile
              ? JSON.parse(storedUserProfile)
              : null;
          } catch (error) {
            console.warn("Failed to parse stored user profile:", error);
          }

          setState({
            isInitialized: true,
            isLoggedIn: true,
            idToken: storedIdToken,
            userProfile: userProfile || globalUserData?.userProfile,
            error: null,
            isLoading: false,
          });

          console.log("✅ Restored state from localStorage");
        }
      }

      return;
    }

    // 🔥 新增：檢查是否已經有有效的 access_token
    const existingToken = localStorage.getItem("access_token");
    if (existingToken) {
      try {
        const payload = JSON.parse(atob(existingToken.split(".")[1]));
        const exp = new Date(payload.exp * 1000);
        const now = new Date();
        console.log("Token expires at:", exp);
        console.log("Current time:", now);
        console.log("Time until expiry:", exp.getTime() - now.getTime(), "ms");
      } catch {
        console.log("Failed to parse token");
      }
    }
    const existingBotUUID = localStorage.getItem("bot_uuid");
    const existingRefreshToken = localStorage.getItem("refresh_token");

    console.log("🔍 Token check:", {
      hasToken: !!existingToken,
      tokenValid: isTokenValid(existingToken),
      botMatches: existingBotUUID === botUUID,
      hasRefreshToken: !!existingRefreshToken,
      refreshTokenValid: isRefreshTokenValid(existingRefreshToken),
    });

    if (
      existingToken &&
      existingBotUUID === botUUID &&
      isTokenValid(existingToken)
    ) {
      // 有有效 token，但仍需初始化 LIFF 來獲取用戶資訊
      console.log("✅ Has valid token, initializing LIFF to get user profile");
      didInitRef.current = true;
      globalLiffInitialized = true;

      const initLiffForProfile = async () => {
        try {
          await liff.init({
            liffId: botInfo.liff_id,
            withLoginOnExternalBrowser: false,
          });
          await liff.ready;

          if (liff.isLoggedIn()) {
            // 已登入，直接獲取用戶資訊
            const idToken = liff.getIDToken();
            const userProfile = await liff.getProfile();

            // 更新全局快取
            globalUserData = {
              idToken,
              userProfile: {
                displayName: userProfile.displayName,
                userId: userProfile.userId,
                pictureUrl: userProfile.pictureUrl ?? "",
              },
            };

            setState((prev) => ({
              ...prev,
              isInitialized: true,
              isLoggedIn: true,
              idToken,
              userProfile,
              isLoading: false,
              error: null,
            }));

            console.log("✅ Got user profile from LIFF without re-login");
          } else {
            // LIFF 顯示未登入，但我們有 token，可能 LIFF session 過期
            console.log("⚠️ LIFF session expired, but we have valid token");

            // 從 localStorage 恢復用戶資訊
            const storedIdToken = localStorage.getItem("id_token");
            const storedUserProfile = localStorage.getItem("user_profile");

            let userProfile = null;
            try {
              userProfile = storedUserProfile
                ? JSON.parse(storedUserProfile)
                : null;
            } catch (error) {
              console.warn("Failed to parse stored user profile:", error);
            }

            // 更新全局快取
            globalUserData = { idToken: storedIdToken, userProfile };

            setState((prev) => ({
              ...prev,
              isInitialized: true,
              isLoggedIn: true,
              idToken: storedIdToken,
              userProfile,
              isLoading: false,
              error: null,
            }));
          }

          clearURLParams();
        } catch (error) {
          console.error("Failed to initialize LIFF for profile:", error);
          // 降級處理：使用存儲的用戶資訊
          const storedIdToken = localStorage.getItem("id_token");
          const storedUserProfile = localStorage.getItem("user_profile");

          let userProfile = null;
          try {
            userProfile = storedUserProfile
              ? JSON.parse(storedUserProfile)
              : null;
          } catch (error) {
            console.warn("Failed to parse stored user profile:", error);
          }

          // 更新全局快取
          globalUserData = { idToken: storedIdToken, userProfile };

          setState((prev) => ({
            ...prev,
            isInitialized: true,
            isLoggedIn: true,
            idToken: storedIdToken,
            userProfile,
            isLoading: false,
            error: null,
          }));

          clearURLParams();
        }
      };

      void initLiffForProfile();
      return;
    }

    // If token is invalid but has valid refresh token, attempt to refresh
    if (
      !isTokenValid(existingToken) &&
      existingRefreshToken &&
      existingBotUUID === botUUID &&
      isRefreshTokenValid(existingRefreshToken)
    ) {
      console.log(
        "🔄 Token expired but has valid refresh token, attempting refresh"
      );
      didInitRef.current = true;
      globalLiffInitialized = true;

      const handleTokenRefresh = async () => {
        const newAccessToken = await attemptTokenRefresh(existingRefreshToken);

        if (newAccessToken) {
          // Token refresh successful, restore user session
          const storedIdToken = localStorage.getItem("id_token");
          const storedUserProfile = localStorage.getItem("user_profile");

          let userProfile = null;
          try {
            userProfile = storedUserProfile
              ? JSON.parse(storedUserProfile)
              : null;
          } catch (error) {
            console.warn("Failed to parse stored user profile:", error);
          }

          // 更新全局快取
          globalUserData = { idToken: storedIdToken, userProfile };

          setState((prev) => ({
            ...prev,
            isInitialized: true,
            isLoggedIn: true,
            idToken: storedIdToken,
            userProfile,
            isLoading: false,
            error: null,
          }));

          clearURLParams();
          return;
        } else {
          // Refresh failed, fall back to LIFF login flow
          console.log("🔄 Token refresh failed, falling back to LIFF login");
          didInitRef.current = false;
          globalLiffInitialized = false;
        }
      };

      void handleTokenRefresh();
      return;
    }

    console.log("🚀 Starting LIFF initialization...");
    didInitRef.current = true;
    globalLiffInitialized = true;

    const initLiff = async () => {
      const loginGuardKey = "liff_login_in_progress";
      try {
        // 建議把自動跳外部關掉，由你自己控制 login 時機
        await liff.init({
          liffId: botInfo.liff_id,
          withLoginOnExternalBrowser: false,
        });
        await liff.ready;

        // Debug
        console.table({
          place: "after liff.ready",
          inClient: liff.isInClient(),
          liffLoggedIn: liff.isLoggedIn(),
          hasIdToken: !!liff.getIDToken(),
          hasAppAT: !!localStorage.getItem("access_token"),
          botUUID,
        });

        // 未登入 → 觸發一次 login 並結束這次初始化（等待重導）
        if (!liff.isLoggedIn()) {
          if (!sessionStorage.getItem(loginGuardKey)) {
            sessionStorage.setItem(loginGuardKey, "1");
            const redirectUri = buildRedirectUriWithBotUUID(botUUID);
            console.log("🔐 Redirecting to LINE login...");
            liff.login({ redirectUri });
          }
          return;
        }

        // 已登入：用 idToken 換取系統 access/refresh token
        const idToken = liff.getIDToken();
        if (!idToken) throw new Error("無法取得 ID Token");

        console.log("🔄 Exchanging ID token for access token...");
        const userProfile = await liff.getProfile();
        const loginResult = await customerLogin({
          line_id_token: idToken,
          bot_id: botUUID,
        }).unwrap();

        localStorage.setItem("access_token", loginResult.access_token);
        localStorage.setItem("refresh_token", loginResult.refresh_token);

        // 🔥 新增：存儲用戶資訊到 localStorage
        localStorage.setItem("id_token", idToken);
        localStorage.setItem("user_profile", JSON.stringify(userProfile));

        // 更新全局快取
        globalUserData = {
          idToken,
          userProfile: {
            displayName: userProfile.displayName,
            userId: userProfile.userId,
            pictureUrl: userProfile.pictureUrl ?? "",
          },
        };

        setState({
          isInitialized: true,
          isLoggedIn: true,
          idToken,
          userProfile,
          error: null,
          isLoading: false, // ✅ 初始化完成
        });

        // 成功後再清 URL 與 guard
        clearURLParams();
        sessionStorage.removeItem(loginGuardKey);

        console.table({
          place: "after customerLogin",
          liffLoggedIn: liff.isLoggedIn(),
          hasIdToken: !!liff.getIDToken(),
          hasAppAT: !!localStorage.getItem("access_token"),
        });

        console.log("✅ LIFF initialization completed successfully");
      } catch (error) {
        sessionStorage.removeItem("liff_login_in_progress");
        didInitRef.current = false; // 失敗允許重試
        globalLiffInitialized = false;
        const errorMessage =
          error instanceof Error ? error.message : String(error);
        console.log("❌ initLiff error:", errorMessage);
        setState((prev) => ({
          ...prev,
          error: errorMessage,
          isLoading: false, // 結束初始化階段，交給 UI 顯示錯誤
        }));
      }
    };

    void initLiff();
  }, [botInfo?.liff_id, botUUID, attemptTokenRefresh]); // 移除會變化的依賴項

  // Step 3: bot 查詢錯誤處理
  useEffect(() => {
    if (botError) {
      const errorMessage =
        "status" in botError ? `API 錯誤: ${botError.status}` : "未知錯誤";
      console.log("❌ 取得 bot 資訊失敗:", errorMessage);
      setState((prev) => ({
        ...prev,
        error: errorMessage,
        isLoading: false,
      }));
    }
  }, [botError]);

  return {
    ...state,
    botInfo,
    botUUID,
    botLoading: isBotLoading,
    loginLoading: isLoginLoading,
    refreshLoading: isRefreshLoading,
  };
};
