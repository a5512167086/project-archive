# coding-practice

舊練習題與課堂作業集中存放。每個子專案原本是獨立 repo，已用 `git subtree` 併入，commit 歷史保留。

命名規則：全小寫 slug-case，`{project}-{type}`，type 放最後。
- `-fe`：純前端
- `-app`：前後端都有
- `-py`：Python 腳本

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
