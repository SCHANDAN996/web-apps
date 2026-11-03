"""Private Study Station Telegram request gateway.

Supported commands (GitHub issue comment or workflow_dispatch):
/telegram help
/telegram status
/telegram plan
/telegram sample

Uses EXISTING TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID secrets.
Only allowlisted content can be sent. Never reads .env, credentials, or arbitrary paths.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")


def api_send(method, values, file_path=None):
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("Existing TELEGRAM_BOT_TOKEN / TELEGRAM_CHANNEL_ID GitHub secrets unavailable")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    if file_path is None:
        data = urllib.parse.urlencode({"chat_id": CHAT_ID, **values}).encode()
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as r:
            response = r.read().decode(errors="replace")
    else:
        # Subprocess argv, not shell; no credentials in output on successful calls.
        args = ["curl", "--fail-with-body", "--silent", "--show-error", "--retry", "2",
                "--max-time", "120", "-F", f"chat_id={CHAT_ID}"]
        for key, value in values.items():
            args.extend(["-F", f"{key}={value}"])
        upload_type = "video" if method == "sendVideo" else "document"
        args.extend(["-F", f"{upload_type}=@{file_path}", url])
        proc = subprocess.run(args, capture_output=True, text=True, timeout=140)
        if proc.returncode != 0:
            # Avoid printing token from curl URL or raw Telegram response.
            raise RuntimeError(f"Telegram {method} request failed (curl exit {proc.returncode})")
        response = proc.stdout
    if '"ok":true' not in response.replace(" ", ""):
        raise RuntimeError(f"Telegram {method} did not confirm successful delivery")


def send_text(message):
    api_send("sendMessage", {"text": message[:3800]})


def generate_video():
    # Requires edge-tts, ffmpeg/ffprobe (installed by dedicated GitHub workflow).
    import voice_demo
    output = ROOT / "study_station" / "sample-voice.mp3"
    subprocess.run([sys.executable, str(ROOT / "study_station" / "voice_demo.py"),
                    "--output", str(output)], check=True, timeout=120)
    probe = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(output)],
        text=True).strip()
    duration = float(probe)
    if duration < 3 or duration > 120:
        raise RuntimeError("Unexpected narration duration")
    video = ROOT / "study_station" / "sample-video.mp4"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", f"color=c=0x111827:s=720x1280:r=25:d={duration}",
        "-i", str(output),
        "-vf", "drawtext=text='STUDY STATION':fontcolor=white:fontsize=52:x=(w-text_w)/2:y=350,"
               "drawtext=text='HINDI GK VOICE SAMPLE':fontcolor=white:fontsize=28:x=(w-text_w)/2:y=450",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
        str(video)
    ], check=True, timeout=240)
    if video.stat().st_size < 10_000:
        raise RuntimeError("Generated MP4 is unexpectedly small")
    return video


def process(message):
    normalized = message.strip()
    if normalized.startswith("/telegram"):
        normalized = normalized[len("/telegram"):].strip()
    cmd = normalized.lower()
    if cmd in ("help", ""):
        send_text("Study Station Telegram Request Gateway\nCommands: /telegram status, /telegram plan, /telegram sample, /telegram help")
    elif cmd == "status":
        send_text("Study Station status\nRepository: SCHANDAN996/web-apps\nModules: website, Flask backend, Android, Telegram, video automation.\nThis is a repository snapshot, not a live server health check.")
    elif cmd == "plan":
        path = ROOT / "study_station" / "MASTER_PLAN.md"
        if not path.is_file():
            raise RuntimeError("MASTER_PLAN.md not found in checked-out branch")
        api_send("sendDocument", {"caption": "Study Station master plan (repository snapshot)"}, path)
    elif cmd == "sample":
        path = generate_video()
        api_send("sendVideo", {"caption": "Study Station Hindi voice sample — preview only, not uploaded to YouTube"}, path)
    else:
        raise ValueError("Unknown request. Use /telegram help; allowed: status, plan, sample")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", required=True)
    args = parser.parse_args()
    try:
        process(args.message)
    except (ValueError, RuntimeError, subprocess.SubprocessError, OSError) as error:
        print(f"Request failed: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(1)
