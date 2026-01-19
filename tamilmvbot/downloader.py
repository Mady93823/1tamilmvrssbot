import os
import time
import asyncio
import logging
import shutil
from qbittorrentapi import Client
from pyrogram import Client as PyrogramClient
from .utils import hrb, get_readable_time, progress_bar_str, progress_callback

# Configs
QBIT_HOST = os.getenv('QBIT_HOST', 'localhost')
QBIT_PORT = int(os.getenv('QBIT_PORT', 8080))
QBIT_USER = os.getenv('QBIT_USER', 'admin')
QBIT_PASS = os.getenv('QBIT_PASS', 'adminadmin')
MAX_SIZE = int(os.getenv('MAX_DOWNLOAD_SIZE', 2147483648))

logger = logging.getLogger(__name__)

# Connect to qBittorrent


def get_qb_client():
    try:
        qb = Client(
            host=QBIT_HOST,
            port=QBIT_PORT,
            username=QBIT_USER,
            password=QBIT_PASS,
            REQUESTS_ARGS={'timeout': (30, 60)},
            HTTPADAPTER_ARGS={
                "pool_maxsize": 500,
                "max_retries": 10,
                "pool_block": True,
            }
        )
        qb.auth_log_in()
        return qb
    except Exception as e:
        logger.exception(f"Failed to connect to qBittorrent: {e}")
        return None


async def download_and_upload(
        magnet_link,
        bot_msg,
        app: PyrogramClient,
        chat_id):
    """
    1. Add magnet to qBit.
    2. Monitor download.
    3. Upload files < MAX_SIZE.
    4. Delete torrent & files.
    """
    qb = get_qb_client()
    if not qb:
        await app.edit_message_text(chat_id, bot_msg.message_id, "❌ Failed to connect to qBittorrent server.")
        return

    # Add torrent
    try:
        torrents = qb.torrents_add(urls=magnet_link)
        # Wait a bit for metadata
        await asyncio.sleep(2)
        # Find the torrent info. Since we just added it, it's likely the latest one or we need the hash.
        # qbittorrentapi doesn't return the hash directly on add for magnets sometimes immediately.
        # We can list recent torrents.
        recent_torrents = qb.torrents_info(
            sort='added_on', reverse=True, limit=1)
        if not recent_torrents:
            await app.edit_message_text(chat_id, bot_msg.message_id, "❌ Failed to add torrent.")
            return

        info = recent_torrents[0]
        torrent_hash = info.hash

        # Monitor Download
        start_time = time.time()
        while True:
            info = qb.torrents_info(torrent_hashes=torrent_hash)[0]
            state = info.state

            if state in ['metaDL', 'downloading', 'stalledDL', 'queuedDL']:
                # Update Progress
                progress = info.progress * 100
                dl_speed = hrb(info.dlspeed)
                eta = get_readable_time(
                    info.eta) if info.eta < 8640000 else "∞"
                size_done = hrb(info.downloaded)
                size_total = hrb(info.total_size)

                text = f"<b>📥 Downloading...</b>\n"
                text += f"[{progress_bar_str(progress)}] {round(progress, 2)}%\n\n"
                text += f"<b>⚡ Speed:</b> {dl_speed}/s\n"
                text += f"<b>💾 Size:</b> {size_done} / {size_total}\n"
                text += f"<b>⏳ ETA:</b> {eta}\n"

                # Update every 5 seconds to avoid flooding
                if time.time() - start_time > 5:
                    try:
                        await app.edit_message_text(chat_id, bot_msg.message_id, text)
                        start_time = time.time()
                    except BaseException:
                        pass

                await asyncio.sleep(3)

            elif state in ['uploading', 'stalledUP', 'queuedUP', 'checkingUP', 'pausedUP']:
                # Completed
                await app.edit_message_text(chat_id, bot_msg.message_id, "<b>✅ Download Completed. Processing files...</b>")
                break

            elif state in ['error', 'missingFiles']:
                await app.edit_message_text(chat_id, bot_msg.message_id, "❌ Download Failed on Server.")
                qb.torrents_delete(
                    torrent_hashes=torrent_hash,
                    delete_files=True)
                return

            else:
                await asyncio.sleep(2)

        # Process Files
        save_path = info.content_path
        files_to_upload = []

        # If content_path is a directory, walk it
        if os.path.isdir(save_path):
            for root, dirs, files in os.walk(save_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.getsize(file_path) <= MAX_SIZE:
                        files_to_upload.append(file_path)
        else:
            # Single file
            if os.path.getsize(save_path) <= MAX_SIZE:
                files_to_upload.append(save_path)

        if not files_to_upload:
            await app.edit_message_text(chat_id, bot_msg.message_id, f"❌ No files found smaller than {hrb(MAX_SIZE)}.")
            qb.torrents_delete(torrent_hashes=torrent_hash, delete_files=True)
            return

        # Upload Files
        count = 1
        for f_path in files_to_upload:
            filename = os.path.basename(f_path)
            await app.edit_message_text(chat_id, bot_msg.message_id, f"<b>📤 Uploading file {count}/{len(files_to_upload)}...</b>\n<code>{filename}</code>")

            start_up = time.time()
            try:
                # Generate thumbnail if video? ( Skipping for now to keep
                # simple )
                await app.send_document(
                    chat_id=chat_id,
                    document=f_path,
                    caption=f"<code>{filename}</code>",
                    progress=progress_callback,
                    progress_args=(app, chat_id, bot_msg.message_id, start_up, f"📤 Uploading {count}/{len(files_to_upload)}")
                )
                count += 1
            except Exception as e:
                logger.error(f"Upload failed: {e}")
                await app.send_message(chat_id, f"❌ Failed to upload {filename}: {e}")

        await app.edit_message_text(chat_id, bot_msg.message_id, "<b>✅ All valid files uploaded!</b>")

        # Cleanup
        qb.torrents_delete(torrent_hashes=torrent_hash, delete_files=True)

    except Exception as e:
        logger.error(f"Downloader error: {e}")
        await app.edit_message_text(chat_id, bot_msg.message_id, f"❌ An error occurred: {e}")
