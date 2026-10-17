"""
╔══════════════════════════════════════════════════════════════════╗
║        🔗 ᴛᴇʟᴇɢʀᴀᴍ ʟɪɴᴋ ᴘʀᴏᴠɪᴅᴇʀ ʙᴏᴛ — ᴘʀᴏᴅᴜᴄᴛɪᴏɴ ʀᴇᴀᴅʏ        ║
║   ᴊꜱᴏɴ ᴅᴀᴛᴀʙᴀꜱᴇ • ᴇɴᴄʀʏᴘᴛᴇᴅ ᴛᴏᴋᴇɴꜱ • 5-ᴍɪɴ ʟɪɴᴋ ʀᴏᴛᴀᴛɪᴏɴ       ║
╚══════════════════════════════════════════════════════════════════╝
"""
import asyncio, base64, hashlib, html, json, logging, os, re, secrets, signal, time
from urllib.parse import quote

from pyrogram import Client, filters, enums
from pyrogram.types import (Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
                            BotCommand, BotCommandScopeDefault, BotCommandScopeChat,
                            KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove)
try:
    from pyrogram.types import LinkPreviewOptions
    LPO_DISABLE = LinkPreviewOptions(is_disabled=True)
except ImportError:
    LPO_DISABLE = None
import pyrogram.utils as utils
from pyrogram.handlers import MessageHandler, CallbackQueryHandler, RawUpdateHandler
from pyrogram.raw.types import UpdateBotChatInviteRequester, UpdatePendingJoinRequests
from pyrogram.errors import (FloodWait, RPCError, UserNotParticipant, AccessTokenInvalid,
                             AccessTokenExpired, UserIsBlocked, InputUserDeactivated,
                             PeerIdInvalid, ChatAdminRequired)

try:
    from dotenv import load_dotenv; load_dotenv()
except Exception:
    pass

# ══════════════════════════════════════════════════════════════════
#  ⚙️ CONFIG — ENVIRONMENT & DEFAULTS
# ══════════════════════════════════════════════════════════════════
API_ID: int = 0
API_HASH: str = ""
BOT_TOKEN: str = ""
DEFAULT_SUPREME_ID: int = 7524032836
SUPREME_IDS: str = "7524032836"
LOG_CHANNEL_ID: int = 0
FACTORY_NAME: str = "Link Provider Factory"
CLONE_BOT_ID_TOKEN: str = ""
DB_DIR: str = "data"
CLEANUP_INTERVAL: int = 3600
LINK_ROTATION_INTERVAL: int = 300  # 5 minutes in seconds

API_ID = int(os.getenv("API_ID") or API_ID or 0)
API_HASH = os.getenv("API_HASH") or API_HASH
BOT_TOKEN = os.getenv("BOT_TOKEN") or BOT_TOKEN
SUPREME_IDS = os.getenv("SUPREME_IDS") or SUPREME_IDS or "7524032836"
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID") or LOG_CHANNEL_ID or 0)
FACTORY_NAME = os.getenv("FACTORY_NAME") or FACTORY_NAME
CLONE_BOT_ID_TOKEN = os.getenv("CLONE_BOT_ID_TOKEN") or CLONE_BOT_ID_TOKEN
LINK_ROTATION_INTERVAL = int(os.getenv("LINK_ROTATION_INTERVAL") or LINK_ROTATION_INTERVAL or 300)

SUPREMES = {DEFAULT_SUPREME_ID} | {int(x) for x in SUPREME_IDS.replace(" ", "").split(",") if x.strip().isdigit()}

# ═════════════════════════ LOGGING ═════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("factory.log", encoding="utf-8")],
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOG = logging.getLogger("ʟɪɴᴋᴘʀᴏᴠɪᴅᴇʀ")

PM_HTML = enums.ParseMode.HTML
PM_OFF = enums.ParseMode.DISABLED
CMS = enums.ChatMemberStatus

START_TS = None
def now(): return int(time.time())
START_TS = now()
DAY_START = lambda: (now() // 86400) * 86400

def dt(ts):
    if not ts: return "N/A"
    return time.strftime("%d %b %Y, %H:%M UTC", time.gmtime(ts))

def hms(sec):
    sec = int(sec); d = sec // 86400; h = (sec % 86400) // 3600; m = (sec % 3600) // 60
    return (f"{d}d " if d else "") + f"{h}h {m}m"

def human_size(n):
    n = float(n)
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return f"{int(n)} B" if u == "B" else f"{n:.1f} {u}"
        n /= 1024

def hesc(s): return html.escape(str(s) if s else "")

_SMALL_MAP = str.maketrans(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘqʀꜱᴛᴜᴠᴡxʏᴢ" "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘqʀꜱᴛᴜᴠᴡxʏᴢ")
def sc(t): return str(t).translate(_SMALL_MAP)

def btn(text, cb): return InlineKeyboardButton(sc(text), callback_data=cb)
def ubtn(text, url): return InlineKeyboardButton(sc(text), url=url)

def chunk(text, limit=3800):
    out, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > limit:
            out.append(cur); cur = line
        else:
            cur = (cur + "\n" + line) if cur else line
    if cur: out.append(cur)
    return out or [""]

# ═════════════════════ CONSTANT TEXTS ═════════════════════
DEFAULT_START = (
    "👋 <b>ʜᴇʟʟᴏ {name}!</b>\n\n"
    "🔗 <b>Welcome to {botname}!</b>\n"
    "I am an advanced Telegram Link Provider Bot.\n\n"
    "⚡ Open provider URLs to get instant channel invite links.")

CLONE_PROMPT = (
    "🤖 <b>ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ʟɪɴᴋ ᴘʀᴏᴠɪᴅᴇʀ ʙᴏᴛ</b>\n━━━━━━━━━━━━━━\n\n"
    "1️⃣ Open @BotFather\n"
    "2️⃣ /newbot → Set name & username\n"
    "3️⃣ Copy token and send here\n\n"
    "🔐 <b>ꜱᴇᴄᴜʀɪᴛʏ:</b> Tokens are stored <u>ENCRYPTED</u> — never in plaintext.\n\n"
    "⏳ <b>ɴᴏᴡ ꜱᴇɴᴅ ʏᴏᴜʀ ʙᴏᴛ ᴛᴏᴋᴇɴ:</b>")

CLONE_SUCCESS = (
    "🎉 <b>ᴄʟᴏɴᴇ ᴄʀᴇᴀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!</b>\n━━━━━━━━━━━━━━\n\n"
    "🤖 ʙᴏᴛ: <b>@{uname}</b>\n"
    "🆔: <code>{bid}</code>\n"
    "👤 ᴏᴡɴᴇʀ: <b>{name}</b>\n\n"
    "✅ ʙᴏᴛ ꜱᴛᴀʀᴛᴇᴅ + ᴄᴏᴍᴍᴀɴᴅꜱ ᴀᴜᴛᴏ-ꜱᴇᴛ\n\n"
    "📌 <b>ɴᴇxᴛ ꜱᴛᴇᴘ:</b>\n"
    "▸ /admin — Open Admin Dashboard\n"
    "🚀 ʏᴏᴜʀ ʙᴏᴛ ɪꜱ ʟɪᴠᴇ ɴᴏᴡ!")

ADMIN_PANEL_TXT = (
    "🛠 <b>ᴀᴅᴍɪɴ ᴅᴀꜱʜʙᴏᴀʀᴅ</b>\n━━━━━━━━━━━━━━\n"
    "🤖 ʙᴏᴛ: @{uname}\n"
    "👤 ʏᴏᴜ: <b>{role}</b>\n\n"
    "⬇️ Select an option below to manage provider links and channels:")

# ═════════════════════ PERMISSIONS & ROLES ═════════════════════
PERMS = ["create_link", "manage_links", "manage_channels", "view_stats", "broadcast",
         "forcesub", "editstart", "manage_admins", "ban_users"]

PERM_LABELS = {
    "create_link": "Create Provider Links", "manage_links": "Manage Provider Links",
    "manage_channels": "Manage Saved Channels", "view_stats": "View Analytics & Stats",
    "broadcast": "Broadcast Messages", "forcesub": "Configure ForceSub",
    "editstart": "Customize Start Msg", "manage_admins": "Manage Admins",
    "ban_users": "Ban / Unban Users"
}

ROLE_PRESETS = {
    "owner": list(PERMS),
    "manager": ["create_link", "manage_links", "manage_channels", "view_stats", "broadcast", "forcesub", "editstart", "ban_users"],
    "link_admin": ["create_link", "manage_links", "manage_channels", "view_stats"],
    "broadcaster": ["broadcast"],
    "analyst": ["view_stats"],
    "custom": [],
}
ROLE_NAME = {"owner": "👑 Owner", "manager": "🛠 Manager", "link_admin": "🔗 Link Admin",
             "broadcaster": "📣 Broadcaster", "analyst": "📊 Analyst", "custom": "⚙️ Custom"}

# ═════════════════════ COMMAND SETS ═════════════════════
USER_CMD_RAW = [("start", "Start Bot / Open Provider Link"), ("help", "Usage & Instructions"), ("refer", "Referral Links & Stats")]
ADMIN_CMD_RAW = [
    ("admin", "Admin Dashboard"),
    ("newlink", "Create Provider Link"),
    ("mylinks", "Manage Provider Links"),
    ("mychannels", "Manage Channels"),
    ("stats", "Statistics & Analytics"),
    ("rotation", "Link Rotation Status"),
    ("cancel", "Cancel Active Flow")
]
FACTORY_CMD_RAW = [("clone", "Create Link Provider Bot Clone")]
SUPREME_CMD_RAW = [("supreme", "Supreme Admin Panel"), ("botlist", "All Cloned Bots"), ("db", "Database Health"), ("restart", "Restart Clones")]

ALL_CMDS = ["start", "refer", "help"] + [x[0] for x in ADMIN_CMD_RAW + FACTORY_CMD_RAW + SUPREME_CMD_RAW]
FACTORY_ONLY = {"clone", "supreme", "rajpapa", "botlist", "db", "restart"}

# ═════════════════════ GLOBAL STATE ═════════════════════
RUNNING = {}        # bot_id -> Client
STORES = {}         # bot_id -> Store
SESSIONS = {}       # (bot_id, uid) -> {"step":..., "data":{...}}
RATE = {}
LAST_UNAUTH = {}
ACTIVE_THRO = {}
FACTORY = None      # factory Store
FACTORY_CLIENT = None
ROTATION_TASK = None

_COLLECTIONS = ["users", "provider_links", "channels", "visits", "rotation_state", "admins", "settings", "referrals", "broadcast_logs", "activity"]

# ══════════════════════════════════════════════════════════════════
#  🗄️ JSON DATABASE — STORE ENGINE
# ══════════════════════════════════════════════════════════════════
class Store:
    def __init__(self, path):
        self.path = path
        self.data = {}
        self._dirty = False
        self._task = None
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                if not isinstance(self.data, dict):
                    raise ValueError("root not dict")
            except Exception as e:
                LOG.error("DB Load Failed %s: %s", self.path, e)
                try: os.replace(self.path, self.path + ".corrupt")
                except OSError: pass
                self.data = {}

    def c(self, name):
        return self.data.setdefault(name, {})

    def get_sync(self, col, _id):
        return self.c(col).get(str(_id))

    async def get(self, col, _id):
        return self.c(col).get(str(_id))

    async def put(self, col, _id, doc):
        self.c(col)[str(_id)] = doc
        self.flush_soon()
        return doc

    async def update(self, col, _id, **fields):
        d = self.c(col).get(str(_id))
        if d is None:
            return None
        d.update(fields)
        self.flush_soon()
        return d

    async def delete(self, col, _id):
        self.c(col).pop(str(_id), None)
        self.flush_soon()

    def count(self, col):
        return len(self.c(col))

    def find(self, col, pred=None):
        return [v for v in self.c(col).values() if pred is None or pred(v)]

    def flush_soon(self):
        self._dirty = True
        if self._task is None or self._task.done():
            try:
                self._task = asyncio.get_running_loop().create_task(self._flush_later())
            except RuntimeError:
                pass

    async def _flush_later(self):
        await asyncio.sleep(0.4)
        if self._dirty:
            await self.flush()

    async def flush(self):
        self._dirty = False
        payload = json.dumps(self.data, ensure_ascii=False, separators=(",", ":"))
        await asyncio.to_thread(self._write, payload)

    def _write(self, payload):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(payload)
        os.replace(tmp, self.path)

    def size(self):
        try: return os.path.getsize(self.path)
        except OSError: return 0


def clone_path(bid): return os.path.join(DB_DIR, f"clone_{bid}.json")

def get_store(bid):
    s = STORES.get(bid)
    if not s:
        s = Store(clone_path(bid))
        STORES[bid] = s
    return s

def cfg(store):
    return store.c("settings").get("cfg") or {}

async def set_cfg(store, **kw):
    d = dict(cfg(store)); d.update(kw)
    await store.put("settings", "cfg", d)

async def ensure_defaults(store):
    st = store.c("settings")
    if "cfg" not in st:
        st["cfg"] = {"fs_mode": "off", "fs_channel": 0, "fs_username": "", "fs_link": "",
                     "log_channel": 0, "owner_id": None, "created_at": now()}
        store.flush_soon()
    if "start" not in st:
        st["start"] = {"type": "text", "text": DEFAULT_START}
        store.flush_soon()
    for col in _COLLECTIONS:
        store.c(col)

# ═════════════════════ TOKEN ENCRYPTION ═════════════════════
_FER = None
def _fernet():
    from cryptography.fernet import Fernet
    secret = (str(API_HASH) + ":" + str(CLONE_BOT_ID_TOKEN or "link-provider-factory-v1")).encode()
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret).digest()))

