# 1TamilMV RSS & Leecher Bot v2.0

A powerful Telegram bot that scrapes **1TamilMV**, lists the latest movies, and offers **Auto-Download & Upload** functionality using qBittorrent and Tailscale.

## 🚀 Features

*   **Scraping**: Fetches the latest 15 movies from 1TamilMV.
*   **Magnet Links**: Retrieves magnet links and torrent files directly.
*   **Auto-Leech**:
    *   Downloads torrents on your VPS using `qBittorrent`.
    *   Uploads files to Telegram using `Pyrogram`.
    *   Shows **Real-time Progress Bars** for downloading and uploading.
*   **Bypass Restrictions**: Uses **Tailscale Funnel** to expose the bot's Webhook without public IPs or open ports.

## 🛠 Prerequisites

*   **VPS** (Ubuntu/Debian recommended)
*   **Python 3.9+**
*   **Tailscale Account** (for Funnel)
*   **Telegram API ID & Hash** (from [my.telegram.org](https://my.telegram.org))

## 📦 Installation

### 1. VPS Setup
Run the included setup script to install qBittorrent and Tailscale:
```bash
chmod +x setup_vps.sh
./setup_vps.sh
```

### 2. Clone & Install Dependencies
```bash
git clone https://github.com/Mady93823/1tamilmvrssbot.git
cd 1tamilmvrssbot
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file based on the example below:

```properties
# Telegram Bot Token (from @BotFather)
TOKEN=your_bot_token

# Webhook URL (from Tailscale Funnel)
WEBHOOK_URL=https://your-node.tailnet.ts.net
PORT=3000

# 1TamilMV Domain (Optional override)
TAMILMV_URL=https://www.1tamilmv.do

# Pyrogram Creds (for Uploading)
API_ID=your_api_id
API_HASH=your_api_hash

# Download Configs
MAX_DOWNLOAD_SIZE=2147483648  # 2GB
QBIT_HOST=localhost
QBIT_PORT=8080
QBIT_USER=admin
QBIT_PASS=adminadmin
```

## 🏃‍♂️ Usage

Run the bot:
```bash
python -m tamilmvbot.angel
```

### Commands
*   `/start` - Check if bot is alive.
*   `/view` - View latest movies and access download options.

## 🔗 Credits
*   **Developer**: [SudoR2spr](https://github.com/SudoR2spr)
*   **Modifications**: [Mady93823](https://github.com/Mady93823)
