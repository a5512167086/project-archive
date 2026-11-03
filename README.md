# project-archive

舊作品、練習題與課堂作業集中存放。全部已停止維護。每個子專案原本是獨立 repo，已用 `git subtree` 併入，commit 歷史保留。

命名規則：全小寫 slug-case，`{project}-{type}`，type 放最後。
- `-api`：後端 API
- `-fe`：純前端
- `-app`：前後端都有
- `-mobile-{platform}`：手機 App
- `-py`：Python 腳本
- `-firmware`：嵌入式韌體

資料夾：`homework/` 課堂作業、`web/` 小型練習、`projects/` 完整作品、`projects/transuai-legacy/` 微服務版 TransuAI（一套 8 個 repo）。全部已停止維護。

## projects/

| 資料夾 | 內容 | 技術 | 原 repo |
|---|---|---|---|
| `cloud-coworker-api` | CloudCoworker 後端 | Node.js + TypeScript + Swagger | CloudCoworker_API |
| `cloud-coworker-fe` | CloudCoworker 前端 | React + TypeScript + Vite | CloudCoworker_Web |
| `order-system-api` | 點餐系統後端 | Laravel (PHP) + Docker | OrderSystem_API |
| `order-system-fe` | 點餐系統前端 | Vue | OrderSystem_Web |
| `ocr-mobile-react-native` | OCR 手機 Demo | React Native (Expo) | OCR_ReactNativeDemo |
| `todo-list-dotnet-api` | 待辦清單 API，含 JWT、EF Migration | ASP.NET Core (C#) | DotnetTodoListPractice |
| `word-web-app` | 文字分析網站 | Flask + scikit-learn | WordWeb |
| `portfolio-fe` | 2021 個人網站 | HTML/CSS/JS | Portfolio |
| `ffxiv-market-tool-fe` | FFXIV 市場板查詢工具 | Next.js 16 + TypeScript | FFXIV_MarketTool |
| `weather-station-ble-firmware` | BLE 氣象站，BME280 + BH1750 + SSD1306 | Zephyr RTOS (C), nRF52840 | WeatherStationWithBLE |
| `web3-ticketing-app` | 區塊鏈票務系統，合約 + 前端 | Hardhat (Solidity) + React (Vite) | Web3TicekingSystem |
| `othello-alphabeta-py` | 黑白棋 AI，期末競賽 | Python | OthelloAlphaBetaBot |
| `chives-beacon-app` | 大學專題：台股分析／預測，LSTM | Flask + Python | TKU-CSIE-Project/ChivesBeacon |
| `stock-tool-api` | 台股資料抓取與查詢 API | FastAPI + SQLAlchemy + Alembic | StockTool |
| `ocr-backend-api` | OCR 後端，搭配 ocr-mobile-react-native | FastAPI + Docker | OCR_BackendDemo |

## projects/transuai-legacy/

TransuAI 第一代：音訊／影片逐字稿 + AI 分析平台，微服務架構。2026-10 停止開發，由 [transuai](https://github.com/a5512167086/transuai) 單體版接手。原本在 TransuAI 組織下 8 個 repo，各自歷史保留。架構文件見 `infra/architecture-design.md`。

資料流：前端上傳 → upload-service 存檔、建 Job → MQ → transcription-service（Deepgram 轉錄、講者分離）→ MQ → ai-service（摘要、章節、embedding）→ MQ → notification-service（WebSocket 推播）。對外只有 gateway 提供 REST，服務間走 gRPC。

| 資料夾 | 內容 | 技術 |
|---|---|---|
| `infra` | docker-compose、k8s manifests、proto 定義、架構文件 | Kubernetes, Docker, gRPC proto |
| `gateway` | 唯一對外 REST API，JWT 驗證 | Spring Boot (Java) |
| `auth-service` | 註冊／登入、簽發 JWT | Spring Boot (Java), gRPC |
| `upload-service` | presigned URL 上傳、Job 狀態 | Spring Boot (Java), gRPC, MinIO |
| `transcription-service` | 抽音軌、Deepgram 轉錄、講者分離、切片 | Python, FFmpeg, RabbitMQ |
| `ai-service` | 摘要、章節、向量、會後處理 agent（Google / Notion） | Python, HF Inference, PostgreSQL |
| `notification-service` | 消費事件，WebSocket 推播 | Python, RabbitMQ |
| `frontend` | 使用者介面 | React 19 + Vite + TypeScript + Tailwind v4 + shadcn/ui |

## homework/

| 資料夾 | 內容 | 語言 |
|---|---|---|
| `tictactoe-alphabeta-py` | 井字遊戲 AI，alpha-beta / minimax | Python |
| `sudoku-py` | 數獨求解 | Python |
| `genetic-algorithm-sqrt-py` | 基因演算法求開根號 | Python |

## web/

| 資料夾 | 內容 | 技術 |
|---|---|---|
| `caesar-cipher-fe` | 凱撒密碼轉換器 | Vanilla JS |
| `guess-number-fe` | 猜數字 | Vanilla JS |
| `tic-tac-toe-fe` | 井字遊戲 | Vanilla JS |
| `todo-list-fe` | 待辦清單 | Vanilla JS |
| `pic-search-fe` | 圖片搜尋（Pexels API） | React (CRA) |
| `post-fun-app` | 貼文平台，含登入 | React + Firebase |
| `map-demo-fe` | 地圖 Demo（Leaflet） | React (CRA) |

## 執行

React 專案：

```bash
cd web/pic-search-fe
cp .env.example .env   # 填入 key
npm install && npm start
```

Python 作業：

```bash
cd homework/sudoku-py
python sudoku_puzzle.py
```
