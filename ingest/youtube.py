"""
Fetches all talk videos from configured YouTube channels,
extracts transcripts (captions first, Whisper fallback),
and saves each as a JSON file in data/raw/youtube/.
"""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List

from tqdm import tqdm
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import YOUTUBE_CHANNELS, MUSIC_FILTER_KEYWORDS, RAW_YOUTUBE_DIR

# yt-dlp may be installed in a user bin not on PATH
YT_DLP = shutil.which("yt-dlp") or "/Users/rishi/Library/Python/3.9/bin/yt-dlp"


def is_music_video(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in MUSIC_FILTER_KEYWORDS)


def get_channel_videos(channel_url: str) -> List[dict]:
    """Use yt-dlp to list all videos in a channel without downloading."""
    print(f"\nFetching video list from: {channel_url}")
    result = subprocess.run(
        [
            YT_DLP,
            "--flat-playlist",
            "--print", "%(id)s\t%(title)s\t%(duration)s",
            "--no-warnings",
            channel_url,
        ],
        capture_output=True,
        text=True,
    )
    videos = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            video_id = parts[0].strip()
            title = parts[1].strip()
            duration = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
            if not is_music_video(title):
                videos.append({"id": video_id, "title": title, "duration": duration, "channel": channel_url})
    print(f"  Found {len(videos)} talk videos (music filtered out)")
    return videos


def get_transcript_via_api(video_id: str) -> Optional[str]:
    """Try to get transcript from YouTube's caption system."""
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        return " ".join(snippet.text for snippet in transcript)
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
        return None
    except Exception:
        return None


def get_transcript_via_whisper(video_id: str) -> Optional[str]:
    """Download audio and transcribe with Whisper."""
    try:
        import whisper
        audio_path = RAW_YOUTUBE_DIR / f"{video_id}.m4a"

        # Download audio only
        subprocess.run(
            [YT_DLP, "-f", "140", "-o", str(audio_path), f"https://www.youtube.com/watch?v={video_id}"],
            capture_output=True,
            check=True,
        )

        model = whisper.load_model("base")
        result = model.transcribe(str(audio_path))
        audio_path.unlink(missing_ok=True)  # delete audio after transcribing
        return result["text"]
    except Exception as e:
        print(f"  Whisper failed for {video_id}: {e}")
        return None


def ingest_channels(use_whisper_fallback: bool = True) -> int:
    RAW_YOUTUBE_DIR.mkdir(parents=True, exist_ok=True)

    all_videos = []
    for channel_url in YOUTUBE_CHANNELS:
        all_videos.extend(get_channel_videos(channel_url))

    print(f"\nTotal talk videos to process: {len(all_videos)}")
    saved = 0
    whisper_count = 0

    for video in tqdm(all_videos, desc="Ingesting transcripts"):
        out_path = RAW_YOUTUBE_DIR / f"{video['id']}.json"
        if out_path.exists():
            saved += 1
            continue

        transcript = get_transcript_via_api(video["id"])
        source = "youtube_captions"

        if not transcript and use_whisper_fallback:
            transcript = get_transcript_via_whisper(video["id"])
            source = "whisper"
            whisper_count += 1
            time.sleep(1)  # be polite to YouTube

        if not transcript:
            continue

        doc = {
            "id": video["id"],
            "title": video["title"],
            "channel": video["channel"],
            "url": f"https://www.youtube.com/watch?v={video['id']}",
            "duration_seconds": video["duration"],
            "source": source,
            "text": transcript,
        }
        out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
        saved += 1

    print(f"\nDone. {saved} transcripts saved ({whisper_count} via Whisper).")
    return saved


if __name__ == "__main__":
    ingest_channels()
