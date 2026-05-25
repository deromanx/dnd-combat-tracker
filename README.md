# ⚔️ D&D 戰鬥紀錄工具 — 海克斯戰役

多玩家即時協作的 D&D 5e 戰鬥追蹤 web app，支援手機使用。

---

## 功能

- 📋 **多角色追蹤**：玩家 + 敵人，每回合獨立填寫
- ⚔️ **完整動作記錄**：主要動作、附贈動作、反應、技能/專長
- ❤️ **HP 管理**：回合起始 HP + 扣血計算，視覺化血量條
- 🔮 **法術追蹤**：專注法術 + 法術環剩餘
- 📛 **狀態標籤**：20+ 常見 D&D 5e 狀態可多選
- 👹 **即時新增敵人**：戰鬥中途可新增新敵人
- 📜 **戰鬥紀錄總覽**：回合紀錄表格 + JSON 匯出
- 🔄 **即時同步**：所有人更新後自動廣播（Socket.IO）

---

## 預設角色（海克斯戰役）

| 角色 | 玩家 | 職業 | 最大 HP |
|------|------|------|---------|
| 🌿 艾蘭達亞 | 游尚傑 | 德魯伊/術士 | 85 |
| 🛡️ 莉莉絲 | Judy | 聖騎士 | 99 |
| 🏹 曼格斯 | Sonia | 遊俠 | 81 |
| 🗡️ 格林 | 大雄 | 刺客 | 47 |
| 🏔️ 山雲盡 | Alex | NPC/DM | 60 |

---

## 本機執行（本地測試）

```bash
cd ~/Downloads/shang-agent/tools/dnd

# 安裝依賴（首次執行）
pip3 install -r requirements.txt

# 啟動（僅自己電腦用）
SOCKETIO_ASYNC_MODE=threading python3 app.py
# → 打開 http://localhost:5001
```

**同桌玩家用手機連線（區域網路）：**
```bash
# 查詢你的 WiFi IP
ipconfig getifaddr en0   # macOS
# 其他人開啟 http://[你的IP]:5001
```

---

## 雲端部署（Railway）

### 步驟 1：建立 GitHub repo

```bash
cd ~/Downloads/shang-agent/tools/dnd
git init
git add .
git commit -m "初始 D&D 戰鬥紀錄工具"
```
推送到 GitHub（新建 repo：`dnd-combat-tracker`）

### 步驟 2：Railway 部署

1. 前往 [railway.app](https://railway.app) → 登入（可用 GitHub）
2. **New Project** → **Deploy from GitHub repo**
3. 選擇 `dnd-combat-tracker`
4. Railway 會自動讀取 `Procfile` 並部署

### 步驟 3：設定環境變數（選填）

在 Railway 專案 → Variables 新增：
- `SECRET_KEY` = 任意隨機字串（加強安全性）
- `PORT` = Railway 自動設定，不用填

### 步驟 4：取得網址

部署完成後，Railway 會給你一個 `xxxx.railway.app` 網址。
把這個網址傳給所有玩家，大家用手機直接開就能用。

> ⚠️ **重要**：Railway 免費方案每月 $5 額度，小型 app 通常夠用。
> 若預算允許，可升級到 $5/月的 Hobby 方案（無休眠）。

---

## 資料存放

- 本機模式：`data/dnd.db`（SQLite，自動建立）
- Railway：持久化 Volume（資料不會因重啟遺失）

若要備份資料，在戰鬥紀錄頁面點「📥 匯出 JSON」。

---

## 自訂角色

編輯 `app.py` 的 `PRESET_PLAYERS` 清單：

```python
PRESET_PLAYERS = [
    {"name": "角色名", "player": "玩家名", "cls": "職業", "maxHP": 100, "emoji": "⚔️"},
    ...
]
```

---

## 技術架構

- **後端**：Python Flask + Flask-SocketIO
- **資料庫**：SQLite（`dnd.db`）
- **前端**：Vanilla HTML/CSS/JS（無框架依賴，手機優化）
- **即時同步**：Socket.IO（WebSocket/polling fallback）
- **部署**：Gunicorn + gevent
