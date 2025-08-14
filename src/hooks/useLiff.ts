import { useState, useEffect } from "react";
import liff from "@line/liff";
import eruda from "eruda";
import { useGetBotInfoQuery } from "../store/api/botApi";
import { useCustomerLoginMutation } from "../store/api/userApi";

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
  isLoading: boolean;
}

export const useLiff = () => {
  const [botUUID, setBotUUID] = useState<string | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [state, setState] = useState<LiffState>({
    isInitialized: false,
    isLoggedIn: false,
    idToken: null,
    userProfile: null,
    error: null,
    isLoading: true,
  });

  // Redux hooks - 只有當 botUUID 存在時才執行查詢
  const {
    data: botInfo,
    error: botError,
    isLoading: isBotLoading,
  } = useGetBotInfoQuery(botUUID!, {
    skip: !botUUID,
  });

  const [customerLogin, { isLoading: isLoginLoading }] =
    useCustomerLoginMutation();

  // 初次載入時檢查現有的 token 和 botUUID
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // 初始化 eruda (調試工具)
        if (import.meta.env.DEV) {
          eruda.init();
        }

        const API_BASE = import.meta.env.VITE_API_BASE_URL;
        if (!API_BASE) {
          throw new Error("VITE_API_BASE_URL 環境變數未設定");
        }

        // 優先從 URL 取得 bot_uuid，沒有才從 localStorage 取得
        const urlParams = new URLSearchParams(window.location.search);
        let foundBotUUID = urlParams.get("bot_uuid");

        // 檢查 liff.state 參數
        if (!foundBotUUID) {
          const liffState = urlParams.get("liff.state");
          if (liffState) {
            const stateParams = new URLSearchParams(
              liffState.startsWith("?") ? liffState : `?${liffState}`
            );
            foundBotUUID = stateParams.get("bot_uuid");
          }
        }

        const existingBotUUID = localStorage.getItem("bot_uuid");
        const existingAccessToken = localStorage.getItem("access_token");

        // 如果 URL 中有新的 bot_uuid，且與現有的不同，需要重新登入
        if (foundBotUUID && foundBotUUID !== existingBotUUID) {
          console.log(
            `🔄 Bot UUID 已更新: ${existingBotUUID} -> ${foundBotUUID}`
          );
          // 清除舊的 tokens
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          localStorage.removeItem("token");
          localStorage.setItem("bot_uuid", foundBotUUID);
          setAccessToken(null);
        } else if (foundBotUUID) {
          // URL 中有相同的 bot_uuid，保存並清理 URL
          localStorage.setItem("bot_uuid", foundBotUUID);
        } else {
          // URL 中沒有才從 localStorage 取得
          foundBotUUID = existingBotUUID;
        }

        // 清理 URL 參數
        if (urlParams.has("bot_uuid") || urlParams.has("liff.state")) {
          const url = new URL(window.location.href);
          url.searchParams.delete("bot_uuid");
          url.searchParams.delete("liff.state");
          window.history.replaceState({}, "", url.toString());
        }

        if (!foundBotUUID) {
          throw new Error("缺少 bot_uuid 參數");
        }

        // 檢查是否有有效的 access token
        if (existingAccessToken && foundBotUUID === existingBotUUID) {
          console.log("✅ 發現現有的 access token，跳過登入流程");
          setAccessToken(existingAccessToken);
          setState((prev) => ({
            ...prev,
            isInitialized: true,
            isLoggedIn: true,
            isLoading: false,
          }));
        }

        console.log(`📱 設置 bot_uuid: ${foundBotUUID}`);
        setBotUUID(foundBotUUID);
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : String(error);
        console.log(`❌ 錯誤: ${errorMessage}`);
        setState((prev) => ({
          ...prev,
          error: errorMessage,
          isLoading: false,
        }));
      }
    };

    initializeAuth();
  }, []);

  // 當 botInfo 可用時，初始化 LIFF
  useEffect(() => {
    if (!botInfo || !botUUID) return;

    const initLiff = async () => {
      try {
        console.log(`✅ 成功取得 bot 資訊，liff_id: ${botInfo.liff_id}`);

        // 初始化 LIFF
        try {
          await liff.init({ liffId: botInfo.liff_id });
        } catch (err) {
          console.log(
            `❌ LIFF 初始化失敗: ${
              err instanceof Error ? err.message : String(err)
            }`
          );
          throw err;
        }

        if (!liff.isLoggedIn()) {
          console.log("🔐 尚未登入，導向登入頁面...");
          liff.login();
          return;
        }

        console.log("✅ 使用者已登入");

        // 取得用戶資訊
        const idToken = liff.getIDToken();
        const userProfile = await liff.getProfile();

        if (!idToken) {
          throw new Error("無法取得 ID Token");
        }

        console.log("✅ 成功取得用戶資訊", userProfile);
        console.log(`✅ 成功取得用戶資訊: ${userProfile.displayName}`);

        // 只有在沒有 access token 時才執行登入流程
        if (!accessToken) {
          // 使用 Redux mutation 登入
          const loginResult = await customerLogin({
            line_id_token: idToken,
            bot_id: botUUID,
          }).unwrap();

          console.log("✅ 後端登入成功！");

          // 儲存 access_token 和 refresh_token 到 localStorage
          localStorage.setItem("access_token", loginResult.access_token);
          localStorage.setItem("refresh_token", loginResult.refresh_token);

          // 為了向後兼容，也保存到 token 鍵
          localStorage.setItem("token", loginResult.access_token);

          console.log("💾 Token 已儲存到 localStorage", {
            access_token_length: loginResult.access_token.length,
            refresh_token_length: loginResult.refresh_token.length,
          });

          setAccessToken(loginResult.access_token);
        }

        setState({
          isInitialized: true,
          isLoggedIn: true,
          idToken,
          userProfile,
          error: null,
          isLoading: false,
        });
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : String(error);
        console.log(`❌ 錯誤: ${errorMessage}`);
        setState((prev) => ({
          ...prev,
          error: errorMessage,
          isLoading: false,
        }));
      }
    };

    initLiff();
  }, [botInfo, botUUID, customerLogin, accessToken]);

  // 處理 bot 查詢錯誤
  useEffect(() => {
    if (botError) {
      const errorMessage =
        "status" in botError
          ? `API 錯誤: ${botError.status}`
          : botError.message || "未知錯誤";
      console.log(`❌ 取得 bot 資訊失敗: ${errorMessage}`);
      setState((prev) => ({
        ...prev,
        error: errorMessage,
        isLoading: false,
      }));
    }
  }, [botError]);

  return {
    ...state,
    isLoading: state.isLoading || isBotLoading || isLoginLoading,
    botInfo,
    botUUID,
  };
};