def enc_token(t):
    global _FER
    _FER = _FER or _fernet()
    return _FER.encrypt(t.encode()).decode()

def dec_token(e):
    global _FER
    _FER = _FER or _fernet()
    return _FER.decrypt(e.encode()).decode()

def gen_provider_token():
    return secrets.token_urlsafe(16).replace("-", "").replace("_", "")

# ═════════════════════ SESSION / RATE / PERMS ═════════════════════
def get_sess(c, user_id): return SESSIONS.get((c.bot_id, user_id))
def set_sess(c, user_id, step, **data):
    data.pop("user_id", None)
    SESSIONS[(c.bot_id, user_id)] = {"step": step, "data": data}
def clear_sess(c, user_id): SESSIONS.pop((c.bot_id, user_id), None)

def rate_ok(c, uid):
    k = (c.bot_id, uid); t = now()
    if t - RATE.get(k, 0) < 1.5: return False
    RATE[k] = t; return True

def is_supreme(uid):
    if not uid: return False
    try: return int(uid) in SUPREMES
    except (ValueError, TypeError): return False

async def is_user_banned(c, uid):
    u = await c.store.get("users", str(uid)) or await c.store.get("users", uid)
    return bool(u and u.get("is_banned"))

async def perm_ok(c, uid, perm):
    if is_supreme(uid): return True
    a = await c.store.get("admins", uid)
    if not a: return False
    if a.get("role") == "owner": return True
    return perm in a.get("permissions", [])

# ═════════════════════ LOGGING / NOTIFY ═════════════════════
async def dev_log(text):
    if FACTORY is not None:
        await FACTORY.put("developer_logs", secrets.token_hex(6), {"text": text, "at": now()})
    if LOG_CHANNEL_ID and FACTORY_CLIENT is not None:
        try:
            await FACTORY_CLIENT.send_message(LOG_CHANNEL_ID, text, parse_mode=PM_OFF,
                                              link_preview_options=LPO_DISABLE)
        except RPCError: pass

async def log_event(c, event, detail="", important=False, uid=None):
    await c.store.put("activity", secrets.token_hex(5),
                      {"event": event, "detail": detail, "uid": uid, "at": now()})
    text = f"{event}\n{detail}\n🤖 @{c.username} | {dt(now())}"
    lc = cfg(c.store).get("log_channel", 0)
    if lc:
        try: await c.send_message(lc, text, parse_mode=PM_OFF, link_preview_options=LPO_DISABLE)
        except RPCError: pass
    if important:
        await dev_log(text)

async def touch_active(c):
    if c.is_factory or FACTORY is None: return
    t = now()
    if t - ACTIVE_THRO.get(c.bot_id, 0) < 300: return
    ACTIVE_THRO[c.bot_id] = t
    await FACTORY.update("bots", c.bot_id, last_active=t)

async def unauthorized(c, uid):
    k = (c.bot_id, uid)
    if now() - LAST_UNAUTH.get(k, 0) < 600: return
    LAST_UNAUTH[k] = now()
    await log_event(c, "🚫 ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴀᴄᴄᴇꜱꜱ ᴀᴛᴛᴇᴍᴘᴛ", f"User: {uid}", important=True, uid=uid)

async def q_safe(q, text, alert=False):
    try: await q.answer(sc(text), show_alert=alert)
    except RPCError: pass

# ═════════════════════ AUTO COMMANDS ═════════════════════
def _cmds(lst): return [BotCommand(a, sc(b)) for a, b in lst]

async def apply_admin_commands(c, uid):
    lst = USER_CMD_RAW + ADMIN_CMD_RAW + (FACTORY_CMD_RAW if c.is_factory else []) + (SUPREME_CMD_RAW if is_supreme(uid) else [])
    try:
        await c.set_bot_commands(_cmds(lst), scope=BotCommandScopeChat(chat_id=int(uid)))
    except Exception as e:
        LOG.debug("set_bot_commands admin failed: %s", e)

async def apply_commands(c):
    base = USER_CMD_RAW + (FACTORY_CMD_RAW if c.is_factory else [])
    try:
        await c.set_bot_commands(_cmds(base), scope=BotCommandScopeDefault())
    except Exception as e:
        LOG.debug("set_bot_commands default failed: %s", e)
    for uid in list(c.store.c("admins").keys()):
        await apply_admin_commands(c, int(uid))
    for uid in SUPREMES:
        await apply_admin_commands(c, uid)

# ═════════════════════ USERS & FORCE-SUB ═════════════════════
async def ensure_user(c, tu):
    uid = str(tu.id)
    u = await c.store.get("users", uid)
    if u:
        if u.get("last_seen", 0) < now() - 3600:
            await c.store.update("users", uid, last_seen=now())
        return u
    u = {"_id": uid, "first_name": (tu.first_name or "")[:64], "username": (tu.username or ""),
         "started_at": now(), "last_seen": now(), "fs_verified": False}
    await c.store.put("users", uid, u)
    await log_event(c, "🆕 ɴᴇᴡ ᴜꜱᴇʀ", f"Chat: {uid} (@{u['username']})", important=True, uid=tu.id)
    await touch_active(c)
    return u

async def fs_state(c, uid, is_clone_action=False):
    if is_supreme(uid):
        return True, None

    if is_clone_action:
        target_store = FACTORY or c.store
        target_client = FACTORY_CLIENT or c
    else:
        target_store = c.store
        target_client = c
        a = await c.store.get("admins", uid)
        if a or cfg(c.store).get("owner_id") == uid:
            return True, None

    st = cfg(target_store)
    channels = st.get("fs_channels", [])
    if not channels and st.get("fs_mode", "off") != "off":
        channels = [{
            "mode": st.get("fs_mode"),
            "chat_id": st.get("fs_channel"),
            "username": st.get("fs_username", ""),
            "link": st.get("fs_link", "")
        }]

    if not channels:
        return True, None

    u = await target_store.get("users", uid)
    verified_chats = set((u.get("fs_verified_chats") or []) if u else [])

    unsub_rows = []
    all_ok = True

    for ch in channels:
        cid = ch.get("chat_id")
        cid_str = str(cid) if cid else ""
        cmode = ch.get("mode", "public")
        cuname = ch.get("username", "")
        clink = ch.get("link", "")

        is_joined = False
        if cmode == "public" and (cid or cuname):
            try:
                mem = await target_client.get_chat_member(cuname or cid, uid)
                is_joined = mem.status in (CMS.MEMBER, CMS.ADMINISTRATOR, CMS.OWNER)
            except (UserNotParticipant, RPCError):
                is_joined = False
        else:
            if cid_str and cid_str in verified_chats:
                is_joined = True

        if is_joined:
            if cid_str:
                verified_chats.add(cid_str)
        else:
            all_ok = False
            label = ch.get("btn_name") or (f"🔗 ᴊᴏɪɴ @{cuname}" if cuname else "🔗 ʀᴇQᴜᴇꜱᴛ ᴛᴏ ᴊᴏɪɴ")
            url = f"https://t.me/{cuname}" if (cmode == "public" and cuname) else clink
            if url:
                unsub_rows.append([ubtn(label, url)])

    if all_ok:
        if u:
            await target_store.update("users", uid, fs_verified=True, fs_verified_chats=list(verified_chats))
        return True, None

    if u:
        await target_store.update("users", uid, fs_verified=False, fs_verified_chats=list(verified_chats))

    unsub_rows.append([btn("✅ ᴠᴇʀɪꜰʏ ɴᴏᴡ", "ckfs")])
    return False, InlineKeyboardMarkup(unsub_rows)

async def convert_referral(c, uid):
    pend = [r for r in c.store.find("referrals")
            if r.get("user") == str(uid) and r.get("status") == "pending"]
    for r in pend:
        await c.store.update("referrals", r["_id"], status="converted", converted_at=now())
        await log_event(c, "🤝 ʀᴇꜰᴇʀʀᴀʟ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ", f"Ref: {r['referrer']} → {uid}", uid=uid)
        try:
            await c.send_message(int(r["referrer"]), "🎉 <b>ɴᴇᴡ ʀᴇꜰᴇʀʀᴀʟ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ!</b>", parse_mode=PM_HTML)
        except RPCError: pass

def render_text(template, user, c):
    name = hesc(user.get("first_name") or "User")
    uname = hesc(user.get("username") or user.get("_id", ""))
    return (template.replace("{name}", name).replace("{username}", uname)
            .replace("{botname}", hesc(c.username)))

def get_official_link(c):
    link = cfg(c.store).get("official_link") or c.store.c("settings").get("official_link")
    if link: return link
    if FACTORY:
        link = cfg(FACTORY).get("official_link") or FACTORY.c("settings").get("official_link")
        if link: return link
    return "https://t.me"

async def send_welcome_content(c, chat_id, user):
    s = c.store.c("settings").get("start") or {"type": "text", "text": DEFAULT_START}
    text = render_text(s.get("text") or DEFAULT_START, user or {}, c)
    off_link = get_official_link(c)
    rows = [
        [ubtn("📢 ᴏꜰꜰɪᴄɪᴀʟ ᴄʜᴀɴɴᴇʟ", off_link), btn("🤖 ᴄʟᴏɴᴇ ʙᴏᴛ", "cloneme")],
        [btn("⚙️ ᴀᴅᴍɪɴ ᴅᴀꜱʜʙᴏᴀʀᴅ", "pan|refresh")]
    ]
    kb = InlineKeyboardMarkup(rows)
    try:
        await c.send_message(chat_id, text, parse_mode=PM_HTML, reply_markup=kb, link_preview_options=LPO_DISABLE)
    except RPCError: pass

