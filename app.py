from __future__ import annotations

import json
import queue
import re
import subprocess
import threading
from pathlib import Path
from flask import Flask, render_template, request, Response, stream_with_context
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

H264_CODECS = {"h264", "avc1", "avc", "libx264"}

DOWNLOAD_DIR = Path.home() / "Downloads" / "Reels"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def extract_urls(text: str) -> list[str]:
    seen, out = set(), []
    for url in URL_PATTERN.findall(text or ""):
        url = url.rstrip(").,;\"'")
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def probe_video_codec(path: Path) -> str:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name", "-of", "default=nw=1:nk=1",
             str(path)],
            capture_output=True, text=True, timeout=15,
        )
        return out.stdout.strip().lower()
    except Exception:
        return ""


def transcode_to_h264(path: Path) -> Path:
    tmp = path.with_name(path.stem + ".h264.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(path),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart",
         str(tmp)],
        check=True, capture_output=True, timeout=600,
    )
    path.unlink(missing_ok=True)
    tmp.rename(path)
    return path


ALLOWED_BROWSERS = {"chrome", "safari", "firefox", "edge", "brave", "chromium", "opera", "vivaldi"}


def download_one(url: str, on_stage=None, browser: str | None = None) -> dict:
    opts = {
        "outtmpl": str(DOWNLOAD_DIR / "%(uploader)s_%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "format": "bv*[vcodec^=avc1][height>=1080]+ba/bv*[height>=1080]+ba/bv*+ba/b",
        "format_sort": ["res:1080", "vcodec:h264", "acodec:aac", "ext:mp4"],
        "merge_output_format": "mp4",
        "retries": 3,
        "concurrent_fragment_downloads": 4,
    }
    if browser and browser.lower() in ALLOWED_BROWSERS:
        opts["cookiesfrombrowser"] = (browser.lower(),)
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            final = Path(filename).with_suffix(".mp4")
            path = final if final.exists() else Path(filename)

        codec = probe_video_codec(path)
        transcoded = False
        if codec and codec not in H264_CODECS:
            if on_stage:
                on_stage("transcode")
            transcode_to_h264(path)
            transcoded = True

        return {
            "url": url,
            "ok": True,
            "filename": path.name,
            "path": str(path),
            "title": info.get("title") or info.get("description", "")[:80],
            "uploader": info.get("uploader", ""),
            "codec_original": codec or "unknown",
            "transcoded": transcoded,
        }
    except DownloadError as e:
        return {"url": url, "ok": False, "error": str(e).split("\n")[0]}
    except subprocess.CalledProcessError as e:
        msg = (e.stderr or b"").decode("utf-8", errors="ignore").strip().split("\n")[-1]
        return {"url": url, "ok": False, "error": f"ffmpeg: {msg or 'transcode failed'}"}
    except Exception as e:
        return {"url": url, "ok": False, "error": f"{type(e).__name__}: {e}"}


@app.route("/")
def index():
    return render_template("index.html", download_dir=str(DOWNLOAD_DIR))


@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json(silent=True) or {}
    urls = data.get("urls") or extract_urls(data.get("text", ""))
    browser = (data.get("browser") or "").strip().lower() or None
    if not urls:
        return {"error": "URL을 찾을 수 없습니다."}, 400

    def generate():
        yield json.dumps({"event": "start", "total": len(urls), "browser": browser}) + "\n"
        for idx, url in enumerate(urls, 1):
            q: queue.Queue = queue.Queue()
            holder: dict = {}

            def on_stage(stage, _idx=idx, _url=url):
                q.put({"event": "progress", "index": _idx, "url": _url, "stage": stage})

            def worker(_url=url):
                holder["result"] = download_one(_url, on_stage=on_stage, browser=browser)
                q.put(None)

            t = threading.Thread(target=worker, daemon=True)
            t.start()
            yield json.dumps({"event": "progress", "index": idx, "url": url, "stage": "download"}) + "\n"
            while True:
                item = q.get()
                if item is None:
                    break
                yield json.dumps(item) + "\n"
            t.join()
            result = holder.get("result", {"url": url, "ok": False, "error": "no result"})
            result["event"] = "result"
            result["index"] = idx
            yield json.dumps(result, ensure_ascii=False) + "\n"
        yield json.dumps({"event": "done"}) + "\n"

    return Response(stream_with_context(generate()), mimetype="application/x-ndjson")


if __name__ == "__main__":
    print(f"\n  📥 저장 위치: {DOWNLOAD_DIR}")
    print(f"  🌐 http://127.0.0.1:5000\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
