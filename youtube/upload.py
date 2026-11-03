"""GitHub Actions se YouTube upload.

Har video ke saath same naam ki .json file:
  youtube/videos/percentage.mp4
  youtube/videos/percentage.json  -> {"title", "description", "tags", "privacy", "publish_at"}

Usage: python youtube/upload.py video1.mp4 [video2.mp4 ...]
Env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
"""
import json
import os
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

LOG = Path(__file__).parent / "uploaded.json"


def youtube():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("youtube", "v3", credentials=creds)


def upload(yt, video: Path):
    meta_file = video.with_suffix(".json")
    meta = json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.exists() else {}

    status = {"privacyStatus": meta.get("privacy", "private"), "selfDeclaredMadeForKids": False}
    if meta.get("publish_at"):  # e.g. "2026-11-10T06:00:00Z" -> scheduled
        status["privacyStatus"] = "private"
        status["publishAt"] = meta["publish_at"]

    body = {
        "snippet": {
            "title": meta.get("title", video.stem)[:100],
            "description": meta.get("description", ""),
            "tags": meta.get("tags", []),
            "categoryId": str(meta.get("category_id", 27)),  # 27 = Education
            "defaultLanguage": meta.get("lang", "hi"),
        },
        "status": status,
    }
    req = yt.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(str(video), chunksize=8 * 1024 * 1024, resumable=True),
    )
    resp = None
    while resp is None:
        prog, resp = req.next_chunk()
        if prog:
            print(f"  {video.name}: {int(prog.progress() * 100)}%")
    return resp["id"]


def main():
    done = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else {}
    yt = youtube()
    for arg in sys.argv[1:]:
        video = Path(arg)
        key = video.as_posix()
        if key in done or not video.exists():
            print(f"skip {key}")
            continue
        vid = upload(yt, video)
        done[key] = vid
        print(f"OK {key} -> https://youtu.be/{vid}")
        LOG.write_text(json.dumps(done, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
