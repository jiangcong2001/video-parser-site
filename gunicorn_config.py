"""Gunicorn 配置文件，兼容各云平台默认启动。"""
import os
import multiprocessing

bind = f"0.0.0.0:{os.getenv('PORT', '8051')}"
workers = int(os.getenv("WEB_CONCURRENCY", 1))
threads = int(os.getenv("PYTHON_MAX_THREADS", 4))
timeout = 120
keepalive = 5
worker_class = "gthread"
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
