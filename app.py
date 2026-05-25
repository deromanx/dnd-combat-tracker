"""
D&D 戰鬥紀錄工具 — Flask + Socket.IO 後端
支援多玩家即時協作，適合雲端部署 (Railway)
"""
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, emit
import sqlite3
import json
import uuid
from datetime import date, datetime
from pathlib import Path
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dnd-hks-2026")

# async_mode: "gevent" for Railway/production, "threading" for simple local use
_async_mode = os.environ.get("SOCKETIO_ASYNC_MODE", "gevent")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=_async_mode)

# ── 資料庫 ────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "dnd.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS battles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_date TEXT NOT NULL,
                data TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


init_db()


# ── 預設角色（含技能資料）────────────────────────────────────────────────────
PRESET_PLAYERS = [
    {
        "name": "艾蘭達亞", "player": "游尚傑", "cls": "德魯伊10/術士2",
        "maxHP": 85, "emoji": "🌿", "portrait": "艾蘭達亞.png",
        "actions": {
            "主要動作": ["施法", "荊棘之鞭", "荊棘叢生", "咒喚獸群", "解除魔法",
                         "潮湧", "召雷術", "植物滋長", "長棍攻擊", "月華之光",
                         "困惑術", "咒喚林地精群", "群體療傷術", "寒冰錐",
                         "樹膚術", "糾纏", "動物交談術", "火牆術", "行動自如"],
            "附贈動作": ["荒野形態", "月光步", "橡棍術", "治癒真言",
                         "火焰刀", "次級復原術", "擒抱藤"],
            "反應":     ["借機施法(戰地施法者)", "吸收元素"],
            "技能/專長": ["月光步", "戰地施法者", "領袖之證", "魔法學徒",
                          "荒野形態", "荒野夥伴", "自然恢復", "大地結社"],
        }
    },
    {
        "name": "莉莉絲", "player": "Judy", "cls": "聖武士12（奉獻之誓）",
        "maxHP": 112, "emoji": "🛡️", "portrait": "莉莉絲.png",
        "actions": {
            "主要動作": ["巨劍攻擊×2", "巨錘攻擊×2", "療傷術（1環）",
                         "命令術（1環）", "召喚坐騎（2環）", "守護之鏈（2環）",
                         "治療禱言（2環）", "棄絕眾敵（引導神力）", "神聖武器（引導神力）"],
            "附贈動作": ["聖療", "神聖感知（引導神力）", "至聖斬（1環）",
                         "熾焰斬（1環）", "激憤斬（1環）", "印記斬（2環）",
                         "致盲斬（3環）"],
            "反應":     ["騎乘戰鬥：轉移攻擊至坐騎", "重甲大師：非魔法武器傷害-3"],
            "技能/專長": ["額外攻擊", "守護靈光（10尺內+4豁免）", "奉獻靈光（免疫魅惑）",
                          "勇氣靈光（免疫恐慌）", "光耀打擊（命中+1d8光耀）",
                          "健壯 Tough", "重甲大師", "騎乘戰鬥",
                          "聖誓固定法術：防護善惡/虔誠護盾/援助術/誠實之域/希望信標/解除魔法"],
        }
    },
    {
        "name": "曼格斯", "player": "Sonia", "cls": "遊俠8",
        "maxHP": 81, "emoji": "🏹", "portrait": "曼格斯.png",
        "actions": {
            "主要動作": ["攻擊(短劍)", "攻擊(長弓)", "攻擊×2", "施法", "療傷術",
                         "冰之吐息"],
            "附贈動作": ["獵人印記(轉移)", "獵人印記(新目標)"],
            "反應":     ["哨兵(藉機攻擊)"],
            "技能/專長": ["哨兵", "穿刺者", "幸運", "宿敵", "額外攻擊",
                          "越野", "德魯伊教戰士"],
        }
    },
    {
        "name": "格林", "player": "大雄", "cls": "刺客12",
        "maxHP": 47, "emoji": "🗡️", "portrait": "格林.png",
        "actions": {
            "主要動作": ["攻擊(匕首)+偷襲", "攻擊(短弓)+偷襲", "疾走",
                         "躲藏", "撤離", "偷襲(6d6)", "獵人印記"],
            "附贈動作": ["巧妙動作(疾走)", "巧妙動作(撤離)", "巧妙動作(躲藏)",
                         "穩定瞄準", "獵人印記(轉移)"],
            "反應":     ["直覺閃避"],
            "技能/專長": ["刺殺", "直覺閃避", "反射閃避", "可靠才能",
                          "詭詐打擊", "進階詭詐打擊", "神射手", "雙持客",
                          "幸運", "警戒"],
        }
    },
    {
        "name": "山雲盡", "player": "Alex", "cls": "NPC/DM",
        "maxHP": 60, "emoji": "🏔️", "portrait": "山雲盡.png",
        "actions": {
            "主要動作": ["攻擊", "施法", "巨大化", "元素爆發"],
            "附贈動作": ["飛簷走壁", "元素調和"],
            "反應":     ["藉機攻擊"],
            "技能/專長": ["巨大化", "元素調和", "元素爆發"],
        }
    },
]


