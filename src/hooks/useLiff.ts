import { useState, useEffect } from "react";
import liff from "@line/liff";
import eruda from "eruda";

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
  const [state, setState] = useState<LiffState>({
    isInitialized: false,
    isLoggedIn: false,
    idToken: null,
    userProfile: null,
    error: null,
    isLoading: true,
  });

  const log = (msg: string) => {
    if (import.meta.env.DEV) {
      console.log(msg);
      const div = document.createElement("div");
      div.textContent = msg;
      div.style.cssText =
        "padding:4px;border-bottom:1px solid #eee;font-size:12px;";
      document.body.appendChild(div);
    }
  };

  useEffect(() => {
    const initializeLiff = async () => {
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
        let botUUID = urlParams.get("bot_uuid");

        // 檢查 liff.state 參數
        if (!botUUID) {
          const liffState = urlParams.get("liff.state");
          if (liffState) {
            const stateParams = new URLSearchParams(
              liffState.startsWith("?") ? liffState : `?${liffState}`
            );
            botUUID = stateParams.get("bot_uuid");
          }
        }

        // 如果 URL 中有 bot_uuid，保存到 localStorage 並清理 URL
        if (botUUID) {
          localStorage.setItem("bot_uuid", botUUID);
          // 清理 URL 參數
          const url = new URL(window.location.href);
          url.searchParams.delete("bot_uuid");
          url.searchParams.delete("liff.state");
          window.history.replaceState({}, "", url.toString());
        } else {
          // URL 中沒有才從 localStorage 取得
          botUUID = localStorage.getItem("bot_uuid");
        }

        if (!botUUID) {
          throw new Error("缺少 bot_uuid 參數");
        }

        log(`📱 開始初始化 LIFF，bot_uuid: ${botUUID}`);

        // 取得 bot 資訊
        const response = await fetch(`${API_BASE}/bots/${botUUID}`);
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || data.message || JSON.stringify(data));
        }

        log(`✅ 成功取得 bot 資訊，liff_id: ${data.liff_id}`);

        // 初始化 LIFF
        try {
          await liff.init({ liffId: data.liff_id });
        } catch (err) {
          log(
            `❌ LIFF 初始化失敗: ${
              err instanceof Error ? err.message : String(err)
            }`
          );
          throw err;
        }

        if (!liff.isLoggedIn()) {
          log("🔐 尚未登入，導向登入頁面...");

          liff.login();
          return;
        }

        log("✅ 使用者已登入");

        // 取得用戶資訊
        const idToken = liff.getIDToken();
        const userProfile = await liff.getProfile();

        if (!idToken) {
          throw new Error("無法取得 ID Token");
        }

        log(`✅ 成功取得用戶資訊: ${userProfile.displayName}`);

        // 發送登入請求到後端
        const loginResponse = await fetch(`${API_BASE}/users/customer-login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            line_id_token: idToken,
            bot_id: botUUID,
          }),
        });

        const loginData = await loginResponse.json();

        if (!loginResponse.ok) {
          throw new Error(
            loginData.detail || loginData.message || JSON.stringify(loginData)
          );
        }

        log("✅ 後端登入成功！");
        localStorage.setItem("token", loginData.token);

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
        log(`❌ 錯誤: ${errorMessage}`);
        setState((prev) => ({
          ...prev,
          error: errorMessage,
          isLoading: false,
        }));
      }
    };

    initializeLiff();
  }, []);

  return state;
};
