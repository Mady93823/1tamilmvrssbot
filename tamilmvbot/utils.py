import time
import math
import os

def hrb(value, digits=2, delim="", postfix=""):
    """Return a human-readable file size."""
    if value is None:
        return None
    if isinstance(value, str):
        value = float(value)
    if value < 1024:
        return f"{value:.{digits}f}" + delim + "B" + postfix
    elif value < 1048576:
        return f"{value / 1024:.{digits}f}" + delim + "KiB" + postfix
    elif value < 1073741824:
        return f"{value / 1048576:.{digits}f}" + delim + "MiB" + postfix
    else:
        return f"{value / 1073741824:.{digits}f}" + delim + "GiB" + postfix

def get_readable_time(seconds: int) -> str:
    """Return a human-readable time string from seconds."""
    result = ""
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f"{days}d "
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f"{hours}h "
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f"{minutes}m "
    seconds = int(seconds)
    result += f"{seconds}s"
    return result

def progress_bar_str(percentage: float) -> str:
    """Return a progress bar string."""
    p_used = int(percentage // 10)
    p_free = 10 - p_used
    return "⬢" * p_used + "⬡" * p_free

async def progress_callback(current, total, message, start_time, status_type="Uploading"):
    """
    Callback function for Pyrogram's progress updates.
    Updates the message every few seconds to avoid flood waits.
    """
    now = time.time()
    diff = now - start_time
    
    # Update every 5 seconds or when complete
    if (diff % 5 < 0.5) or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        elapsed_time = round(diff)
        eta = round((total - current) / speed) if speed > 0 else 0
        
        text = f"<b>{status_type}...</b>\n"
        text += f"[{progress_bar_str(percentage)}] {round(percentage, 2)}%\n\n"
        text += f"<b>⚡ Speed:</b> {hrb(speed)}/s\n"
        text += f"<b>✅ Done:</b> {hrb(current)} / {hrb(total)}\n"
        text += f"<b>⏳ ETA:</b> {get_readable_time(eta)}\n"
        text += f"<b>🕒 Elapsed:</b> {get_readable_time(elapsed_time)}"
        
        try:
            await message.edit(text)
        except Exception as e:
            # Ignore specific errors like "Message Not Modified"
            pass
