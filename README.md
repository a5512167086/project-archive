# project-archive

舊作品、練習題與課堂作業集中存放。全部已停止維護。每個子專案原本是獨立 repo，已用 `git subtree` 併入，commit 歷史保留。

命名規則：全小寫 slug-case，`{project}-{type}`，type 放最後。
- `-api`：後端 API
- `-fe`：純前端
- `-app`：前後端都有
- `-mobile-{platform}`：手機 App
- `-py`：Python 腳本
- `-firmware`：嵌入式韌體

三個資料夾：`homework/` 課堂作業、`web/` 小型練習、`projects/` 完整作品（已停止維護）。

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
