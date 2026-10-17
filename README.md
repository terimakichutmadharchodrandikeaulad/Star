# 🔗 Telegram Link Provider Bot System

Production-ready, asynchronous, highly scalable **Telegram Link Provider Bot** built with **Python 3.11+**, **Pyrogram**, **TgCrypto**, and an ultra-fast **JSON Database Engine**.

---

## ✨ Features

- 📢 **Easy Channel Selection Workflow (`/newlink`)**:
  - Forward a message from your target channel.
  - Send the channel public username (`@channelname`), URL (`https://t.me/channelname`), or channel ID (`-100...`).
  - Select from previously saved verified channels in **My Channels**.
- 🎯 **Three Distinct Delivery Link Modes**:
  1. **🌐 Public Link**: Delivers the channel's static public URL (`https://t.me/username`).
  2. **🔒 Private Invite Link**: Generates a Telegram invite link (`creates_join_request=False`) that auto-rotates every 5 minutes.
  3. **✅ Join Request Link**: Generates a join-request enabled invite link (`creates_join_request=True`) that auto-rotates every 5 minutes.
- 🔄 **Automatic 5-Minute Link Rotation Service**:
  - Background rotation service runs every 300 seconds (`LINK_ROTATION_INTERVAL = 300`).
  - Generates replacement invite links before expiration.
  - Revokes previous bot-generated invite links via `revokeChatInviteLink`.
  - Persists rotation lifecycle timestamps (`last_rotation_at`, `next_rotation_at`) across VPS restarts.
- 🔐 **Admin Isolation & Role-Based Access**:
  - **Superadmin (Supreme)**: Global oversight, clone management, database health, global broadcast (`/broadcast all`).
  - **Administrator**: Manage owned provider links, channels, analytics, enable/disable links, and role permissions.
  - Strict authorization checks on all commands and inline callbacks.
- 📊 **Comprehensive Analytics & Statistics (`/stats`, `/mylinks`)**:
  - Provider link total visits, unique visitors, repeat visitors, successful deliveries, and failed deliveries.
  - Detailed link-level, admin-level, and superadmin global analytics.
- 🏭 **Bot Cloning Engine (`/clone`)**:
  - Clone isolated Link Provider Bots instantly via `@BotFather` token.
  - Bot tokens are encrypted using **Fernet** cryptography before database storage.
- 🔐 **Force Subscribe Integration (`/setfs`)**:
  - Supports Public Channels (membership verification) and Private Channels (join request verification).
- 🧾 **Audit Logging & Activity Tracking**:
  - Configure log channel ID (`/admin` → Log Channel) to receive live operational logs.

---

## 🛠️ Configuration & Installation

### Environment Variables / `.env` Setup

Copy `.env.example` to `.env` or set environment variables:

```bash
cp .env.example .env
```

| Variable | Description |
| :--- | :--- |
| `API_ID` | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | Telegram API Hash from [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | Main Factory Bot Token from [@BotFather](https://t.me/BotFather) |
| `SUPREME_IDS` | Comma-separated Telegram User IDs for Supreme Administrators |
| `LOG_CHANNEL_ID` | Developer log channel ID (optional, 0 = disabled) |
| `LINK_ROTATION_INTERVAL` | Rotation interval in seconds (default: `300` = 5 minutes) |
| `FACTORY_NAME` | Custom name for your Link Provider Factory |

---

## 🤖 BotFather & Channel Permissions Setup

1. Create your main bot with [@BotFather](https://t.me/BotFather) (`/newbot`).
2. Add your bot as an **Administrator** in your target channels.
3. Grant permissions:
   - **Add Members** / **Invite Users via Link**
   - **Manage Join Requests** (for Join Request link mode)

---

## 🚀 Commands

| Command | Description |
| :--- | :--- |
| `/start` | Open provider link or view welcome menu |
| `/help` | View help instructions and command usage |
| `/refer` | Generate referral link & view referral stats |
| `/admin` | Open interactive Admin Dashboard |
| `/newlink` | Start new provider link creation flow |
| `/mylinks` | View, manage, enable/disable, or delete provider links |
| `/mychannels` | View, add, and revalidate target channels |
| `/stats` | View link and administrator analytics |
| `/rotation` | Inspect active 5-minute invite link rotation status |
| `/cancel` | Cancel active conversation or input state |
| `/clone` | Create your own cloned Link Provider Bot |
| `/supreme` | Supreme control panel (Superadmin only) |
| `/botlist` | List all cloned instances (Superadmin only) |
| `/db` | Database health and statistics (Superadmin only) |
| `/restart` | Gracefully restart clones (Superadmin only) |

---

## 💻 Local Testing & Running

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Unit Tests:**
   ```bash
   python3 -m unittest discover
   ```

3. **Start Bot:**
   ```bash
   python3 app.py
   # or
   python3 main.py
   ```

---

## 🌐 VPS Deployment Guide (Ubuntu / Debian)

```bash
# Update system & install required packages
sudo apt update && sudo apt install -y python3 python3-pip git screen

# Clone repository & navigate
git clone <repo_url>
cd link-provider-bot

# Install requirements
pip3 install -r requirements.txt

# Run inside a detached screen session
screen -S linkbot
python3 app.py
```

---

## 📜 License

Distributed under the MIT License.
