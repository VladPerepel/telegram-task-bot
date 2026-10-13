import os
import re
import asyncio
import logging
from typing import List, Dict, Any, Optional

import static_ffmpeg
static_ffmpeg.add_paths()

import yt_dlp

logger = logging.getLogger(__name__)

DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)


def format_duration(seconds: Optional[float]) -> str:
    if not seconds:
        return "0:00"
    seconds = int(seconds)
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins}:{secs:02d}"


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name)[:80]


async def search_tracks(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Searches tracks across SoundCloud using yt-dlp."""
    def _search():
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Search for more items to filter out very short previews if full tracks exist
            search_query = f"scsearch{limit * 2}:{query}"
            info = ydl.extract_info(search_query, download=False)
            entries = info.get("entries", [])
            
            tracks = []
            for e in entries:
                if not e:
                    continue
                track_id = str(e.get("id"))
                title = e.get("title", "Без названия")
                duration = e.get("duration") or 0
                uploader = e.get("uploader") or "Исполнитель"
                url = e.get("url") or e.get("webpage_url")

                # Prefer tracks that are reasonably long (> 45s) unless nothing else found
                tracks.append({
                    "id": track_id,
                    "title": title,
                    "uploader": uploader,
                    "duration": duration,
                    "duration_str": format_duration(duration),
                    "url": url,
                })
            
            # Sort to prioritize non-30s previews
            full_tracks = [t for t in tracks if t["duration"] > 45]
            if len(full_tracks) >= 3:
                return full_tracks[:limit]
            return tracks[:limit]

    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _search)
    except Exception as exc:
        logger.error(f"Error during music search: {exc}")
        return []


async def download_track(track_id: str, track_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Downloads a track by track_id or url, converts it to MP3 and returns file info."""
    def _download():
        target_url = track_url if track_url else f"https://api.soundcloud.com/tracks/{track_id}"
        out_template = os.path.join(DOWNLOADS_DIR, f"{track_id}_%(id)s.%(ext)s")
        
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=True)
            title = info.get("title", "Unknown Track")
            uploader = info.get("uploader", "Unknown Artist")
            duration = int(info.get("duration", 0))
            
            # Locate the generated mp3 file
            expected_mp3 = os.path.join(DOWNLOADS_DIR, f"{track_id}_{info.get('id', track_id)}.mp3")
            if os.path.exists(expected_mp3):
                return {
                    "file_path": expected_mp3,
                    "title": title,
                    "performer": uploader,
                    "duration": duration,
                }
            
            # Fallback search in downloads dir for recently created mp3 matching track_id
            for f in os.listdir(DOWNLOADS_DIR):
                if f.startswith(str(track_id)) and f.endswith(".mp3"):
                    return {
                        "file_path": os.path.join(DOWNLOADS_DIR, f),
                        "title": title,
                        "performer": uploader,
                        "duration": duration,
                    }
            return None

    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _download)
    except Exception as exc:
        logger.error(f"Error downloading track {track_id}: {exc}")
        return None
