import http from "k6/http";
import { CONFIG } from "../utils/config";

export function getBrandsData(botUuid: string, token: string) {
  const url = `${CONFIG.BASE_URL}/brands/${botUuid}`;

  const params = {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  };

  return http.get(url, params);
}
