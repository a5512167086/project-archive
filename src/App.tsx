import { useEffect, useState } from "react";
import liff from "@line/liff";
import eruda from "eruda";
import { aw } from "react-router/dist/development/route-data-aSUFWnQ6";

function App() {
  const [idToken, setIdToken] = useState<string | null>(null);
  eruda.init();

  useEffect(() => {
    const log = (msg: string) => {
      const div = document.createElement("div");
      div.textContent = msg;
      document.body.appendChild(div);
    };

    const API_BASE = import.meta.env.VITE_API_BASE_URL;

    // ✅ 優先從 sessionStorage 取 bot_uuid，若沒有則從 URL 抓
    let botUUID = sessionStorage.getItem("bot_uuid");
    if (!botUUID) {
      const urlParams = new URLSearchParams(window.location.search);
      botUUID = urlParams.get("bot_uuid");

      // ✅ 若沒有直接找到，就解析 liff.state 中的 query string
      if (!botUUID) {
        const liffState = urlParams.get("liff.state"); // 可能是 "?bot_uuid=xxx"
        if (liffState) {
          const stateParams = new URLSearchParams(
            liffState.startsWith("?") ? liffState : `?${liffState}`
          );
          botUUID = stateParams.get("bot_uuid");
        }
      }

      if (botUUID) {
        sessionStorage.setItem("bot_uuid", botUUID);
      }
    }

    if (!botUUID) {
      log("❌ 缺少 bot_uuid");
      return;
    }

    // ✅ 先取 bot 資訊（取得 liff_id）
    fetch(`${API_BASE}/bots/${botUUID}`)
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) {
          console.error("❌ 錯誤回應內容:", data);
          throw new Error(data.detail || data.message || JSON.stringify(data));
        }
        return data;
      })
      .then(async (botInfo) => {
        log(`✅ 成功取得 bot 資訊，liff_id: ${botInfo.liff_id}`);

        await liff.init({ liffId: botInfo.liff_id });

        if (!liff.isLoggedIn()) {
          log("🔐 尚未登入，導向中...");
          liff.login({});
          return;
        }
        const idToken = await liff.getIDToken();
        console.log(await liff.getProfile());
        setIdToken(idToken);
        if (!idToken) {
          log("❌ 缺少 ID Token");
          return;
        }

        fetch(`${API_BASE}/users/customer-login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            line_id_token: idToken,
            bot_id: botUUID,
          }),
        })
          .then(async (res) => {
            const body = await res.json();
            if (!res.ok) {
              console.error("❌ 登入錯誤:", body);
              throw new Error(
                body.detail || body.message || JSON.stringify(body)
              );
            }
            return body;
          })
          .then((data) => {
            log("✅ 登入成功！");
            localStorage.setItem("token", data.token);
          })
          .catch((err) => {
            log(`❌ 登入失敗: ${err.message}`);
          });
      })
      .catch((err) => {
        log(`❌ 取得 bot 資訊或 LIFF 初始化失敗: ${err.message}`);
      });
  }, []);

  useEffect(() => {
    console.log(idToken);
  }, [idToken]);

  return null;
}

export default App;
