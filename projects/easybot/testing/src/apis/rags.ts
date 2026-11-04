import http from "k6/http";
import { CONFIG } from "../utils/config";

export function queryRagApi(botUuid: string, queryText: string = "test") {
  const url = `${CONFIG.RAG_BASE_URL}/query`;

  const payload = JSON.stringify({
    bot_uuid: botUuid,
    query: queryText,
    top_k: 3,
    fetch_k: 15,
    score_threshold: 0.3,
    model: "local_model",
  });

  const params = {
    headers: {
      "Content-Type": "application/json",
    },
  };

  return http.post(url, payload, params);
}
