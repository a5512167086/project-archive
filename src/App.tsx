import { useEffect } from "react";
import liff from "@line/liff";
import eruda from "eruda";

function App() {
  eruda.init();

  useEffect(() => {
    const log = (msg: string) => {
      const div = document.createElement("div");
      div.textContent = msg;
      document.body.appendChild(div);
    };

    liff
      .init({ liffId: import.meta.env.VITE_LIFF_ID })
      .then(() => {
        if (!liff.isLoggedIn()) {
          log("🔐 尚未登入，導向中...");
          liff.login();
          return;
        }

        const urlParams = new URLSearchParams(window.location.search);
        const botUUID = urlParams.get("bot_uuid");
        const idToken = liff.getIDToken();

        log("✅ LIFF 初始化成功");
        log(`ID Token: ${idToken}`);
        log(`bot_uuid: ${botUUID}`);

        if (!idToken || !botUUID) {
          log("❌ 缺少 ID Token 或 bot_uuid");
          return;
        }

        const API_BASE = import.meta.env.VITE_API_BASE_URL;

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
              console.error("❌ 錯誤回應內容:", body);
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
        log(`❌ LIFF 初始化失敗: ${err.message}`);
      });
  }, []);

  return null;
}

export default App;
