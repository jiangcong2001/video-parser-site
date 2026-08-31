"""
下载保存接口：将解析出的视频/图片/音频保存到服务器本地 downloads/ 目录。
"""
import os
import re
import time
import mimetypes
from urllib.parse import urlparse

import requests
from flask import Blueprint, request, jsonify, send_from_directory, abort
from configs.logging_config import get_logger
from src.api.response import make_response

logger = get_logger(__name__)
bp = Blueprint("download", __name__)

DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "downloads"))
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 安全文件名
_INVALID = re.compile(r'[\\/:*?"<>|\r\n\t]+')


def _safe_name(name: str, default: str = "media") -> str:
    name = _INVALID.sub("_", (name or "").strip())
    name = name[:80] or default
    return name


def _guess_ext(url: str, content_type: str = "") -> str:
    # 从URL里找扩展名
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    if ext and len(ext) <= 6 and ext not in (".php", ".html", ".htm", ".jsp", ".aspx", ".do"):
        return ext
    # 从content-type推断
    if content_type:
        guess = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if guess:
            return guess
    return ".mp4"


@bp.route("/save", methods=["POST"])
def save():
    """
    将媒体URL下载到服务器本地
    入参: { url: str, title?: str, type?: 'video'|'image'|'audio' }
    """
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url or not url.startswith("http"):
        return make_response(400, "缺少有效的媒体URL", None, False, "INVALID_URL"), 400

    title = _safe_name(data.get("title", ""), default="download")
    media_type = data.get("type", "video")
    ts = time.strftime("%Y%m%d_%H%M%S")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Referer": urlparse(url)._replace(path="/", params="", query="", fragment="").geturl(),
        }
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
            "download_url": f"/download/file/{filename}",
        }, True), 200
    except Exception as e:
        logger.exception(f"Save failed: {e}")
        return make_response(500, f"保存失败：{e}", None, False, "SAVE_ERROR"), 500


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
        for f in sorted(os.listdir(DOWNLOAD_DIR), reverse=True)[:50]:
            fp = os.path.join(DOWNLOAD_DIR, f)
            if os.path.isfile(fp):
                items.append({
                    "filename": f,
                    "size": os.path.getsize(fp),
                    "mtime": os.path.getmtime(fp),
                    "url": f"/download/file/{f}",
                })
        return make_response(200, "ok", {"files": items}, True), 200
    except Exception as e:
        return make_response(500, str(e), None, False), 500