# ── REST API ──────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", preset_players=json.dumps(PRESET_PLAYERS, ensure_ascii=False))


@app.route("/api/battles", methods=["GET"])
def list_battles():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, created_date, data FROM battles ORDER BY rowid DESC"
        ).fetchall()
    result = []
    for r in rows:
        d = json.loads(r["data"])
        result.append({
            "id": r["id"],
            "name": r["name"],
            "date": r["created_date"],
            "charCount": len(d.get("characters", [])),
            "roundCount": sum(1 for rnd in d.get("rounds", []) if rnd.get("entries")),
        })
    return jsonify(result)


@app.route("/api/battles", methods=["POST"])
def create_battle():
    body = request.get_json()
    bid = str(uuid.uuid4())
    today = str(date.today())
    battle = {
        "id": bid,
        "name": body["name"],
        "date": today,
        "characters": body.get("characters", []),
        "rounds": [{"number": 1, "entries": {}}],
    }
    with get_db() as conn:
        conn.execute(
            "INSERT INTO battles (id, name, created_date, data) VALUES (?, ?, ?, ?)",
            (bid, battle["name"], today, json.dumps(battle, ensure_ascii=False))
        )
        conn.commit()
    socketio.emit("battle_list_changed")
    return jsonify(battle), 201


@app.route("/api/battles/<bid>", methods=["GET"])
def get_battle(bid):
    with get_db() as conn:
        row = conn.execute("SELECT data FROM battles WHERE id = ?", (bid,)).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify(json.loads(row["data"]))


@app.route("/api/battles/<bid>", methods=["PUT"])
def update_battle(bid):
    battle = request.get_json()
    battle["id"] = bid  # ensure ID is preserved
    with get_db() as conn:
        conn.execute(
            "UPDATE battles SET data = ?, name = ?, updated_at = datetime('now') WHERE id = ?",
            (json.dumps(battle, ensure_ascii=False), battle.get("name", ""), bid)
        )
        conn.commit()
    # Broadcast to all clients watching this battle
    socketio.emit("battle_updated", {"id": bid}, to=f"battle_{bid}")
    return jsonify({"ok": True})


@app.route("/api/battles/<bid>", methods=["DELETE"])
def delete_battle(bid):
    with get_db() as conn:
        conn.execute("DELETE FROM battles WHERE id = ?", (bid,))
        conn.commit()
    socketio.emit("battle_list_changed")
    return jsonify({"ok": True})


# ── Socket.IO ─────────────────────────────────────────────────────────────────
@socketio.on("join_battle")
def on_join(data):
    battle_id = data.get("battle_id")
    if battle_id:
        join_room(f"battle_{battle_id}")
        emit("joined", {"battle_id": battle_id})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    socketio.run(app, host="0.0.0.0", port=port, debug=False,
                 allow_unsafe_werkzeug=True)
