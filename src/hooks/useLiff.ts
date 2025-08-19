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
  // 確保重導回來仍帶著 bot_uuid（避免登入回來遺失）
  url.searchParams.set("bot_uuid", botUUID);
  return url.toString();
}

function clearURLParams() {
  const url = new URL(window.location.href);
  url.searchParams.delete("bot_uuid");
  url.searchParams.delete("liff.state");
  window.history.replaceState({}, "", url.toString());
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

  // 只有當 botUUID 存在時才取 bot info
  const {
    data: botInfo,
    error: botError,
    isLoading: isBotLoading,
  } = useGetBotInfoQuery(botUUID!, { skip: !botUUID });

  const [customerLogin, { isLoading: isLoginLoading }] =
    useCustomerLoginMutation();

  // 防併發初始化鎖
  const didInitRef = useRef(false);

  // Step 1: 啟動時先解析/保存 bot_uuid（不要急著清 URL）
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        eruda.init();

        let foundBotUUID = extractBotUUIDFromURL();
        const existingBotUUID = localStorage.getItem("bot_uuid");

        if (!foundBotUUID) {
          foundBotUUID = existingBotUUID || null;
        }

        if (!foundBotUUID) {
          throw new Error("缺少 bot_uuid 參數");
        }

        // 若帶來的新 bot_uuid 與現存不同：清 token、覆寫
        if (foundBotUUID !== existingBotUUID) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          localStorage.setItem("bot_uuid", foundBotUUID);
        }

        setBotUUID(foundBotUUID);
        // ⚠️ 不要此時清 URL，等登入與換 token 完成再清
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

  // Step 2: botInfo 到位後，初始化 LIFF 並處理登入/換 token
  useEffect(() => {
    if (!botInfo || !botUUID) return;

    // ✅ 進入 effect 立刻上鎖，避免 React 18/StrictMode 造成的雙執行/併發
    if (didInitRef.current) return;
    didInitRef.current = true;

    const initLiff = async () => {
      const loginGuardKey = "liff_login_in_progress";
      try {
        console.log(`✅ 取得 bot 資訊，liff_id: ${botInfo.liff_id}`);

        await liff.init({
          liffId: botInfo.liff_id,
          // 只在外部瀏覽器開啟自動導向，LINE App 內避免跳外部造成循環
          withLoginOnExternalBrowser: !liff.isInClient(),
        });
        await liff.ready;

        // ── Debug：初始化後先印狀態
        console.table({
          place: "after liff.ready",
          inClient: liff.isInClient(),
          liffLoggedIn: liff.isLoggedIn(),
          hasIdToken: !!liff.getIDToken(),
          hasAppAT: !!localStorage.getItem("access_token"),
          botUUID,
        });

        // 若尚未登入 LIFF → 僅觸發一次 login（避免無限循環）
        if (!liff.isLoggedIn()) {
          const inProgress = sessionStorage.getItem(loginGuardKey) === "1";
          if (!inProgress) {
            sessionStorage.setItem(loginGuardKey, "1");
            const redirectUri = buildRedirectUriWithBotUUID(botUUID);
            console.table({
              place: "before liff.login",
              redirectUri,
              inClient: liff.isInClient(),
              withLoginOnExternalBrowser: !liff.isInClient(),
            });
            liff.login({ redirectUri });
          }
          return; // 等重導回來
        }

        // 已登入 LIFF：用 idToken 換取 app access/refresh token
        const idToken = liff.getIDToken();
        if (!idToken) throw new Error("無法取得 ID Token");

        const userProfile = await liff.getProfile();

        // 呼叫你的後端，取得 access/refresh token
        const loginResult = await customerLogin({
          line_id_token: idToken,
          bot_id: botUUID,
        }).unwrap();

        localStorage.setItem("access_token", loginResult.access_token);
        localStorage.setItem("refresh_token", loginResult.refresh_token);

        setState({
          isInitialized: true,
          isLoggedIn: true,
          idToken,
          userProfile,
          error: null,
          isLoading: false,
        });

        // 成功後再清 URL，避免下次又觸發
        clearURLParams();
        sessionStorage.removeItem(loginGuardKey);

        // ── Debug：完成後印狀態
        console.table({
          place: "after customerLogin",
          liffLoggedIn: liff.isLoggedIn(),
          hasIdToken: !!liff.getIDToken(),
          hasAppAT: !!localStorage.getItem("access_token"),
        });
      } catch (error) {
        sessionStorage.removeItem(loginGuardKey);
        // 若你想允許之後「手動重試」，可以在這裡把鎖打開：
        // didInitRef.current = false;
        const errorMessage =
          error instanceof Error ? error.message : String(error);
        console.log("❌ initLiff error:", errorMessage);
        setState((prev) => ({
          ...prev,
          error: errorMessage,
          isLoading: false,
        }));
      }
    };

    void initLiff();
  }, [botInfo, botUUID]); // 🔸 刻意不把 customerLogin 放進依賴

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
    isLoading: state.isLoading || isBotLoading || isLoginLoading,
    botInfo,
    botUUID,
  };
};