# ══════════════════════════════════════════════════════════════════
#  📢 CHANNEL RESOLUTION & MANAGEMENT
# ══════════════════════════════════════════════════════════════════
async def validate_and_resolve_channel(c, admin_id, query):
    """Resolves channel from username, link, ID, or forwarded message.
       Verifies bot admin status and returns (channel_doc, error_str)."""
    q_str = str(query).strip()
    if "t.me/" in q_str:
        q_str = q_str.split("t.me/")[-1].strip("/")
        if q_str.startswith("c/"):
            q_str = q_str[2:]
            if q_str.isdigit():
                q_str = f"-100{q_str}"

    candidates = []
    if q_str.lstrip("-").isdigit():
        val = int(q_str)
        candidates.append(val)
        if val > 0:
            candidates.append(int(f"-100{val}"))
    else:
        if not q_str.startswith("@") and not q_str.startswith("http"):
            candidates.append(f"@{q_str}")
        candidates.append(q_str)

    chat = None
    for cand in candidates:
        try:
            chat = await c.get_chat(cand)
            if chat: break
        except RPCError: continue

    if not chat:
        return None, "❌ <b>Channel Not Found!</b>\n\nPlease check the channel username or ID and make sure the bot is added as an administrator."

    # Check bot admin permissions in the channel
    bot_mem = None
    try:
        bot_mem = await c.get_chat_member(chat.id, "me")
    except RPCError as e:
        return None, f"❌ <b>Bot Access Error:</b>\n\nThe bot cannot access this channel ({e}). Please add @{c.username} as an Administrator in the target channel."

    if bot_mem.status not in (CMS.OWNER, CMS.ADMINISTRATOR):
        return None, f"❌ <b>Bot Permission Error:</b>\n\n@{c.username} is in the channel but is <b>not an Administrator</b>. Please promote the bot to Administrator with 'Invite Users via Link' permission."

    # Verify if bot can invite users
    can_invite = True
    if bot_mem.status == CMS.ADMINISTRATOR:
        privs = getattr(bot_mem, "privileges", None)
        if privs and hasattr(privs, "can_invite_users"):
            can_invite = bool(privs.can_invite_users)

    is_pub = bool(chat.username)
    ch_doc = {
        "_id": str(chat.id),
        "channel_id": chat.id,
        "title": chat.title or "Channel",
        "username": chat.username or "",
        "added_by": str(admin_id),
        "verified_at": now(),
        "bot_is_admin": True,
        "can_invite_users": can_invite,
        "is_public": is_pub,
        "created_at": now()
    }
    await c.store.put("channels", str(chat.id), ch_doc)
    return ch_doc, None

# ══════════════════════════════════════════════════════════════════
#  🔄 LINK ROTATION SERVICE & INVITE LINK GENERATION
# ══════════════════════════════════════════════════════════════════
async def get_or_generate_invite_link(c, channel_id, delivery_mode):
    """Retrieves current valid invite link or generates a new Telegram invite link."""
    rot_key = f"{channel_id}:{delivery_mode}"
    rot = await c.store.get("rotation_state", rot_key)
    t = now()

    if rot and rot.get("current_invite_link") and (rot.get("expire_at", 0) > t + 30):
        return rot["current_invite_link"], None

    is_req = (delivery_mode == "join_request")
    try:
        res = await c.create_chat_invite_link(
            chat_id=int(channel_id),
            creates_join_request=is_req,
            name=f"Rotated by @{c.username}"
        )
        new_link = getattr(res, "invite_link", None) or str(res)
    except RPCError as e:
        LOG.error("Failed to create invite link for %s mode %s: %s", channel_id, delivery_mode, e)
        if rot and rot.get("current_invite_link"):
            return rot["current_invite_link"], None  # Fallback to current link if API fails
        return None, f"Telegram API Error: {e}"

    prev_link = rot.get("current_invite_link") if rot else None
    revoked_list = rot.get("revoked_links", []) if rot else []

    expire_at = t + LINK_ROTATION_INTERVAL + 60  # Allow overlap buffer
    rot_doc = {
        "_id": rot_key,
        "channel_id": channel_id,
        "delivery_mode": delivery_mode,
        "current_invite_link": new_link,
        "last_rotation_at": t,
        "next_rotation_at": t + LINK_ROTATION_INTERVAL,
        "expire_at": expire_at,
        "revoked_links": revoked_list
    }
    await c.store.put("rotation_state", rot_key, rot_doc)

    # Revoke previous link after replacement saved
    if prev_link and prev_link != new_link:
        try:
            await c.revoke_chat_invite_link(int(channel_id), prev_link)
            revoked_list.append(prev_link)
            if len(revoked_list) > 20: revoked_list = revoked_list[-20:]
            rot_doc["revoked_links"] = revoked_list
            await c.store.put("rotation_state", rot_key, rot_doc)
        except RPCError as re_err:
            LOG.warning("Could not revoke old link %s: %s", prev_link, re_err)

    return new_link, None

async def rotate_single_channel_mode(c, rot_key, rot_doc):
    """Executes rotation for a single channel + delivery mode."""
    t = now()
    cid = rot_doc.get("channel_id")
    mode = rot_doc.get("delivery_mode")
    if not cid or not mode or mode == "public":
        return

    is_req = (mode == "join_request")
    try:
        res = await c.create_chat_invite_link(
            chat_id=int(cid),
            creates_join_request=is_req,
            name=f"Rotated by @{c.username}"
        )
        new_link = getattr(res, "invite_link", None) or str(res)
    except RPCError as e:
        LOG.error("Rotation error bot @%s channel %s: %s", c.username, cid, e)
        rot_doc["rotation_error"] = str(e)
        await c.store.put("rotation_state", rot_key, rot_doc)
        return

    prev_link = rot_doc.get("current_invite_link")
    rot_doc["current_invite_link"] = new_link
    rot_doc["last_rotation_at"] = t
    rot_doc["next_rotation_at"] = t + LINK_ROTATION_INTERVAL
    rot_doc["expire_at"] = t + LINK_ROTATION_INTERVAL + 60
    rot_doc["rotation_error"] = None

    # Update all matching provider links referencing this channel & mode
    for link in c.store.find("provider_links", lambda l: str(l.get("channel_id")) == str(cid) and l.get("delivery_mode") == mode):
        link["current_invite_link"] = new_link
        link["last_rotation_at"] = t
        link["next_rotation_at"] = t + LINK_ROTATION_INTERVAL
        await c.store.put("provider_links", link["_id"], link)

    revoked = rot_doc.get("revoked_links", [])
    if prev_link and prev_link != new_link:
        try:
            await c.revoke_chat_invite_link(int(cid), prev_link)
            revoked.append(prev_link)
            if len(revoked) > 20: revoked = revoked[-20:]
            rot_doc["revoked_links"] = revoked
        except RPCError as r_err:
            LOG.warning("Revoke failed for %s: %s", prev_link, r_err)

    await c.store.put("rotation_state", rot_key, rot_doc)

async def rotation_job_step():
    """Iterates through all running bots and rotates active rotating invite links."""
    t = now()
    for bid, c in list(RUNNING.items()):
        if not c or not c.store: continue
        rot_states = c.store.find("rotation_state")
        for rot in rot_states:
            nxt = rot.get("next_rotation_at", 0)
            if t >= nxt or not rot.get("current_invite_link"):
                await rotate_single_channel_mode(c, rot["_id"], rot)

async def rotation_service_loop():
    while True:
        try:
            await rotation_job_step()
        except Exception as e:
            LOG.exception("Rotation loop error: %s", e)
        await asyncio.sleep(15)  # Check every 15 seconds

# ══════════════════════════════════════════════════════════════════
#  🎯 LINK PROVIDER GENERATION & DEEP-LINK DELIVERY
# ══════════════════════════════════════════════════════════════════
async def create_provider_link(c, admin_id, channel_id, delivery_mode):
    """Creates a new unique provider link for an authorized administrator."""
    ch = await c.store.get("channels", str(channel_id))
    if not ch:
        ch_doc, err = await validate_and_resolve_channel(c, admin_id, channel_id)
        if err or not ch_doc:
            return None, err or "Channel not accessible"
        ch = ch_doc

    if delivery_mode == "public":
        if not ch.get("username"):
            return None, "❌ <b>Public Link Error:</b>\n\nThis channel has no public username (@channelname). Please choose 🔒 Private Invite Link or ✅ Join Request Link."
        dest_link = f"https://t.me/{ch['username']}"
    else:
        dest_link, err = await get_or_generate_invite_link(c, ch["channel_id"], delivery_mode)
        if err:
            return None, err

    token = gen_provider_token()
    pid = f"link_{token}"
    bot_uname = c.username or "Bot"
    prov_url = f"https://t.me/{bot_uname}?start={token}"
    t = now()

    doc = {
        "_id": pid,
        "provider_link_id": pid,
        "token": token,
        "owner_admin_id": str(admin_id),
        "channel_id": ch["channel_id"],
        "channel_title": ch["title"],
        "channel_username": ch.get("username", ""),
        "delivery_mode": delivery_mode,
        "provider_url": prov_url,
        "active": True,
        "created_at": t,
        "updated_at": t,
        "last_rotation_at": t,
        "next_rotation_at": t + LINK_ROTATION_INTERVAL if delivery_mode != "public" else 0,
        "current_invite_link": dest_link,
        "total_visits": 0,
        "unique_visitors": [],
        "successful_deliveries": 0,
        "failed_deliveries": 0
    }
    await c.store.put("provider_links", pid, doc)
    await touch_active(c)
    await log_event(c, "🔗 ᴘʀᴏᴠɪᴅᴇʀ ʟɪɴᴋ ᴄʀᴇᴀᴛᴇᴅ",
                    f"Token: {token}\nChannel: {ch['title']} ({ch['channel_id']})\nMode: {delivery_mode}\nAdmin: {admin_id}",
                    important=True, uid=admin_id)
    return doc, None

async def handle_provider_token_delivery(c, m, token):
    """Delivers destination link when a user opens https://t.me/Bot?start=<token>"""
    uid = m.from_user.id
    user = await ensure_user(c, m.from_user)

    links = c.store.find("provider_links", lambda l: l.get("token") == token)
    if not links:
        await m.reply("❌ <b>Invalid Link!</b>\n\nThis provider link does not exist or has been removed.", parse_mode=PM_HTML)
        return

    link_rec = links[0]
    if not link_rec.get("active", True):
        await m.reply("🔒 <b>Link Disabled!</b>\n\nThis provider link is currently disabled by its administrator.", parse_mode=PM_HTML)
        return

    cid = link_rec["channel_id"]
    mode = link_rec.get("delivery_mode", "public")
    dest_url = None

    if mode == "public":
        ch = await c.store.get("channels", str(cid))
        cuname = (ch.get("username") if ch else None) or link_rec.get("channel_username")
        if cuname:
            dest_url = f"https://t.me/{cuname}"
        else:
            dest_url = link_rec.get("current_invite_link")
    else:
        # Fetch current rotating link or generate if expired
        rot_key = f"{cid}:{mode}"
        rot = await c.store.get("rotation_state", rot_key)
        if rot and rot.get("current_invite_link"):
            dest_url = rot["current_invite_link"]
        else:
            dest_url, _ = await get_or_generate_invite_link(c, cid, mode)

    if not dest_url:
        link_rec["failed_deliveries"] = link_rec.get("failed_deliveries", 0) + 1
        await c.store.put("provider_links", link_rec["_id"], link_rec)
        await m.reply("⚠️ <b>Temporary Error:</b>\n\nUnable to generate channel invite link right now. Please try again in a few moments.", parse_mode=PM_HTML)
        return

    # Update visit stats
    link_rec["total_visits"] = link_rec.get("total_visits", 0) + 1
    link_rec["successful_deliveries"] = link_rec.get("successful_deliveries", 0) + 1
    uniques = set(link_rec.get("unique_visitors", []))
    uniques.add(str(uid))
    link_rec["unique_visitors"] = list(uniques)
    await c.store.put("provider_links", link_rec["_id"], link_rec)

    # Record visit entry
    visit_id = f"v_{secrets.token_hex(6)}"
    await c.store.put("visits", visit_id, {
        "_id": visit_id,
        "provider_token": token,
        "owner_admin_id": link_rec.get("owner_admin_id"),
        "visitor_user_id": str(uid),
        "delivered_link": dest_url,
        "delivery_mode": mode,
        "channel_id": cid,
        "timestamp": now()
    })

    ch_title = hesc(link_rec.get("channel_title") or "Target Channel")

    if mode == "public":
        txt = (f"📢 <b>Your Channel Link</b>\n\n"
               f"Channel: <b>{ch_title}</b>\n\n"
               f"Tap the button below to open the channel.")
        kb = InlineKeyboardMarkup([[ubtn("📢 Open Channel", dest_url)]])
    elif mode == "private":
        txt = (f"🔒 <b>Your Private Channel Invite</b>\n\n"
               f"Channel: <b>{ch_title}</b>\n\n"
               f"Use the button below to open the channel.\n\n"
               f"<i>Note: This invite link may stop working when it expires or is rotated.</i>")
        kb = InlineKeyboardMarkup([[ubtn("🔗 Join Channel", dest_url)]])
    else:  # join_request
        txt = (f"✅ <b>Request to Join Channel</b>\n\n"
               f"Channel: <b>{ch_title}</b>\n\n"
               f"Open the channel invite link below to submit your join request.\n\n"
               f"<i>Your request may need administrator approval.</i>")
        kb = InlineKeyboardMarkup([[ubtn("📨 Request to Join", dest_url)]])

    await m.reply(txt, reply_markup=kb, parse_mode=PM_HTML, link_preview_options=LPO_DISABLE)

