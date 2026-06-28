import { check, sleep } from "k6";
import { Options } from "k6/options";
import exec from "k6/execution";

import { login } from "../apis/users";
import { getBrandsData } from "../apis/brands";
import { getCategoriesData } from "../apis/categories";
import { getProductsData } from "../apis/products";
import { getServicesData } from "../apis/services";
import { queryRagApi } from "../apis/rags";
import { CONFIG } from "../utils/config";

type SetupData = {
  token: string;
};

const API_NAME = __ENV.API_NAME;

// ==========================================
// 測試設定 (Options)：尋找系統極限斷點 (Capacity Testing)
// ==========================================
export const options: Options = {
  setupTimeout: "2m",
  scenarios: {
    find_breakpoint: {
      executor: "ramping-vus",
      startVUs: 1,
      // 階梯式爬升：給伺服器反應時間，精準抓出在哪個區間開始報錯
      stages: [
        { duration: "1m", target: 50 }, // 暖身區：快速回到你已知安全的 50 VUs
        { duration: "2m", target: 100 }, // 探索區：測試 50~100 的承載力
        { duration: "2m", target: 200 }, // 壓力區：測試 100~200 (這通常是許多基礎 API 的瓶頸)
        { duration: "2m", target: 300 }, // 超載區：測試 200~300
        { duration: "2m", target: 500 }, // 極限區：上探至 500 VUs
      ],
      gracefulRampDown: "30s",
    },
  },
  // ==========================================
  // 自動中斷機制 (Thresholds) - 找斷點必備
  // ==========================================
  thresholds: {
    // 當請求失敗率超過 10% 時，代表系統已經崩潰，提早中止測試 (Abort On Fail)
    // delayAbortEval: 讓系統先跑 10 秒再開始評估，避免剛啟動時的偶發錯誤觸發中止
    http_req_failed: [
      { threshold: "rate<0.1", abortOnFail: true, delayAbortEval: "10s" },
    ],
    // (選用) 當 95% 的請求都超過 10 秒才回來時，雖然沒報錯，但也等同於服務癱瘓，直接中止
    http_req_duration: [
      { threshold: "p(95)<10000", abortOnFail: true, delayAbortEval: "10s" },
    ],
  },
};

// ==========================================
// 初始化階段 (Setup)
// ==========================================
export function setup(): SetupData {
  const loginRes = login();

  if (loginRes.status !== 200) {
    return { token: "" };
  }

  const body = loginRes.json() as any;
  const token = body.access_token || body.token;

  return { token };
}

// ==========================================
// 虛擬使用者執行邏輯 (Default Function)
// ==========================================
export default function (data: SetupData) {
  if (!data.token) return;

  const botUuid = CONFIG.BOT_UUID;
  let res;

  // 根據環境變數切換測試的 API
  switch (API_NAME) {
    case "brands":
      res = getBrandsData(botUuid, data.token);
      break;
    case "categories":
      res = getCategoriesData(botUuid, data.token);
      break;
    case "products":
      res = getProductsData(botUuid, data.token);
      break;
    case "services":
      res = getServicesData(botUuid, data.token);
      break;
    case "rags":
      res = queryRagApi(botUuid, "test");
      break;
    default:
      throw new Error(`Unsupported API_NAME: ${API_NAME}`);
  }

  // ==========================================
  // 斷點檢測與紀錄
  // ==========================================
  const passed = check(res, {
    "status is 200": (r) => r.status === 200,
  });

  // 如果狀態碼不是 200 (代表 API 崩潰、Timeout 或回傳 500)
  if (!passed) {
    // 精準印出崩潰當下的壓力狀況
    console.log(
      `[系統崩潰] 併發人數: ${exec.instance.vusActive} VUs | 狀態碼: ${res.status} | 耗時: ${res.timings.duration}ms`,
    );
  }

  // 每次請求間稍微休息 1 秒，模擬真實人類操作
  sleep(1);
}
