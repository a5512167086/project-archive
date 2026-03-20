import { check, sleep } from "k6";
import { Options } from "k6/options";
import { login } from "../apis/users";
import { getBrandsData } from "../apis/brands";
import { getCategoriesData } from "../apis/categories";
import { getProductsData } from "../apis/products";
import { getServicesData } from "../apis/services";
import { CONFIG } from "../utils/config";

type SetupData = {
  token: string;
};

const API_NAME = __ENV.API_NAME;

export const options: Options = {
  scenarios: {
    find_limit: {
      executor: "ramping-vus",
      startVUs: 50,
      stages: [
        { duration: "30s", target: 100 },
        { duration: "30s", target: 150 },
        { duration: "30s", target: 200 },
        { duration: "30s", target: 200 },
      ],
      gracefulRampDown: "0s",
    },
  },
};
export function setup(): SetupData {
  const loginRes = login();

  if (loginRes.status !== 200) {
    return { token: "" };
  }

  const body = loginRes.json() as any;
  const token = body.access_token || body.token;

  return { token };
}

export default function (data: SetupData) {
  if (!data.token) return;

  const botUuid = CONFIG.BOT_UUID;
  let res;

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
    default:
      throw new Error(`Unsupported API_NAME: ${API_NAME}`);
  }

  check(res, {
    "status is 200": (r) => r.status === 200,
  });

  sleep(1);
}