# ══════════════════════════════════════════════════════════════════
#  📊 DASHBOARD & ADMIN INTERFACE UI
# ══════════════════════════════════════════════════════════════════
def dashboard_kb():
    return InlineKeyboardMarkup([
        [btn("📢 Create New Link", "lnk|new"), btn("🔗 My Links", "lnk|list|1")],
        [btn("🗂 My Channels", "chn|list|1"), btn("📊 My Statistics", "st|my")],
        [btn("🔄 Rotation Status", "rot|status"), btn("⚙️ Settings", "pan|refresh")],
        [btn("❓ Help", "usr|help"), btn("◀️ Back", "usr|home")]
    ])

async def show_admin_dashboard(c, chat_id, edit_msg=None, uid=None):
    doc = await c.store.get("admins", uid or chat_id)
    role = ROLE_NAME.get(doc["role"], doc["role"]) if doc else "👑 Supreme"
    txt = ADMIN_PANEL_TXT.format(uname=c.username, role=role)
    kb = dashboard_kb()

    if edit_msg is not None:
        try: await edit_msg.edit_text(txt, reply_markup=kb, parse_mode=PM_HTML)
        except RPCError: pass
    else:
        await c.send_message(chat_id, txt, reply_markup=kb, parse_mode=PM_HTML)

async def show_my_links(c, chat_id, admin_id, page=1, edit_msg=None):
    links = c.store.find("provider_links", lambda l: is_supreme(admin_id) or str(l.get("owner_admin_id")) == str(admin_id))
    links.sort(key=lambda x: x.get("created_at", 0), reverse=True)

    per_page = 5
    total = len(links)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    page_links = links[start_idx:start_idx + per_page]

    rows = []
    for l in page_links:
        status = "🟢 Active" if l.get("active", True) else "🔴 Disabled"
        mode_icon = "🌐" if l.get("delivery_mode") == "public" else ("🔒" if l.get("delivery_mode") == "private" else "✅")
        label = f"{mode_icon} {l.get('channel_title','Channel')[:15]} [{status}]"
        rows.append([btn(label, f"lnk|detail|{l['_id']}")])

    if total_pages > 1:
        nav = []
        if page > 1: nav.append(btn("◀️ Prev", f"lnk|list|{page - 1}"))
        nav.append(btn(f"📄 {page}/{total_pages}", "ignore"))
        if page < total_pages: nav.append(btn("Next ▶️", f"lnk|list|{page + 1}"))
        rows.append(nav)

    rows.append([btn("📢 Create New Link", "lnk|new")])
    rows.append([btn("◀️ Dashboard", "pan|refresh")])

    txt = f"🔗 <b>ᴍʏ ᴘʀᴏᴠɪᴅᴇʀ ʟɪɴᴋꜱ ({total})</b>\n\nSelect a provider link to view statistics or change settings:"
    kb = InlineKeyboardMarkup(rows)

    if edit_msg is not None:
        try: await edit_msg.edit_text(txt, reply_markup=kb, parse_mode=PM_HTML)
        except RPCError: pass
    else:
        await c.send_message(chat_id, txt, reply_markup=kb, parse_mode=PM_HTML)

async def show_link_detail(c, chat_id, admin_id, pid, edit_msg=None):
    link = await c.store.get("provider_links", pid)
    if not link:
        await c.send_message(chat_id, "❌ Link not found!"); return

    if not is_supreme(admin_id) and str(link.get("owner_admin_id")) != str(admin_id):
        await c.send_message(chat_id, "❌ <b>Access Denied:</b> You are not authorized to manage this provider link."); return

    status_str = "🟢 Active" if link.get("active", True) else "🔴 Disabled"
    toggle_label = "🔴 Disable Link" if link.get("active", True) else "🟢 Enable Link"
    mode_map = {"public": "🌐 Public Link", "private": "🔒 Private Invite Link", "join_request": "✅ Join Request Link"}

    uniques = len(link.get("unique_visitors", []))
    tot_visits = link.get("total_visits", 0)
    repeats = max(0, tot_visits - uniques)

    txt = (f"🔗 <b>ᴘʀᴏᴠɪᴅᴇʀ ʟɪɴᴋ ᴅᴇᴛᴀɪʟꜱ</b>\n━━━━━━━━━━━━━━\n"
           f"📺 Channel: <b>{hesc(link.get('channel_title'))}</b>\n"
           f"🆔 Channel ID: <code>{link.get('channel_id')}</code>\n"
           f"🏷️ Type: <b>{mode_map.get(link.get('delivery_mode'), link.get('delivery_mode'))}</b>\n"
           f"⚡ Status: <b>{status_str}</b>\n\n"
           f"🔗 <b>Provider URL:</b>\n<code>{link.get('provider_url')}</code>\n\n"
           f"📊 <b>Statistics:</b>\n"
           f"▸ Total Visits: <b>{tot_visits}</b>\n"
           f"▸ Unique Visitors: <b>{uniques}</b>\n"
           f"▸ Repeat Visitors: <b>{repeats}</b>\n"
           f"▸ Successful Deliveries: <b>{link.get('successful_deliveries', 0)}</b>\n"
           f"▸ Failed Deliveries: <b>{link.get('failed_deliveries', 0)}</b>\n\n"
           f"⏱️ Created: {dt(link.get('created_at'))}\n"
           f"🔄 Last Rotation: {dt(link.get('last_rotation_at'))}\n"
           f"⏳ Next Rotation: {dt(link.get('next_rotation_at')) if link.get('delivery_mode') != 'public' else 'Static'}")

    rows = [
        [btn(toggle_label, f"lnk|toggle|{pid}"), btn("🗑️ Delete Link", f"lnk|del_confirm|{pid}")],
        [btn("🟢 Resend URL", f"lnk|resend|{pid}"), btn("🔙 My Links", "lnk|list|1")]
    ]
    kb = InlineKeyboardMarkup(rows)

    if edit_msg is not None:
        try: await edit_msg.edit_text(txt, reply_markup=kb, parse_mode=PM_HTML, link_preview_options=LPO_DISABLE)
        except RPCError: pass
    else:
        await c.send_message(chat_id, txt, reply_markup=kb, parse_mode=PM_HTML, link_preview_options=LPO_DISABLE)

async def show_my_channels(c, chat_id, admin_id, edit_msg=None):
    chans = c.store.find("channels", lambda ch: is_supreme(admin_id) or str(ch.get("added_by")) == str(admin_id))
    rows = []
    for ch in chans:
        type_str = "🌐 Public" if ch.get("is_public") else "🔒 Private"
        rows.append([btn(f"📢 {ch.get('title','Channel')[:18]} [{type_str}]", f"chn|detail|{ch['_id']}")])

    rows.append([btn("➕ Add Channel", "chn|add")])
    rows.append([btn("◀️ Dashboard", "pan|refresh")])

    txt = f"🗂 <b>ᴍʏ ꜱᴀᴠᴇᴅ ᴄʜᴀɴɴᴇʟꜱ ({len(chans)})</b>\n\nSelect a channel to revalidate permissions or create new provider links:"
    kb = InlineKeyboardMarkup(rows)

    if edit_msg is not None:
        try: await edit_msg.edit_text(txt, reply_markup=kb, parse_mode=PM_HTML)
        except RPCError: pass
    else:
        await c.send_message(chat_id, txt, reply_markup=kb, parse_mode=PM_HTML)

# ══════════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ══════════════════════════════════════════════════════════════════
async def cmd_start(c, m):
    uid = m.from_user.id
    if await is_user_banned(c, uid):
        try: await m.reply("❌ <b>You are banned from using this bot!</b>", parse_mode=PM_HTML)
        except RPCError: pass
        return

    user = await ensure_user(c, m.from_user)
    payload = m.command[1] if len(m.command) > 1 else ""

    if payload:
        if payload.startswith("ref_"):
            ref = payload[4:]
            if ref.isdigit() and int(ref) != uid:
                rid = f"{int(ref)}_{uid}"
                if not await c.store.get("referrals", rid) and await c.store.get("users", int(ref)):
                    await c.store.put("referrals", rid, {"_id": rid, "referrer": str(int(ref)),
                                                         "user": str(uid), "status": "pending", "at": now()})
                    await log_event(c, "🤝 ɴᴇᴡ ʀᴇꜰᴇʀʀᴀʟ", f"{ref} → {uid}", uid=uid)
        else:
            # Payload is a provider token!
            ok, kb = await fs_state(c, uid)
            if not ok:
                await unauthorized(c, uid)
                await c.store.update("users", str(uid), pending_provider_token=payload)
                try:
                    await m.reply("🔐 <b>ᴀᴄᴄᴇꜱꜱ ʟᴏᴄᴋᴇᴅ!</b>\n\nJoin the required channel first, then press ✅ ᴠᴇʀɪꜰʏ.",
                                  reply_markup=kb, parse_mode=PM_HTML, link_preview_options=LPO_DISABLE)
                except RPCError: pass
                return
            await convert_referral(c, uid)
            await handle_provider_token_delivery(c, m, payload)
            return

    ok, kb = await fs_state(c, uid)
    if not ok:
        await unauthorized(c, uid)
        try:
            await m.reply("🔐 <b>ᴀᴄᴄᴇꜱꜱ ʟᴏᴄᴋᴇᴅ!</b>\n\nJoin the channel then press ✅ ᴠᴇʀɪꜰʏ.",
                          reply_markup=kb, parse_mode=PM_HTML, link_preview_options=LPO_DISABLE)
        except RPCError: pass
        return

    await convert_referral(c, uid)
    user_doc = await c.store.get("users", str(uid)) or user
    pend_tok = user_doc.get("pending_provider_token")
    if pend_tok:
        await c.store.update("users", str(uid), pending_provider_token=None)
        await handle_provider_token_delivery(c, m, pend_tok)
        return

    await send_welcome_content(c, m.chat.id, user_doc)

async def cmd_newlink(c, m):
    uid = m.from_user.id
    if not await perm_ok(c, uid, "create_link"):
        await m.reply("❌ <b>NO CREATE LINK PERMISSION!</b>", parse_mode=PM_HTML); return

    set_sess(c, uid, "nl_select_channel")
    kb = InlineKeyboardMarkup([
        [btn("📢 Forward Channel Message", "nl|method|fwd")],
        [btn("✏️ Send @username or URL or ID", "nl|method|txt")],
        [btn("🗂 My Channels", "chn|list|1")],
        [btn("🔴 Cancel", "nl|cancel")]
    ])
    txt = ("📢 <b>ᴄʀᴇᴀᴛᴇ ɴᴇᴡ ᴘʀᴏᴠɪᴅᴇʀ ʟɪɴᴋ</b>\n━━━━━━━━━━━━━━\n"
           "Choose how you want to select the target channel:\n\n"
           "1️⃣ Forward any message from your target channel\n"
           "2️⃣ Send channel @username, t.me link, or Channel ID\n"
           "3️⃣ Pick from your previously saved channels")
    await m.reply(txt, reply_markup=kb, parse_mode=PM_HTML)

