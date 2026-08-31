"""
Vercel Serverless 入口
Vercel Python Runtime 会把此文件作为一个 Serverless Function 挂载。
通过把所有请求转发给 Flask app 实现整站部署。
"""
import os
import sys

# 把项目根目录加入 sys.path，以便能 import app.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Vercel 运行时为只读文件系统，强制把下载目录改到 /tmp
os.environ.setdefault("DOWNLOAD_DIR", "/tmp/video_parser_downloads")

from app import app  # noqa: E402

# Vercel Python Runtime 约定导出一个名为 `app` 的 WSGI callable
# 我们的 Flask 实例正好叫 app，可以直接复用
