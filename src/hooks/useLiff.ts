import { useEffect, useRef, useState } from "react";
import liff from "@line/liff";
import eruda from "eruda";
import { useGetBotInfoQuery } from "../store/apis/botApi";
import { useCustomerLoginMutation } from "../store/apis/userApi";

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

function getCleanRedirectUri() {
  // 只保留 pathname，避免殘留 liff.state/bot_uuid 再次觸發流程
  return `${window.location.origin}${window.location.pathname}`;
}

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

function clearURLParams() {
  const url = new URL(window.location.href);
  url.searchParams.delete("bot_uuid");
  url.searchParams.delete("liff.state");
  window.history.replaceState({}, "", url.toString());
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

  // 防止 DEV/StrictMode 重複初始化 LIFF
  const didInitRef = useRef(false);

  // 初次載入：處理 eruda、API_BASE、bot_uuid、既有 token
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        if (import.meta.env.DEV) {
          // 僅 DEV 啟用 eruda
          eruda.init();
        }

        const API_BASE = import.meta.env.VITE_API_BASE_URL;
        if (!API_BASE) {
          throw new Error("VITE_API_BASE_URL 環境變數未設定");
        }

        // 1) 取得 bot_uuid（URL > liff.state > localStorage）
        let foundBotUUID = extractBotUUIDFromURL();
        const existingBotUUID = localStorage.getItem("bot_uuid");
        const existingAccessToken = localStorage.getItem("access_token");

        // 2) 如 URL 帶來的新 bot_uuid 不同於現存，需重設 tokens
        if (foundBotUUID && foundBotUUID !== existingBotUUID) {
          console.log(
            `🔄 Bot UUID 已更新: ${existingBotUUID} -> ${foundBotUUID}`
          );
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          localStorage.setItem("bot_uuid", foundBotUUID);
          setAccessToken(null);
        } else if (foundBotUUID) {
          // URL 與現存一致 -> 同步到 localStorage
          localStorage.setItem("bot_uuid", foundBotUUID);
        } else {
          // URL 沒帶 -> 用 localStorage
          foundBotUUID = existingBotUUID;
        }

        // 3) 清除 URL 參數（避免回來又被判定需要重跑）
        clearURLParams();

        if (!foundBotUUID) {
          throw new Error("缺少 bot_uuid 參數");
        }

        // 4) 若已有本地 access_token 且 bot_uuid 未變，先標記登入完成，跳過之後的 LIFF 登入
        if (existingAccessToken && foundBotUUID === existingBotUUID) {
          console.log("✅ 發現現有的 access token，跳過 LIFF 登入流程");
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

  // 當 botInfo 到位後初始化 LIFF（只跑一次）
  useEffect(() => {
    if (!botInfo || !botUUID) return;
    if (didInitRef.current) return;
    didInitRef.current = true;

    const initLiff = async () => {
      try {
        console.log(`✅ 成功取得 bot 資訊，liff_id: ${botInfo.liff_id}`);

        // 1) 初始化 LIFF（外部瀏覽器可自動導向 LINE 登入）
        await liff.init({
          liffId: botInfo.liff_id,
          withLoginOnExternalBrowser: true,
        });

        // 2) 若本地已經有 access_token，直接視為已登入完成
        const storedAccessToken = localStorage.getItem("access_token");
        if (storedAccessToken) {
          console.log("✅ 已有 access_token，跳過 LIFF login 及後端換 token");
          setAccessToken(storedAccessToken);

          // 嘗試補齊基本的 LIFF 狀態（若在 LINE 內部已登入）
          try {
            await liff.ready;
            if (liff.isLoggedIn()) {
              const profile = await liff.getProfile();
              setState((prev) => ({
                ...prev,
                isInitialized: true,
                isLoggedIn: true,
                idToken: liff.getIDToken(),
                userProfile: profile,
                isLoading: false,
              }));
              return;
            }
          } catch {
            // ignore：非 LINE 內登入或取不到 profile 不阻擋
          }

          // 若取不到 LIFF profile，也至少標記登入完成
          setState((prev) => ({
            ...prev,
            isInitialized: true,
            isLoggedIn: true,
            isLoading: false,
          }));
          return;
        }

        // 3) 尚無本地 access_token：等 LIFF 就緒再判斷登入狀態
        await liff.ready;

        if (!liff.isLoggedIn()) {
          console.log("🔐 尚未登入，導向 LIFF 登入頁面...");
          liff.login({ redirectUri: getCleanRedirectUri() });
          return;
        }

        // 4) 已登入 LIFF：取得 idToken 與 profile，向後端換取 access/refresh token
        const idToken = liff.getIDToken();
        if (!idToken) throw new Error("無法取得 ID Token");
        const userProfile = await liff.getProfile();

        const loginResult = await customerLogin({
          line_id_token: idToken,
          bot_id: botUUID,
        }).unwrap();

        localStorage.setItem("access_token", loginResult.access_token);
        localStorage.setItem("refresh_token", loginResult.refresh_token);
        setAccessToken(loginResult.access_token);

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

    void initLiff();
    // 只依賴 botInfo/botUUID（與 customerLogin），不要把 accessToken 放進來避免重跑
  }, [botInfo, botUUID, customerLogin, accessToken]);

  // 處理 bot 查詢錯誤
  useEffect(() => {
    if (botError) {
      const errorMessage =
        "status" in botError ? `API 錯誤: ${botError.status}` : "未知錯誤";
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