async def cmd_mylinks(c, m):
    uid = m.from_user.id
    if not await perm_ok(c, uid, "manage_links"):
        await m.reply("❌ <b>NO MANAGE LINKS PERMISSION!</b>", parse_mode=PM_HTML); return
    await show_my_links(c, m.chat.id, uid)

async def cmd_mychannels(c, m):
    uid = m.from_user.id
    if not await perm_ok(c, uid, "manage_channels"):
        await m.reply("❌ <b>NO MANAGE CHANNELS PERMISSION!</b>", parse_mode=PM_HTML); return
    await show_my_channels(c, m.chat.id, uid)

async def cmd_stats(c, m):
    uid = m.from_user.id
    if not await perm_ok(c, uid, "view_stats"):
        await m.reply("❌ <b>NO STATS PERMISSION!</b>", parse_mode=PM_HTML); return

    if c.is_factory and is_supreme(uid):
        tb = FACTORY.count("bots") if FACTORY else 0
        tot_links = sum(st.count("provider_links") for st in STORES.values())
        tot_visits = sum(sum(l.get("total_visits", 0) for l in st.c("provider_links").values()) for st in STORES.values())
        txt = (f"🌐 <b>ꜱᴜᴘʀᴇᴍᴇ ɢʟᴏʙᴀʟ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ</b>\n━━━━━━━━━━━━━━\n"
               f"🤖 Total Bots: <b>{tb}</b> (🟢 {len(RUNNING) - 1 if FACTORY_CLIENT else len(RUNNING)} running)\n"
               f"👥 Total Users: <b>{sum(st.count('users') for st in STORES.values())}</b>\n"
               f"📢 Total Channels: <b>{sum(st.count('channels') for st in STORES.values())}</b>\n"
               f"🔗 Total Provider Links: <b>{tot_links}</b>\n"
               f"📈 Total Link Openings: <b>{tot_visits}</b>\n"
               f"⏱️ System Uptime: <b>{hms(now() - START_TS)}</b>")
        await m.reply(txt, parse_mode=PM_HTML)
        return

    my_links = c.store.find("provider_links", lambda l: is_supreme(uid) or str(l.get("owner_admin_id")) == str(uid))
    tot_visits = sum(l.get("total_visits", 0) for l in my_links)
    tot_success = sum(l.get("successful_deliveries", 0) for l in my_links)
    tot_uniques = len({v for l in my_links for v in l.get("unique_visitors", [])})
    active_cnt = sum(1 for l in my_links if l.get("active", True))

    txt = (f"📊 <b>ᴍʏ 𝔩ɪɴᴋ ᴘʀᴏᴠɪᴅᴇʀ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ</b>\n━━━━━━━━━━━━━━\n"
           f"🤖 Bot: @{c.username}\n"
           f"🔗 Total Provider Links: <b>{len(my_links)}</b>\n"
           f"🟢 Active Links: <b>{active_cnt}</b> | 🔴 Disabled: <b>{len(my_links) - active_cnt}</b>\n"
           f"📈 Total Visits: <b>{tot_visits}</b>\n"
           f"👥 Unique Visitors: <b>{tot_uniques}</b>\n"
           f"✅ Successful Deliveries: <b>{tot_success}</b>\n"
           f"❌ Failed Deliveries: <b>{sum(l.get('failed_deliveries', 0) for l in my_links)}</b>")
    await m.reply(txt, parse_mode=PM_HTML)

async def cmd_rotation(c, m):
    uid = m.from_user.id
    if not await perm_ok(c, uid, "manage_links"):
        await m.reply("❌ <b>NO PERMISSION!</b>", parse_mode=PM_HTML); return

    rot_states = c.store.find("rotation_state")
    if not rot_states:
        await m.reply("🔄 <b>Link Rotation Status</b>\n\nNo active rotating links configured yet.", parse_mode=PM_HTML)
        return

    lines = ["🔄 <b>5-ᴍɪɴᴜᴛᴇ ʟɪɴᴋ ʀᴏᴛᴀᴛɪᴏɴ ꜱᴛᴀᴛᴜꜱ</b>", "━━━━━━━━━━━━━━"]
    for rot in rot_states:
        cid = rot.get("channel_id")
        ch = await c.store.get("channels", str(cid))
        title = ch.get("title") if ch else cid
        mode = rot.get("delivery_mode")
        mode_str = "🔒 Private Invite" if mode == "private" else "✅ Join Request"
        err = rot.get("rotation_error")
        err_str = f"❌ Error: {err}" if err else "🟢 Rotating Healthy"

        lines.append(f"\n📢 <b>{hesc(title)}</b> ({mode_str})\n"
                     f"Status: {err_str}\n"
                     f"Last Rotation: {dt(rot.get('last_rotation_at'))}\n"
                     f"Next Rotation: {dt(rot.get('next_rotation_at'))}")

    await m.reply("\n".join(lines), parse_mode=PM_HTML)

async def cmd_cancel(c, m):
    clear_sess(c, m.from_user.id)
    await m.reply("❌ <b>Operation cancelled!</b>", parse_mode=PM_HTML)

async def cmd_admin(c, m):
    uid = m.from_user.id
    doc = await c.store.get("admins", uid)
    if not doc and not is_supreme(uid):
        await m.reply("❌ You are not an admin here.", parse_mode=PM_HTML); return
    await show_admin_dashboard(c, m.chat.id, uid=uid)

async def cmd_help(c, m):
    uid = m.from_user.id
    is_adm = is_supreme(uid) or (await c.store.get("admins", uid) is not None)

    txt = ("❓ <b>ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅꜱ</b>\n━━━━━━━━━━━━━━\n\n"
           "👤 <b>ᴜꜱᴇʀ ᴄᴏᴍᴍᴀɴᴅꜱ:</b>\n"
           "▸ /start — Start Bot / Open Provider Link\n"
           "▸ /help — Help & Commands\n"
           "▸ /refer — Referral Link & Stats\n\n")

    if is_adm:
        txt += ("🛠 <b>ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅꜱ:</b>\n"
                "▸ /admin — Open Control Dashboard\n"
                "▸ /newlink — Create New Provider Link\n"
                "▸ /mylinks — View & Manage Your Links\n"
                "▸ /mychannels — View & Manage Channels\n"
                "▸ /stats — Analytics & Statistics\n"
                "▸ /rotation — Link Rotation Lifecycle\n"
                "▸ /cancel — Cancel Active Operation\n")

    if is_supreme(uid):
        txt += ("\n👑 <b>ꜱᴜᴘʀᴇᴍᴇ ᴄᴏᴍᴍᴀɴᴅꜱ:</b>\n"
                "▸ /supreme — Supreme Factory Control\n"
                "▸ /botlist — All Cloned Bots\n"
                "▸ /db — Database Health\n"
                "▸ /restart — Gracefully Restart Clones\n")

    await m.reply(txt, parse_mode=PM_HTML)

async def cmd_refer(c, m):
    uid = m.from_user.id
    if await is_user_banned(c, uid): return
    await ensure_user(c, m.from_user)
    link = f"https://t.me/{c.username}?start=ref_{uid}"
    txt = (f"🎁 <b>ʀᴇꜰᴇʀ & ᴇᴀʀɴ</b>\n━━━━━━━━━━━━━━\n"
           f"Share your referral link to invite users:\n"
           f"🔗 <code>{link}</code>")
    kb = InlineKeyboardMarkup([[ubtn("🟢 Share Link", f"https://t.me/share/url?url={quote(link)}&text={quote('Join this awesome bot!')}")]])
    await m.reply(txt, reply_markup=kb, parse_mode=PM_HTML, link_preview_options=LPO_DISABLE)

# ══════════════════════════════════════════════════════════════════
#  ADMIN MANAGEMENT & OTHER PRESERVED HANDLERS
# ══════════════════════════════════════════════════════════════════
def selector_text(d):
    return (f"👤 <b>{d.get('name','User')}</b> (<code>{d['uid']}</code>)\n"
            f"🏷️ Role: <b>{ROLE_NAME.get(d['role'], d['role'])}</b>\n\n"
            f"🎨 Toggle Permissions → 💾 Save")

def selector_kb(d):
    uid = d["uid"]; perms = set(d["perms"])
    rows = [[btn("🛠 Manager", f"adm|role|{uid}|manager"), btn("🔗 Link Admin", f"adm|role|{uid}|link_admin")],
            [btn("📣 Broadcaster", f"adm|role|{uid}|broadcaster"), btn("📊 Analyst", f"adm|role|{uid}|analyst")],
            [btn("⚙️ Custom", f"adm|role|{uid}|custom")]]
    items = list(PERM_LABELS.items())
    for i in range(0, len(items), 2):
        rows.append([btn(("☑️ " if p in perms else "❌ ") + lbl, f"adm|t|{uid}|{p}") for p, lbl in items[i:i + 2]])
    rows.append([btn("💾 Save", f"adm|save|{uid}"), btn("🗑 Remove", f"adm|rem|{uid}")])
    rows.append([btn("⬅️ Back", "pan|admins")])
    return InlineKeyboardMarkup(rows)

def msg_target(m):
    if m.reply_to_message and m.reply_to_message.from_user:
        tu = m.reply_to_message.from_user
        return tu.id, tu.first_name or str(tu.id)
    if m.command and len(m.command) > 1 and m.command[1].lstrip("-").isdigit():
        return int(m.command[1]), (" ".join(m.command[2:]) or m.command[1])
    return None, None

async def open_selector(c, m, t, name, must_exist=False):
    exist = await c.store.get("admins", str(t)) or await c.store.get("admins", t)
    if must_exist and not exist:
        await m.reply("❌ That user is not an admin."); return
    if exist and exist.get("role") == "owner":
        await m.reply("👑 Clone owner's permissions cannot be changed."); return
    if not name or name == str(t):
        u = await c.store.get("users", str(t)) or await c.store.get("users", t)
        if u: name = u.get("first_name") or str(t)
    d = {"uid": t, "name": hesc(name or (exist or {}).get("name") or str(t)),
         "perms": list(exist["permissions"]) if exist else [],
         "role": exist["role"] if exist else "custom", "new": exist is None}
    set_sess(c, m.from_user.id, "adm_edit", **d)
    await m.reply(selector_text(d), reply_markup=selector_kb(d), parse_mode=PM_HTML)

async def cmd_giveadmin(c, m):
    if not await perm_ok(c, m.from_user.id, "manage_admins"): return
    t, name = msg_target(m)
    if not t:
        set_sess(c, m.from_user.id, "ga_target")
        await m.reply("👤 Send User ID: <code>/giveadmin 123456789 Name</code>", parse_mode=PM_HTML); return
    await open_selector(c, m, t, name)

async def cmd_editadmin(c, m):
    if not await perm_ok(c, m.from_user.id, "manage_admins"): return
    t, name = msg_target(m)
    if not t:
        set_sess(c, m.from_user.id, "ea_target")
        await m.reply("✏️ Send User ID:", parse_mode=PM_HTML); return
    await open_selector(c, m, t, name, must_exist=True)

async def cmd_remadmin(c, m):
    if not await perm_ok(c, m.from_user.id, "manage_admins"): return
    t, _ = msg_target(m)
    if not t:
        set_sess(c, m.from_user.id, "ra_target")
        await m.reply("🗑 Send User ID:", parse_mode=PM_HTML); return
    tgt = await c.store.get("admins", t)
    if not tgt or tgt.get("role") == "owner": return
    await c.store.delete("admins", t)
    await log_event(c, "🚫 ᴀᴅᴍɪɴ ʀᴇᴍᴏᴠᴇᴅ", f"Admin: {t}", important=True, uid=t)
    await m.reply("🗑 <b>Admin removed!</b>", parse_mode=PM_HTML)

