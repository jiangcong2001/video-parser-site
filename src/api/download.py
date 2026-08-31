"""
下载模块：
1. /save         —— 保存到服务器（本地/Docker可用，云环境用/tmp临时目录）
2. /fetch        —— 代理流式下载（云环境推荐，不占服务器磁盘，直接转发给浏览器）
3. /file/<name>  —— 下载已保存到服务器的文件
4. /list         —— 列出最近保存的文件
"""
import os
import re
import time
import mimetypes
from urllib.parse import urlparse

import requests
from flask import Blueprint, request, jsonify, send_from_directory, abort, Response, stream_with_context
from configs.logging_config import get_logger
from src.api.response import make_response

logger = get_logger(__name__)
bp = Blueprint("download", __name__)

# 云平台（Vercel/Render等）无持久化磁盘时使用 /tmp；本地/Docker 使用项目目录 downloads/
_DEFAULT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "downloads")
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", _DEFAULT_DIR)
# 如果默认目录不可写（典型如云平台只读文件系统），自动降级到 /tmp
if not os.access(os.path.dirname(DOWNLOAD_DIR) or ".", os.W_OK):
    DOWNLOAD_DIR = "/tmp/video_parser_downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

_INVALID = re.compile(r'[\\/:*?"<>|\r\n\t]+')


def _safe_name(name: str, default: str = "media") -> str:
    name = _INVALID.sub("_", (name or "").strip())
    name = name[:80] or default
    return name


def _guess_ext(url: str, content_type: str = "") -> str:
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    if ext and len(ext) <= 6 and ext not in (".php", ".html", ".htm", ".jsp", ".aspx", ".do"):
        return ext
    if content_type:
        guess = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if guess:
            return guess
    return ".mp4"


def _build_headers(url: str) -> dict:
    parsed = urlparse(url)
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Referer": f"{parsed.scheme}://{parsed.netloc}/",
    }


@bp.route("/save", methods=["POST"])
def save():
    """将媒体URL下载到服务器本地（云环境下载到/tmp临时目录，不持久化）"""
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url or not url.startswith("http"):
        return make_response(400, "缺少有效的媒体URL", None, False, "INVALID_URL"), 400

    title = _safe_name(data.get("title", ""), default="download")
    media_type = data.get("type", "video")
    ts = time.strftime("%Y%m%d_%H%M%S")

    try:
        headers = _build_headers(url)
        with requests.get(url, headers=headers, stream=True, timeout=60, allow_redirects=True) as resp:
            resp.raise_for_status()
            ctype = resp.headers.get("content-type", "")
            ext = _guess_ext(url, ctype)
            if media_type == "image" and ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".bmp"):
                ext = ".jpg"
            if media_type == "audio" and ext not in (".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac"):
                ext = ".mp3"
            filename = f"{ts}_{title}{ext}"
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
        size = os.path.getsize(filepath)
        logger.info(f"Saved media: {filename} ({size} bytes)")
        return make_response(200, "保存成功", {
            "filename": filename,
            "size": size,
            "download_url": f"/api/download/file/{filename}",
        }, True), 200
    except Exception as e:
        logger.exception(f"Save failed: {e}")
        return make_response(500, f"保存失败：{e}", None, False, "SAVE_ERROR"), 500


@bp.route("/fetch", methods=["GET"])
def fetch():
    """
    代理流式下载：服务器作为中转，直接将媒体流转发给浏览器。
    不占用服务器磁盘，适合云平台（Vercel/Render等）使用。
    用法：GET /api/download/fetch?url=<媒体URL>&filename=<文件名>&type=video
    """
    url = request.args.get("url", "")
    if not url.startswith("http"):
        return "无效URL", 400

    filename = _safe_name(request.args.get("filename", "download"), default="download")
    media_type = request.args.get("type", "video")
    ctype_hint = request.args.get("ct", "")

    # 推断扩展名与content-type
    sample_headers = _build_headers(url)
    try:
        head_resp = requests.head(url, headers=sample_headers, timeout=15, allow_redirects=True)
        ctype = head_resp.headers.get("content-type", "") or ctype_hint
        ext = _guess_ext(url, ctype)
        if media_type == "image" and ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".bmp"):
            ext = ".jpg"
        if media_type == "audio" and ext not in (".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac"):
            ext = ".mp3"
        if media_type == "video" and ext not in (".mp4", ".mov", ".webm", ".m3u8", ".flv", ".avi", ".mkv"):
            ext = ".mp4"
    except Exception:
        ctype = ctype_hint or {"video": "video/mp4", "image": "image/jpeg", "audio": "audio/mpeg"}.get(media_type, "application/octet-stream")
        ext = {"video": ".mp4", "image": ".jpg", "audio": ".mp3"}.get(media_type, ".bin")

    if not filename.endswith(ext):
        filename = filename + ext

    # 流式下载给浏览器
    def generate():
        try:
            with requests.get(url, headers=sample_headers, stream=True, timeout=120, allow_redirects=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        yield chunk
        except Exception as e:
            logger.exception(f"Proxy fetch failed: {e}")
            # 客户端已断开时无需处理
            pass

    resp_headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{requests.utils.quote(filename)}",
        "Content-Type": ctype or "application/octet-stream",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # 避免nginx缓冲
    }
    # 如果 HEAD 拿到了大小，透传
    try:
        if "content-length" in head_resp.headers:
            resp_headers["Content-Length"] = head_resp.headers["content-length"]
    except Exception:
        pass

    return Response(stream_with_context(generate()), headers=resp_headers)


@bp.route("/file/<path:filename>")
def file(filename):
    """提供已保存文件的下载"""
    safe_path = os.path.normpath(os.path.join(DOWNLOAD_DIR, filename))
    if not safe_path.startswith(DOWNLOAD_DIR):
        abort(403)
    if not os.path.exists(safe_path):
        abort(404)
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)


@bp.route("/list", methods=["GET"])
def list_files():
    """列出最近保存的文件"""
    try:
        items = []
        if os.path.isdir(DOWNLOAD_DIR):
            for f in sorted(os.listdir(DOWNLOAD_DIR), reverse=True)[:50]:
                fp = os.path.join(DOWNLOAD_DIR, f)
                if os.path.isfile(fp) and not f.startswith("."):
                    items.append({
                        "filename": f,
                        "size": os.path.getsize(fp),
                        "mtime": os.path.getmtime(fp),
                        "url": f"/api/download/file/{f}",
                    })
        return make_response(200, "ok", {"files": items, "dir": DOWNLOAD_DIR}, True), 200
    except Exception as e:
        return make_response(500, str(e), None, False), 500
