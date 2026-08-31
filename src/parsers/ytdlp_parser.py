"""
yt-dlp 通用解析器 —— 用于处理 Instagram、TikTok、YouTube、Twitter/X、Facebook 等国外平台。
通过调用本地安装的 yt-dlp 可执行文件获取无水印视频/音频直链。
"""
import os
import re
import json
import shutil
import subprocess
from urllib.parse import urlparse

from src.parsers.base_parser import BaseParser
from src.parser_factory import register_parser
from configs.logging_config import get_logger

logger = get_logger(__name__)


YTDLP_PLATFORMS = [
    "Instagram", "TikTok", "YouTube", "Twitter/X", "Facebook", "Reddit",
    "Pinterest", "Vimeo", "Twitch", "SoundCloud", "Spotify", "LinkedIn",
    "Threads", "Tumblr", "Dailymotion", "VK", "OK.ru", "Snapchat", "CapCut"
]


@register_parser(*YTDLP_PLATFORMS)
class YtDlpParser(BaseParser):
    """使用 yt-dlp 提取国外平台的视频与图信息。"""

    def __init__(self, real_url):
        super().__init__(real_url)
        self._info = None

    # ------------ 内部工具 ------------
    def _get_ytdlp_path(self):
        return shutil.which("yt-dlp") or os.environ.get("YT_DLP_PATH", "yt-dlp")

    def _extract_info(self):
        if self._info is not None:
            return self._info
        ytdlp = self._get_ytdlp_path()
        cmd = [
            ytdlp,
            "--no-warnings",
            "--dump-json",
            "--no-playlist",
            "--geo-bypass",
            "--no-check-certificates",
            "--quiet",
            self.real_url,
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                logger.error(f"yt-dlp failed: {result.stderr[:500]}")
                self._info = {}
                return self._info
            # yt-dlp 可能输出多行 JSON（播放列表场景），取第一行即可
            line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
            self._info = json.loads(line) if line else {}
        except FileNotFoundError:
            logger.error("yt-dlp 未安装，请先 pip install yt-dlp 或下载可执行文件")
            self._info = {}
        except Exception as e:
            logger.exception(f"yt-dlp extract error: {e}")
            self._info = {}
        return self._info

    # ------------ 统一接口 ------------
    def get_title_content(self):
        info = self._extract_info()
        return info.get("title") or info.get("description") or ""

    def get_cover_photo_url(self):
        info = self._extract_info()
        return info.get("thumbnail")

    def get_author_info(self):
        info = self._extract_info()
        uploader = info.get("uploader") or info.get("channel") or info.get("creator")
        avatar = None
        channel_url = info.get("channel_url") or info.get("uploader_url")
        return {
            "name": uploader,
            "avatar": avatar,
            "uid": info.get("uploader_id") or info.get("channel_id"),
            "url": channel_url,
        }

    def get_real_video_url(self):
        info = self._extract_info()
        if not info:
            return None
        # 视频优先
        if info.get("_type") == "video" or info.get("url"):
            # 优先选最佳mp4
            fmts = info.get("formats") or []
            best = None
            for f in fmts:
                if f.get("vcodec") != "none" and (f.get("ext") in ("mp4", "webm")):
                    best = f
            if best:
                return best.get("url")
            return info.get("url")
        return None

    def get_video_list(self):
        url = self.get_real_video_url()
        return [url] if url else []

    def get_audio_url(self):
        info = self._extract_info()
        if not info:
            return None
        fmts = info.get("formats") or []
        # 纯音频
        for f in fmts:
            if f.get("vcodec") == "none" and f.get("acodec") != "none":
                return f.get("url")
        return None

    def get_image_list(self):
        """Instagram/Threads/Pinterest 等可能返回图片帖子。"""
        info = self._extract_info()
        images = []
        # 图集/多图：通常 entries 里每一项都是一个页面
        entries = info.get("entries") or []
        if entries:
            for e in entries:
                if isinstance(e, dict):
                    if e.get("thumbnail") and "http" in e.get("thumbnail", ""):
                        images.append(e["thumbnail"])
                    # 图片直链
                    for k in ("url", "original_url"):
                        if e.get(k) and str(e[k]).startswith("http"):
                            images.append(e[k])
        # 单张 thumbnail
        thumb = info.get("thumbnail")
        if thumb and thumb not in images:
            images.append(thumb)
        return images