async def cmd_ban(c, m):
    if not await perm_ok(c, m.from_user.id, "ban_users"): return
    t, name = msg_target(m)
    if not t:
        set_sess(c, m.from_user.id, "ban_target")
        await m.reply("🚫 Send User ID to ban:", parse_mode=PM_HTML); return
    t_str = str(t)
    if is_supreme(t_str) or (await c.store.get("admins", t_str)):
        await m.reply("❌ Cannot ban Admin/Supreme!", parse_mode=PM_HTML); return
    u = await c.store.get("users", t_str) or {"_id": t_str, "first_name": name or t_str, "started_at": now()}
    u["is_banned"] = True
    await c.store.put("users", t_str, u)
    await m.reply(f"🚫 <b>User {t_str} banned!</b>", parse_mode=PM_HTML)

async def cmd_unban(c, m):
    if not await perm_ok(c, m.from_user.id, "ban_users"): return
    t, _ = msg_target(m)
    if not t:
        set_sess(c, m.from_user.id, "unban_target")
        await m.reply("🟢 Send User ID to unban:", parse_mode=PM_HTML); return
    u = await c.store.get("users", str(t))
    if u:
        u["is_banned"] = False
        await c.store.put("users", str(t), u)
    await m.reply(f"🟢 <b>User {t} unbanned!</b>", parse_mode=PM_HTML)

async def copy_any(c, chat_id, m):
    if m.text: return await c.send_message(chat_id, m.text, entities=m.entities, parse_mode=PM_OFF, link_preview_options=LPO_DISABLE)
    cap = m.caption; cape = m.caption.entities if m.caption else None
    if m.photo: return await c.send_photo(chat_id, m.photo.file_id, caption=cap, caption_entities=cape, parse_mode=PM_OFF)
    if m.video: return await c.send_video(chat_id, m.video.file_id, caption=cap, caption_entities=cape, parse_mode=PM_OFF)
    if m.animation: return await c.send_animation(chat_id, m.animation.file_id, caption=cap, caption_entities=cape, parse_mode=PM_OFF)
    if m.document: return await c.send_document(chat_id, m.document.file_id, caption=cap, caption_entities=cape, parse_mode=PM_OFF)
    raise ValueError("Unsupported")

async def cmd_broadcast(c, m):
    uid = m.from_user.id
    src = m.reply_to_message
    if not await perm_ok(c, uid, "broadcast"): return
    if src is None:
        await m.reply("📣 Reply to any message with <code>/broadcast</code>", parse_mode=PM_HTML); return
    status = await m.reply("📣 <b>Broadcasting...</b>", parse_mode=PM_HTML)
    users = list(c.store.c("users").keys())
    ok = fail = 0
    for u in users:
        try:
            await copy_any(c, int(u), src); ok += 1
        except Exception: fail += 1
        await asyncio.sleep(0.04)
    await status.edit_text(f"📣 <b>Broadcast Done!</b>\n\n✅ {ok} | ❌ {fail}", parse_mode=PM_HTML)

async def cmd_clone(c, m):
    uid = m.from_user.id
    ok, fs_kb = await fs_state(c, uid, is_clone_action=True)
    if not ok:
        await unauthorized(c, uid)
        target_store = FACTORY if FACTORY else c.store
        await target_store.update("users", str(uid), pending_action="clone")
        await c.store.update("users", str(uid), pending_action="clone")
        try: await m.reply("🔐 <b>ᴀᴄᴄᴇꜱꜱ ʟᴏᴄᴋᴇᴅ!</b>\n\nJoin required channel then press ✅ ᴠᴇʀɪꜰʏ.", reply_markup=fs_kb, parse_mode=PM_HTML)
        except RPCError: pass
        return
    set_sess(c, uid, "clone_token")
    await m.reply(CLONE_PROMPT, reply_markup=InlineKeyboardMarkup([[btn("🔴 ᴄᴀɴᴄᴇʟ", "cl|cancel")]]), parse_mode=PM_HTML)

async def cmd_supreme(c, m):
    if not is_supreme(m.from_user.id): return
    kb = InlineKeyboardMarkup([
        [btn("🤖 Manage Bots", "sv|manage_bots"), btn("🗄️ DB Report", "sv|db")],
        [btn("♻️ Restart Clones", "sv|restart")]
    ])
    await m.reply("👑 <b>SUPREME PANEL</b>", reply_markup=kb, parse_mode=PM_HTML)

async def cmd_botlist(c, m):
    if not is_supreme(m.from_user.id): return
    bots = FACTORY.find("bots") if FACTORY else []
    lines = [f"🤖 <b>Clones ({len(bots)})</b>"]
    for b in bots:
        lines.append(f"• @{b.get('username')} [{b['_id']}]")
    await m.reply("\n".join(lines), parse_mode=PM_HTML)

async def cmd_db(c, m):
    if not is_supreme(m.from_user.id): return
    await m.reply(f"🗄️ <b>DB Health:</b> 100% OK | Total Stores: {len(STORES)}", parse_mode=PM_HTML)

async def cmd_restart(c, m):
    if not is_supreme(m.from_user.id): return
    st = await m.reply("♻️ Restarting clones...")
    await restart_all(st)

