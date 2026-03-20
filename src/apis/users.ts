import http from "k6/http";
import { CONFIG } from "../utils/config";

export function login(email?: string, password?: string) {
  const url = `${CONFIG.BASE_URL}/users/login`;

  const payload = JSON.stringify({
    email: email || CONFIG.EMAIL,
    password: password || CONFIG.PASSWORD,
    remember: true,
  });

  const params = {
    headers: {
      "Content-Type": "application/json",
    },
  };

  return http.post(url, payload, params);
}