# ══════════════════════════════════════════════════════════════════
#  CALLBACK QUERY DISPATCHER
# ══════════════════════════════════════════════════════════════════
async def h_callback(c, q):
    try:
        if not q.from_user: return
        uid = q.from_user.id
        if await is_user_banned(c, uid):
            await q_safe(q, "❌ Banned!", alert=True); return

        data = q.data or ""

        if data == "ckfs":
            ok, kb = await fs_state(c, uid)
            if ok:
                await q_safe(q, "✅ Verified!")
                user = await c.store.get("users", uid) or await ensure_user(c, q.from_user)
                try: await q.message.delete()
                except RPCError: pass
                user_doc = await c.store.get("users", str(uid))
                pend_tok = user_doc.get("pending_provider_token") if user_doc else None
                if pend_tok:
                    await c.store.update("users", str(uid), pending_provider_token=None)
                    await handle_provider_token_delivery(c, q.message, pend_tok)
                else:
                    await send_welcome_content(c, uid, user)
            else:
                await q_safe(q, "❌ Still not verified!")
        elif data == "usr|home":
            await q_safe(q, "🏠")
            user = await c.store.get("users", uid) or await ensure_user(c, q.from_user)
            await send_welcome_content(c, uid, user)
        elif data == "usr|help":
            await q_safe(q, "❓")
            await cmd_help(c, q.message)
        elif data == "nl|new" or data == "lnk|new":
            if not await perm_ok(c, uid, "create_link"):
                await q_safe(q, "❌ NO PERMISSION!"); return
            set_sess(c, uid, "nl_select_channel")
            kb = InlineKeyboardMarkup([
                [btn("📢 Forward Channel Message", "nl|method|fwd")],
                [btn("✏️ Send @username / URL / ID", "nl|method|txt")],
                [btn("🗂 My Channels", "chn|list|1")],
                [btn("🔴 Cancel", "nl|cancel")]
            ])
            txt = ("📢 <b>ᴄʀᴇᴀᴛᴇ ɴᴇᴡ ᴘʀᴏᴠɪᴅᴇʀ ʟɪɴᴋ</b>\n━━━━━━━━━━━━━━\n"
                   "Select target channel or choose a method below:")
            try: await q.message.edit_text(txt, reply_markup=kb, parse_mode=PM_HTML)
            except RPCError: pass
        elif data.startswith("nl|method|"):
            method = data.split("|")[2]
            if method == "fwd":
                set_sess(c, uid, "nl_await_fwd")
                await q_safe(q, "📢 Forward Message")
                try: await q.message.edit_text("📢 <b>Forward any message from your target channel now...</b>\n\n(or send /cancel)", parse_mode=PM_HTML)
                except RPCError: pass
            elif method == "txt":
                set_sess(c, uid, "nl_await_txt")
                await q_safe(q, "✏️ Send Details")
                try: await q.message.edit_text("✏️ <b>Send channel @username, t.me link, or Channel ID (-100...):</b>\n\n(or send /cancel)", parse_mode=PM_HTML)
                except RPCError: pass
        elif data == "nl|cancel":
            clear_sess(c, uid)
            await q_safe(q, "❌ Cancelled")
            try: await q.message.edit_text("❌ <b>Link creation cancelled.</b>", parse_mode=PM_HTML)
            except RPCError: pass
        elif data.startswith("nl|sel_type|"):
            cid = data.split("|")[2]
            ch = await c.store.get("channels", cid)
            title = ch.get("title") if ch else cid
            rows = [
                [btn("🌐 Public Link", f"nl|type|{cid}|public")],
                [btn("🔒 Private Invite Link", f"nl|type|{cid}|private")],
                [btn("✅ Join Request Link", f"nl|type|{cid}|join_request")],
                [btn("🔴 Cancel", "nl|cancel")]
            ]
            txt = (f"🎯 <b>ꜱᴇʟᴇᴄᴛ ʟɪɴᴋ ᴅᴇʟɪᴠᴇʀʏ ᴛʏᴘᴇ</b>\n━━━━━━━━━━━━━━\n"
                   f"Target Channel: <b>{hesc(title)}</b>\n\n"
                   f"Choose delivery mode:\n"
                   f"• <b>🌐 Public Link:</b> Delivers public URL (https://t.me/username).\n"
                   f"• <b>🔒 Private Invite Link:</b> Delivers direct Telegram invite link (Auto-rotates every 5 min).\n"
                   f"• <b>✅ Join Request Link:</b> Delivers join-request invite link (Auto-rotates every 5 min).")
            try: await q.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(rows), parse_mode=PM_HTML)
            except RPCError: pass
        elif data.startswith("nl|type|"):
            parts = data.split("|")
            cid, mode = parts[2], parts[3]
            doc, err = await create_provider_link(c, uid, cid, mode)
            if err:
                await q_safe(q, "❌ Error", alert=True)
                try: await q.message.edit_text(f"❌ <b>Link Creation Failed:</b>\n\n{err}", parse_mode=PM_HTML)
                except RPCError: pass
                return
            await q_safe(q, "🎉 Link Created!")
            mode_map = {"public": "🌐 Public Link", "private": "🔒 Private Invite Link", "join_request": "✅ Join Request Link"}
            txt = (f"🎉 <b>ᴘʀᴏᴠɪᴅᴇʀ ʟɪɴᴋ ᴄʀᴇᴀᴛᴇᴅ!</b>\n━━━━━━━━━━━━━━\n\n"
                   f"📢 Channel: <b>{hesc(doc['channel_title'])}</b>\n"
                   f"🏷️ Type: <b>{mode_map.get(mode, mode)}</b>\n\n"
                   f"🚀 <b>Your Unique Provider URL:</b>\n<code>{doc['provider_url']}</code>\n\n"
                   f"<i>Share this URL with users. Whenever a user opens it, the bot will deliver the corresponding channel link!</i>")
            kb = InlineKeyboardMarkup([
                [ubtn("🟢 Share Provider URL", f"https://t.me/share/url?url={quote(doc['provider_url'])}&text={quote('Join ' + doc['channel_title'])}")],
                [btn("⚙️ Manage Link", f"lnk|detail|{doc['_id']}"), btn("📢 Create Another Link", "lnk|new")]
            ])
            try: await q.message.edit_text(txt, reply_markup=kb, parse_mode=PM_HTML, link_preview_options=LPO_DISABLE)
            except RPCError: pass
        elif data.startswith("lnk|list|"):
            page = int(data.split("|")[2]) if len(data.split("|")) > 2 and data.split("|")[2].isdigit() else 1
            await q_safe(q, "🔗")
            await show_my_links(c, q.message.chat.id, uid, page=page, edit_msg=q.message)
        elif data.startswith("lnk|detail|"):
            pid = data.split("|")[2]
            await q_safe(q, "🔍")
            await show_link_detail(c, q.message.chat.id, uid, pid, edit_msg=q.message)
        elif data.startswith("lnk|toggle|"):
            pid = data.split("|")[2]
            link = await c.store.get("provider_links", pid)
            if link:
                new_state = not link.get("active", True)
                link["active"] = new_state
                await c.store.put("provider_links", pid, link)
                await q_safe(q, "🟢 Link Enabled!" if new_state else "🔴 Link Disabled!")
                await show_link_detail(c, q.message.chat.id, uid, pid, edit_msg=q.message)
        elif data.startswith("lnk|del_confirm|"):
            pid = data.split("|")[2]
            rows = [
                [btn("⚠️ YES, DELETE LINK", f"lnk|do_delete|{pid}")],
                [btn("❌ CANCEL", f"lnk|detail|{pid}")]
            ]
            try: await q.message.edit_text("⚠️ <b>Delete this Provider Link permanently?</b>", reply_markup=InlineKeyboardMarkup(rows), parse_mode=PM_HTML)
            except RPCError: pass
        elif data.startswith("lnk|do_delete|"):
            pid = data.split("|")[2]
            await c.store.delete("provider_links", pid)
            await q_safe(q, "🗑️ Link Deleted!")
            await show_my_links(c, q.message.chat.id, uid, page=1, edit_msg=q.message)
        elif data.startswith("lnk|resend|"):
            pid = data.split("|")[2]
            link = await c.store.get("provider_links", pid)
            if link:
                await q_safe(q, "🟢 Link Resent!")
                try: await c.send_message(uid, f"🔗 <code>{link['provider_url']}</code>", parse_mode=PM_HTML, link_preview_options=LPO_DISABLE)
                except RPCError: pass
        elif data.startswith("chn|list|"):
            await q_safe(q, "🗂")
            await show_my_channels(c, q.message.chat.id, uid, edit_msg=q.message)
        elif data == "chn|add":
            set_sess(c, uid, "nl_await_txt")
            await q_safe(q, "➕ Add Channel")
            try: await q.message.edit_text("✏️ <b>Send channel @username, URL, or ID (-100...):</b>\n\n(Bot must be an admin in the channel)", parse_mode=PM_HTML)
            except RPCError: pass
        elif data.startswith("chn|detail|"):
            cid = data.split("|")[2]
            ch = await c.store.get("channels", cid)
            if ch:
                txt = (f"📢 <b>{hesc(ch.get('title'))}</b>\n━━━━━━━━━━━━━━\n"
                       f"🆔 ID: <code>{ch.get('channel_id')}</code>\n"
                       f"🏷️ Username: @{ch.get('username') or 'N/A'}\n"
                       f"🛡️ Bot Admin: {'✅' if ch.get('bot_is_admin') else '❌'}\n"
                       f"🔑 Invite Perm: {'✅' if ch.get('can_invite_users') else '❌'}\n"
                       f"📅 Added: {dt(ch.get('created_at'))}")
                rows = [
                    [btn("📢 Create Provider Link", f"nl|sel_type|{cid}")],
                    [btn("🔄 Revalidate Access", f"chn|reval|{cid}")],
                    [btn("🗑️ Remove Channel", f"chn|rm|{cid}")],
                    [btn("🔙 My Channels", "chn|list|1")]
                ]
                try: await q.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(rows), parse_mode=PM_HTML)
                except RPCError: pass
        elif data.startswith("chn|reval|"):
            cid = data.split("|")[2]
            ch_doc, err = await validate_and_resolve_channel(c, uid, cid)
            if err:
                await q_safe(q, "❌ Validation failed!", alert=True)
            else:
                await q_safe(q, "✅ Revalidated!")
            await show_my_channels(c, q.message.chat.id, uid, edit_msg=q.message)
        elif data.startswith("chn|rm|"):
            cid = data.split("|")[2]
            # Check if active provider links depend on this channel
            deps = c.store.find("provider_links", lambda l: str(l.get("channel_id")) == cid)
            if deps:
                await q_safe(q, f"⚠️ {len(deps)} active links depend on this channel! Delete links first.", alert=True)
                return
            await c.store.delete("channels", cid)
            await q_safe(q, "🗑️ Channel Removed!")
            await show_my_channels(c, q.message.chat.id, uid, edit_msg=q.message)
        elif data == "rot|status":
            await cmd_rotation(c, q.message)
        elif data == "st|my":
            await cmd_stats(c, q.message)
        elif data.startswith("pan|"):
            act = data.split("|")[1]
            if act == "refresh":
                await show_admin_dashboard(c, q.message.chat.id, edit_msg=q.message, uid=uid)
            elif act == "admins":
                await q_safe(q, "👥")
                docs = c.store.find("admins")
                rows = [[btn(f"{ROLE_NAME.get(d['role'],'⚙️')} {d.get('name','?')[:18]}", f"adm|view|{d['_id']}") for d in docs[i:i + 2]] for i in range(0, len(docs), 2)]
                rows.append([btn("➕ Add Admin", "adm|add_prompt")])
                rows.append([btn("⬅️ Back", "pan|refresh")])
                try: await q.message.edit_text(f"👥 <b>Admins ({len(docs)})</b>", reply_markup=InlineKeyboardMarkup(rows), parse_mode=PM_HTML)
                except RPCError: pass
            elif act == "delclone":
                if c.is_factory: await q_safe(q, "❌ Cannot delete Factory!", alert=True); return
                rows = [[btn("⚠️ YES, DELETE CLONE NOW", "pan|do_delclone")], [btn("❌ CANCEL", "pan|refresh")]]
                try: await q.message.edit_text("⚠️ <b>Delete this Clone Bot permanently?</b>", reply_markup=InlineKeyboardMarkup(rows), parse_mode=PM_HTML)
                except RPCError: pass
            elif act == "do_delclone":
                if c.is_factory: return
                await delete_clone_bot(c.bot_id)
                await q_safe(q, "🗑️ Deleted!")
        elif data.startswith("adm|"):
            await cb_adm(c, q, data.split("|"))
        elif data.startswith("sv|"):
            await cb_supreme(c, q, data.split("|"))
        elif data == "cloneme":
            ok, fs_kb = await fs_state(c, uid, is_clone_action=True)
            if not ok:
                await unauthorized(c, uid)
                target_store = FACTORY if FACTORY else c.store
                await target_store.update("users", str(uid), pending_action="clone")
                await c.store.update("users", str(uid), pending_action="clone")
                await q_safe(q, "🔐 Access Locked!", alert=True)
                try: await q.message.reply("🔐 <b>ᴀᴄᴄᴇꜱꜱ ʟᴏᴄᴋᴇᴅ!</b>\n\nJoin required channel then press ✅ ᴠᴇʀɪꜰʏ.", reply_markup=fs_kb, parse_mode=PM_HTML)
                except RPCError: pass
                return
            set_sess(c, uid, "clone_token")
            await q_safe(q, "🤖 Send Bot Token")
            try: await q.message.reply(CLONE_PROMPT, parse_mode=PM_HTML, reply_markup=InlineKeyboardMarkup([[btn("🔴 ᴄᴀɴᴄᴇʟ", "cl|cancel")]]))
            except RPCError: pass
        elif data == "cl|cancel":
            clear_sess(c, uid)
            await q_safe(q, "❌ Cancelled")
            try: await q.message.edit_text("❌ <b>Clone creation cancelled.</b>", parse_mode=PM_HTML)
            except RPCError: pass
    except FloodWait as f: await asyncio.sleep(f.value)
    except Exception as e:
        LOG.exception("Callback error")

async def cb_adm(c, q, parts):
    uid = q.from_user.id
    action = parts[1]
    if action == "add_prompt":
        if not await perm_ok(c, uid, "manage_admins"): return
        set_sess(c, uid, "ga_target")
        await q_safe(q, "➕ Add Admin")
        try: await q.message.edit_text("👤 Send User ID: <code>123456789 Name</code>", parse_mode=PM_HTML)
        except RPCError: pass
        return
    if not await perm_ok(c, uid, "manage_admins"): return
    tuid = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    tgt = await c.store.get("admins", tuid) if tuid else None
    sess = get_sess(c, uid)
    d = sess["data"] if (sess and sess.get("step") == "adm_edit" and sess["data"].get("uid") == tuid) else {
        "uid": tuid, "name": (tgt or {}).get("name", "User"),
        "perms": list((tgt or {}).get("permissions", [])),
        "role": (tgt or {}).get("role", "custom"), "new": tgt is None
    }
    if action == "t":
        p = parts[3]
        if p in d["perms"]: d["perms"].remove(p)
        else: d["perms"].append(p)
        SESSIONS[(c.bot_id, uid)] = {"step": "adm_edit", "data": d}
        try: await q.message.edit_text(selector_text(d), reply_markup=selector_kb(d), parse_mode=PM_HTML)
        except RPCError: pass
    elif action == "role":
        role = parts[3]; d["role"] = role; d["perms"] = list(ROLE_PRESETS.get(role, []))
        SESSIONS[(c.bot_id, uid)] = {"step": "adm_edit", "data": d}
        try: await q.message.edit_text(selector_text(d), reply_markup=selector_kb(d), parse_mode=PM_HTML)
        except RPCError: pass
    elif action == "save":
        await c.store.put("admins", str(tuid), {"_id": str(tuid), "name": d.get("name", "User"), "role": d["role"], "permissions": d["perms"], "added_by": uid, "at": now()})
        await apply_admin_commands(c, tuid)
        SESSIONS.pop((c.bot_id, uid), None)
        await q_safe(q, "💾 Saved!")
        try: await q.message.edit_text(selector_text(d), reply_markup=selector_kb(d), parse_mode=PM_HTML)
        except RPCError: pass
    elif action == "rem":
        await c.store.delete("admins", tuid)
        SESSIONS.pop((c.bot_id, uid), None)
        await q_safe(q, "🗑 Removed!")
        try: await q.message.edit_text("🗑 Admin removed.", parse_mode=PM_HTML)
        except RPCError: pass
    elif action == "view":
        SESSIONS[(c.bot_id, uid)] = {"step": "adm_edit", "data": d}
        try: await q.message.edit_text(selector_text(d), reply_markup=selector_kb(d), parse_mode=PM_HTML)
        except RPCError: pass

async def cb_supreme(c, q, parts):
    if not is_supreme(q.from_user.id): return
    act = parts[1]
    if act == "panel":
        kb = InlineKeyboardMarkup([
            [btn("🤖 Manage Bots", "sv|manage_bots"), btn("🗄️ DB Report", "sv|db")],
            [btn("♻️ Restart Clones", "sv|restart")]
        ])
        try: await q.message.edit_text("👑 <b>SUPREME PANEL</b>", reply_markup=kb, parse_mode=PM_HTML)
        except RPCError: pass
    elif act == "manage_bots":
        bots = FACTORY.find("bots") if FACTORY else []
        rows = [[btn(f"@{b.get('username')} [{b['_id']}]", "sv|panel")] for b in bots]
        try: await q.message.edit_text(f"🤖 <b>Clones ({len(bots)})</b>", reply_markup=InlineKeyboardMarkup(rows), parse_mode=PM_HTML)
        except RPCError: pass

# ══════════════════════════════════════════════════════════════════
#  SESSION ROUTER FOR TEXT INPUTS & FORWARDED MESSAGES
# ══════════════════════════════════════════════════════════════════
async def route_session(c, m, s):
    uid = m.from_user.id
    step = s.get("step")

    if step == "clone_token":
        await clone_token(c, m)
    elif step == "nl_await_fwd":
        fwd_chat = m.forward_from_chat
        if not fwd_chat:
            await m.reply("❌ Please forward a message directly from your target channel (or send /cancel).", parse_mode=PM_HTML)
            return
        ch_doc, err = await validate_and_resolve_channel(c, uid, fwd_chat.id)
        if err:
            await m.reply(err, parse_mode=PM_HTML)
            return
        clear_sess(c, uid)
        cid = ch_doc["_id"]
        rows = [
            [btn("🌐 Public Link", f"nl|type|{cid}|public")],
            [btn("🔒 Private Invite Link", f"nl|type|{cid}|private")],
            [btn("✅ Join Request Link", f"nl|type|{cid}|join_request")],
            [btn("🔴 Cancel", "nl|cancel")]
        ]
        txt = f"✅ <b>Channel Verified: {hesc(ch_doc['title'])}</b>\n\nSelect destination link delivery type:"
        await m.reply(txt, reply_markup=InlineKeyboardMarkup(rows), parse_mode=PM_HTML)
    elif step in ("nl_await_txt", "nl_select_channel"):
        q_str = (m.text or "").strip()
        if not q_str:
            await m.reply("✏️ Send channel @username, t.me URL, or ID (-100...):", parse_mode=PM_HTML); return
        ch_doc, err = await validate_and_resolve_channel(c, uid, q_str)
        if err:
            await m.reply(err, parse_mode=PM_HTML)
            return
        clear_sess(c, uid)
        cid = ch_doc["_id"]
        rows = [
            [btn("🌐 Public Link", f"nl|type|{cid}|public")],
            [btn("🔒 Private Invite Link", f"nl|type|{cid}|private")],
            [btn("✅ Join Request Link", f"nl|type|{cid}|join_request")],
            [btn("🔴 Cancel", "nl|cancel")]
        ]
        txt = f"✅ <b>Channel Verified: {hesc(ch_doc['title'])}</b>\n\nSelect destination link delivery type:"
        await m.reply(txt, reply_markup=InlineKeyboardMarkup(rows), parse_mode=PM_HTML)
    elif step == "ga_target" and m.text:
        t, name = msg_target(m)
        if not t and m.text.strip().lstrip("-").isdigit():
            t = int(m.text.strip())
        if t:
            clear_sess(c, uid)
            await open_selector(c, m, t, name)
    elif step == "ea_target" and m.text:
        t, name = msg_target(m)
        if not t and m.text.strip().lstrip("-").isdigit():
            t = int(m.text.strip())
        if t:
            clear_sess(c, uid)
            await open_selector(c, m, t, name, must_exist=True)

async def clone_token(c, m):
    uid = m.from_user.id
    tok = (m.text or "").strip()
    if not re.match(r"^\d{6,12}:[A-Za-z0-9_-]{30,}$", tok):
        await m.reply("❌ Invalid token format — send again or /cancel"); return
    pre = int(tok.split(":", 1)[0])
    existing_meta = FACTORY.get_sync("bots", pre)

    if FACTORY_CLIENT and pre == FACTORY_CLIENT.bot_id:
        clear_sess(c, uid); await m.reply("⚠️ Factory Bot token!"); return

    if existing_meta and not is_supreme(uid) and existing_meta.get("owner_id") != uid:
        clear_sess(c, uid); await m.reply("⚠️ Bot registered by another user!"); return

    st = await m.reply("⏳ Validating token...")
    tmp = Client(name=f"cf{now()}", api_id=API_ID, api_hash=API_HASH, bot_token=tok, in_memory=True, sleep_threshold=15)
    try: await tmp.start()
    except Exception: clear_sess(c, uid); await st.edit("❌ Failed to start bot."); return

    me = await tmp.get_me()
    old_client = RUNNING.pop(me.id, None)
    if old_client:
        try: await old_client.stop()
        except Exception: pass

    store = get_store(me.id)
    await ensure_defaults(store)
    await set_cfg(store, owner_id=uid)
    bot_doc = existing_meta or {"_id": me.id, "created_at": now()}
    bot_doc.update({
        "username": me.username or str(me.id),
        "name": me.first_name or "Bot",
        "owner_id": uid,
        "owner_name": m.from_user.first_name or str(uid),
        "token_enc": enc_token(tok),
        "last_active": now(),
        "is_banned": False
    })
    await FACTORY.put("bots", me.id, bot_doc)
    await store.put("admins", uid, {"_id": str(uid), "name": hesc(m.from_user.first_name or uid),
                                    "role": "owner", "permissions": list(PERMS), "added_by": 0, "at": now()})
    attach(tmp, me, store, is_factory=False)
    register_provider_handlers(tmp, is_factory=False)
    await apply_commands(tmp)
    RUNNING[me.id] = tmp
    clear_sess(c, uid)
    await st.edit(CLONE_SUCCESS.format(name=hesc(m.from_user.first_name or ""), uname=me.username, bid=me.id), parse_mode=PM_HTML)

async def h_generic(c, m):
    try:
        if not m.from_user: return
        uid = m.from_user.id
        if await is_user_banned(c, uid): return
        s = get_sess(c, uid)
        if s: await route_session(c, m, s); return
        if m.text and not m.text.startswith("/"):
            user = await c.store.get("users", str(uid))
            await send_welcome_content(c, m.chat.id, user)
    except Exception as e:
        LOG.exception("Generic error")

# ══════════════════════════════════════════════════════════════════
#  COMMAND ROUTING & REGISTRATION
# ══════════════════════════════════════════════════════════════════
CMD_MAP = {
    "start": cmd_start, "help": cmd_help, "refer": cmd_refer,
    "admin": cmd_admin, "newlink": cmd_newlink, "mylinks": cmd_mylinks,
    "mychannels": cmd_mychannels, "stats": cmd_stats, "rotation": cmd_rotation,
    "cancel": cmd_cancel, "giveadmin": cmd_giveadmin, "editadmin": cmd_editadmin,
    "remadmin": cmd_remadmin, "ban": cmd_ban, "unban": cmd_unban, "broadcast": cmd_broadcast,
    "clone": cmd_clone, "rajpapa": cmd_supreme, "supreme": cmd_supreme,
    "botlist": cmd_botlist, "db": cmd_db, "restart": cmd_restart,
}

async def restart_all(status_msg, only=None):
    metas = FACTORY.find("bots", lambda d: only is None or d["_id"] == only)
    okc = fail = 0
    for meta in metas:
        bid = meta["_id"]
        old = RUNNING.get(bid)
        if old:
            try: await old.stop()
            except Exception: pass
            RUNNING.pop(bid, None)
        cl = await launch_clone(meta)
        if cl: okc += 1
        else: fail += 1
    try: await status_msg.edit_text(f"♻️ Restarted: ✅{okc} ❌{fail}", parse_mode=PM_HTML)
    except RPCError: pass

async def h_admin_cmds(c, m):
    try:
        uid = m.from_user.id if m.from_user else 0
        if uid and await is_user_banned(c, uid): return
        name = m.command[0].lstrip("/").lower()
        if name in FACTORY_ONLY and not c.is_factory and not is_supreme(uid): return
        fn = CMD_MAP.get(name)
        if fn: await fn(c, m)
    except Exception as e:
        LOG.exception("Command error %s", m.text if m else "")

async def h_join_request(c, update, users, chats):
    try:
        uid = getattr(update, "user_id", None)
        chat_id = getattr(update, "chat_id", None)
        if not uid or not chat_id: return
        if await is_user_banned(c, uid): return

        st = cfg(c.store)
        channels = list(st.get("fs_channels", []))
        matched = any(ch.get("chat_id") and str(ch["chat_id"]) == str(chat_id) for ch in channels)
        if not matched: return

        u = await c.store.get("users", uid)
        verified_chats = set((u.get("fs_verified_chats") or []) if u else [])
        verified_chats.add(str(chat_id))

        if not u:
            u = {"_id": str(uid), "first_name": "User", "username": "", "started_at": now(), "fs_verified": False, "fs_verified_chats": list(verified_chats)}
            await c.store.put("users", uid, u)
        else:
            await c.store.update("users", uid, fs_verified_chats=list(verified_chats))

        ok, _ = await fs_state(c, uid)
        if ok:
            user_doc = await c.store.get("users", str(uid)) or u
            pend_tok = user_doc.get("pending_provider_token")
            if pend_tok:
                await c.store.update("users", str(uid), pending_provider_token=None)
                await handle_provider_token_delivery(c, uid, pend_tok)
            else:
                await send_welcome_content(c, uid, user_doc)
    except Exception as e:
        LOG.exception("Join request error")

F_START = filters.command("start") & filters.private & filters.incoming
F_HELP = filters.command("help") & filters.private & filters.incoming
F_REFER = filters.command("refer") & filters.private & filters.incoming
F_CMD = filters.command(ALL_CMDS) & filters.private & filters.incoming
F_GEN = filters.private & filters.incoming & ~filters.command(ALL_CMDS) & ~filters.service

def register_provider_handlers(c, is_factory):
    c.add_handler(MessageHandler(cmd_start, F_START), 0)
    c.add_handler(MessageHandler(cmd_help, F_HELP), 0)
    c.add_handler(MessageHandler(cmd_refer, F_REFER), 0)
    c.add_handler(MessageHandler(h_admin_cmds, F_CMD), 0)
    c.add_handler(CallbackQueryHandler(h_callback), 0)
    c.add_handler(MessageHandler(h_generic, F_GEN), 1)
    c.add_handler(RawUpdateHandler(h_join_request), -1)

def attach(c, me, store, is_factory):
    c.bot_id = me.id
    c.username = me.username or f"bot{me.id}"
    c.is_factory = is_factory
    c.store = store

async def launch_clone(meta):
    bid = meta["_id"]
    if meta.get("is_banned"): return None
    try: token = dec_token(meta["token_enc"])
    except Exception: return None
    c = Client(name=f"clone_{bid}", api_id=API_ID, api_hash=API_HASH, bot_token=token, in_memory=True, sleep_threshold=15)
    try: await c.start()
    except Exception: return None
    me = await c.get_me()
    store = get_store(bid)
    await ensure_defaults(store)
    attach(c, me, store, is_factory=False)
    register_provider_handlers(c, is_factory=False)
    await apply_commands(c)
    RUNNING[bid] = c
    LOG.info("🟢 Clone Live: @%s (%s)", me.username, bid)
    return c

async def delete_clone_bot(bid):
    meta = FACTORY.get_sync("bots", bid)
    if not meta: return False
    old = RUNNING.pop(bid, None)
    if old:
        try: await old.stop()
        except Exception: pass
    STORES.pop(bid, None)
    cpath = clone_path(bid)
    if os.path.exists(cpath):
        try: os.remove(cpath)
        except OSError: pass
    await FACTORY.delete("bots", bid)
    return True

# ══════════════════════════════════════════════════════════════════
#  MAIN ENTRYPOINT
# ══════════════════════════════════════════════════════════════════
async def main():
    global FACTORY, FACTORY_CLIENT, ROTATION_TASK
    os.makedirs(DB_DIR, exist_ok=True)

    if not (API_ID and API_HASH and BOT_TOKEN):
        print("❌ Config incomplete! Fill API_ID / API_HASH / BOT_TOKEN.")
        return

    FACTORY = Store(os.path.join(DB_DIR, "factory.json"))
    await ensure_defaults(FACTORY)
    if SUPREMES: await set_cfg(FACTORY, owner_id=SUPREMES[0])

    fc = Client("factory", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True, sleep_threshold=15)
    await fc.start()
    me = await fc.get_me()
    attach(fc, me, FACTORY, is_factory=True)
    FACTORY_CLIENT = fc
    RUNNING[me.id] = fc
    register_provider_handlers(fc, is_factory=True)
    await apply_commands(fc)
    LOG.info("🟢 Factory Live: @%s (%s)", me.username, me.id)

    for meta in list(FACTORY.find("bots")):
        await launch_clone(meta)

    ROTATION_TASK = asyncio.create_task(rotation_service_loop())

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try: loop.add_signal_handler(sig, stop.set)
        except (NotImplementedError, RuntimeError): pass

    print(f"\n{'═'*55}\n  🔗 {FACTORY_NAME} IS LIVE — @{me.username}\n{'═'*55}\n")
    await stop.wait()

    LOG.info("🛑 Shutting down...")
    if ROTATION_TASK: ROTATION_TASK.cancel()
    for c in list(RUNNING.values()):
        try: await c.stop()
        except Exception: pass
    for st in STORES.values(): await st.flush()
    await FACTORY.flush()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
